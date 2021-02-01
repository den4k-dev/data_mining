import scrapy
from pymongo import MongoClient


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['http://auto.youla.ru/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = MongoClient()['db_parse']

    def parse(self, response, **kwargs):
        brands = response.css('a.blackLink')
        for brand_link in brands:
            yield response.follow(brand_link.attrib.get('href', '/'), callback=self.brand_parse)

    def brand_parse(self, response):
        pag_links = response.css('div.Paginator_block__2XAPy a.Paginator_button__u1e7D')
        for pag_link in pag_links:
            yield response.follow(pag_link.attrib.get('href'),  callback=self.brand_parse)

        ads_links = response.css('article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_photoWrapper__3W9J4')
        for ads_link in ads_links:
            yield response.follow(ads_link.attrib.get('href'), callback=self.ads_parse)

    def ads_parse(self, response):
        data = {
            'url': response.url,
            'title': response.css('div.AdvertCard_advertTitle__1S1Ak::text').get(),
            'price': response.css('div.AdvertCard_price__3dDCr::text').get().replace('\u2009', ''),
            'photo_links': [photo.attrib['src'] for photo in response.css('figure.PhotoGallery_photo__36e_r img')],
            'properties': self.get_properties(response.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_row__ljPcX')),
            'description': response.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
        }
        collection = self.db[self.name]
        collection.insert_one(data)

    def get_properties(self, list_properties_tags):
        properties = {}
        for item in list_properties_tags:
            key = item.css('div.AdvertSpecs_label__2JHnS::text').get()
            value = item.css('div.AdvertSpecs_data__xK2Qx::text').get()
            if not value:
                value = item.css('div.AdvertSpecs_data__xK2Qx a.blackLink::text').get()
            properties.update([(key, value)])
        return properties




