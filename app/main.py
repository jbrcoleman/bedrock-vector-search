from fastapi import FastAPI
import os
import boto3

app = FastAPI(title="Knowledge Base API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "AI Knowledge Base API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "environment": os.environ.get("AWS_REGION", "unknown"),
        "opensearch_endpoint": os.environ.get("OPENSEARCH_ENDPOINT", "not-configured")
    }

@app.get("/test-aws")
async def test_aws():
    try:
        # Test AWS connectivity
        session = boto3.Session()
        region = session.region_name or os.environ.get("AWS_REGION", "us-east-1")
        return {
            "aws_available": True,
            "region": region,
            "boto3_version": boto3.__version__
        }
    except Exception as e:
        return {
            "aws_available": False,
            "error": str(e)
        }
