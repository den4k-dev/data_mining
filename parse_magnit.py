import requests
import time
import bs4
from urllib.parse import urljoin
from pymongo import MongoClient
import dotenv
import os

dotenv.load_dotenv('.env')


class StatusCodeError(Exception):
    def __init__(self, text):
        self.text = text


class MagnitParser:
    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.collection = db_client['db_parse']['magnit']

    # сделать запрос на url
    @staticmethod
    def _get_response(url: str, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code == 200:
                    return response
                raise StatusCodeError(f'{response.status_code}')
            except (requests.exceptions.HTTPError,
                    requests.exceptions.ConnectTimeout,
                    StatusCodeError):
                time.sleep(0.2)

    # получить soup
    @staticmethod
    def _get_soup(response: requests.Response) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self):
        page_soup = self._get_soup(self._get_response(self.start_url))
        for product in self._get_product(page_soup):
            self.save(product)

    # обработать soup, извлечь данные
    def _get_product(self, soup: bs4.BeautifulSoup):
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        for tag_product in catalog.find_all('a', recursive=False, attrs={'class': 'card-sale card-sale_catalogue'}):
            yield self._product_parse(tag_product)

    def _product_parse(self, tag_product: bs4.Tag) -> dict:
        try:
            url = urljoin(self.start_url, tag_product.get('href'))
            img_url = urljoin('https://magnit.ru', tag_product.find('img').get('data-src'))
            tag_price = tag_product.find('div', attrs={'class': 'label__price label__price_new'}).find_all('span')
            price = f'{tag_price[0].text},{tag_price[1].text}'
            title = tag_product.find('div', attrs={'card-sale__title'}).text
            period_tag = tag_product.find('div', attrs={'card-sale__date'}).find_all('p')
            period = f'{period_tag[0].text} {period_tag[1].text}'
            product = {'title': title, 'url': url, 'image_url': img_url, 'price': price, 'period': period}
            return product
        except Exception:
            exit()

    # сохранить в БД
    def save(self, product: dict):
        self.collection.insert_one(product)


if __name__ == '__main__':
    db_client = MongoClient(os.getenv('MONGO_DB_URL'))
    parser = MagnitParser('https://magnit.ru/promo/?geo=moskva', db_client)
    parser.run()
