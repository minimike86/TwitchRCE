import pytest

from twitchrce.utils.utils import Utils


# Test cases for the redact_secret_string method
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
