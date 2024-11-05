import pytest

from twitchrce import custom_bot
from twitchrce.cogs.ascii_cog import AsciiCog


@pytest.fixture
def mock_bot(mocker):
    mock_bot: custom_bot.CustomBot = mocker.Mock()
    mock_bot._checks = []
    return mock_bot


@pytest.fixture
def mock_ctx(mocker, mock_bot):
    mock_ctx = mocker.Mock()
    mock_ctx.bot = mock_bot
    mock_ctx.author = mocker.Mock()
    mock_ctx.author.name = "author_name"
    mock_ctx.channel = mocker.Mock()
    mock_ctx.channel.name = "channel_name"
    mock_ctx.channel.channel.name = "channel_name"
    mock_ctx.channel.__messageable_channel__ = True
    mock_ctx.send = mocker.AsyncMock()
    return mock_ctx


@pytest.mark.asyncio
async def test_kill_everyone(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.kill_everyone(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_mario(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.mario(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_spider(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.spider(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_spider_swarm(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.spider_swarm(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_deez(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.deez(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_secplus(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.secplus(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_letsgo(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.letsgo(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_capybara(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.capybara(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_weeb1(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.weeb1(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_weeb2(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.weeb2(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_shark(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.shark(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_gotem(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.gotem(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_fuchat(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.fuchat(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_creeper(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.creeper(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")


@pytest.mark.asyncio
async def test_timehascome(mock_bot, mock_ctx):
    ascii_cog = AsciiCog(bot=mock_bot)
    try:
        await ascii_cog.timehascome(mock_ctx)
    except Exception as error:
        pytest.fail(f"Raised an exception: {error}")
