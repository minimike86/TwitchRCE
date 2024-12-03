import json
import logging
import os
from typing import Tuple

import boto3
import requests
from botocore.exceptions import ClientError
from urllib3 import encode_multipart_formdata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_parameter(parameter_name):
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def get_secret(parameter):
    try:
        return get_parameter(parameter)
    except Exception:
        raise


def refresh_token(_refresh_token: str) -> Tuple[bool, any]:
    # Retrieve client id from AWS Parameter Store
    # Retrieve client secret from AWS Parameter Store
    # TODO: Don't hardcode secret name arn needs to fetch from env_var
    client_id_param_arn = (
        "arn:aws:ssm:eu-west-2:339713094915:parameter/twitch/client_id"
    )
    client_secret_param_arn = (
        "arn:aws:ssm:eu-west-2:339713094915:parameter/twitch/client_secret"
    )
    try:
        client_id = get_secret(client_id_param_arn)
        client_secret = get_secret(client_secret_param_arn)
    except Exception as exception:
        raise exception

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
        response = requests.post(url, data=encoded_data, headers=headers)

        # Check if request was successful
        if response.status_code == 200:
            return True, json.loads(response.json())
        else:
            return False, json.loads(response.json())

    except Exception as exception:
        raise exception


def store_in_dynamodb(_refresh_token, refresh_response):
    """
    Stores or updates the refresh and access tokens in DynamoDB.

    Parameters:
    - _refresh_token: The current refresh token held by the system.
    - refresh_response: The result of a web request for a new token, containing the access token,
      refresh token, scope, and token type.

    Returns:
    - A dictionary with the HTTP status code and a message about the operation.
    """
    dynamodb = boto3.resource("dynamodb")
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    table = dynamodb.Table(table_name)

    try:
        # Check if the item exists
        get_item_outcome = table.get_item(Key={"refresh_token": _refresh_token})
        if "Item" in get_item_outcome:
            # Item exists, update it
            table.update_item(
                Key={"id": int(get_item_outcome["Item"]["id"])},
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
    except ClientError as client_error:
        logger.error(f"[client_error]: {client_error.response['Error']['Message']}")
        return {
            "statusCode": 500,
            "body": json.dumps(f'Error: {client_error.response["Error"]["Message"]}'),
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
    try:
        is_refreshed, refresh_response = refresh_token(_refresh_token)
    except Exception as exception:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Error retrieving secret: {str(exception)}"}
            ),
        }

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
