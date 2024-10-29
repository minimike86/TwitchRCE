import pytest

from twitchrce.utils.utils import Utils


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_get_app_token(mocker):
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

    access_token = await Utils.get_app_token()
    assert access_token == "access_token_xyz789"
    mock_client_credentials_grant_flow.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_valid_token_is_valid(mocker):
    mock_validate_token = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.validate_token"
    )
    mock_validate_token.return_value = True

    mock_user = {}

    is_valid_token = await Utils().check_valid_token(user=mock_user)
    assert bool(is_valid_token)
    mock_validate_token.assert_awaited_once()


@pytest.mark.parametrize(
    "secret_string, visible_chars, expected",
    [
        ("abcdefg", 4, "*******"),  # Normal case
        ("abcdefghij", 4, "abcd**ghij"),  # Normal case
        ("abc", 4, "***"),  # Too short
        ("ab", 4, "**"),  # Too short
        ("", 4, ""),  # Empty string
        ("aaaaaaaaaa", 2, "aa******aa"),  # Long string with small visible chars
    ],
)
def test_redact_secret_string(secret_string, visible_chars, expected):
    result = Utils.redact_secret_string(secret_string, visible_chars)
    assert result == expected
