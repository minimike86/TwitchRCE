import pytest

from config import BotConfig


@pytest.fixture(autouse=True)
def set_environment_variables(monkeypatch):
    # Set default environment variables for all tests
    monkeypatch.setenv("CLIENT_ID", "12345")
    monkeypatch.setenv("CLIENT_SECRET", "abcde")
    monkeypatch.setenv("BOT_USER_ID", "123456")
    monkeypatch.setenv("BOT_OAUTH_TOKEN", "access_token_xyz789")
    monkeypatch.setenv("VIRUS_TOTAL_API_KEY", "virus_total_api_key_xyz789")
    monkeypatch.setenv("REGION_NAME", "eu-west-2")
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-2")
    monkeypatch.setenv(
        "API_GATEWAY_INVOKE_URL",
        "https://12345.execute-api.eu-west-2.amazonaws.com",
    )
    monkeypatch.setenv("API_GATEWAY_ROUTE", "/twitch/oauth2/authorization_code")
    monkeypatch.setenv("DYNAMODB_USER_TABLE_NAME", "MSecBot_User")


def test_config(monkeypatch):
    expected_cmd_allow_list = [
        "aux",
        "cat",
        "echo",
        "grep",
        "id",
        "ifconfig",
        "ls",
        "netstat",
        "nslookup",
        "ping",
        "pwd",
        "which",
        "who",
        "whoami",
    ]
    BOT_CONFIG = BotConfig().get_bot_config()

    # Twitch Developer Credentials
    app_auth = BOT_CONFIG.get("twitch").get("app_auth")
    assert app_auth.get("client_id") == "12345"
    assert app_auth.get("client_secret") == "abcde"

    # Twitch Bot User Credentials
    bot_auth = BOT_CONFIG.get("twitch").get("bot_auth")
    assert bot_auth.get("bot_user_id") == "123456"
    assert bot_auth.get("bot_oauth_token") == "access_token_xyz789"
    bot_initial_channels = BOT_CONFIG.get("twitch").get("bot_initial_channels")
    assert bot_initial_channels[0].get("id") == 125444292
    assert bot_initial_channels[0].get("login") == "msec"

    # Bot Features Vars
    assert BOT_CONFIG.get("bot_features").get("announce_join") is True
    assert BOT_CONFIG.get("bot_features").get("enable_commands") is True
    assert BOT_CONFIG.get("bot_features").get("enable_psclient") is False
    assert BOT_CONFIG.get("bot_features").get("enable_esclient") is False
    assert (
        BOT_CONFIG.get("bot_features")
        .get("cogs")
        .get("ascii_cog")
        .get("enable_ascii_cog")
        is True
    )
    assert (
        BOT_CONFIG.get("bot_features").get("cogs").get("rce_cog").get("enable_rce_cog")
        is False
    )
    assert (
        BOT_CONFIG.get("bot_features").get("cogs").get("rce_cog").get("cmd_allow_list")
        == expected_cmd_allow_list
    )
    assert (
        BOT_CONFIG.get("bot_features").get("cogs").get("vip_cog").get("enable_vip_cog")
        is False
    )
    assert (
        BOT_CONFIG.get("bot_features").get("virus_total").get("enable_virus_total")
        is True
    )
    assert (
        BOT_CONFIG.get("bot_features").get("virus_total").get("virus_total_api_key")
        == "virus_total_api_key_xyz789"
    )

    # AWS Credentials
    assert BOT_CONFIG.get("aws").get("aws_region") == "eu-west-2"
    assert BOT_CONFIG.get("aws").get("aws_default_region") == "eu-west-2"
    assert BOT_CONFIG.get("aws").get("region_name") == "eu-west-2"
    assert (
        BOT_CONFIG.get("aws").get("api_gateway").get("api_gateway_invoke_url")
        == "https://12345.execute-api.eu-west-2.amazonaws.com"
    )
    assert (
        BOT_CONFIG.get("aws").get("api_gateway").get("api_gateway_route")
        == "/twitch/oauth2/authorization_code"
    )


# List the commands you want to test in CMD_ALLOW_LIST
@pytest.mark.parametrize(
    "command, is_safe",
    [
        ("aux", True),
        ("cat", True),
        ("echo", True),
        ("grep", True),
        ("id", True),
        ("ifconfig", True),
        ("ls", True),
        ("netstat", True),
        ("nslookup", True),
        ("ping", True),
        ("pwd", True),
        ("which", True),
        ("who", True),
        ("whoami", True),
        ("rm", False),
        ("shutdown", False),
        ("reboot", False),
        ("curl", False),
        ("wget", False),
        ("bash", False),
        ("python", False),
        ("perl", False),
    ],
)
def test_cmd_allow_list(command, is_safe):
    cmd_allow_list = (
        BotConfig()
        .get_bot_config()
        .get("bot_features")
        .get("cogs")
        .get("rce_cog")
        .get("cmd_allow_list")
    )
    # Check if the command is expected to be safe or unsafe
    if is_safe:
        assert command in cmd_allow_list, f"Command '{command}' is allowed!"
    else:
        assert (
            command not in cmd_allow_list
        ), f"Unsafe command '{command}' is not allowed!"
