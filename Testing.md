# 🧪 Testing Your AI Knowledge Base

## 1. Get Your Infrastructure Details

First, let's get the important endpoints and resource names:

```bash
cd terraform
terraform output
```

You should see outputs like:
- `api_endpoint` - Your API URL
- `s3_bucket_name` - Where to upload documents
- `opensearch_endpoint` - Your vector database
- `lambda_function_name` - Document processor

## 2. Build and Deploy the API Container

### Step 2.1: Get ECR Repository URL
```bash
ECR_REPO=$(terraform output -raw ecr_repository_url)
echo "ECR Repository: $ECR_REPO"
```

### Step 2.2: Build and Push API Container
```bash
# Navigate to app directory
cd ../app

# Create a basic FastAPI app if not exists
cat > main.py << 'EOF'
from fastapi import FastAPI
import os

app = FastAPI(title="Knowledge Base API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "AI Knowledge Base API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": os.environ.get("AWS_REGION", "unknown")}

@app.get("/config")
async def get_config():
    return {
        "opensearch_endpoint": os.environ.get("OPENSEARCH_ENDPOINT", "not-set"),
        "aws_region": os.environ.get("AWS_REGION", "not-set"),
        "bedrock_region": os.environ.get("BEDROCK_REGION", "not-set")
    }
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create basic requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.34.0
EOF

# Login to ECR
aws ecr get-login-password --region $(cd ../terraform && terraform output -raw aws_region) | \
docker login --username AWS --password-stdin $ECR_REPO

# Build and push
docker build -t knowledge-base-api .
docker tag knowledge-base-api:latest $ECR_REPO:latest
docker push $ECR_REPO:latest
```

### Step 2.3: Update ECS Service
```bash
# Force deployment of new container
aws ecs update-service \
  --cluster $(cd ../terraform && terraform output -raw ecs_cluster_name) \
  --service knowledge-base-service \
  --force-new-deployment
```

## 3. Test the API

### Step 3.1: Wait for Service to be Running
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster $(cd terraform && terraform output -raw ecs_cluster_name) \
  --services knowledge-base-service \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

### Step 3.2: Test API Endpoints
```bash
API_ENDPOINT=$(cd terraform && terraform output -raw api_endpoint)

# Test health endpoint
curl -s "$API_ENDPOINT/health" | jq .

# Test configuration
curl -s "$API_ENDPOINT/config" | jq .

# Test root endpoint
curl -s "$API_ENDPOINT/" | jq .
```

Expected responses:
```json
{
  "status": "healthy",
  "environment": "us-east-1"
}
```

## 4. Test Document Processing

### Step 4.1: Create Test Documents
```bash
# Create a test directory
mkdir -p test-documents

# Create sample text file
cat > test-documents/sample.txt << 'EOF'
Artificial Intelligence and Machine Learning

Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.

Machine Learning (ML) is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. ML focuses on the development of computer programs that can access data and use it to learn for themselves.

Key concepts in AI/ML include:
- Neural networks and deep learning
- Natural language processing
- Computer vision
- Reinforcement learning
- Supervised and unsupervised learning

Applications of AI include autonomous vehicles, medical diagnosis, search engines, and recommendation systems.
EOF

# Create another test file
cat > test-documents/cloud-computing.txt << 'EOF'
Cloud Computing Overview

Cloud computing is the delivery of computing services including servers, storage, databases, networking, software, analytics, and intelligence over the Internet ("the cloud") to offer faster innovation, flexible resources, and economies of scale.

Types of Cloud Services:
1. Infrastructure as a Service (IaaS) - Provides virtualized computing infrastructure
2. Platform as a Service (PaaS) - Provides a platform for developing applications
3. Software as a Service (SaaS) - Provides software applications over the internet

Major cloud providers include Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP).

Benefits of cloud computing include cost reduction, scalability, flexibility, and accessibility from anywhere with an internet connection.
EOF
```

### Step 4.2: Upload Documents to S3
```bash
BUCKET_NAME=$(cd terraform && terraform output -raw s3_bucket_name)

# Upload test documents
aws s3 cp test-documents/sample.txt s3://$BUCKET_NAME/
aws s3 cp test-documents/cloud-computing.txt s3://$BUCKET_NAME/

# Verify upload
aws s3 ls s3://$BUCKET_NAME/
```

### Step 4.3: Check Lambda Processing
```bash
LAMBDA_NAME=$(cd terraform && terraform output -raw lambda_function_name)

# Check Lambda logs (wait a minute after upload)
aws logs tail /aws/lambda/$LAMBDA_NAME --follow --since 5m
```

You should see logs showing document processing.

## 5. Test OpenSearch Integration

### Step 5.1: Check OpenSearch Health
```bash
OPENSEARCH_ENDPOINT=$(cd terraform && terraform output -raw opensearch_endpoint)

# Note: This might not work if OpenSearch is in VPC without public access
# Check OpenSearch domain status instead
aws opensearch describe-domain --domain-name $(cd terraform && terraform output -raw opensearch_endpoint | cut -d'.' -f1 | cut -d'/' -f3)
```

## 6. End-to-End Test Script

Create a comprehensive test script:

```bash
#!/bin/bash
# test-system.sh

set -e

echo "🧪 Testing AI Knowledge Base System"
echo "=================================="

# Get Terraform outputs
cd terraform
API_ENDPOINT=$(terraform output -raw api_endpoint)
BUCKET_NAME=$(terraform output -raw s3_bucket_name)
LAMBDA_NAME=$(terraform output -raw lambda_function_name)
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)

echo "📋 System Configuration:"
echo "API Endpoint: $API_ENDPOINT"
echo "S3 Bucket: $BUCKET_NAME"
echo "Lambda Function: $LAMBDA_NAME"
echo ""

# Test 1: API Health Check
echo "🏥 Testing API Health..."
if curl -sf "$API_ENDPOINT/health" > /dev/null; then
    echo "✅ API is healthy"
    curl -s "$API_ENDPOINT/health" | jq .
else
    echo "❌ API health check failed"
    echo "Checking ECS service status..."
    aws ecs describe-services --cluster $CLUSTER_NAME --services knowledge-base-service
fi
echo ""

# Test 2: Document Upload
echo "📄 Testing Document Upload..."
echo "Sample AI document" > test-doc.txt
aws s3 cp test-doc.txt s3://$BUCKET_NAME/
echo "✅ Document uploaded to S3"
echo ""

# Test 3: Lambda Processing
echo "⚡ Checking Lambda Processing..."
sleep 10  # Wait for processing
aws logs filter-log-events \
    --log-group-name "/aws/lambda/$LAMBDA_NAME" \
    --start-time $(date -d '5 minutes ago' +%s)000 \
    --query 'events[].message' \
    --output text | head -20
echo ""

# Test 4: System Status
echo "📊 System Status Summary:"
echo "- API: $(curl -sf "$API_ENDPOINT/health" && echo "✅ Healthy" || echo "❌ Unhealthy")"
echo "- S3 Objects: $(aws s3 ls s3://$BUCKET_NAME/ | wc -l) files"
echo "- Lambda Invocations: $(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$LAMBDA_NAME" --query 'logGroups[0].storedBytes' --output text) bytes of logs"

echo ""
echo "🎉 Testing completed!"

# Cleanup
rm -f test-doc.txt
```

## 7. Troubleshooting Common Issues

### API Not Responding
```bash
# Check ECS service logs
aws logs tail /ecs/knowledge-base-api --follow

# Check service status
aws ecs describe-services --cluster $CLUSTER_NAME --services knowledge-base-service
```

### Lambda Errors
```bash
# Check Lambda logs
aws logs tail /aws/lambda/$LAMBDA_NAME --follow

# Test Lambda directly
aws lambda invoke --function-name $LAMBDA_NAME \
  --payload '{"Records":[{"s3":{"bucket":{"name":"test"},"object":{"key":"test.txt"}}}]}' \
  response.json && cat response.json
```

### OpenSearch Issues
```bash
# Check domain status
aws opensearch describe-domain --domain-name knowledge-base-vectors

# Check VPC settings if connection fails
aws ec2 describe-security-groups --group-ids $(terraform output -raw opensearch_security_group_id)
```

## 8. Next Steps

Once basic testing is complete:

1. **Implement Full Vector Search**: Update the API to actually query OpenSearch
2. **Add Bedrock Integration**: Implement the full RAG pipeline
3. **Upload Real Documents**: Test with PDFs and larger documents
4. **Performance Testing**: Use tools like `hey` or `wrk` to load test
5. **Monitoring**: Set up CloudWatch dashboards and alerts

```bash
# Performance test example
hey -n 100 -c 10 "$API_ENDPOINT/health"
```

## 🎯 Success Criteria

Your system is working correctly if:
- ✅ API responds to health checks
- ✅ Documents upload to S3 successfully  
- ✅ Lambda processes documents without errors
- ✅ OpenSearch domain is active and accessible
- ✅ ECS service is running with desired task count
