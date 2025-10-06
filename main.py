# main.py
from google.cloud import bigquery
from google.cloud import storage
import json
import os

def load_gcs_to_bigquery(event, context):
    bucket_name = event['bucket']
    file_name = event['name']
    
    if not file_name.endswith('.jsonl'):
        print(f"Skipping non-JSONL file: {file_name}")
        return
    
    bigquery_client = bigquery.Client()
    
    dataset_id = os.getenv('BIGQUERY_DATASET', 'raw_glamira')
    table_id = os.getenv('BIGQUERY_TABLE', 'glamira_user_event_raw_logs')
    location = "asia-southeast1"

    table_ref = bigquery_client.dataset(dataset_id).table(table_id)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=False,
        ignore_unknown_values=True,
        max_bad_records=10,
    )

    gcs_uri = f"gs://{bucket_name}/{file_name}"

    try:
        print(f"Loading {file_name} to {dataset_id}.{table_id}")
        print(f"GCS URI: {gcs_uri}")
        
        load_job = bigquery_client.load_table_from_uri(
            gcs_uri, table_ref, job_config=job_config, location=location
        )
        
        load_job.result()
        
        print(f"Successfully loaded {load_job.output_rows} rows")
        print(f"Job ID: {load_job.job_id}")
        
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        raise e
