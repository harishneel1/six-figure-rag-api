import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("SUPABASE_API_URL") or not os.getenv("SUPABASE_SECRET_KEY"):
    raise ValueError(
        "SUPABASE_API_URL and SUPABASE_SECRET_KEY must be set in .env file"
    )

if not os.getenv("CLERK_SECRET_KEY") or not os.getenv("DOMAIN"):
    raise ValueError("CLERK_SECRET_KEY and DOMAIN must be set in .env file")


if (
    not os.getenv("S3_BUCKET_NAME")
    or not os.getenv("AWS_REGION")
    or not os.getenv("AWS_SECRET_ACCESS_KEY")
    or not os.getenv("AWS_ACCESS_KEY_ID")
    or not os.getenv("AWS_ENDPOINT_URL_S3")
):
    raise ValueError(
        "S3_BUCKET_NAME, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_ENDPOINT_URL_S3 and AWS_SECRET_ACCESS_KEY must be set in .env file"
    )

if not os.getenv("REDIS_URL"):
    raise ValueError("REDIS_URL must be set in .env file")

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY must be set in .env file")

if not os.getenv("SCRAPINGBEE_API_KEY"):
    raise ValueError("SCRAPINGBEE_API_KEY must be set in .env file")

if not os.getenv("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY must be set in .env file")

appConfig = {
    "supabase_api_url": os.getenv("SUPABASE_API_URL"),
    "supabase_secret_key": os.getenv("SUPABASE_SECRET_KEY"),
    "clerk_secret_key": os.getenv("CLERK_SECRET_KEY"),
    "domain": os.getenv("DOMAIN"),
    "s3_bucket_name": os.getenv("S3_BUCKET_NAME"),
    "aws_region": os.getenv("AWS_REGION"),
    "aws_endpoint_url_s3": os.getenv("AWS_ENDPOINT_URL_S3"),
    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "redis_url": os.getenv("REDIS_URL"),
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "scrapingbee_api_key": os.getenv("SCRAPINGBEE_API_KEY"),
    "tavily_api_key": os.getenv("TAVILY_API_KEY")
}
