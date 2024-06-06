import scrapy
from asyncio import gather


class DRSpider(scrapy.Spider):
    name = 'DR'
    allowed_domains = ['dr.dk']
    start_urls = ['https://www.dr.dk/nyheder/politik/ep-valg/din-stemmeseddel']

    def parse(self, response):
        kandidat_urls = response.css("a[aria-label*='gå til kandidatprofil']")
        for urls in kandidat_urls:
            yield scrapy.Request(response.urljoin(urls.attrib['href']), callback=self.parse_kandidat, meta={"playwright": True, "playwright_include_page": True})

    async def parse_kandidat(self, response):
        page = response.meta["playwright_page"]
        aNc = await gather(page.evaluate('() => __NEXT_DATA__.props.pageProps.candidateAnswers'), page.evaluate('() => __NEXT_DATA__.props.pageProps.candidate'))
        yield {'kandidat': aNc}
        await page.close()
