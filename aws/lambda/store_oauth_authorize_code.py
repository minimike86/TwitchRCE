import json

import boto3
import urllib3
from botocore.exceptions import ClientError


def get_parameter(parameter_name):
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def validate_token(access_token):
    http = urllib3.PoolManager()
    try:
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"OAuth {access_token}"}
        response = http.request("GET", url, headers=headers)

        # Check if request was successful
        if response.status == 200:
            return True, json.loads(response.data.decode("utf-8"))
        else:
            return False, None
    finally:
        http.clear()


def store_in_dynamodb(token_response, validation_response):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("MSecBot_User")  # TODO: Don't hardcode dynamodb.Table name

    try:
        # Check if the item exists
        response = table.get_item(Key={"id": int(validation_response.get("user_id"))})
        if "Item" in response:
            # Item exists, update it
            table.update_item(
                Key={"id": int(validation_response.get("user_id"))},
                UpdateExpression="set login=:l, "
                "access_token=:a, "
                "expires_in=:e, "
                "refresh_token=:r, "
                "client_id=:c, "
                "scopes=:s",
                ExpressionAttributeValues={
                    ":l": validation_response.get("login"),
                    ":a": token_response.get("access_token"),
                    ":e": validation_response.get("expires_in"),
                    ":r": token_response.get("refresh_token"),
                    ":c": validation_response.get("client_id"),
                    ":s": validation_response.get("scopes"),
                },
            )
        else:
            # Item does not exist, put it
            table.put_item(
                Item={
                    "id": int(validation_response.get("user_id")),
                    "login": validation_response.get("login"),
                    "access_token": token_response.get("access_token"),
                    "expires_in": validation_response.get("expires_in"),
                    "refresh_token": token_response.get("refresh_token"),
                    "client_id": validation_response.get("client_id"),
                    "scopes": validation_response.get("scopes"),
                }
            )
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f'Error: {e.response["Error"]["Message"]}'),
        }


def get_secret(parameter):
    try:
        return get_parameter(parameter)
    except Exception:
        raise


def lambda_handler(event, _context):
    # Extract code from query string parameters
    code = event.get("queryStringParameters", {}).get("code")

    # Check if code is present
    if not code:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Code parameter missing"}),
        }

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

    # Retrieve redirect_uri from AWS Parameter Store
    try:
        redirect_uri = get_parameter(
            "arn:aws:ssm:eu-west-2:339713094915:parameter/twitch/oath2/redirect_url"
        )  # TODO: Don't hardcode twitch/oath2/redirect_url arn
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error retrieving redirect uri: {str(e)}"}),
        }

    # Define parameters for POST request
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    encoded_params = json.dumps(params).encode("utf-8")

    # Make POST request to Twitch API
    http = urllib3.PoolManager()
    try:
        url = "https://id.twitch.tv/oauth2/token"
        headers = {"Content-Type": "application/json"}
        response = http.request("POST", url, body=encoded_params, headers=headers)

        # Check if request was successful
        if response.status == 200:
            # Parse the JSON response
            token_response = json.loads(response.data.decode("utf-8"))

            # Check received token is valid and grab extra metadata
            is_valid, validation_response = validate_token(
                token_response.get("access_token")
            )

            if is_valid:
                # Store validation response in DynamoDB
                store_in_dynamodb(token_response, validation_response)

                return {"statusCode": 200, "body": response.data.decode("utf-8")}

            else:
                return {
                    "statusCode": 401,
                    "body": json.dumps({"message": "Token is not valid"}),
                }

        else:
            return {
                "statusCode": response.status,
                "body": json.dumps({"message": "Failed to retrieve access token"}),
            }

    finally:
        http.clear()
