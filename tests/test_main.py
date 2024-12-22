import asyncio
import logging
import os

import boto3
import pytest
from moto import mock_aws
from twitchio import AuthenticationError, BroadcasterTypeEnum, UserTypeEnum

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
    level=logging.INFO,
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
    monkeypatch.setenv("DYNAMODB_USER_TABLE_NAME", "User")


@pytest.fixture
def bot_user(mocker):
    bot_user = mocker.Mock()
    bot_user.id = 123456789
    bot_user.name = "name"
    bot_user.display_name = "display_name"
    bot_user.type = UserTypeEnum.none
    bot_user.broadcaster_type = BroadcasterTypeEnum.none
    bot_user.description = "description"
    return bot_user


@pytest.fixture
def db_item_with_missing_access_token():
    return dict(
        id=875992093,
        access_token=None,
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
def test_main(mocker, capfd, bot_user):
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
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_dynamodb.create_table(
        TableName=table_name,
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
    mock_table = mock_dynamodb.Table(table_name)
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

    mock_bot_fetch_users = mocker.patch("twitchio.client.Client.fetch_users")
    mock_bot_fetch_users.return_value = [bot_user]

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
def test_setup_bot_if_bot_user_has_no_access_token_should_raise_value_error(
    mocker, db_item_with_missing_access_token
):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.utils.utils.Utils.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_table = mock_dynamodb.create_table(
        TableName=table_name,
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
    mock_table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    mock_table.put_item(
        Item={
            "id": "875992093",
            "access_token": "invalid_token",
            "client_id": BOT_CONFIG.get("twitch").get("client_id"),
            "expires_in": 12345,
            "login": "username_bot",
            "refresh_token": "refresh_token_abc123",
        }
    )
    mock_user_table = mocker.patch("twitchrce.main.user_table")
    mock_user_table.return_value = mock_table

    mock_get_item = mocker.patch("twitchrce.main.user_table.get_item")
    mock_get_item.return_value = {"Item": db_item_with_missing_access_token}

    with pytest.raises(
        AuthenticationError, match="Invalid or unauthorized Access Token passed."
    ):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(setup_bot())


@mock_aws
def test_setup_bot_if_db_has_no_bot_user_should_raise_value_error(mocker):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.utils.utils.Utils.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_dynamodb.create_table(
        TableName=table_name,
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
    mock_table = mock_dynamodb.Table(table_name)
    mock_get_item = mocker.patch("twitchrce.main.user_table.get_item")
    mock_get_item.return_value = mock_table.get_item(
        Key={"id": BOT_CONFIG.get("twitch").get("bot_user_id")}
    )

    with pytest.raises((RuntimeError, ValueError)):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(setup_bot())


@mock_aws
def test_setup_bot_if_bot_user_has_access_token_but_describe_instances_has_no_reservations(
    mocker, capfd, bot_user
):
    from twitchrce.main import setup_bot

    BOT_CONFIG = bot_config.BotConfig().get_bot_config()

    mock_get_app_token = mocker.patch("twitchrce.utils.utils.Utils.get_app_token")
    mock_get_app_token.return_value = "access_token_abc123"

    mock_dynamodb = boto3.resource(
        "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
    )
    table_name = os.getenv("DYNAMODB_USER_TABLE_NAME")
    mock_dynamodb.create_table(
        TableName=table_name,
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
    mock_table = mock_dynamodb.Table(table_name)
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

    mock_bot_fetch_users = mocker.patch("twitchio.client.Client.fetch_users")
    mock_bot_fetch_users.return_value = [bot_user]

    mock_check_valid_token = mocker.patch(
        "twitchrce.utils.utils.Utils.check_valid_token"
    )
    mock_check_valid_token.return_value = True

    with pytest.raises((RuntimeError, ValueError, TypeError)):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(setup_bot())
