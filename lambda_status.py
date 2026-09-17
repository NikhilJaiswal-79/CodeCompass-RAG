import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "IngestionStatus")

def lambda_handler(event, context):
    """
    Status Lambda:
    - Receives HTTP API Gateway requests (GET /status?repo=...).
    - Checks DynamoDB for the current ingestion status of the repository.
    - Returns the status to the frontend.
    """
    try:
        # Get query string parameters
        query_params = event.get('queryStringParameters', {})
        repo_id = query_params.get('repo')
        
        if not repo_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'repo' query parameter."})
            }
            
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'repo_id': repo_id})
        
        if 'Item' not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"status": "not_found", "message": "Repository not ingested yet."})
            }
            
        item = response['Item']
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "repo_id": item.get('repo_id'),
                "status": item.get('status'),
                "error": item.get('error')
            })
        }
        
    except Exception as e:
        print(f"Status Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
