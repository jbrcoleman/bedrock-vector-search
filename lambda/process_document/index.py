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
                        
                        # Store in OpenSearch (simplified for now - just log)
                        logger.info(f"Generated embedding for chunk {i} of {key} (embedding size: {len(embedding)})")
                        processed_chunks += 1
                        
                        # In a real implementation, you would store this in OpenSearch here
                        # store_in_opensearch(chunk, embedding, key, i)
                        
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
        
        # Call Bedrock
        response = bedrock_client.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        
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
    This is a placeholder - you would implement the actual OpenSearch client here
    """
    # This function would use opensearch-py to store the data
    # For now, it's just a placeholder
    pass