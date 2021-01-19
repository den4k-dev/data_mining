import requests
import json
from pathlib import Path
import time


class StatusCodeError(Exception):
    def __init__(self, txt):
        self.txt = txt


class Parser5ka:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'}
    params = {}

    def __init__(self, start_url):
        self.start_url = start_url

    def run(self):
        try:
            for product in self.parse(self.start_url):
                file_path = Path(__file__).parent.joinpath('products', f'{product["id"]}.json')
                self.save(product, file_path)
        except requests.exceptions.MissingSchema:
            exit()

    def get_response(self, url, **kwargs):
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code != 200:
                    raise StatusCodeError(response.status_code)
                time.sleep(0.05)
                return response
            except (requests.exceptions.HTTPError,
                    requests.exceptions.BaseHTTPError,
                    requests.exceptions.ConnectTimeout,
                    StatusCodeError):
                time.sleep(0.2)

    def parse(self, url):
        while url:
            response = self.get_response(url, headers=self.headers, params=self.params)
            data = response.json()
            url = data["next"]
            for product in data["results"]:
                yield product

    def save(self, data: dict, file_path):
        with open(file_path, 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)


class Parser5kaCat(Parser5ka):
    """class парсит категории товаров и сохраняет все товары
     категории в отдельный json с названием категории"""
    def run(self):
        for item in self.get_category():
            name = item["parent_group_name"]
            code = item["parent_group_code"]
            products = self.get_products(code)
            file_path = Path(__file__).parent.joinpath('categories', f'{name}.json')
            data = dict(name=name, code=code, products=products)
            self.save(data, file_path)

    def get_category(self):
        response = self.get_response(self.start_url)
        categories = response.json()
        for category in categories:
            yield category

    def get_products(self, cat_code):
        response = self.get_response(f'{self.start_url}{cat_code}')
        data = response.json()
        all_products = []
        for item in data:
            self.params.update(categories=item["group_code"])
            products = list(self.parse('https://5ka.ru/api/v2/special_offers/'))
            if products:
                all_products.extend(products)
        return all_products


if __name__ == '__main__':
    # parser = Parser5ka('https://5ka.ru/api/v2/special_offers/')
    # parser.run()
    cat_parser = Parser5kaCat('https://5ka.ru/api/v2/categories/')
    cat_parser.run()
