# GCS to BigQuery Cloud Function

A Google Cloud Function that automatically loads JSONL files from Google Cloud Storage (GCS) to BigQuery when they are uploaded to a specified bucket.

## Overview

This Cloud Function is triggered by GCS bucket events and automatically loads JSONL files into a BigQuery table. It's designed to process user event logs from Glamira but can be adapted for other use cases.

## Architecture

```
GCS Bucket → Cloud Function → BigQuery Table
```

When a file is uploaded to the GCS bucket, the Cloud Function is triggered and loads the data into the specified BigQuery table.

## Prerequisites

Before deploying this Cloud Function, ensure you have:

1. **Google Cloud SDK** installed and configured
2. **Required APIs enabled**:
   - Cloud Functions API
   - Cloud Storage API
   - BigQuery API
   - Cloud Build API (for deployment)
3. **Service Account** with appropriate permissions
4. **BigQuery dataset and table** created

## Setup Instructions

### 1. Enable Required APIs

```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Create Service Account (Optional)

If you want to use a custom service account:

```bash
# Create service account
gcloud iam service-accounts create gcs-to-bq-function \
    --display-name="GCS to BigQuery Function"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gcs-to-bq-function@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gcs-to-bq-function@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gcs-to-bq-function@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### 3. Create BigQuery Dataset and Table

```bash
# Create dataset
bq mk --dataset YOUR_PROJECT_ID:raw_glamira

# Create table (adjust schema as needed)
bq mk --table YOUR_PROJECT_ID:raw_glamira.glamira_user_event_raw_logs
```

### 4. Create GCS Bucket

```bash
gsutil mb gs://YOUR_BUCKET_NAME
```

## Deployment

### Option 1: Deploy with gcloud CLI

```bash
gcloud functions deploy load-gcs-to-bigquery \
    --runtime python39 \
    --trigger-bucket YOUR_BUCKET_NAME \
    --entry-point load_gcs_to_bigquery \
    --memory 512MB \
    --timeout 540s \
    --region asia-southeast1 \
    --set-env-vars BIGQUERY_DATASET=raw_glamira,BIGQUERY_TABLE=glamira_user_event_raw_logs
```

### Option 2: Deploy with Custom Service Account

```bash
gcloud functions deploy load-gcs-to-bigquery \
    --runtime python39 \
    --trigger-bucket YOUR_BUCKET_NAME \
    --entry-point load_gcs_to_bigquery \
    --memory 512MB \
    --timeout 540s \
    --region asia-southeast1 \
    --service-account gcs-to-bq-function@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars BIGQUERY_DATASET=raw_glamira,BIGQUERY_TABLE=glamira_user_event_raw_logs
```

### Option 3: Deploy with YAML Configuration

Create a `function.yaml` file:

```yaml
name: load-gcs-to-bigquery
runtime: python39
entryPoint: load_gcs_to_bigquery
eventTrigger:
  eventType: google.storage.object.finalize
  resource: projects/YOUR_PROJECT_ID/buckets/YOUR_BUCKET_NAME
environmentVariables:
  BIGQUERY_DATASET: raw_glamira
  BIGQUERY_TABLE: glamira_user_event_raw_logs
availableMemoryMb: 512
timeout: 540s
```

Then deploy:

```bash
gcloud functions deploy --source . --config function.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `BIGQUERY_DATASET` | BigQuery dataset ID | `raw_glamira` |
| `BIGQUERY_TABLE` | BigQuery table ID | `glamira_user_event_raw_logs` |

### Function Configuration

- **Runtime**: Python 3.9
- **Memory**: 512MB (adjustable based on file size)
- **Timeout**: 540s (9 minutes)
- **Region**: asia-southeast1 (configurable)

## File Processing

The function processes files with the following criteria:

- **File Format**: Only JSONL (JSON Lines) files
- **Trigger**: Files uploaded to the specified GCS bucket
- **Processing**: Automatic schema detection disabled, append mode
- **Error Handling**: Up to 10 bad records allowed per job

## Monitoring and Logging

### View Function Logs

```bash
gcloud functions logs read load-gcs-to-bigquery --limit 50
```

### Monitor Function Performance

```bash
gcloud functions describe load-gcs-to-bigquery --region asia-southeast1
```

## Testing

### Test with Sample File

1. Create a sample JSONL file:
```bash
echo '{"user_id": "123", "event": "page_view", "timestamp": "2023-10-06T10:00:00Z"}' > sample.jsonl
echo '{"user_id": "456", "event": "click", "timestamp": "2023-10-06T10:01:00Z"}' >> sample.jsonl
```

2. Upload to GCS bucket:
```bash
gsutil cp sample.jsonl gs://YOUR_BUCKET_NAME/
```

3. Check BigQuery table:
```bash
bq query --use_legacy_sql=false 'SELECT * FROM `YOUR_PROJECT_ID.raw_glamira.glamira_user_event_raw_logs` LIMIT 10'
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure the Cloud Function service account has BigQuery and Storage permissions
   - Check IAM roles: `bigquery.dataEditor`, `bigquery.jobUser`, `storage.objectViewer`

2. **Schema Errors**
   - BigQuery table schema must be compatible with JSONL data
   - Consider using `autodetect=True` for dynamic schemas

3. **Timeout Errors**
   - Increase function timeout for large files
   - Consider chunking large files or using Dataflow for very large datasets

4. **Memory Errors**
   - Increase function memory allocation
   - Monitor function execution metrics

### Debug Commands

```bash
# Check function status
gcloud functions describe load-gcs-to-bigquery --region asia-southeast1

# View recent logs
gcloud functions logs read load-gcs-to-bigquery --limit 100

# Check BigQuery job history
bq ls -j --max_results=10
```

## Security Considerations

- Use least-privilege IAM roles
- Consider using VPC connectors for private networks
- Enable audit logging for compliance
- Regularly rotate service account keys if using custom service accounts

## Cost Optimization

- Set appropriate memory allocation (avoid over-provisioning)
- Use regional deployment to reduce egress costs
- Monitor BigQuery slot usage for large loads
- Consider BigQuery streaming inserts for real-time requirements

## Maintenance

### Update Function

```bash
gcloud functions deploy load-gcs-to-bigquery \
    --source . \
    --runtime python39 \
    --trigger-bucket YOUR_BUCKET_NAME \
    --entry-point load_gcs_to_bigquery
```

### Update Dependencies

1. Modify `requirements.txt`
2. Redeploy the function

## Support

For issues and questions:
- Check Cloud Function logs
- Review BigQuery job history
- Monitor Cloud Function metrics in Cloud Monitoring

## License

[Add your license information here]