import asyncio
import vt

import settings


class VirusTotalApiClient:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.client = vt.Client(settings.VIRUS_TOTAL_API_KEY)

    async def get_file_report(self, hash_id: str):
        """ https://virustotal.github.io/vt-py/quickstart.html#get-information-about-a-file
         https://developers.virustotal.com/reference/file-info """
        file_report = await self.client.get_object_async(path=f"/files/{hash_id}")
        return file_report

    async def get_url_report(self, url: str):
        """ https://virustotal.github.io/vt-py/quickstart.html#get-information-about-an-url
        https://developers.virustotal.com/reference/domain-info """
        url_id = vt.url_id(url)
        url_report = await self.client.get_object_async(path=f"/urls/{url_id}")
        return url_report
