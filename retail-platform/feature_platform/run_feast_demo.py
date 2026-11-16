"""Verify customer/product historical features and explicitly archival online lookup.
No trained model; archived 2018 values are never relabelled as current data.
"""
import importlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime,timedelta,timezone
from importlib.metadata import version

ROOT=Path(__file__).resolve().parent
REPO=ROOT/"feature_repo"
PROJECT=os.environ["GCP_PROJECT_ID"]

def main():
    import pandas as pd
    from google.cloud import bigquery
    from feast import FeatureStore
    from feature_checks import matching_records
    sys.path.insert(0,str(REPO))
    client=bigquery.Client(project=PROJECT)
    evidence=ROOT/"evidence"
    evidence.mkdir(exist_ok=True)
    started=time.perf_counter()
    report={"started_at":datetime.now(timezone.utc).isoformat(),"feast_version":version("feast"),
            "mode":"historical_archive_demo","entities":{}}
    def query(sql):
        job=client.query(sql,location="US")
        return [dict(row.items()) for row in job.result(timeout=300)]
    groups=[]
    objects=[]
    for kind,key in [("customer","customer_unique_id"),("product","product_id")]:
        module=importlib.import_module(kind+"_features")
        view=getattr(module,kind+"_activity")
        archive=getattr(module,kind+"_activity_archive")
        service=getattr(module,kind+"_activity_service")
        online_service=getattr(module,kind+"_activity_archive_service")
        objects.extend([getattr(module,kind),view,archive,service,online_service])
        groups.append((kind,key,module.FIELDS,view,archive,service,online_service))
    def clean(frame,key,fields,prefix=""):
        records=[]
        for row in frame.to_dict("records"):
            result={key:str(row[key])}
            for field in fields:
                value=row.get(prefix+field)
                result[field]=None if pd.isna(value) else value
            records.append(result)
        return records
    try:
        summaries={}
        for kind,key,fields,*_ in groups:
            ref=PROJECT+".olist_analytics."+kind+"_features_monthly"
            metadata=client.get_table(ref)
            if metadata.time_partitioning is not None or metadata.range_partitioning is not None:
                raise RuntimeError(ref+" is still partitioned; use the unpartitioned dbt model.")
            summary=query("SELECT COUNT(*) AS feature_rows,COUNT(DISTINCT "+key+") AS entities,"
                "COUNT(DISTINCT feature_timestamp) AS monthly_cutoffs,MIN(feature_timestamp) AS earliest,"
                "MAX(feature_timestamp) AS latest FROM `"+ref+"`")[0]
            if summary["feature_rows"]<=0 or summary["monthly_cutoffs"]<2:
                raise RuntimeError(ref+" has insufficient historical data; build and test first.")
            summaries[kind]=summary
            report["entities"][kind]={"source":summary,"partitioned":False,"status":"preflight_passed"}
            print(kind+": "+str(summary["feature_rows"])+" rows; "+str(summary["monthly_cutoffs"])+
                  " cutoffs; earliest="+str(summary["earliest"]))
        scratch=bigquery.Dataset(PROJECT+".olist_feast_work")
        scratch.location="US"
        client.create_dataset(scratch,exists_ok=True)
        os.chdir(REPO)
        (REPO/"data").mkdir(exist_ok=True)
        store=FeatureStore(repo_path=str(REPO))
        store.apply(objects)
        print("Customer and product definitions registered.")
        for kind,key,fields,fv,archive,service,online_service in groups:
            ref=PROJECT+".olist_analytics."+kind+"_features_monthly"
            first,cutoff=summaries[kind]["earliest"],summaries[kind]["latest"]
            cutoff_sql="TIMESTAMP('"+cutoff.isoformat()+"')"
            entity_sql=("SELECT "+key+",feature_timestamp AS event_timestamp FROM `"+ref+
                        "` WHERE feature_timestamp="+cutoff_sql+" ORDER BY "+key+" LIMIT 5")
            expected=query("SELECT "+key+","+",".join(fields)+" FROM `"+ref+
                "` WHERE feature_timestamp="+cutoff_sql+" ORDER BY "+key+" LIMIT 5")
            lookup_start=time.perf_counter()
            frame=store.get_historical_features(entity_df=entity_sql,features=service,
                                                full_feature_names=True).to_df()
            historical_seconds=time.perf_counter()-lookup_start
            actual=clean(frame,key,fields,fv.name+"__")
            matching_records(actual,expected,key,fields)
            frame.to_csv(evidence/(kind+"_historical_sample.csv"),index=False)
            # The first snapshot cannot be used one second before it exists.
            early_sql=("SELECT "+key+",TIMESTAMP_SUB(feature_timestamp,INTERVAL 1 SECOND) AS event_timestamp "
                "FROM `"+ref+"` WHERE feature_timestamp=TIMESTAMP('"+first.isoformat()+
                "') ORDER BY "+key+" LIMIT 5")
            early=store.get_historical_features(entity_df=early_sql,features=service,
                                                full_feature_names=True).to_df()
            early_records=clean(early,key,fields,fv.name+"__")
            if not early_records:
                raise RuntimeError("Before-first-snapshot test returned no entity rows.")
            matching_records(early_records,[{key:r[key],**{n:None for n in fields}}
                                            for r in early_records],key,fields)
            early.to_csv(evidence/(kind+"_before_first_cutoff.csv"),index=False)
            prior_sql=entity_sql.replace("feature_timestamp AS event_timestamp",
                       "TIMESTAMP_SUB(feature_timestamp,INTERVAL 1 SECOND) AS event_timestamp")
            prior=store.get_historical_features(entity_df=prior_sql,features=service,
                                                full_feature_names=True).to_df()
            prior_expected=query("SELECT "+key+","+",".join(fields)+" FROM `"+ref+
                "` WHERE "+key+" IN (SELECT "+key+" FROM ("+entity_sql+")) "
                "AND feature_timestamp < "+cutoff_sql+" AND feature_timestamp >= TIMESTAMP_SUB(TIMESTAMP_SUB("+
                cutoff_sql+",INTERVAL 1 SECOND),INTERVAL 35 DAY) QUALIFY ROW_NUMBER() OVER(PARTITION BY "+
                key+" ORDER BY feature_timestamp DESC)=1")
            by_id={str(r[key]):r for r in prior_expected}
            padded=[by_id.get(r[key],{key:r[key],**{n:None for n in fields}}) for r in actual]
            matching_records(clean(prior,key,fields,fv.name+"__"),padded,key,fields)
            print(kind+": historical values and two time-boundary checks passed.")
            # Materialize only archive view; preserve original event timestamps.
            materialize_start=time.perf_counter()
            store.materialize(start_date=cutoff-timedelta(seconds=1),
                end_date=cutoff+timedelta(seconds=1),feature_views=[archive.name])
            materialize_seconds=time.perf_counter()-materialize_start
            online_start=time.perf_counter()
            response=store.get_online_features(features=online_service,
                entity_rows=[{key:r[key]} for r in actual],full_feature_names=True)
            online_seconds=time.perf_counter()-online_start
            found=0
            for column,result in zip(response.proto.metadata.feature_names.val,response.proto.results):
                if not column.startswith(archive.name+"__"):
                    continue
                found+=1
                enum=result.DESCRIPTOR.fields_by_name["statuses"].enum_type
                if len(result.statuses)!=len(actual) or any(
                    enum.values_by_number[s].name!="PRESENT" for s in result.statuses):
                    raise RuntimeError("Online archive value absent: "+column)
                if len(result.event_timestamps)!=len(actual) or any(
                    abs(t.ToDatetime(tzinfo=timezone.utc).timestamp()-cutoff.timestamp())>0.001
                    for t in result.event_timestamps):
                    raise RuntimeError("Archive event timestamp changed: "+column)
            if found!=len(fields):
                raise RuntimeError("Online feature count differs from schema.")
            online=clean(response.to_df(),key,fields,archive.name+"__")
            matching_records(online,expected,key,fields)
            (evidence/(kind+"_online_archive_sample.json")).write_text(
                json.dumps({"snapshot_timestamp":cutoff.isoformat(),"rows":online},indent=2,default=str),
                encoding="utf-8")
            report["entities"][kind].update(status="passed",sample_entities=len(actual),
                historical_values=True,before_first_snapshot=True,prior_snapshot_values=True,
                archive_online_values=True,original_timestamps_preserved=True,
                historical_lookup_seconds=historical_seconds,materialize_seconds=materialize_seconds,
                online_lookup_seconds=online_seconds)
            print(kind+": historical/online values and timestamps match.")
        report["status"]="passed"
        print("CUSTOMER AND PRODUCT FEATURE DEMO PASSED.")
        print("Archive views have no online age limit; not for present-day predictions.")
    except Exception as exc:
        report.update(status="failed",error_type=type(exc).__name__,error=str(exc)[:600])
        raise
    finally:
        report["total_seconds"]=time.perf_counter()-started
        report["finished_at"]=datetime.now(timezone.utc).isoformat()
        path=evidence/"feature_platform_verification.json"
        path.write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
        print("Verification report: "+str(path))

if __name__=="__main__":
    main()
