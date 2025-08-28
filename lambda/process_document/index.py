# lambda/process_document/index.py
import json
import boto3
import os
import logging
from urllib.parse import unquote_plus
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function to process documents uploaded to S3
    Extracts text, generates embeddings using Bedrock, and stores in OpenSearch
    """
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3')
        bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ['BEDROCK_REGION'])
        
        # Process each S3 record
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing file: {key} from bucket: {bucket}")
            
            try:
                # Download file from S3
                response = s3_client.get_object(Bucket=bucket, Key=key)
                file_content = response['Body'].read()
                
                # Extract text based on file type
                text_content = extract_text(file_content, key)
                
                if not text_content.strip():
                    logger.warning(f"No text content extracted from {key}")
                    continue
                
                # Chunk the text into manageable pieces
                chunks = chunk_text(text_content)
                logger.info(f"Split {key} into {len(chunks)} chunks")
                
                # Process each chunk
                processed_chunks = 0
                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:  # Skip very short chunks
                        continue
                        
                    try:
                        # Generate embeddings using Bedrock
                        embedding = generate_embedding(bedrock_client, chunk)
                        
                        # Store in OpenSearch
                        store_in_opensearch(chunk, embedding, key, i)
                        logger.info(f"Generated embedding for chunk {i} of {key} (embedding size: {len(embedding)})")
                        processed_chunks += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk {i} of {key}: {str(e)}")
                        continue
                
                logger.info(f"Successfully processed {processed_chunks} chunks from {key}")
                
            except Exception as e:
                logger.error(f"Error processing file {key}: {str(e)}")
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing completed',
                'processed_files': len(event['Records'])
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def extract_text(file_content, filename):
    """
    Extract text from various file types
    """
    try:
        if filename.lower().endswith('.txt'):
            return file_content.decode('utf-8')
        elif filename.lower().endswith('.pdf'):
            # For now, return a placeholder - you'd use PyPDF2 here
            return "PDF text extraction would be implemented here with PyPDF2"
        elif filename.lower().endswith('.docx'):
            # For now, return a placeholder - you'd use python-docx here
            return "DOCX text extraction would be implemented here with python-docx"
        else:
            # Try to decode as text
            return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        return f"Error extracting text: {str(e)}"

def chunk_text(text, chunk_size=1000, overlap=100):
    """
    Split text into overlapping chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending within the last 100 characters
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start + chunk_size - 100:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def generate_embedding(bedrock_client, text):
    """
    Generate embeddings using AWS Bedrock Titan model
    """
    try:
        # Prepare the request for Titan embedding model
        body = json.dumps({
            "inputText": text
        })
        
        # Call Bedrock - try multiple models in order of preference
        models_to_try = [
            'amazon.titan-embed-text-v1',
            'amazon.titan-embed-text-v2:0',
            'cohere.embed-english-v3'
        ]
        
        last_error = None
        for model_id in models_to_try:
            try:
                response = bedrock_client.invoke_model(
                    modelId=model_id,
                    body=body,
                    contentType='application/json',
                    accept='application/json'
                )
                logger.info(f"Successfully used model: {model_id}")
                break
            except Exception as e:
                logger.warning(f"Model {model_id} failed: {str(e)}")
                last_error = e
                continue
        else:
            raise last_error or ValueError("No embedding models available")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])
        
        if not embedding:
            raise ValueError("No embedding returned from Bedrock")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def store_in_opensearch(content, embedding, source_file, chunk_index):
    """
    Store document chunk and embedding in OpenSearch
    """
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection
        
        # Get OpenSearch endpoint from environment
        opensearch_endpoint = os.environ['OPENSEARCH_ENDPOINT']
        
        # Remove protocol prefix if present
        clean_endpoint = opensearch_endpoint.replace('https://', '').replace('http://', '')
        
        client = OpenSearch(
            hosts=[{'host': clean_endpoint, 'port': 443}],
            http_auth=None,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        # Create index if it doesn't exist
        index_name = "documents"
        if not client.indices.exists(index=index_name):
            # Create index with vector mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "file_name": {"type": "keyword"},
                        "chunk_id": {"type": "integer"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimilarity"
                            }
                        }
                    }
                }
            }
            client.indices.create(index=index_name, body=mapping)
            logger.info(f"Created OpenSearch index: {index_name}")
        
        # Store document
        doc = {
            "content": content,
            "file_name": source_file,
            "chunk_id": chunk_index,
            "embedding": embedding
        }
        
        response = client.index(
            index=index_name,
            body=doc,
            id=f"{source_file}_{chunk_index}"
        )
        
        logger.info(f"Stored document chunk in OpenSearch: {response['_id']}")
        
    except Exception as e:
        logger.error(f"Error storing in OpenSearch: {str(e)}")
        raise