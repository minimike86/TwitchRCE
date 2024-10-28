import asyncio
import logging
import secrets

import boto3
import nest_asyncio
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from colorama import Fore, Style
from twitchio import AuthenticationError

from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
from twitchrce.config import bot_config
from twitchrce.custom_bot import CustomBot

nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def get_app_token() -> str:
    """Uses the bots' client id and secret to generate a new application token via client credentials grant flow"""
    client_creds_grant_flow = await TwitchApiAuth().client_credentials_grant_flow()
    logger.info(
        f"{Fore.LIGHTWHITE_EX}Updated {Fore.LIGHTCYAN_EX}app access token{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
    )
    return client_creds_grant_flow["access_token"]


# TODO: Replace with lambda calls
async def check_valid_token(user: any) -> bool:
    """
    Asynchronously checks if a user's access token is valid. If the token is invalid,
    attempts to refresh the token and validates it again.

    Args:
        user (any): A user object or dictionary containing the user's access token
            under the key "access_token".

    Returns:
        bool: True if the user's access token is valid after validation or refresh;
              False if it remains invalid.
    """
    is_valid_token = await TwitchApiAuth().validate_token(
        access_token=user.get("access_token")
    )
    if not is_valid_token:
        access_token = await refresh_user_token(user=user)
        is_valid_token = await TwitchApiAuth().validate_token(access_token=access_token)
    return is_valid_token


# TODO: Replace with lambda calls
async def refresh_user_token(user: any) -> str:
    auth_result = await TwitchApiAuth().refresh_access_token(
        refresh_token=user.get("refresh_token")
    )
    try:
        # Insert the item
        user_table.update_item(
            Key={"id": user.get("id")},
            UpdateExpression="set access_token=:a, refresh_token=:r, expires_in=:e",
            ExpressionAttributeValues={
                ":a": auth_result.get("access_token"),
                ":r": auth_result.get("refresh_token"),
                ":e": auth_result.get("expires_in"),
            },
            ReturnValues="UPDATED_NEW",
        )
        logger.info(
            f"{Fore.LIGHTWHITE_EX}Updated access_token and refresh_token for user {Fore.LIGHTCYAN_EX}{user['login']}"
            f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
        )
    except (NoCredentialsError, PartialCredentialsError) as error:
        logger.error("Credentials not available")
        raise error
    return auth_result.get("access_token")


"""
██████   ██████  ████████         ██ ███    ██ ██ ████████ 
██   ██ ██    ██    ██            ██ ████   ██ ██    ██    
██████  ██    ██    ██            ██ ██ ██  ██ ██    ██    
██   ██ ██    ██    ██            ██ ██  ██ ██ ██    ██    
██████   ██████     ██    ███████ ██ ██   ████ ██    ██    
Start the pubsub client for the Twitch channel
"""

bot_config = bot_config.BotConfig()
dynamodb = boto3.resource(
    "dynamodb", region_name=bot_config.get_bot_config().get("aws").get("region_name")
)
user_table = dynamodb.Table("MSecBot_User")
ec2 = boto3.client("ec2", region_name=bot_config.get_bot_config().get("aws").get("region_name"))


async def setup_bot() -> CustomBot:
    splash = {
        "name": "TwitchRCE",
        "version": "v1.0.0",
        "description": f"{Fore.LIGHTWHITE_EX}TwitchRCE is an advanced bot for interacting with Twitch's PubSub, EventSub and API services.{Style.RESET_ALL}",
        "project_url": f"{Fore.LIGHTWHITE_EX}Project URL: https://github.com/minimike86/TwitchRCE{Style.RESET_ALL}",
        "copyright": f"{Fore.LIGHTWHITE_EX}Copyright (c) 2024 MSec @minimike86.{Style.RESET_ALL}",
    }

    logger.info(
        f"""{Fore.WHITE}
    
    ▄▄▄█████▓ █     █░ ██▓▄▄▄█████▓ ▄████▄   ██░ ██  ██▀███   ▄████▄  ▓█████
    ▓  ██▒ ▓▒▓█░ █ ░█░▓██▒▓  ██▒ ▓▒▒██▀ ▀█  ▓██░ ██▒▓██ ▒ ██▒▒██▀ ▀█  ▓█   ▀
    ▒ ▓██░ ▒░▒█░ █ ░█ ▒██▒▒ ▓██░ ▒░▒▓█    ▄ ▒██▀▀██░▓██ ░▄█ ▒▒▓█    ▄ ▒███
    ░ ▓██▓ ░ ░█░ █ ░█ ░██░░ ▓██▓ ░ ▒▓▓▄ ▄██▒░▓█ ░██ ▒██▀▀█▄  ▒▓▓▄ ▄██▒▒▓█  ▄
    ▒██▒ ░ ░░██▒██▓ ░██░  ▒██▒ ░ ▒ ▓███▀ ░░▓█▒░██▓░██▓ ▒██▒▒ ▓███▀ ░░▒████▒
    ▒ ░░   ░ ▓░▒ ▒  ░▓    ▒ ░░   ░ ░▒ ▒  ░ ▒ ░░▒░▒░ ▒▓ ░▒▓░░ ░▒ ▒  ░░░ ▒░ ░
    ░      ▒ ░ ░   ▒ ░    ░      ░  ▒    ▒ ░▒░ ░  ░▒ ░ ▒░  ░  ▒    ░ ░  ░
    ░        ░   ░   ▒ ░  ░      ░         ░  ░░ ░  ░░   ░ ░           ░
    ░     ░           ░ ░       ░  ░  ░   ░     ░ ░         ░  ░
░                         ░                                             {splash['version']}
    
    {splash['description']}
    {splash['project_url']}
    {splash['copyright']}
    {Fore.RED}
    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS 
    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    
    {Fore.LIGHTWHITE_EX}Starting up...{Style.RESET_ALL}
    """
    )

    # init asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # fetch bot app token
    app_token = loop.run_until_complete(get_app_token())

    scope = (
        "user:read:chat user:write:chat moderator:read:suspicious_users moderator:read:chatters "
        "user:manage:chat_color moderator:manage:chat_messages moderator:manage:chat_settings "
        "moderator:read:chat_settings chat:read chat:edit user:read:email user:edit:broadcast "
        "user:read:broadcast clips:edit bits:read channel:moderate channel:read:subscriptions "
        "whispers:read whispers:edit moderation:read channel:read:redemptions channel:edit:commercial "
        "channel:read:hype_train channel:manage:broadcast user:edit:follows channel:manage:redemptions "
        "user:read:blocked_users user:manage:blocked_users user:read:subscriptions user:read:follows "
        "channel:manage:polls channel:manage:predictions channel:read:polls channel:read:predictions "
        "moderator:manage:automod channel:read:goals moderator:read:automod_settings "
        "moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms "
        "channel:manage:raids moderator:manage:announcements channel:read:vips channel:manage:vips "
        "user:manage:whispers channel:read:charity moderator:read:shield_mode moderator:manage:shield_mode "
        "moderator:read:shoutouts moderator:manage:shoutouts moderator:read:followers "
        "channel:read:guest_star channel:manage:guest_star moderator:read:guest_star "
        "moderator:manage:guest_star channel:bot user:bot channel:read:ads user:read:moderated_channels "
        "user:read:emotes moderator:read:unban_requests moderator:manage:unban_requests channel:read:editors "
        "analytics:read:games analytics:read:extensions"
    )
    api_gateway_invoke_url = (
        bot_config.get_bot_config().get("aws").get("api_gateway").get("api_gateway_invoke_url")
    )
    api_gateway_route = (
        bot_config.get_bot_config().get("aws").get("api_gateway").get("api_gateway_route")
    )
    redirect_uri = f"{api_gateway_invoke_url}{api_gateway_route}"
    authorization_url = (
        f"https://id.twitch.tv/oauth2/authorize?client_id={bot_config.get_bot_config().get('twitch').get('client_id')}"
        f"&force_verify=true"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={secrets.token_hex(16)}"
    )

    # fetch bot user token (refresh it if needed)
    bot_user = None
    try:
        response = user_table.get_item(
            Key={"id": int(bot_config.get_bot_config().get("twitch").get("bot_auth").get("bot_user_id"))}
        )
        bot_user = response.get("Item")

        # the bot user has no twitch access token stored in db so can't use chat programmatically
        if not bot_user.get("access_token"):
            # Send URL to stdout allows the user to grant the oauth flow and store an access token in the db
            # TODO: Deduplicate code
            logger.error(
                f"{Fore.CYAN}Bot has no access_token. Authenticate to update your token!{Style.RESET_ALL}"
            )
            logger.info(
                f"{Fore.CYAN}Launching auth site: {Fore.MAGENTA}{authorization_url}{Fore.CYAN}.\n{Style.RESET_ALL}"
            )

            # TODO: Keep bot here / crash out until bot user has a new access token
            raise ValueError(
                "Bot has no access_token. Authenticate to update your token!"
            )

        else:
            # the bot user has a twitch access token stored in db so check its actually valid else refresh it
            is_valid = loop.run_until_complete(check_valid_token(user=bot_user))
            if is_valid:
                bot_config.BOT_OAUTH_TOKEN = bot_user.get("access_token")

    except AttributeError:
        # database doesn't have an item for the bot_user_id provided

        # Send URL to stdout allows the user to grant the oauth flow and store an access token in the db
        # TODO: Deduplicate code
        logger.error(
            f"{Fore.CYAN}Failed to get bot user object for {Fore.MAGENTA}{bot_config.get_bot_config().get('twitch').get('bot_user_id')}{Fore.CYAN}!"
            f"{Style.RESET_ALL}"
        )
        logger.info(
            f"{Fore.CYAN}Launching auth site: {Fore.MAGENTA}{authorization_url}{Fore.CYAN}.{Style.RESET_ALL}"
        )
        raise ValueError(
            "Bot user is not in the database. Authenticate to get an access token!"
        )

    response = ec2.describe_instances(
        InstanceIds=["i-0100638f13e5451d8"]
    )  # TODO: Don't hardcode InstanceIds
    if response.get("Reservations"):
        public_url = f"https://{response.get('Reservations')[0].get('Instances')[0].get('PublicDnsName')}"
    else:
        public_url = None

    # Create a bot from your twitchapi client credentials
    bot = CustomBot(bot_config)

    # Start the pubsub client for the Twitch channel
    if bot_config.get_bot_config().get("bot_features").get("enable_psclient"):
        bot.loop.run_until_complete(bot.__psclient_init__())

    # Start the eventsub client for the Twitch channel
    if bot_config.get_bot_config().get("bot_features").get("enable_esclient"):
        if public_url:
            bot.loop.run_until_complete(bot.__esclient_init__())

    return bot


if __name__ == "__main__":
    bot = asyncio.run(setup_bot())
    try:
        bot.run()
    except AuthenticationError as error:
        logger.error(msg=error)
