import json
import os

import boto3
import pytest
import responses
from botocore.exceptions import ClientError
from moto import mock_aws
from moto.ssm.exceptions import ParameterNotFound

from aws.lambdas.store_oauth_authorize_code import get_parameter, get_secret
from aws.lambdas.store_oauth_authorize_code import (
    lambda_handler as store_oauth_authorize_code_handler,
)
from aws.lambdas.store_oauth_authorize_code import store_in_dynamodb, validate_token


@pytest.fixture
def set_environment_variables(monkeypatch):
    monkeypatch.setenv("DYNAMODB_USER_TABLE_NAME", "MSecBot_User")


@mock_aws
def test_get_parameter_success():
    # Set up the mocked SSM service
    mock_ssm = boto3.client("ssm")
    parameter_name = "test_parameter"
    parameter_value = "test_value"

    # This simulates adding the parameter to the SSM Parameter Store
    mock_ssm.put_parameter(
        Name=parameter_name, Value=parameter_value, Type="String", Overwrite=True
    )

    # Call the function and verify the success case
    result = get_parameter(parameter_name=parameter_name)
    assert result == parameter_value


@mock_aws
def test_get_parameter_aws_client_error():
    # Simulate a general error when calling SSM
    with pytest.raises(ClientError) as exc_info:
        boto3.client("ssm").get_parameter(Name="invalid_name")

    # Verify that an error is raised
    assert exc_info.value.response["Error"]["Code"]


@mock_aws
def test_get_parameter_not_found():
    # Call the function with a non-existent parameter and verify it raises an error
    with pytest.raises(ClientError) as exc_info:
        get_parameter("non_existent_parameter")

    # Verify that the error is for a missing parameter
    assert exc_info.value.response["Error"]["Code"] == "ParameterNotFound"


@mock_aws
def test_get_parameter_access_denied():
    # Set up the mocked SSM service
    mock_ssm = boto3.client("ssm")
    parameter_name = "test_parameter"
    parameter_value = "test_value"

    # Add a parameter with SecureString (mocked by moto, but won't deny access by default)
    mock_ssm.put_parameter(
        Name=parameter_name, Value=parameter_value, Type="SecureString"
    )

    # Manually raise a ClientError to simulate access denial
    with pytest.raises(ClientError) as exc_info:
        # Raise the error manually to simulate an access-denied scenario
        raise ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to access parameter.",
                }
            },
            operation_name="GetParameter",
        )

    # Check that the error msecbot is "AccessDeniedException"
    assert exc_info.value.response["Error"]["Code"] == "AccessDeniedException"


@mock_aws
def test_get_parameter_incorrect_type(mocker):
    # Set up the mocked SSM service
    mock_ssm = boto3.client("ssm")
    parameter_name = "test_parameter"
    parameter_value = "test_value"

    # Add a parameter as SecureString, which requires decryption permissions
    mock_ssm.put_parameter(
        Name=parameter_name, Value=parameter_value, Type="SecureString"
    )

    # Patch `get_parameter` on the actual `ssm` client to simulate an AccessDeniedException
    # We'll patch it globally on the boto3 client, ensuring it's the one that's called
    mocker.patch(
        "boto3.client", return_value=mock_ssm
    )  # Ensure boto3.client returns the mock SSM client
    mocker.patch.object(
        mock_ssm,
        "get_parameter",
        side_effect=ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to decrypt the parameter.",
                }
            },
            operation_name="GetParameter",
        ),
    )

    # Test that `get_parameter` raises an AccessDeniedException due to decryption issue
    with pytest.raises(ClientError) as exc_info:
        get_parameter(parameter_name)

    # Assert that the correct error msecbot was raised
    assert exc_info.value.response["Error"]["Code"] == "AccessDeniedException"


@responses.activate
def test_validate_token_success():
    # Mock the response for the validation URL with a successful response
    responses.add(
        responses.GET,
        "https://id.twitch.tv/oauth2/validate",
        json={
            "client_id": "wbmytr93xzw8zbg0p1izqyzzc5mbiz",
            "login": "twitchdev",
            "scopes": ["channel:read:subscriptions"],
            "user_id": "141981764",
            "expires_in": 5520838,
        },
        status=200,
    )

    # Call the function and assert the expected result
    result, data = validate_token("valid_token")

    # Assert the expected result
    assert result is True
    assert data == {
        "client_id": "wbmytr93xzw8zbg0p1izqyzzc5mbiz",
        "login": "twitchdev",
        "scopes": ["channel:read:subscriptions"],
        "user_id": "141981764",
        "expires_in": 5520838,
    }


@responses.activate
def test_validate_token_invalid_access_token():
    # Mock the response for the validation URL with a failed response
    responses.add(
        responses.GET,
        "https://id.twitch.tv/oauth2/validate",
        json={"status": 401, "message": "invalid access token"},
        status=401,  # Bad request or invalid token
    )

    # Call the function and assert the expected result
    result, data = validate_token("invalid_token")

    # Assert the expected result
    assert result is False
    assert data == {"status": 401, "message": "invalid access token"}


def test_validate_token_exception(mocker):
    mock_requests = mocker.patch("requests.get")
    mock_requests.side_effect = TypeError("Unexpected error")

    # Call the function and check if it returns False and the correct error message
    result, data = validate_token("valid_token")

    assert result is False
    assert data == {"status": 500, "message": "Unexpected error"}


@mock_aws
def test_store_in_dynamodb_update_item_where_item_already_exists(
    set_environment_variables,
):
    from aws.lambdas.store_oauth_authorize_code import store_in_dynamodb

    # Insert an initial item into the table
    mock_dynamodb = boto3.resource("dynamodb")
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "N"},  # Number
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(table_name)
    mock_table.put_item(
        Item={
            "id": 123,
            "login": "existing_user",
            "access_token": "old_token",
            "expires_in": 1000,
            "refresh_token": "old_refresh_token",
            "client_id": "client_id",
            "scopes": ["old_scopes"],
        }
    )

    # The validation response and token response
    token_response = {
        "access_token": "new_token",
        "refresh_token": "new_refresh_token",
    }
    validation_response = {
        "user_id": 123,
        "login": "existing_user",
        "expires_in": 2000,
        "client_id": "client_id",
        "scopes": ["new_scopes"],
    }

    # Call the function
    store_in_dynamodb(token_response, validation_response)

    # Retrieve the updated item and assert values
    response = mock_table.get_item(Key={"id": int(validation_response.get("user_id"))})

    # Assert that the login was updated
    item = response.get("Item")

    # Ensure item exists and check the values
    assert item is not None, "Item should exist"
    assert item.get("login") == "existing_user"
    assert item.get("access_token") == "new_token"
    assert item.get("expires_in") == 2000
    assert item.get("refresh_token") == "new_refresh_token"
    assert item.get("client_id") == "client_id"
    assert item.get("scopes") == ["new_scopes"]


@mock_aws
def test_store_in_dynamodb_update_item_where_item_does_not_exist(
    set_environment_variables,
):
    # Insert an initial item into the table
    mock_dynamodb = boto3.resource("dynamodb")
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "N"},  # Number
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(table_name)

    # The validation response and token response
    token_response = {
        "access_token": "new_token",
        "refresh_token": "new_refresh_token",
    }
    validation_response = {
        "user_id": 123,
        "login": "existing_user",
        "expires_in": 2000,
        "client_id": "client_id",
        "scopes": ["new_scopes"],
    }

    # Call the function
    store_in_dynamodb(token_response, validation_response)

    # Retrieve the updated item and assert values
    response = mock_table.get_item(Key={"id": int(validation_response.get("user_id"))})

    # Assert that the login was updated
    item = response.get("Item")

    # Ensure item exists and check the values
    assert item is not None, "Item should exist"
    assert item.get("login") == "existing_user"
    assert item.get("access_token") == "new_token"
    assert item.get("expires_in") == 2000
    assert item.get("refresh_token") == "new_refresh_token"
    assert item.get("client_id") == "client_id"
    assert item.get("scopes") == ["new_scopes"]


@mock_aws
def test_store_in_dynamodb_type_error(set_environment_variables):
    # The validation response and token response
    token_response = {}
    validation_response = {}

    # Call the function
    actual = store_in_dynamodb(token_response, validation_response)
    assert actual.get("statusCode") == 500
    assert (
        actual.get("body")
        == "\"Error: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'\""
    )


@mock_aws
def test_store_in_dynamodb_client_error(mocker, set_environment_variables):
    mock_dynamodb = mocker.patch("boto3.session.Session.resource")
    mock_table = mocker.Mock()
    mock_table.get_item.side_effect = ClientError(
        operation_name="operation_name",
        error_response={"Error": {"Code": "ClientError", "Message": "Unknown"}},
    )
    mock_dynamodb.return_value.Table.return_value = mock_table

    # The validation response and token response
    token_response = {}
    validation_response = {"user_id": 123}

    # Call the function
    actual = store_in_dynamodb(token_response, validation_response)

    # Assert that the correct error msecbot was raised
    assert actual.get("statusCode") == 500
    assert actual.get("body") == '"Error: Unknown"'


@pytest.fixture
def mock_get_parameter(mocker):
    return mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter", autospec=True
    )


def test_get_secret_success(mock_get_parameter):
    # Simulate the behavior of get_parameter
    mock_get_parameter.return_value = "some_value"

    parameter = "test_parameter"

    # Call the function
    result = get_secret(parameter)

    # Ensure get_parameter was called
    mock_get_parameter.assert_called_once_with(parameter)

    # Assert that the result is what we expect
    assert result == "some_value"


def test_get_secret_failure(mock_get_parameter):
    # Simulate the behavior of get_parameter raising an exception
    mock_get_parameter.side_effect = Exception("Error retrieving parameter")

    parameter = "test_parameter"

    # Call the function and ensure it raises an exception
    with pytest.raises(Exception):
        get_secret(parameter)

    # Ensure get_parameter was called
    mock_get_parameter.assert_called_once_with(parameter)


@mock_aws
def test_lambda_handler_success(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_get_parameter = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter"
    )
    mock_get_parameter.return_value = "redirect_uri"

    mock_token_response = mocker.Mock()
    mock_token_response.status_code = 200
    mock_response = mocker.patch("requests.post")
    mock_response.return_value = mock_token_response

    mock_json_loads = mocker.patch("json.loads")
    mock_json_loads.return_value = {
        "access_token": "jostpf5q0uzmxmkba9iyug38kjtgh",
        "expires_in": 5011271,
        "token_type": "bearer",
    }

    mock_validate_token = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.validate_token"
    )
    mock_validate_token.return_value = True, json.dumps(
        {
            "client_id": "wbmytr93xzw8zbg0p1izqyzzc5mbiz",
            "login": "twitchdev",
            "scopes": ["channel:read:subscriptions"],
            "user_id": "141981764",
            "expires_in": 5520838,
        }
    )

    mock_store_in_dynamodb = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.store_in_dynamodb"
    )
    mock_store_in_dynamodb.return_value = None

    event_in = {
        "body": "eyJ0ZXN0IjoiYm9keSJ9",
        "resource": "/{proxy+}",
        "path": "/path/to/resource",
        "httpMethod": "POST",
        "isBase64Encoded": True,
        "queryStringParameters": {
            "code": "jath2p663cpl35wikfhd2d1qds5t4x",
            "state": "875992093",
            "scope": "user%3Aread%3Achat+user%3Awrite%3Achat+moderator%3Aread%3Asuspicious_users+moderator%3Aread%3A"
            "chatters+user%3Amanage%3Achat_color+moderator%3Amanage%3Achat_messages+moderator%3Amanage%3A"
            "chat_settings+moderator%3Aread%3Achat_settings+chat%3Aread+chat%3Aedit+user%3Aread%3A"
            "email+user%3Aedit%3Abroadcast+user%3Aread%3Abroadcast+clips%3Aedit+bits%3Aread+channel%3A"
            "moderate+channel%3Aread%3Asubscriptions+whispers%3Aread+whispers%3Aedit+moderation%3A"
            "read+channel%3Aread%3Aredemptions+channel%3Aedit%3Acommercial+channel%3Aread%3A"
            "hype_train+channel%3Amanage%3Abroadcast+user%3Aedit%3Afollows+channel%3Amanage%3A"
            "redemptions+user%3Aread%3Ablocked_users+user%3Amanage%3Ablocked_users+user%3Aread%3A"
            "subscriptions+user%3Aread%3Afollows+channel%3Amanage%3Apolls+channel%3Amanage%3A"
            "predictions+channel%3Aread%3Apolls+channel%3Aread%3Apredictions+moderator%3Amanage%3A"
            "automod+channel%3Aread%3Agoals+moderator%3Aread%3Aautomod_settings+moderator%3Amanage%3A"
            "banned_users+moderator%3Aread%3Ablocked_terms+moderator%3Amanage%3Ablocked_terms+channel%3A"
            "manage%3Araids+moderator%3Amanage%3Aannouncements+channel%3Aread%3Avips+channel%3Amanage%3A"
            "vips+user%3Amanage%3Awhispers+channel%3Aread%3Acharity+moderator%3Aread%3A"
            "shield_mode+moderator%3Amanage%3Ashield_mode+moderator%3Aread%3Ashoutouts+moderator%3A"
            "manage%3Ashoutouts+moderator%3Aread%3Afollowers+channel%3Aread%3Aguest_star+channel%3A"
            "manage%3Aguest_star+moderator%3Aread%3Aguest_star+moderator%3Amanage%3Aguest_star+channel%3A"
            "bot+user%3Abot+channel%3Aread%3Aads+user%3Aread%3Amoderated_channels+user%3Aread%3A"
            "emotes+moderator%3Aread%3Aunban_requests+moderator%3Amanage%3Aunban_requests+channel%3A"
            "read%3Aeditors+analytics%3Aread%3Agames+analytics%3Aread%3Aextensions",
        },
        "multiValueQueryStringParameters": {"foo": ["bar"]},
        "pathParameters": {"proxy": "/path/to/resource"},
        "stageVariables": {"baz": "qux"},
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "US",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Custom User Agent String",
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
        },
        "multiValueHeaders": {
            "Accept": [
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            ],
            "Accept-Encoding": ["gzip, deflate, sdch"],
            "Accept-Language": ["en-US,en;q=0.8"],
            "Cache-Control": ["max-age=0"],
            "CloudFront-Forwarded-Proto": ["https"],
            "CloudFront-Is-Desktop-Viewer": ["true"],
            "CloudFront-Is-Mobile-Viewer": ["false"],
            "CloudFront-Is-SmartTV-Viewer": ["false"],
            "CloudFront-Is-Tablet-Viewer": ["false"],
            "CloudFront-Viewer-Country": ["US"],
            "Host": ["0123456789.execute-api.us-east-1.amazonaws.com"],
            "Upgrade-Insecure-Requests": ["1"],
            "User-Agent": ["Custom User Agent String"],
            "Via": ["1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)"],
            "X-Amz-Cf-Id": ["cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA=="],
            "X-Forwarded-For": ["127.0.0.1, 127.0.0.2"],
            "X-Forwarded-Port": ["443"],
            "X-Forwarded-Proto": ["https"],
        },
        "requestContext": {
            "accountId": "123456789012",
            "resourceId": "123456",
            "stage": "prod",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "requestTime": "09/Apr/2015:12:34:56 +0000",
            "requestTimeEpoch": 1428582896000,
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "accessKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None,
            },
            "path": "/prod/path/to/resource",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "apiId": "1234567890",
            "protocol": "HTTP/1.1",
        },
    }

    actual = store_oauth_authorize_code_handler(event=event_in, _context={})

    assert actual.get("statusCode") == 200
    assert actual.get("body") == (
        '{"access_token": "jostpf5q0uzmxmkba9iyug38kjtgh", '
        '"expires_in": 5011271, '
        '"token_type": "bearer"}'
    )


def test_lambda_handler_code_is_none():
    event_in = {"queryStringParameters": {"code": None}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 400
    assert json.loads(actual.get("body")).get("message") == "Code parameter missing"


def test_lambda_handler_get_secret_parameter_not_found(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ParameterNotFound(message="message")

    event_in = {"queryStringParameters": {"code": "code"}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert json.loads(actual.get("body")).get("message") == (
        'Error retrieving secret: 400 Bad Request: {"__type": "ParameterNotFound", '
        '"message": "message"}'
    )


def test_lambda_handler_get_secret_exception(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = Exception

    event_in = {"queryStringParameters": {"code": "code"}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert json.loads(actual.get("body")).get("message") == (
        "Error retrieving secret: "
    )


def test_lambda_handler_get_parameter_exception(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_get_parameter = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter"
    )
    mock_get_parameter.side_effect = Exception

    event_in = {"queryStringParameters": {"code": "code"}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert json.loads(actual.get("body")).get("message") == (
        "Error retrieving redirect uri: "
    )


def test_lambda_handler_invalid_token_response(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_get_parameter = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter"
    )
    mock_get_parameter.return_value = "redirect_uri"

    mock_token_response = mocker.Mock()
    mock_token_response.status_code = 200
    mock_json = mocker.Mock()
    mock_token_response.json.return_value = mock_json
    mock_json.decode.return_value = json.dumps(
        {
            "access_token": "jostpf5q0uzmxmkba9iyug38kjtgh",
            "expires_in": 5011271,
            "token_type": "bearer",
        }
    )
    mock_response = mocker.patch("requests.post")
    mock_response.return_value = mock_token_response

    mock_validate_token = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.validate_token"
    )
    mock_validate_token.return_value = False, json.dumps(
        {"status": 401, "message": "invalid access token"}
    )

    event_in = {"queryStringParameters": {"code": "code"}}
    actual_result = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual_result.get("statusCode") == 401
    actual_message = json.loads(actual_result.get("body")).get("message")
    assert actual_message == "Token is not valid"


def test_lambda_handler_failed_token_response(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_get_parameter = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter"
    )
    mock_get_parameter.return_value = "redirect_uri"

    mock_token_response = mocker.Mock()
    mock_token_response.status_code = 500
    mock_json = mocker.Mock()
    mock_token_response.json.return_value = mock_json
    mock_json.decode.return_value = json.dumps({})
    mock_response = mocker.patch("requests.post")
    mock_response.return_value = mock_token_response

    event_in = {"queryStringParameters": {"code": "code"}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert json.loads(actual.get("body")).get("message") == (
        "Failed to retrieve access token"
    )


def test_lambda_handler_http_error_response(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.store_oauth_authorize_code.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_get_parameter = mocker.patch(
        "aws.lambdas.store_oauth_authorize_code.get_parameter"
    )
    mock_get_parameter.return_value = "redirect_uri"

    mocker.patch("requests.post", side_effect=Exception("Mocked exception"))

    event_in = {"queryStringParameters": {"code": "code"}}
    actual = store_oauth_authorize_code_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert json.loads(actual.get("body")).get("error") == "Mocked exception"
