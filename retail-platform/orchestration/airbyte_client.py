"""Small client for the documented Airbyte public API; never logs credentials."""
import json
from http.client import HTTPException
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ACTIVE = {"pending", "running", "incomplete"}
CONNECTION_ID = os.getenv("AIRBYTE_CONNECTION_ID", "")

class AirbyteError(RuntimeError):
    pass

class AirbyteHTTPError(AirbyteError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status

class AirbyteClient:
    def __init__(self, base_url=None, client_id=None, client_secret=None):
        if not CONNECTION_ID:
            raise AirbyteError("Set AIRBYTE_CONNECTION_ID before importing the pipeline.")
        self.base = (base_url or os.getenv("AIRBYTE_URL", "http://localhost:8000")).rstrip("/")
        parsed = urlparse(self.base)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise AirbyteError("Invalid AIRBYTE_URL")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise AirbyteError("Use HTTPS for a non-local Airbyte endpoint")
        self.client_id = client_id or os.getenv("AIRBYTE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AIRBYTE_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise AirbyteError("Airbyte application client ID/secret are missing. Use start_pipeline.py.")
        self.token = None
        self.expires = 0
        self.log = lambda message: None

    def _http(self, method, path, payload=None, token=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        attempts = 4 if method == "GET" else 1
        for attempt in range(attempts):
            request = Request(self.base + path, data=data, headers=headers, method=method)
            delay = min(2 ** (attempt + 1), 15)
            try:
                with urlopen(request, timeout=60) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                retryable = method == "GET" and exc.code in {408, 429, 500, 502, 503, 504}
                if not retryable or attempt + 1 >= attempts:
                    raise AirbyteHTTPError(exc.code,
                        "Airbyte HTTP " + str(exc.code) + " for " + method + " " + path) from None
                try:
                    delay = min(30, max(delay, float(exc.headers.get("Retry-After", delay))))
                except (ValueError, TypeError, AttributeError):
                    pass
                reason = "HTTP " + str(exc.code)
            except (URLError, TimeoutError, OSError, HTTPException, ValueError, UnicodeError) as exc:
                if attempt + 1 >= attempts:
                    suffix = (" The Airbyte job may still be running; check Timeline."
                              if method == "GET" else
                              " Request outcome may be unknown; inspect Timeline before retrying.")
                    raise AirbyteError("Airbyte network/response error (" +
                        type(exc).__name__ + ") for " + method + " " + path +
                        " after " + str(attempts) + " attempt(s)." + suffix) from None
                reason = type(exc).__name__
            self.log("Airbyte GET retry " + str(attempt + 1) + "/" + str(attempts - 1) +
                     ": " + path + " (" + reason + "); waiting " + str(delay) + " seconds")
            time.sleep(delay)

    def authenticate(self):
        result = self._http("POST", "/api/public/v1/applications/token", {
            "client_id": self.client_id, "client_secret": self.client_secret,
            "grant-type": "client_credentials",
        })
        self.token = result.get("access_token")
        if not self.token:
            raise AirbyteError("Airbyte token endpoint returned no access token")
        self.expires = time.monotonic() + max(1, int(result.get("expires_in", 900)) - 60)

    def request(self, method, path, payload=None):
        if not self.token or time.monotonic() >= self.expires:
            self.authenticate()
        # No automatic POST retries: an ambiguous network failure must not start duplicate syncs.
        try:
            return self._http(method, "/api/public/v1" + path, payload, token=self.token)
        except AirbyteHTTPError as exc:
            if exc.status != 401:
                raise
            # A definite authentication rejection can be retried after token refresh.
            self.authenticate()
            return self._http(method, "/api/public/v1" + path, payload, token=self.token)

    def get_connection(self, connection_id=CONNECTION_ID):
        return self.request("GET", "/connections/" + connection_id)

    def resume_job(self, job_id, connection_id=CONNECTION_ID):
        if int(job_id) < 1:
            raise AirbyteError("Resume job ID must be a positive integer")
        job = self.request("GET", "/jobs/" + str(int(job_id)))
        if job.get("connectionId") != connection_id:
            raise AirbyteError("Resume job does not identify the expected connection; stopping.")
        if str(job.get("jobType", "sync")).lower() != "sync":
            raise AirbyteError("Only sync jobs can be resumed")
        if str(job.get("status", "")).lower() not in ACTIVE | {"succeeded"}:
            raise AirbyteError("Job " + str(job_id) + " is " + str(job.get("status")) +
                               "; it cannot be resumed as a successful sync. Inspect its Airbyte logs.")
        return job

    def start_or_attach(self, connection_id=CONNECTION_ID):
        query = urlencode({"connectionId": connection_id, "jobType": "sync",
                           "limit": 100, "orderBy": "updatedAt|DESC"})
        response = self.request("GET", "/jobs?" + query)
        active = [job for job in response.get("data", [])
                  if str(job.get("status", "")).lower() in ACTIVE]
        if len(active) > 1:
            raise AirbyteError("Multiple active Airbyte jobs found; inspect Timeline.")
        if active:
            return active[0], True
        job = self.request("POST", "/jobs", {"connectionId": connection_id, "jobType": "sync"})
        if job.get("jobId") is None:
            raise AirbyteError("Sync request returned no jobId. Inspect Timeline before retrying.")
        return job, False

    def wait_for_success(self, job_id, log=print, timeout_seconds=3600, poll_seconds=15):
        deadline = time.monotonic() + timeout_seconds
        previous = None
        while time.monotonic() < deadline:
            result = self.request("GET", "/jobs/" + str(job_id))
            status = str(result.get("status", "")).lower()
            if status != previous:
                log("Airbyte job " + str(job_id) + ": " + status)
                previous = status
            if status == "succeeded":
                return result
            if status in {"failed", "cancelled", "canceled"}:
                raise AirbyteError("Airbyte job " + str(job_id) + " ended as " + status +
                                   ". dbt will not run; inspect Airbyte Timeline.")
            if status not in ACTIVE:
                raise AirbyteError("Unknown Airbyte job status: " + status)
            time.sleep(poll_seconds)
        raise AirbyteError("Airbyte wait exceeded timeout. Job may still be running; inspect Timeline. dbt was not started.")
