import boto3
from src.config.index import appConfig

s3_client = boto3.client(
    "s3",
    aws_access_key_id=appConfig["aws_access_key_id"],
    aws_secret_access_key=appConfig["aws_secret_access_key"],
    region_name=appConfig["aws_region"],
)
