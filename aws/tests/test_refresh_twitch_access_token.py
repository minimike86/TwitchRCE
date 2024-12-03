import json
import os

import boto3
import pytest
import responses
from botocore.exceptions import ClientError
from moto import mock_aws

from aws.lambdas.refresh_twitch_access_token import get_parameter, get_secret
from aws.lambdas.refresh_twitch_access_token import (
    lambda_handler as refresh_twitch_access_token_handler,
)
from aws.lambdas.refresh_twitch_access_token import refresh_token, store_in_dynamodb


@pytest.fixture
def set_environment_variables(monkeypatch):
    monkeypatch.setenv("DYNAMODB_USER_TABLE_NAME", "MSecBot_User")


@pytest.fixture
def db_item():
    return dict(
        id=875992093,
        access_token="access_token",
        expires_in=12345,
        login="login",
        refresh_token="refresh_token_xyz789",
        scopes=[
            {"S": "analytics:read:extensions"},
            {"S": "analytics:read:games"},
            {"S": "bits:read"},
            {"S": "channel:bot"},
            {"S": "channel:edit:commercial"},
            {"S": "channel:manage:broadcast"},
            {"S": "channel:manage:guest_star"},
            {"S": "channel:manage:polls"},
            {"S": "channel:manage:predictions"},
            {"S": "channel:manage:raids"},
            {"S": "channel:manage:redemptions"},
            {"S": "channel:manage:vips"},
            {"S": "channel:moderate"},
            {"S": "channel:read:ads"},
            {"S": "channel:read:charity"},
            {"S": "channel:read:editors"},
            {"S": "channel:read:goals"},
            {"S": "channel:read:guest_star"},
            {"S": "channel:read:hype_train"},
            {"S": "channel:read:polls"},
            {"S": "channel:read:predictions"},
            {"S": "channel:read:redemptions"},
            {"S": "channel:read:subscriptions"},
            {"S": "channel:read:vips"},
            {"S": "chat:edit"},
            {"S": "chat:read"},
            {"S": "clips:edit"},
            {"S": "moderation:read"},
            {"S": "moderator:manage:announcements"},
            {"S": "moderator:manage:automod"},
            {"S": "moderator:manage:banned_users"},
            {"S": "moderator:manage:blocked_terms"},
            {"S": "moderator:manage:chat_messages"},
            {"S": "moderator:manage:chat_settings"},
            {"S": "moderator:manage:guest_star"},
            {"S": "moderator:manage:shield_mode"},
            {"S": "moderator:manage:shoutouts"},
            {"S": "moderator:manage:unban_requests"},
            {"S": "moderator:read:automod_settings"},
            {"S": "moderator:read:blocked_terms"},
            {"S": "moderator:read:chat_settings"},
            {"S": "moderator:read:chatters"},
            {"S": "moderator:read:followers"},
            {"S": "moderator:read:guest_star"},
            {"S": "moderator:read:shield_mode"},
            {"S": "moderator:read:shoutouts"},
            {"S": "moderator:read:suspicious_users"},
            {"S": "moderator:read:unban_requests"},
            {"S": "user:bot"},
            {"S": "user:edit:broadcast"},
            {"S": "user:edit:follows"},
            {"S": "user:manage:blocked_users"},
            {"S": "user:manage:chat_color"},
            {"S": "user:manage:whispers"},
            {"S": "user:read:blocked_users"},
            {"S": "user:read:broadcast"},
            {"S": "user:read:chat"},
            {"S": "user:read:email"},
            {"S": "user:read:emotes"},
            {"S": "user:read:follows"},
            {"S": "user:read:moderated_channels"},
            {"S": "user:read:subscriptions"},
            {"S": "user:write:chat"},
            {"S": "whispers:edit"},
            {"S": "whispers:read"},
        ],
    )


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


@pytest.fixture
def mock_get_parameter(mocker):
    return mocker.patch(
        "aws.lambdas.refresh_twitch_access_token.get_parameter", autospec=True
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


@responses.activate
def test_refresh_token_success_path(mocker):
    """
    If the request succeeds, the response contains the new access token, refresh token, and scopes associated with
    the new grant. Because refresh tokens may change, your app should safely store the new refresh token to use the
    next time.

    https://dev.twitch.tv/docs/authentication/refresh-tokens/
    """
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    expected_response = json.dumps(
        {
            "access_token": "1ssjqsqfy6bads1ws7m03gras79zfr",
            "refresh_token": "eyJfMzUtNDU0OC4MWYwLTQ5MDY5ODY4NGNlMSJ9%asdfasdf=",
            "scope": ["channel:read:subscriptions", "channel:manage:polls"],
            "token_type": "bearer",
        }
    )
    responses.add(
        method=responses.POST,
        url="https://id.twitch.tv/oauth2/token",
        json=expected_response,
        status=200,
    )

    actual_success, actual_json = refresh_token(_refresh_token="refresh_token")

    assert actual_success is True
    assert actual_json.get("access_token") == "1ssjqsqfy6bads1ws7m03gras79zfr"
    assert (
        actual_json.get("refresh_token")
        == "eyJfMzUtNDU0OC4MWYwLTQ5MDY5ODY4NGNlMSJ9%asdfasdf="
    )
    assert actual_json.get("scope")[0] == "channel:read:subscriptions"
    assert actual_json.get("scope")[1] == "channel:manage:polls"
    assert actual_json.get("token_type") == "bearer"


def test_refresh_token_get_secret_raises_exception(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = Exception("some exception")

    with pytest.raises(Exception):
        refresh_token("_refresh_token")


def test_refresh_token_requests_post_raises_exception(mocker):
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    mock_requests_post = mocker.patch("requests.post")
    mock_requests_post.side_effect = Exception("some exception")

    with pytest.raises(Exception):
        refresh_token("_refresh_token")


def test_refresh_token_invalid_token(mocker):
    """
    Refresh tokens, like access tokens, can become invalid if the user changes their password or disconnects your
    app. Most refresh tokens do not expire, but refresh tokens generated by a Public client type will expire 30
    days after they are generated, which will invalidate the refresh token. Most applications are set to the
    Confidential client type, of which the refresh tokens do not have an expiration time.

    A refresh request can fail with HTTP status code 401 Unauthorized if the refresh token is no longer valid. If
    the refresh fails, the application should re-prompt the end user for consent using the Authorization Code Grant
    flow or OIDC Authorization Code Grant flow.

    https://dev.twitch.tv/docs/authentication/refresh-tokens/
    """
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    expected_response = json.dumps(
        {
            "error": "Bad Request",
            "status": 400,
            "message": "Invalid refresh token",
        }
    )
    responses.add(
        method=responses.POST,
        url="https://id.twitch.tv/oauth2/token",
        json=expected_response,
        status=400,
    )

    actual_success, actual_json = refresh_token(_refresh_token="refresh_token")

    assert actual_success is False
    assert actual_json.get("error") == "Bad Request"
    assert actual_json.get("status") == 400
    assert actual_json.get("message") == "Invalid refresh token"


@responses.activate
@mock_aws
def test_refresh_twitch_access_token_handler_success(mocker, set_environment_variables):
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    expected_token_refresh_response = json.dumps(
        {
            "access_token": "1ssjqsqfy6bads1ws7m03gras79zfr",
            "refresh_token": "eyJfMzUtNDU0OC4MWYwLTQ5MDY5ODY4NGNlMSJ9%asdfasdf=",
            "scope": ["channel:read:subscriptions", "channel:manage:polls"],
            "token_type": "bearer",
        }
    )
    responses.add(
        method=responses.POST,
        url="https://id.twitch.tv/oauth2/token",
        json=expected_token_refresh_response,
        status=200,
    )

    event_in = {"queryStringParameters": {"refresh_token": "refresh_token"}}

    actual = refresh_twitch_access_token_handler(event=event_in, _context={})
    actual_refresh_response = json.loads(actual.get("body")).get("refresh_response")

    assert actual.get("statusCode") == 200
    assert (
        actual_refresh_response.get("access_token") == "1ssjqsqfy6bads1ws7m03gras79zfr"
    )
    assert (
        actual_refresh_response.get("refresh_token")
        == "eyJfMzUtNDU0OC4MWYwLTQ5MDY5ODY4NGNlMSJ9%asdfasdf="
    )
    assert actual_refresh_response.get("scope")[0] == "channel:read:subscriptions"
    assert actual_refresh_response.get("scope")[1] == "channel:manage:polls"
    assert actual_refresh_response.get("token_type") == "bearer"


def test_refresh_twitch_access_token_handler_missing_refresh_token():
    event_in = {"queryStringParameters": {}}

    actual = refresh_twitch_access_token_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 400
    assert json.loads(actual.get("body")).get("message") == "Refresh token missing"


def test_refresh_twitch_access_token_handler_refresh_token_raises_exception(mocker):
    mock_refresh_token = mocker.patch(
        "aws.lambdas.refresh_twitch_access_token.refresh_token"
    )
    mock_refresh_token.side_effect = Exception("some exception")

    event_in = {"queryStringParameters": {"refresh_token": "refresh_token"}}

    actual = refresh_twitch_access_token_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 500
    assert (
        json.loads(actual.get("body")).get("message")
        == "Error retrieving secret: some exception"
    )


def test_refresh_twitch_access_token_handler_refresh_token_fails_to_refresh_token(
    mocker,
):
    mock_refresh_token = mocker.patch(
        "aws.lambdas.refresh_twitch_access_token.refresh_token"
    )
    mock_refresh_token.return_value = False, json.dumps(
        {
            "error": "Bad Request",
            "status": 400,
            "message": "Invalid refresh token",
        }
    )

    event_in = {"queryStringParameters": {"refresh_token": "refresh_token"}}

    actual = refresh_twitch_access_token_handler(event=event_in, _context={})
    assert actual.get("statusCode") == 401
    assert json.loads(actual.get("body")).get("message") == "Token is not valid"


@responses.activate
@mock_aws
def test_refresh_twitch_access_token_handler_store_in_dynamodb_put_and_update(
    mocker, set_environment_variables, db_item
):
    mock_get_secret = mocker.patch("aws.lambdas.refresh_twitch_access_token.get_secret")
    mock_get_secret.side_effect = ["client_id", "client_secret"]

    expected_token_refresh_response = json.dumps(
        {
            "access_token": "access_token%s1ws7m03gras79zfr",
            "refresh_token": "refresh_token%asdfasdf=",
            "scope": ["channel:read:subscriptions", "channel:manage:polls"],
            "token_type": "bearer",
        }
    )
    responses.add(
        method=responses.POST,
        url="https://id.twitch.tv/oauth2/token",
        json=expected_token_refresh_response,
        status=200,
    )

    # Set up mock DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "refresh_token", "KeyType": "HASH"},  # Sort key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "N"},
            {"AttributeName": "refresh_token", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    mock_table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    mock_table.put_item(
        Item={
            "id": 123,
            "login": "existing_user",
            "access_token": "stale_access_token",
            "expires_in": 1000,
            "refresh_token": "active_refresh_token",
            "client_id": "client_id",
            "scopes": ["old_scopes"],
        }
    )

    # Test Case 1: Insert new token
    _refresh_response_first = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "scope": "new_scope",
        "token_type": "bearer",
    }
    result_insert = store_in_dynamodb("active_refresh_token", _refresh_response_first)

    # Assertions for new token insert
    assert result_insert["statusCode"] == 500
    assert (
        json.loads(result_insert["body"])
        == "Error: The provided key element does not match the schema"
    )
