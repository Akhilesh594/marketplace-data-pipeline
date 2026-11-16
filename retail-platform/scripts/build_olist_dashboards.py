"""Create two Olist dashboards in an existing local Metabase instance.
Uses Python standard library only. Password is prompted, never written to disk.
Run with --plan to review SQL without logging in or changing anything.
All measures cover the full loaded dataset; no dashboard date filters are installed.
"""
import argparse
from decimal import Decimal
from getpass import getpass
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

PROJECT = os.environ["GCP_PROJECT_ID"]
SCHEMA = "olist_analytics"
MARKER = "[olist-dashboard-builder-v1]"
NOTE = ("Full loaded dataset. Sales = delivered-order item prices in BRL, excluding freight. "
        "Dates use order purchase date. Repeat rate = buyers with >=2 delivered orders / delivered-order buyers. "
        "No profit/margin: product costs unavailable. No date filters in this version.")

def table(name):
    return "`" + PROJECT + "." + SCHEMA + "." + name + "`"

def card(key, name, sql, display, position, dimension=None, metric=None, suffix=None, description=None):
    settings = {}
    if dimension:
        settings.update({"graph.dimensions": [dimension], "graph.metrics": [metric]})
    if display == "scalar":
        settings.update({"scalar.decimals": 2 if suffix else 0})
        if suffix:
            settings["scalar.suffix"] = suffix
    return dict(key=key, name=name, sql=sql, display=display, position=position,
                settings=settings, description=description or NOTE)

def specs():
    business, daily, fact = table("metrics_business_summary"), table("metrics_daily_sales"), table("fact_sales_history")
    product, store = table("dim_product"), table("dim_store")
    overview = [
        card("gross", "Delivered item sales (BRL)", "SELECT revenue_brl AS gross_item_sales_brl FROM " + business,
             "scalar", (0,0,6,4), suffix=" BRL"),
        card("orders", "Delivered orders", "SELECT order_count AS delivered_orders FROM " + business,
             "scalar", (0,6,6,4)),
        card("aov", "Average order value (BRL)", "SELECT average_order_value_brl FROM " + business,
             "scalar", (0,12,6,4), suffix=" BRL"),
        card("repeat", "Repeat buyer rate (%)", "SELECT 100 * repeat_customer_rate AS repeat_buyer_rate_pct FROM " + business,
             "scalar", (0,18,6,4), suffix="%"),
        card("monthly_sales", "Monthly delivered item sales (BRL)",
             "SELECT DATE_TRUNC(sales_date, MONTH) AS sales_month, SUM(revenue_brl) AS gross_item_sales_brl FROM " +
             daily + " GROUP BY 1 ORDER BY 1", "line", (4,0,12,8),
             "sales_month", "gross_item_sales_brl"),
        card("monthly_orders", "Monthly delivered orders",
             "SELECT DATE_TRUNC(sales_date, MONTH) AS sales_month, SUM(order_count) AS delivered_orders FROM " +
             daily + " GROUP BY 1 ORDER BY 1", "line", (4,12,12,8),
             "sales_month", "delivered_orders"),
    ]
    breakdown = [
        card("categories", "Top 10 categories by delivered item sales (BRL)",
             "SELECT COALESCE(p.category_name, 'unknown') AS category, SUM(f.item_price) AS gross_item_sales_brl FROM " +
             fact + " AS f LEFT JOIN " + product + " AS p USING (product_key) WHERE f.order_status = 'delivered' " +
             "GROUP BY 1 ORDER BY 2 DESC LIMIT 10", "bar", (0,0,12,8), "category", "gross_item_sales_brl"),
        card("states", "Top 10 seller states by delivered item sales (BRL)",
             "SELECT COALESCE(s.state, 'unknown') AS seller_state, SUM(f.item_price) AS gross_item_sales_brl FROM " +
             fact + " AS f LEFT JOIN " + store + " AS s USING (store_key) WHERE f.order_status = 'delivered' " +
             "GROUP BY 1 ORDER BY 2 DESC LIMIT 10", "bar", (0,12,12,8), "seller_state", "gross_item_sales_brl"),
        card("statuses", "Orders by status (all source orders)",
             "SELECT COALESCE(order_status, 'unknown') AS order_status, COUNT(*) AS order_count FROM " +
             table("stg_orders") + " GROUP BY 1 ORDER BY 2 DESC", "bar", (8,0,12,8),
             "order_status", "order_count",
             description="All source orders, including orders without items. Each staging order counted once; not delivered-only."),
        card("sellers", "Top 20 sellers - delivered sales and orders",
             "SELECT f.store_key AS seller_id, s.state AS seller_state, COUNT(DISTINCT f.order_id) AS delivered_orders, " +
             "SUM(f.item_price) AS gross_item_sales_brl FROM " + fact + " AS f LEFT JOIN " + store +
             " AS s USING (store_key) WHERE f.order_status = 'delivered' GROUP BY 1,2 ORDER BY 4 DESC LIMIT 20",
             "table", (8,12,12,8)),
    ]
    return [("Sales Overview", overview), ("Marketplace Breakdown", breakdown)]

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Client:
    def __init__(self, base):
        self.base, self.token = base.rstrip("/"), None
        self.opener = build_opener(NoRedirect())
    def call(self, method, path, payload=None):
        headers = {"Accept":"application/json", "Content-Type":"application/json"}
        if self.token:
            headers["X-Metabase-Session"] = self.token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(self.base + "/api" + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=180) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            # Do not echo response bodies, headers, or credentials.
            raise RuntimeError("Metabase HTTP " + str(exc.code) + " for " + method + " " + path +
                               ". Check the Metabase UI/server logs. No automatic retry was made.") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise RuntimeError("Connection/response failure for " + method + " " + path +
                               ". A write may already have succeeded; rerun to find marked objects.") from None
    def query(self, database, sql):
        result = self.call("POST", "/dataset", {
            "database":database, "type":"native", "native":{"query":sql, "template-tags":{}}})
        if result.get("status") != "completed":
            raise RuntimeError("BigQuery query did not complete: " + str(result.get("error", "See Metabase logs"))[:400])
        return result.get("data", {}).get("rows", [])

def rows(value):
    return value.get("data", []) if isinstance(value, dict) else value

def owned(items, name):
    found = [i for i in items if i.get("name") == name and MARKER in (i.get("description") or "")
             and not i.get("archived")]
    if len(found) > 1:
        raise RuntimeError("Multiple builder-owned objects named " + name + "; resolve duplicates in Metabase.")
    return found[0] if found else None

def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3001")
    parser.add_argument("--database-name", default="Olist Analytics")
    parser.add_argument("--database-id", type=int, help="Use the numeric Metabase connection ID instead of its name")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    groups = specs()
    if args.plan:
        for name, cards in groups:
            print("\nDASHBOARD: Olist - " + name)
            for item in cards:
                print("\n-- " + item["name"] + "\n" + item["sql"] + ";")
        return
    parsed = urlparse(args.url)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise RuntimeError("Use a local HTTP Metabase base URL, e.g. http://localhost:3001")
    client = Client(args.url)
    print("Use your METABASE account, not Airbyte or Google credentials.")
    email = input("Metabase email: ").strip()
    password = getpass("Metabase password (hidden): ")
    session = client.call("POST", "/session", {"username":email, "password":password})
    password = None
    client.token = session["id"]
    try:
        available = rows(client.call("GET", "/database"))
        if args.database_id is not None:
            databases = [d for d in available if d.get("id") == args.database_id]
        else:
            normalize = lambda value: " ".join(str(value).split()).casefold()
            databases = [d for d in available if normalize(d.get("name", "")) == normalize(args.database_name)]
        if len(databases) != 1:
            choices = ", ".join(str(d.get("id")) + ": " + str(d.get("name")) for d in available)
            raise RuntimeError("Expected one matching Metabase connection. Available connections: " + choices +
                               ". Select the correct BigQuery connection with --database-id <ID>.")
        database = databases[0]
        print("Selected connection " + str(database["id"]) + ": " + database["name"])
        if database.get("engine") != "bigquery-cloud-sdk":
            raise RuntimeError("Selected database is not the expected BigQuery driver.")
        dbid = database["id"]
        print("Checking queries through your existing BigQuery connection (normal BigQuery query usage applies)...")
        # Execute every proposed query before creating any cards or dashboards.
        for _, cards in groups:
            for item in cards:
                values = client.query(dbid, item["sql"])
                if not values:
                    raise RuntimeError("No rows returned for " + item["name"])
                print("  OK: " + item["name"])
        check = client.query(dbid,
            "SELECT b.revenue_brl, b.order_count, d.revenue_brl, d.order_count FROM " +
            table("metrics_business_summary") + " AS b CROSS JOIN (SELECT SUM(revenue_brl) AS revenue_brl, " +
            "SUM(order_count) AS order_count FROM " + table("metrics_daily_sales") + ") AS d")
        if len(check) != 1 or any(v is None for v in check[0]):
            raise RuntimeError("Reconciliation did not return one complete summary row.")
        a,b,c,d = check[0]
        if abs(Decimal(str(a)) - Decimal(str(c))) > Decimal("0.01") or int(b) != int(d):
            raise RuntimeError("Daily sales/order totals do not reconcile to business summary; stopped.")
        print("Daily sales and order totals reconcile.")
        all_cards = rows(client.call("GET", "/card"))
        all_dashboards = rows(client.call("GET", "/dashboard"))
        output = []
        for group, cards in groups:
            dashboard_name = "Olist - " + group
            dashboard = owned(all_dashboards, dashboard_name)
            if not dashboard:
                dashboard = client.call("POST", "/dashboard", {
                    "name":dashboard_name, "description":MARKER + " " + NOTE})
            dashboard_id = dashboard["id"]
            print("Preparing " + dashboard_name + " (ID " + str(dashboard_id) + ")")
            layout = {}
            for item in cards:
                name = "Olist | " + item["name"]
                old = owned(all_cards, name)
                payload = {"name":name, "description":MARKER + " " + item["description"],
                    "dataset_query":{"database":dbid, "type":"native",
                                     "native":{"query":item["sql"], "template-tags":{}}},
                    "display":item["display"], "visualization_settings":item["settings"]}
                if old:
                    # Reuse existing builder-owned questions; leave manual edits in place.
                    saved = old
                else:
                    saved = client.call("POST", "/card", payload)
                    all_cards.append(saved)
                layout[saved["id"]] = item["position"]
            current = client.call("GET", "/dashboard/" + str(dashboard_id))
            dashcards, placed = [], set()
            for dc in current.get("dashcards", []):
                keep = {k:dc[k] for k in ("id","card_id","row","col","size_x","size_y",
                        "dashboard_tab_id","parameter_mappings","visualization_settings","series","action_id")
                        if k in dc}
                if keep.get("series"):
                    keep["series"] = [{"id":s["id"]} for s in keep["series"]]
                if dc.get("card_id") in layout:
                    placed.add(dc["card_id"])
                dashcards.append(keep)
            # Preserve existing cards/layouts; append missing builder cards only.
            bottom = max((dc["row"] + dc["size_y"] for dc in dashcards), default=0)
            for n,(card_id,pos) in enumerate(layout.items(),1):
                if card_id in placed:
                    continue
                row,col,sx,sy = pos
                dashcards.append({"id":-n, "card_id":card_id, "row":row + bottom, "col":col,
                                  "size_x":sx, "size_y":sy, "parameter_mappings":[],
                                  "visualization_settings":{}})
            client.call("PUT", "/dashboard/" + str(dashboard_id), {"dashcards":dashcards})
            verified = client.call("GET", "/dashboard/" + str(dashboard_id))
            attached = {d.get("card_id") for d in verified.get("dashcards", [])}
            if not set(layout).issubset(attached):
                raise RuntimeError("Dashboard verification failed: not all questions were attached.")
            link = client.base + "/dashboard/" + str(dashboard_id)
            print("Dashboard ready: " + link)
            output.append({"name":dashboard_name,"url":link,"dashboard_id":dashboard_id})
        report = Path(__file__).resolve().with_name("olist_dashboard_links.json")
        report.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print("\nBoth dashboards verified. Links saved to " + str(report))
        print("Open the links to check chart appearance. No source tables were changed.")
    finally:
        if client.token:
            try:
                client.call("DELETE", "/session", {})
            except RuntimeError:
                pass
            client.token = None

if __name__ == "__main__":
    try:
        run()
    except (RuntimeError, KeyError) as exc:
        print("STOPPED: " + str(exc), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
        sys.exit(130)
