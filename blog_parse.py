import requests
import bs4
from urllib.parse import urljoin
import database
from datetime import datetime


class BlogParse:

    def __init__(self, start_url, db):
        self.db = db
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [self.posts_line_parse(self.start_url)]
        self.done_urls.add(self.start_url)

    def _get_soup(self, url):
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def run(self):
        for task in self.tasks:
            task()

    def posts_line_parse(self, url):
        url = url

        def task():
            soup = self._get_soup(url)
            pagination = soup.find('ul', attrs={'class': 'gb__pagination'})
            for task_url in [urljoin(self.start_url, url.get('href')) for url in pagination.find_all('a')]:
                if task_url not in self.done_urls:
                    self.tasks.append(self.posts_line_parse(task_url))
                    self.done_urls.add(task_url)
            posts_wrapper = soup.find('div', attrs={'class': 'post-items-wrapper'})
            for post_url in {urljoin(self.start_url, url.get('href')) for url in
                             posts_wrapper.find_all('a', attrs={'class': 'post-item__title'})}:
                self.tasks.append(self.post_parse(post_url))
                self.done_urls.add(post_url)

        return task

    def post_parse(self, url):
        def task():
            soup = self._get_soup(url)
            author_name_tag = soup.find('div', attrs={'itemprop': 'author'})
            date = soup.find('time').get('datetime')
            dt = datetime.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')
            data = {
                'post_data': {
                    'url': url,
                    'title': soup.find('h1').text,
                    'created_at': dt,
                    'first_image_url': soup.find('img').get('src')
                },
                'author': {
                    'name': author_name_tag.text,
                    'url': urljoin(self.start_url, author_name_tag.parent.get('href'))
                },
                'comments': self.get_comments(soup),
                'tags': self.get_tags(soup)
            }
            self.save(data)

        return task

    def get_comments(self, soup):
        params_tag = soup.find('comments').attrs
        params = {'commentable_type': params_tag['commentable-type'], 'commentable_id': params_tag['commentable-id']}
        response = requests.get('https://geekbrains.ru/api/v2/comments', params=params)
        return [i['comment'] for i in response.json()]

    def get_tags(self, soup):
        tag_links = soup.find_all('a', attrs={'class': 'small'})
        return [{'name': tag.text, 'url': urljoin('https://geekbrains.ru', tag.get('href'))} for tag in tag_links] \
            if tag_links else tag_links

    def save(self, data):
        self.db.create_post(data)


if __name__ == '__main__':
    db = database.Database('sqlite:///gb_blog.db')
    parser = BlogParse('https://geekbrains.ru/posts', db)
    parser.run()
