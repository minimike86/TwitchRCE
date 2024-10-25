import re

import pytest


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_get_app_token(monkeypatch):
    # monkeypatch.setenv('CLIENT_ID', 'client_id')
    # monkeypatch.setenv('CLIENT_SECRET', 'client_secret')

    from twitchrce.main import get_app_token

    token = await get_app_token()
    expected_token_pattern = r"^[a-z0-9]{30}$"
    assert re.match(
        expected_token_pattern, token
    ), f"Token '{token}' does not match the expected pattern."
