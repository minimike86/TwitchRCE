import pytest

from twitchrce.config import bot_config


@pytest.fixture(autouse=True)
def set_environment_variables(monkeypatch):
    # Set default environment variables for all tests
    monkeypatch.setenv("CLIENT_ID", "12345")
    monkeypatch.setenv("CLIENT_SECRET", "abcde")
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-2")
    monkeypatch.setenv("REGION_NAME", "eu-west-2")
    monkeypatch.setenv("BOT_USER_ID", "123456")
    monkeypatch.setenv("BOT_JOIN_CHANNEL", "#general")
    monkeypatch.setenv("BOT_JOIN_CHANNEL_ID", "123456")
    monkeypatch.setenv("MAX_VIP_SLOTS", "10")
    monkeypatch.setenv("VIRUS_TOTAL_API_KEY", "xyz")


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
    BOT_CONFIG = bot_config.BotConfig().get_bot_config()
    assert BOT_CONFIG.get("twitch").get("client_id") == "12345"
    assert BOT_CONFIG.get("twitch").get("client_secret") == "abcde"
    assert BOT_CONFIG.get("aws").get("aws_region") == "eu-west-2"
    assert BOT_CONFIG.get("aws").get("aws_default_region") == "eu-west-2"
    assert BOT_CONFIG.get("aws").get("region_name") == "eu-west-2"
    assert (
        BOT_CONFIG.get("twitch").get("channel").get("bot_join_channel_id") == "123456"
    )
    assert BOT_CONFIG.get("twitch").get("channel").get("bot_join_channel") == "#general"
    assert BOT_CONFIG.get("twitch").get("channel").get("max_vip_slots") == "10"
    assert BOT_CONFIG.get("virus_total").get("virus_total_api_key") == "xyz"
    assert BOT_CONFIG.get("rce_cog").get("cmd_allow_list") == expected_cmd_allow_list


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
    BOT_CONFIG = bot_config.BotConfig().get_bot_config()
    # Check if the command is expected to be safe or unsafe
    if is_safe:
        assert command in BOT_CONFIG.get("rce_cog").get(
            "cmd_allow_list"
        ), f"Command '{command}' is allowed!"
    else:
        assert command not in BOT_CONFIG.get("rce_cog").get(
            "cmd_allow_list"
        ), f"Unsafe command '{command}' is not allowed!"
