from unittest.mock import AsyncMock, patch

import pytest

from twitchrce.main import get_app_token


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_get_app_token():
    # Mock the response from client_credentials_grant_flow
    mock_response = {
        "access_token": "1234567890abcdef1234567890abcdef",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": ["user:read", "user:edit"],
    }

    # Patch the TwitchApiAuth class to mock the client_credentials_grant_flow method
    with patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.client_credentials_grant_flow",
        new_callable=AsyncMock,
    ) as mock_method:
        mock_method.return_value = mock_response
        access_token = await get_app_token()
        assert access_token == "1234567890abcdef1234567890abcdef"
        mock_method.assert_awaited_once()
