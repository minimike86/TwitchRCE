import asyncio
import logging

import boto3
import pytest
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from moto import mock_aws

from twitchrce.config import bot_config

MOCK_REFRESH_ACCESS_TOKEN_RESPONSE_SUCCESS = {
    "access_token": "access_token_xyz789",
    "refresh_token": "refresh_token_xyz789",
    "scope": ["channel:read:subscriptions", "channel:manage:polls"],
    "token_type": "bearer",
}
MOCK_REFRESH_ACCESS_TOKEN_RESPONSE_FAIL = {
    "error": "Bad Request",
    "status": 400,
    "message": "Invalid refresh token",
}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def set_environment_variables(monkeypatch):
    # Set default environment variables for all tests
    monkeypatch.setenv("CLIENT_ID", "12345")
    monkeypatch.setenv("CLIENT_SECRET", "abcde")
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-2")
    monkeypatch.setenv("REGION_NAME", "eu-west-2")
    monkeypatch.setenv("BOT_USER_ID", "875992093")
    monkeypatch.setenv("BOT_JOIN_CHANNEL", "#general")
    monkeypatch.setenv("BOT_JOIN_CHANNEL_ID", "123456")
    monkeypatch.setenv("MAX_VIP_SLOTS", "10")
    monkeypatch.setenv("VIRUS_TOTAL_API_KEY", "xyz")


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_get_app_token(mocker):
    from twitchrce.main import get_app_token

    mock_client_credentials_grant_flow_response = {
        "access_token": "access_token_xyz789",
        "expires_in": 12345,
        "token_type": "bearer",
    }

    mock_client_credentials_grant_flow = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.client_credentials_grant_flow"
    )
    mock_client_credentials_grant_flow.return_value = (
        mock_client_credentials_grant_flow_response
    )

    access_token = await get_app_token()
    assert access_token == "access_token_xyz789"
    mock_client_credentials_grant_flow.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_valid_token_is_valid(mocker):
    from twitchrce.main import check_valid_token

    mock_validate_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.validate_token"
    )
    mock_validate_token.return_value = True

    mock_user = {}

    is_valid_token = await check_valid_token(user=mock_user)
    assert bool(is_valid_token)
    mock_validate_token.assert_awaited_once()


@mock_aws
def test_check_valid_token_is_invalid(mocker):
    from twitchrce.main import check_valid_token

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_validate_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.validate_token"
    )
    mock_validate_token.side_effect = [False, True]

    mock_refresh_access_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.refresh_access_token"
    )
    mock_refresh_access_token.return_value = MOCK_REFRESH_ACCESS_TOKEN_RESPONSE_SUCCESS

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    mock_table_name = "user"
    mock_dynamodb.create_table(
        TableName=mock_table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # String
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(mock_table_name)
    mock_table.put_item(
        Item={
            "id": "123456",
            "access_token": "access_token_abc123",
            "client_id": BOT_CONFIG.get("twitch").get("client_id"),
            "expires_in": 12345,
            "login": "username_bot",
            "refresh_token": "refresh_token_abc123",
        }
    )
    mock_user_table = mocker.patch("twitchrce.main.user_table")
    mock_user_table.return_value = mock_table

    mock_user = {"id": "123", "login": "username_bot"}

    event_loop = asyncio.get_event_loop()
    is_valid_token = event_loop.run_until_complete(check_valid_token(user=mock_user))
    assert bool(is_valid_token)
    assert mock_validate_token.await_count == 2
    mock_validate_token.assert_awaited()
    mock_refresh_access_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_user_token_no_credentials(mocker):
    from twitchrce.main import refresh_user_token

    mock_refresh_access_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.refresh_access_token"
    )
    mock_refresh_access_token.return_value = MOCK_REFRESH_ACCESS_TOKEN_RESPONSE_SUCCESS

    mock_user_table_update_item = mocker.patch("twitchrce.main.user_table.update_item")
    mock_user_table_update_item.side_effect = (
        NoCredentialsError()
    )  # simulate missing AWS credentials

    mock_user = {"id": "123", "login": "username_bot"}

    with pytest.raises(NoCredentialsError):
        await refresh_user_token(mock_user)


@pytest.mark.asyncio
async def test_refresh_user_token_partial_credentials(mocker):
    from twitchrce.main import refresh_user_token

    mock_refresh_access_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.refresh_access_token"
    )
    mock_refresh_access_token.return_value = MOCK_REFRESH_ACCESS_TOKEN_RESPONSE_SUCCESS

    mock_user_table_update_item = mocker.patch("twitchrce.main.user_table.update_item")
    mock_user_table_update_item.side_effect = PartialCredentialsError(
        provider="mock_provider", cred_var="mock_cred_var"
    )  # simulate missing AWS credentials

    mock_user = {"id": "123", "login": "username_bot"}

    with pytest.raises(PartialCredentialsError):
        await refresh_user_token(mock_user)


@mock_aws
def test_main(mocker, capfd):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_client_credentials_grant_flow = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.client_credentials_grant_flow"
    )
    mock_client_credentials_grant_flow_response = {
        "access_token": "access_token_xyz789",
        "expires_in": 12345,
        "token_type": "bearer",
    }
    mock_client_credentials_grant_flow.return_value = (
        mock_client_credentials_grant_flow_response
    )

    mock_validate_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.validate_token"
    )
    mock_validate_token.return_value = True

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    mock_table_name = "user"
    mock_dynamodb.create_table(
        TableName=mock_table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # String
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(mock_table_name)
    mock_table.put_item(
        Item={
            "id": "123456",
            "access_token": "access_token_abc123",
            "client_id": BOT_CONFIG.get("twitch").get("client_id"),
            "expires_in": 12345,
            "login": "username_bot",
            "refresh_token": "refresh_token_abc123",
        }
    )
    mock_user_table = mocker.patch("twitchrce.main.user_table")
    mock_user_table.return_value = mock_table

    mock_describe_instances_response = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0100638f13e5451d8",
                        "PublicDnsName": "ec2-203-0-113-25.compute-1.amazonaws.com",
                        "State": {"Name": "running"},
                    }
                ]
            }
        ]
    }
    mock_describe_instances = mocker.patch("twitchrce.main.ec2.describe_instances")
    mock_describe_instances.return_value = mock_describe_instances_response

    mock_bot_psclient = mocker.patch("twitchrce.custom_bot.CustomBot.__psclient_init__")
    mock_bot_psclient.return_value = None

    mock_bot_esclient = mocker.patch("twitchrce.custom_bot.CustomBot.__esclient_init__")
    mock_bot_esclient.return_value = None

    mock_custom_bot_class = mocker.patch("twitchrce.custom_bot.CustomBot")
    mock_custom_bot_instance = mock_custom_bot_class.return_value
    mock_custom_bot_instance.run = mocker.AsyncMock()

    mock_twitchio_http_validate = mocker.patch("twitchio.http.TwitchHTTP.validate")
    mock_twitchio_http_validate_response = {
        "login": "login",
        "user_id": "user_id",
        "client_id": "client_id",
    }
    mock_twitchio_http_validate.return_value = mock_twitchio_http_validate_response

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(setup_bot())


@mock_aws
def test_setup_bot_if_bot_user_has_no_access_token_should_raise_value_error(mocker):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.main.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    mock_table_name = "user"
    mock_dynamodb.create_table(
        TableName=mock_table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # String
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(mock_table_name)
    mock_table.put_item(
        Item={
            "id": "875992093",
            "access_token": None,
            "client_id": BOT_CONFIG.get("twitch").get("client_id"),
            "expires_in": 12345,
            "login": "username_bot",
            "refresh_token": "refresh_token_abc123",
        }
    )

    mock_get_item = mocker.patch("twitchrce.main.user_table.get_item")
    mock_get_item.return_value = mock_table.get_item(
        Key={"id": BOT_CONFIG.get("twitch").get("bot_user_id")}
    )

    with pytest.raises(ValueError):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(setup_bot())


@mock_aws
def test_setup_bot_if_db_has_no_bot_user_should_raise_value_error(mocker):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.main.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    mock_table_name = "user"
    mock_dynamodb.create_table(
        TableName=mock_table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # String
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(mock_table_name)
    mock_get_item = mocker.patch("twitchrce.main.user_table.get_item")
    mock_get_item.return_value = mock_table.get_item(
        Key={"id": BOT_CONFIG.get("twitch").get("bot_user_id")}
    )

    with pytest.raises(ValueError):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(setup_bot())


@mock_aws
def test_setup_bot_if_bot_user_has_access_token_but_describe_instances_has_no_reservations(
    mocker, capfd
):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.main.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    mock_table_name = "user"
    mock_dynamodb.create_table(
        TableName=mock_table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},  # String
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )
    mock_table = mock_dynamodb.Table(mock_table_name)
    mock_table.put_item(
        Item={
            "id": "875992093",
            "access_token": "access_token_abc123",
            "client_id": BOT_CONFIG.get("twitch").get("client_id"),
            "expires_in": 12345,
            "login": "bot_user_id",
            "refresh_token": "refresh_token_abc123",
        }
    )

    mock_get_item = mocker.patch("twitchrce.main.user_table.get_item")
    mock_get_item.side_effect = [
        mock_table.get_item(
            Key={"id": BOT_CONFIG.get("twitch").get("bot_auth").get("bot_user_id")}
        ),
        mock_table.get_item(
            Key={
                "id": BOT_CONFIG.get("twitch").get("bot_initial_channels")[0].get("id")
            }
        ),
    ]

    mock_check_valid_token = mocker.patch("twitchrce.main.check_valid_token")
    mock_check_valid_token.return_value = True

    mock_describe_instances_response = {}
    mock_describe_instances = mocker.patch("twitchrce.main.ec2.describe_instances")
    mock_describe_instances.return_value = mock_describe_instances_response

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(setup_bot())
