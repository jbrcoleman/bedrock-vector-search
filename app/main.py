from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from typing import List, Optional

app = FastAPI(title="Knowledge Base API", version="1.0.0")

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

class DocumentSource(BaseModel):
    file: str
    chunk: int
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]

# Initialize clients
bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ.get("AWS_REGION", "us-east-1"))
opensearch_endpoint = os.environ.get("OPENSEARCH_ENDPOINT", "")

def get_opensearch_client():
    if not opensearch_endpoint:
        return None
    
    # Remove protocol prefix if present
    clean_endpoint = opensearch_endpoint.replace('https://', '').replace('http://', '')
    
    return OpenSearch(
        hosts=[{'host': clean_endpoint, 'port': 443}],
        http_auth=None,  # Use IAM auth instead of basic auth
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )

def get_embedding(text: str) -> List[float]:
    """Generate embeddings using AWS Bedrock Titan"""
    try:
        # Try multiple models in order of preference
        models_to_try = [
            'amazon.titan-embed-text-v1',
            'amazon.titan-embed-text-v2:0',
            'cohere.embed-english-v3'
        ]
        
        body = json.dumps({"inputText": text})
        
        last_error = None
        for model_id in models_to_try:
            try:
                response = bedrock_client.invoke_model(
                    modelId=model_id,
                    body=body,
                    contentType='application/json',
                    accept='application/json'
                )
                response_body = json.loads(response['body'].read())
                return response_body.get('embedding', [])
            except Exception as e:
                print(f"Model {model_id} failed: {str(e)}")
                last_error = e
                continue
        
        raise last_error or ValueError("No embedding models available")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

def search_similar_documents(query_embedding: List[float], top_k: int = 5) -> List[dict]:
    """Search for similar documents in OpenSearch"""
    opensearch_client = get_opensearch_client()
    if not opensearch_client:
        return []
    
    try:
        search_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k
                    }
                }
            },
            "_source": ["content", "file_name", "chunk_id"]
        }
        
        response = opensearch_client.search(
            index="documents",
            body=search_body
        )
        
        return response['hits']['hits']
    except Exception as e:
        print(f"OpenSearch error: {str(e)}")
        return []

def generate_answer(question: str, context: str) -> str:
    """Generate answer using AWS Bedrock Claude"""
    try:
        prompt = f"""Based on the following context, answer the question. If the context doesn't contain enough information, say so.

Context: {context}

Question: {question}

Answer:"""

        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    except Exception as e:
        return f"Error generating answer: {str(e)}"

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

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base with a question"""
    try:
        # Generate embedding for the question
        query_embedding = get_embedding(request.question)
        
        # Search for similar documents
        search_results = search_similar_documents(query_embedding, request.top_k)
        
        if not search_results:
            return QueryResponse(
                answer="I couldn't find any relevant documents to answer your question.",
                sources=[]
            )
        
        # Prepare context from search results
        context_parts = []
        sources = []
        
        for i, hit in enumerate(search_results):
            source_data = hit['_source']
            context_parts.append(source_data.get('content', ''))
            sources.append(DocumentSource(
                file=source_data.get('file_name', 'unknown'),
                chunk=source_data.get('chunk_id', i),
                score=hit['_score']
            ))
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using the context
        answer = generate_answer(request.question, context)
        
        return QueryResponse(answer=answer, sources=sources)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
