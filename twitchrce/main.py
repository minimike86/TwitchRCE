import asyncio
import logging
import secrets

import boto3
import nest_asyncio
from colorama import Fore, Style
from twitchio import AuthenticationError

from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
from twitchrce.config import bot_config
from twitchrce.custom_bot import CustomBot
from twitchrce.utils.utils import Utils

nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


"""
██████   ██████  ████████         ██ ███    ██ ██ ████████ 
██   ██ ██    ██    ██            ██ ████   ██ ██    ██    
██████  ██    ██    ██            ██ ██ ██  ██ ██    ██    
██   ██ ██    ██    ██            ██ ██  ██ ██ ██    ██    
██████   ██████     ██    ███████ ██ ██   ████ ██    ██    
Start the pubsub client for the Twitch channel
"""

config = bot_config.BotConfig()
region_name = config.get_bot_config().get("aws").get("region_name")

# Database
dynamodb = boto3.resource(
    "dynamodb", region_name=region_name
)
user_table = dynamodb.Table("MSecBot_User")

# Worker
ec2 = boto3.client(
    "ec2", region_name=region_name
)


async def setup_bot() -> CustomBot:
    splash = {
        "name": "TwitchRCE",
        "version": "v1.0.0",
        "description": f"""{Fore.LIGHTWHITE_EX}TwitchRCE is an advanced bot for interacting with Twitch's PubSub, 
                            EventSub and API services.{Style.RESET_ALL}""",
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
    WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS 
    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    
    {Fore.LIGHTWHITE_EX}Starting up...{Style.RESET_ALL}
    """
    )

    # init asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # fetch bot app token
    _app_token = loop.run_until_complete(Utils().get_app_token())

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
        config.get_bot_config()
        .get("aws")
        .get("api_gateway")
        .get("api_gateway_invoke_url")
    )
    api_gateway_route = (
        config.get_bot_config()
        .get("aws")
        .get("api_gateway")
        .get("api_gateway_route")
    )
    redirect_uri = f"{api_gateway_invoke_url}{api_gateway_route}"
    authorization_url = (
        f"https://id.twitch.tv/oauth2/authorize?client_id={config.get_bot_config().get('twitch').get('client_id')}"
        f"&force_verify=true"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={secrets.token_hex(16)}"
    )

    # fetch bot user token (refresh it if needed)
    _bot_user = None
    try:
        response = user_table.get_item(
            Key={
                "id": int(
                    config.get_bot_config()
                    .get("twitch")
                    .get("bot_auth")
                    .get("bot_user_id")
                )
            }
        )
        _bot_user = response.get("Item")

        # the bot user has no twitch access token stored in db so can't use chat programmatically
        if not _bot_user.get("access_token"):
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
            is_valid = loop.run_until_complete(Utils().check_valid_token(user=_bot_user))
            if is_valid:
                config.BOT_OAUTH_TOKEN = _bot_user.get("access_token")

    except AttributeError:
        # database doesn't have an item for the bot_user_id provided

        # Send URL to stdout allows the user to grant the oauth flow and store an access token in the db
        # TODO: Deduplicate code
        logger.error(
            f"{Fore.CYAN}Failed to get bot user object for "
            f"{Fore.MAGENTA}{config.get_bot_config().get('twitch').get('bot_user_id')}{Fore.CYAN}!"
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
    custom_bot = CustomBot(config)

    # Start the pubsub client for the Twitch channel
    if config.get_bot_config().get("bot_features").get("enable_psclient"):
        custom_bot.loop.run_until_complete(custom_bot.__psclient_init__())

    # Start the eventsub client for the Twitch channel
    if config.get_bot_config().get("bot_features").get("enable_esclient"):
        if public_url:
            custom_bot.loop.run_until_complete(custom_bot.__esclient_init__())

    return custom_bot


if __name__ == "__main__":
    bot = asyncio.run(setup_bot())
    try:
        bot.run()
    except AuthenticationError as error:
        logger.error(msg=error)
