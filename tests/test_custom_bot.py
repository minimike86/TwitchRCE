import asyncio

import pytest
from moto import mock_aws


@mock_aws
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_get_app_token(mocker):
    from twitchrce.main import get_app_token

    # Mock the response from client_credentials_grant_flow
    client_credentials_grant_flow_response = {
        "access_token": "1234567890abcdef1234567890abcdef",
        "expires_in": 3600,
        "token_type": "bearer",
        "scope": ["user:read", "user:edit"],
    }

    mock_client_credentials_grant_flow = mocker.patch(
        "twitchrce.api.twitch.twitch_api_auth.TwitchApiAuth.client_credentials_grant_flow"
    )
    mock_client_credentials_grant_flow.return_value = (
        client_credentials_grant_flow_response
    )

    event_loop = asyncio.get_event_loop()
    access_token = event_loop.run_until_complete(get_app_token())
    assert access_token == "1234567890abcdef1234567890abcdef"
    mock_client_credentials_grant_flow.assert_awaited_once()
