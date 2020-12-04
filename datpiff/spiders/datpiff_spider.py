from scrapy import Spider
from datpiff.items import DatpiffItem
from scrapy import Request
import re

class datpiff_spider(Spider):
    name = 'datpiff_spider'
    allowed_urls = ['https://www.datpiff.com/']
    start_urls = ['https://www.datpiff.com/mixtapes.php?filter=all&p=1']

    def parse(self, response):
    # Get current page number and next page number for iteration
    # Page numbers continue endlessley, even if pages are blank
    # 'Next page' button on the last populated page points to itself, this is how end of mixtapes is detected
        current_page = int(response.xpath('//div[@class="pagination"]//a[@class="active"]/text()').extract_first())
        next_page = int(str.split(response.xpath('//div[@class="pagination"]/a[@class="next"]/@href').extract_first(),'=')[-1])
        next_page_url = 'https://www.datpiff.com' + response.xpath('//div[@class="pagination"]/a[@class="next"]/@href').extract_first()

        #Get Mixtape boxes on page
        mixtapes = response.xpath('//div[@id="leftColumnWide"]//div[@class="contentItemInner"]')
        
        for mixtape in mixtapes:
            
            banners = mixtape.xpath('./a/div/@class').extract()

            # Only scrape official mixtapes
            if "banner official" not in banners:
                continue
            #     official = "official"
            # else: 
            #     official = "unofficial"

            if "banner sponsor" in banners:
                banner = "sponsored"
            elif "banner exclusive" in banners:
                banner = "exclusive"
            else:
                banner = "none"

            mixtape_url = 'https://www.datpiff.com' + mixtape.xpath('.//div[@class="title"]//@href').extract_first()
            artist = mixtape.xpath('./div[@class="artist"]/text()').extract_first().strip()
            title = mixtape.xpath('./div[@class="title"]//text()').extract_first().strip()

            try:
                listens = int(''.join(re.findall('\d+', mixtape.xpath('./div[text()="Listens: "]/span/text()').extract_first())))
            except Exception as e:
                print(type(e), e)
                listens = "failed"

            try:
                rating_score = int(re.split(' ',mixtape.xpath('./div[@class="text"]/img/@alt').extract_first())[0])
            except Exception as e:
                print(type(e), e)
                rating_score = "failed"

            try:
                rating_count = int(''.join(re.findall('\d+', re.split(' ',mixtape.xpath('./div[@class="text"]/img/@title').extract_first())[0])))
            except Exception as e:
                print(type(e), e)
                rating_count = "failed"

            meta = {'artist' : artist,
                    'title' : title,
                    'listens' : listens,
                    'rating_score': rating_score,
                    'rating_count' : rating_count,
                    'banner' : banner,
                    # 'official' : official
                    }
            yield Request(url = mixtape_url, callback = self.parse_mixtape_page, meta = meta)
        if current_page < next_page:
            yield Request(url = next_page_url, callback = self.parse)

    def parse_mixtape_page(self, response):
        info = response.xpath('//div[@class="module1"]')
        listens = response.meta['listens']

        try:
            host = str.strip(info.xpath('.//li[@class="dj"]/text()').extract_first())   
        except Exception as e:
            print(type(e),e)
            host = None

        try:
            views = ''.join(re.findall('\d+', info.xpath('.//li[@class="listens"]/text()').extract_first()))
        except Exception as e:
            print(type(e),e)
            views = None

        try:
            release_date = info.xpath('//div[@class = "left"]//span/text()').extract_first()
        except Exception as e:
            print(type(e),e)
            release_date = None

        try:
            added_by = info.xpath('//div[@class = "left"]//a/text()').extract_first()
        except Exception as e:
            print(type(e),e)
            added_by = None

        try:
            description = str.strip(info.xpath('.//div[@class="description"]//text()').extract_first())
        except Exception as e:
            print(type(e),e)
            description = ''
        
        try:
            stat = [re.split('\-|\.',value)[-2] for value in info.xpath('.//div[@class="downloads right"]//li/img/@src').extract()]
            count = [str.strip(x) for x in info.xpath('.//div[@class="downloads right"]//li/text()').extract()]
            stats = {stat[x]:count[x] for x in range(0,len(stat))}
            # listens = stats['listens']
            if listens == "failed":
                listens = int(''.join(re.findall('\d+', stats['listens'])))
            downloads = int(''.join(re.findall('\d+', stats['downloads'])))
        except Exception as e:
            print(type(e),e)
            downloads = None

        try:
            tracks = len(response.xpath('//span[@class="tracknumber"]/text()').extract())
        except Exception as e:
            print(type(e),e)
            tracks = len(response.xpath('//span[@class="tracknumber"]/text()').extract())
        
        buttons = response.xpath('//div[@class="actionButtons"]//text()').extract()

        if "Stream" in buttons:
            streaming_enabled = "yes"
        else:
            streaming_enabled = "no"

        if "Download" in buttons:
            download_enabled = "yes"
        else:
            download_enabled = "no"

        if "BUY" in buttons:
            buy_enabled = "yes"
        else:
            buy_enabled = "no"


        item = DatpiffItem()
        item['title'] = response.meta['title']
        item['artist'] = response.meta['artist']
        # item['official'] = response.meta['official']
        item['downloads'] = downloads
        # item['award'] = award
        item['host'] = host
        item['views'] = views
        item['release_date'] = release_date
        item['added_by'] = added_by
        item['description'] = description
        item['listens'] = listens
        item['tracks'] = tracks
        item['rating_count'] = response.meta['rating_count']
        item['rating_score'] = response.meta['rating_score']
        item['banner'] = response.meta['banner']
        item['streaming_enabled'] = streaming_enabled
        item['download_enabled'] = download_enabled
        item['buy_enabled'] = buy_enabled
        yield item  