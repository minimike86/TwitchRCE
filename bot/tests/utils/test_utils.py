import pytest


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_get_app_token(mocker):
    mock_client_credentials_grant_flow_response = {
        "access_token": "access_token_xyz789",
        "expires_in": 12345,
        "token_type": "bearer",
    }

    mock_client_credentials_grant_flow = mocker.patch(
        "msecbot.api.twitch.twitch_api_auth.TwitchApiAuth.client_credentials_grant_flow"
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
        "msecbot.api.twitch.twitch_api_auth.TwitchApiAuth.validate_token"
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


@pytest.mark.parametrize(
    "currency_string, expected",
    [
        ("AED", "د.إ"),
        ("AFN", "؋"),
        ("ALL", "L"),
        ("AMD", "֏"),
        ("ANG", "ƒ"),
        ("AOA", "Kz"),
        ("ARS", "$"),
        ("AUD", "$"),
        ("AWG", "ƒ"),
        ("AZN", "₼"),
        ("BAM", "KM"),
        ("BBD", "$"),
        ("BDT", "৳"),
        ("BGN", "лв"),
        ("BHD", ".د.ب"),
        ("BIF", "FBu"),
        ("BMD", "$"),
        ("BND", "$"),
        ("BOB", "Bs."),
        ("BRL", "R$"),
        ("BSD", "$"),
        ("BTN", "Nu."),
        ("BWP", "P"),
        ("BYN", "Br"),
        ("BZD", "BZ$"),
        ("CAD", "$"),
        ("CDF", "FC"),
        ("CHF", "CHF"),
        ("CLP", "$"),
        ("CNY", "¥"),
        ("COP", "$"),
        ("CRC", "₡"),
        ("CUP", "$"),
        ("CVE", "$"),
        ("CZK", "Kč"),
        ("DJF", "Fdj"),
        ("DKK", "kr"),
        ("DOP", "$"),
        ("DZD", "د.ج"),
        ("EGP", "E£"),
        ("ERN", "Nfk"),
        ("ETB", "Br"),
        ("EUR", "€"),
        ("FJD", "$"),
        ("FKP", "£"),
        ("GBP", "£"),
        ("GEL", "₾"),
        ("GGP", "£"),
        ("GHS", "₵"),
        ("GIP", "£"),
        ("GMD", "D"),
        ("GNF", "FG"),
        ("GTQ", "Q"),
        ("GYD", "$"),
        ("HKD", "$"),
        ("HNL", "L"),
        ("HRK", "kn"),
        ("HTG", "G"),
        ("HUF", "Ft"),
        ("IDR", "Rp"),
        ("ILS", "₪"),
        ("IMP", "£"),
        ("INR", "₹"),
        ("IQD", "ع.د"),
        ("IRR", "﷼"),
        ("ISK", "kr"),
        ("JEP", "£"),
        ("JMD", "$"),
        ("JOD", "د.ا"),
        ("JPY", "¥"),
        ("KES", "KSh"),
        ("KGS", "сом"),
        ("KHR", "៛"),
        ("KID", "$"),
        ("KMF", "CF"),
        ("KRW", "₩"),
        ("KWD", "د.ك"),
        ("KYD", "$"),
        ("KZT", "₸"),
        ("LAK", "₭"),
        ("LBP", "ل.ل"),
        ("LKR", "₨"),
        ("LRD", "$"),
        ("LSL", "L"),
        ("LYD", "ل.د"),
        ("MAD", "د.م."),
        ("MDL", "L"),
        ("MGA", "Ar"),
        ("MKD", "ден"),
        ("MMK", "K"),
        ("MNT", "₮"),
        ("MOP", "P"),
        ("MRU", "UM"),
        ("MUR", "₨"),
        ("MVR", "Rf"),
        ("MWK", "MK"),
        ("MXN", "$"),
        ("MYR", "RM"),
        ("MZN", "MT"),
        ("NAD", "$"),
        ("NGN", "₦"),
        ("NIO", "C$"),
        ("NOK", "kr"),
        ("NPR", "₨"),
        ("NZD", "$"),
        ("OMR", "ر.ع."),
        ("PAB", "B/."),
        ("PEN", "S/."),
        ("PGK", "K"),
        ("PHP", "₱"),
        ("PKR", "₨"),
        ("PLN", "zł"),
        ("PYG", "₲"),
        ("QAR", "ر.ق"),
        ("RON", "lei"),
        ("RSD", "дин."),
        ("RUB", "₽"),
        ("RWF", "RF"),
        ("SAR", "ر.س"),
        ("SBD", "$"),
        ("SCR", "₨"),
        ("SDG", "ج.س."),
        ("SEK", "kr"),
        ("SGD", "$"),
        ("SHP", "£"),
        ("SLL", "Le"),
        ("SOS", "Sh"),
        ("SRD", "$"),
        ("SSP", "£"),
        ("STN", "Db"),
        ("SYP", "£"),
        ("SZL", "L"),
        ("THB", "฿"),
        ("TJS", "SM"),
        ("TMT", "T"),
        ("TND", "د.ت"),
        ("TOP", "T$"),
        ("TRY", "₺"),
        ("TTD", "$"),
        ("TVD", "$"),
        ("TWD", "NT$"),
        ("TZS", "TSh"),
        ("UAH", "₴"),
        ("UGX", "USh"),
        ("USD", "$"),
        ("UYU", "$"),
        ("UZS", "лв"),
        ("VES", "Bs."),
        ("VND", "₫"),
        ("VUV", "VT"),
        ("WST", "WS$"),
        ("XAF", "FCFA"),
        ("XCD", "$"),
        ("XDR", "SDR"),
        ("XOF", "CFA"),
        ("XPF", "CFP"),
        ("YER", "﷼"),
        ("ZAR", "R"),
        ("ZMW", "ZK"),
        ("ZWL", "$"),
    ],
)
def test_get_currency_symbols(currency_string, expected):
    currency_symbols = Utils.get_currency_symbols()
    assert currency_symbols.get(currency_string) == expected
