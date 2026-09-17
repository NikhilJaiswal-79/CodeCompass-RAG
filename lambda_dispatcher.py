import json
import os
import boto3

# Initialize AWS clients outside the handler for connection reuse
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Ensure these environment variables are set in the AWS Lambda configuration
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "IngestionStatus")
WORKER_LAMBDA_NAME = os.environ.get("WORKER_LAMBDA_NAME")

def extract_repo_id(url: str) -> str:
    url = url.strip().rstrip("/")
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}-{parts[-1]}"
    return "unknown-repo"

def lambda_handler(event, context):
    """
    Dispatcher Lambda: 
    - Receives HTTP API Gateway requests (POST /ingest).
    - Writes the initial "indexing" state to DynamoDB.
    - Asynchronously triggers the heavy Ingestion Worker Lambda.
    - Returns a 202 Accepted instantly to bypass the 29-second API Gateway timeout.
    """
    try:
        # Parse the incoming JSON body
        body = json.loads(event.get('body', '{}'))
        repo_url = body.get('repo_url')
        
        if not repo_url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'repo_url' in request body."})
            }
            
        repo_id = extract_repo_id(repo_url)
        force_reindex = body.get('force_reindex', False)
        
        # 1. Check if already indexed (Cache Check)
        table = dynamodb.Table(TABLE_NAME)
        if not force_reindex:
            try:
                response = table.get_item(Key={'repo_id': repo_id})
                if 'Item' in response and response['Item'].get('status') == 'completed':
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                        },
                        "body": json.dumps({
                            "message": "Already indexed. Skipping background ingestion.",
                            "repo_id": repo_id
                        })
                    }
            except Exception as e:
                print(f"Warning: Cache check failed: {e}")
            
        # 2. Write the initial state to DynamoDB
        table.put_item(
            Item={
                'repo_id': repo_id,
                'status': 'indexing',
                'repo_url': repo_url
            }
        )
        
        # 2. Asynchronously invoke the Heavy Worker Lambda
        if WORKER_LAMBDA_NAME:
            payload = {
                "repo_url": repo_url,
                "repo_id": repo_id
            }
            
            # InvocationType='Event' guarantees it fires asynchronously in the background
            lambda_client.invoke(
                FunctionName=WORKER_LAMBDA_NAME,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
        else:
            print("WARNING: WORKER_LAMBDA_NAME environment variable not set. Cannot invoke worker.")

        # 3. Return immediately to the frontend
        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" # CORS for frontend
            },
            "body": json.dumps({
                "message": "Ingestion started in the background.",
                "repo_id": repo_id
            })
        }
        
    except Exception as e:
        print(f"Dispatcher Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
