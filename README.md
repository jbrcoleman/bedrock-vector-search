# bedrock-vector-search

> **Intelligent document processing and semantic search powered by AWS Bedrock, OpenSearch, and modern DevOps practices**

A production-ready, cloud-native knowledge base system that automatically ingests documents, generates embeddings using AWS Bedrock, and provides intelligent Q&A capabilities through semantic search.

[![Deploy](https://github.com/your-username/ai-knowledge-base-platform/workflows/Deploy%20Knowledge%20Base/badge.svg)](https://github.com/your-username/ai-knowledge-base-platform/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-blue)](https://www.terraform.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange)](https://aws.amazon.com/bedrock/)

## 🚀 Features

- **🤖 AI-Powered**: Leverages AWS Bedrock (Titan embeddings + Claude 3) for intelligent document processing
- **🔍 Semantic Search**: Vector-based similarity search using OpenSearch with k-NN capabilities  
- **📄 Multi-Format Support**: Processes PDFs and text documents automatically
- **☁️ Cloud-Native**: Built on AWS with serverless and containerized components
- **🏗️ Infrastructure as Code**: Complete Terraform configuration for reproducible deployments
- **🔄 CI/CD Ready**: GitHub Actions pipeline with automated testing and deployment
- **📊 Production-Ready**: Load balancing, auto-scaling, monitoring, and health checks
- **🔒 Secure**: Proper IAM roles, VPC networking, and access controls

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documents     │    │   S3 Bucket      │    │   Lambda        │
│   (PDF/TXT)     │───▶│   Storage        │───▶│   Processing    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   FastAPI        │    │   AWS Bedrock   │
│   (ALB)         │───▶│   Service        │───▶│   (AI Models)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   OpenSearch     │    │   Vector        │
                       │   Cluster        │───▶│   Embeddings    │
                       └──────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Infrastructure** | Terraform | Infrastructure as Code |
| **Cloud Platform** | AWS | Hosting and managed services |
| **AI/ML** | AWS Bedrock | Embeddings and text generation |
| **Vector Database** | AWS OpenSearch | Semantic search and storage |
| **API Framework** | FastAPI | High-performance REST API |
| **Processing** | AWS Lambda | Serverless document processing |
| **Storage** | Amazon S3 | Document storage |
| **Orchestration** | Amazon ECS | Container orchestration |
| **CI/CD** | GitHub Actions | Automated deployment pipeline |
| **Monitoring** | CloudWatch | Logging and metrics |

## 🚀 Quick Start

### Prerequisites

- AWS Account with Bedrock access enabled
- Terraform >= 1.5.0
- Docker
- Python 3.9+
- AWS CLI configured

### 1. Clone and Setup

```bash
git clone https://github.com/jbrcoleman/bedrock-vector-search.git
cd bedrock-vector-search
```
### 2. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Build and Deploy Application

```bash
# Get ECR repository URL from Terraform
cd terraform
terraform refresh
ECR_REPO=$(terraform output -raw ecr_repository_url)

# Build and push API container
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO
docker build -t knowledge-base-api ./app
docker tag knowledge-base-api:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Update ECS service to use the new image
aws ecs update-service \
  --cluster knowledge-base-cluster \
  --service knowledge-base-api \
  --force-new-deployment \
  --region us-east-1
```

### 4. Verify Deployment

```bash
# Check ECS service status
aws ecs describe-services --cluster knowledge-base-cluster --services knowledge-base-api

# Check running tasks
aws ecs list-tasks --cluster knowledge-base-cluster --service-name knowledge-base-api

# Test the API endpoints
ALB_URL=$(terraform output -raw api_endpoint)
curl -X GET "${ALB_URL}/health"
curl -X GET "${ALB_URL}/"

# Check S3 bucket name for document uploads
S3_BUCKET=$(terraform output -raw s3_bucket_name)
```

## 📖 Usage

### Upload Documents

Simply upload documents to the S3 bucket to trigger automatic processing:

```bash
# Upload via AWS CLI
aws s3 cp document.pdf s3://knowledge-base-documents-<suffix>/

# Upload via S3 Console
# Navigate to your bucket and drag/drop files
```

### Query the Knowledge Base

```bash
# Get your API endpoint
terraform output api_endpoint

# Query the knowledge base
curl -X POST "http://your-alb-endpoint/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main topics discussed in the documents?",
    "top_k": 5
  }'
```

### Example Response

```json
{
  "answer": "Based on the uploaded documents, the main topics include cloud architecture patterns, serverless computing benefits, and cost optimization strategies for AWS workloads...",
  "sources": [
    {
      "file": "aws-whitepaper.pdf",
      "chunk": 3,
      "score": 0.94
    },
    {
      "file": "architecture-guide.pdf", 
      "chunk": 1,
      "score": 0.91
    }
  ]
}
```

## 🔧 Configuration

### AWS Bedrock Models

The system automatically tries multiple embedding models in order:

- **Primary**: `amazon.titan-embed-text-v1`
- **Fallback**: `amazon.titan-embed-text-v2:0`
- **Alternative**: `cohere.embed-english-v3`
- **Text Generation**: `anthropic.claude-3-sonnet-20240229-v1:0`

**Model Access**: Ensure you have enabled model access in the AWS Bedrock console for at least one of the embedding models listed above.

To change models, update the `models_to_try` array in:
- `lambda/process_document/index.py`
- `app/main.py`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENSEARCH_ENDPOINT` | OpenSearch cluster endpoint | Set by Terraform |
| `BEDROCK_REGION` | AWS region for Bedrock | `us-east-1` |
| `DOCUMENTS_BUCKET` | S3 bucket for documents | Set by Terraform |
| `AWS_REGION` | AWS region | `us-east-1` |

### ⚠️ Known Issues

**Lambda OpenSearch Integration**: Currently, the Lambda function generates embeddings successfully but cannot store them in OpenSearch due to a dependency issue with `opensearch-py`. 

**Current Status:**
- ✅ API endpoints working (`/health`, `/query`)
- ✅ Document upload to S3 triggers Lambda
- ✅ Embedding generation with Bedrock Titan
- ❌ Document storage in OpenSearch (dependency issue)

**Workaround**: The API returns "no documents found" until the Lambda dependency is resolved.

**Fix**: Update Lambda deployment to properly include opensearch-py dependency.

### Scaling Configuration

Modify these Terraform variables for scaling:

```hcl
# terraform/variables.tf
variable "ecs_desired_count" {
  default = 2
}

variable "opensearch_instance_type" {
  default = "t3.small.search"
}
```

## 🧪 Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Integration Tests

```bash
# Test the deployed API
python tests/integration/test_api_integration.py

# Load testing
python tests/load/load_test.py
```

## 🚢 Deployment

### Using GitHub Actions

1. **Set up secrets** in your GitHub repository:
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   ```

2. **Push to main branch** to trigger deployment:
   ```bash
   git push origin main
   ```

3. **Monitor deployment** in GitHub Actions tab

### Manual Deployment

```bash
# Deploy infrastructure changes
cd terraform && terraform apply

# Build and deploy the API container
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY=$(aws ecr describe-repositories --repository-names knowledge-base-api --query 'repositories[0].repositoryUri' --output text)

# Build and push container
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
docker build -t knowledge-base-api ./app
docker tag knowledge-base-api:latest ${ECR_REPOSITORY}:latest  
docker push ${ECR_REPOSITORY}:latest

# Force ECS service deployment
aws ecs update-service \
  --cluster knowledge-base-cluster \
  --service knowledge-base-api \
  --force-new-deployment

# Update Lambda function (if changed)
cd lambda/process_document
pip install -r requirements.txt -t .
zip -r ../../terraform/process_document.zip . -x "__pycache__/*" "*.pyc"
cd ../../terraform
aws lambda update-function-code \
  --function-name knowledge-base-process-document \
  --zip-file fileb://process_document.zip
```

## 📊 Monitoring

### CloudWatch Dashboards

The deployment creates dashboards for:
- API response times and error rates
- Lambda function metrics
- OpenSearch cluster health
- ECS service performance

### Logs

```bash
# View API logs
aws logs tail /ecs/knowledge-base-api --follow

# View Lambda logs  
aws logs tail /aws/lambda/process-document --follow

# View OpenSearch logs
aws opensearch describe-domain --domain-name knowledge-base-vectors
```

## 🔒 Security

### IAM Roles

The system uses least-privilege IAM roles:
- **Lambda Role**: S3 read, Bedrock invoke, OpenSearch write
- **ECS Role**: Bedrock invoke, OpenSearch read/write
- **GitHub Actions**: Limited deployment permissions

### Network Security

- VPC with private/public subnets
- Security groups with minimal required access
- OpenSearch within VPC
- Application Load Balancer with health checks

### Data Protection

- S3 bucket encryption at rest
- OpenSearch encryption in transit and at rest
- Bedrock API calls over HTTPS
- No sensitive data in logs

### Development Setup

```bash
# Clone repo
git clone https://github.com/your-username/ai-knowledge-base-platform.git

# Set up development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] **Multi-modal Support**: Images and audio processing
- [ ] **Advanced RAG**: Hybrid search combining vector + keyword search  
- [ ] **Fine-tuning**: Custom model training on domain-specific data
- [ ] **Multi-tenancy**: Support for multiple isolated knowledge bases
- [ ] **Real-time Updates**: WebSocket API for live document processing
- [ ] **Analytics Dashboard**: Usage metrics and insights
- [ ] **Mobile App**: React Native companion app

## ❓ FAQ

### How do I enable Bedrock access?

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Go to "Model access" in the left sidebar
4. Request access to required models (Titan, Claude)
5. Wait for approval (usually instant for standard models)

### Why am I getting "no documents found" responses?

This indicates the Lambda function processed documents but couldn't store them in OpenSearch. Check:

1. **Lambda logs**: `aws logs filter-log-events --log-group-name "/aws/lambda/knowledge-base-process-document" --region us-east-1`
2. **Bedrock access**: Ensure embedding models are enabled
3. **OpenSearch dependency**: The Lambda currently has an `opensearch-py` import issue

### How do I fix the Lambda dependency issue?

The Lambda deployment may not include all required packages. To fix:

```bash
cd terraform
# Force Lambda redeployment
terraform apply -target=aws_lambda_function.process_document -auto-approve

# Monitor logs after uploading a test document
aws s3 cp test.pdf s3://your-bucket-name/
aws logs tail /aws/lambda/knowledge-base-process-document --follow
```

### Can I use different vector databases?

Yes! The system is designed to be database-agnostic. You can replace OpenSearch with:
- Pinecone
- Weaviate  
- Chroma
- PostgreSQL with pgvector

Update the database client code in `lambda/process_document/index.py` and `app/main.py`.

### How do I handle large documents?

The system automatically chunks large documents. For very large files:

1. Adjust chunk size in `chunk_text()` function
2. Increase Lambda timeout and memory
3. Consider using Step Functions for complex workflows
4. Implement parallel processing for multiple files

### What file formats are supported?

Currently: PDF and TXT files. To add more formats:

1. Install appropriate libraries (`python-docx`, `openpyxl`, etc.)
2. Update `extract_text()` function in Lambda
3. Add file extensions to S3 event filters

