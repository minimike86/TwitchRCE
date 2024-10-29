import json

import boto3
import urllib3
from botocore.exceptions import ClientError
from urllib3 import encode_multipart_formdata


def get_parameter(parameter_name):
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def get_secret(parameter):
    try:
        return get_parameter(parameter)
    except Exception:
        raise


def refresh_token(_refresh_token):
    # Retrieve client id from AWS Parameter Store
    # Retrieve client secret from AWS Parameter Store
    try:
        client_id = get_secret(
            "arn:aws:ssm:eu-west-2:339713094915:parameter/twitch/client_id"
        )  # TODO: Don't hardcode secret name arn
        client_secret = get_secret(
            "arn:aws:ssm:eu-west-2:339713094915:parameter/twitch/client_secret"
        )  # TODO: Don't hardcode secret name arn
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error retrieving secret: {str(e)}"}),
        }
    http = urllib3.PoolManager()
    try:
        url = "https://id.twitch.tv/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": _refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        encoded_data = encode_multipart_formdata(data)[1]
        headers = {"Content-Type": "application/x-www-form-urlencoded}"}
        response = http.request("POST", url, body=encoded_data, headers=headers)

        # Check if request was successful
        if response.status == 200:
            return True, json.loads(response.data.decode("utf-8"))
        else:
            return False, None
    finally:
        http.clear()


def store_in_dynamodb(_refresh_token, refresh_response):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("MSecBot_User")  # TODO: Don't hardcode dynamodb.Table name

    try:
        # Check if the item exists
        response = table.get_item(Key={"refresh_token": _refresh_token})
        if "Item" in response:
            # Item exists, update it
            table.update_item(
                Key={"refresh_token": _refresh_token},
                UpdateExpression="set access_token=:a, refresh_token=:r, scope=:s, token_type=:t",
                ExpressionAttributeValues={
                    ":a": refresh_response.get("access_token"),
                    ":r": refresh_response.get("refresh_token"),
                    ":s": refresh_response.get("scope"),
                    ":t": refresh_response.get("token_type"),
                },
            )
            return {
                "statusCode": 200,
                "body": json.dumps("Token updated successfully!"),
            }

        else:
            # Item does not exist, put it
            table.put_item(
                Item={
                    "access_token": (
                        refresh_response.get("access_token")
                        if refresh_response
                        else None
                    ),
                    "refresh_token": (
                        refresh_response.get("refresh_token")
                        if refresh_response
                        else None
                    ),
                    "scope": (
                        refresh_response.get("scope") if refresh_response else None
                    ),
                    "token_type": (
                        refresh_response.get("token_type") if refresh_response else None
                    ),
                }
            )
            return {"statusCode": 200, "body": json.dumps("Token stored successfully!")}
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f'Error: {e.response["Error"]["Message"]}'),
        }


def lambda_handler(event, _context):
    # Extract access token from query string parameters
    _refresh_token = event.get("queryStringParameters", {}).get("refresh_token")

    # Check if access token is present
    if not _refresh_token:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Refresh token missing"}),
        }

    # Validate access token
    is_refreshed, refresh_response = _refresh_token(refresh_token)

    if is_refreshed:
        # Update user refresh token in DynamoDB
        store_in_dynamodb(_refresh_token, refresh_response)
        return {
            "statusCode": 200,
            "body": json.dumps({"refresh_response": refresh_response}),
        }

    else:
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Token is not valid"}),
        }
