import boto3
import logging


logger = logging.getLogger(__name__)

class S3Connection:
    def __init__(self, aws_access_key: str, aws_secret_key: str, bucket_name, aws_region: str = 'eu-west-1'):
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        self.s3 = self.session.client('s3')
        self.bucket_name = bucket_name
    
    def upload_file(self, df, s3_key) -> str:
        try:
            # Convert to CSV
            csv_buffer = df.to_csv(index=False)
            # Upload to S3
            logger.info(f"Uploading to s3://{self.bucket_name}/{s3_key}")
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer.encode('utf-8'),
                ContentType='text/csv'
            )
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"[OK] Uploaded {len(df):,} rows to {s3_uri}") 
            return s3_uri
        except Exception as e:
            logger.error(f"[FAIL] Failed to upload to S3: {e}")
            raise