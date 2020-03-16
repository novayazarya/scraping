import aiohttp
import asyncio
import json
import re
from bs4 import BeautifulSoup as soup

URL = ""
HEADERS = {
    "User-agent": 
    "Mozilla/5.0 (compatible; YandexAccessibilityBot/3.0; +http://yandex.com/bots)"}
MAX_REQ = 2

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls, loop):
        async with aiohttp.ClientSession(loop=loop, headers=HEADERS) as session:
            results = await asyncio.gather(*[fetch(session, url) 
                for url in urls], return_exceptions=True)
        return results

def get_html(html):
    result = {}
    doc = soup(html, 'html.parser')
    try:
        url = doc.find('link', {'rel':'canonical'})['href']
        name = doc.h1.string.strip()
        img = doc.find('link', {'itemprop': 'image'})['href']
        try:
            gallery = [x['data-src'] for x in doc.select('.product__photos img')]
        except IndexError:
            gallery = []
        try:
            params = [x.text.strip() for x in doc.select('.product__params-name')]
            values = [x.text.replace('?', '').strip() for x in doc.select('.product__params-value')]
            characts = {p: v for p, v in zip(params, values)}
        except IndexError:
            characts = {}
        try:
            price = int(''.join(re.findall(r'\d+', doc.select('.product__offer-price')[0].text)))
        except IndexError:
            price = 0
        try: 
            tags = [x.text for x in doc.select('.tags__item')]
        except IndexError:
            tags = []
        description = doc.select('.content')[0].text.strip()
    except Exception as e:
        print(e)
    else:
        result['url'] = url
        result['tags'] = tags
        result['features'] = characts
        result['price'] = price
        result['name'] = name
        result['description'] = description
        result['image'] = [img] + gallery if gallery else img 
    return json.dumps(result)

if __name__ == '__main__':
        with open('links_out') as out:
           urls_list = [x.strip() for x in out.readlines()]
        len_data = len([x for x in open('data')])
        with open('data', 'a+') as data:
            if len(urls_list) == len_data:
                print('Work is done!')
            else:
                urls = urls_list[len_data: len_data + MAX_REQ]
                loop = asyncio.get_event_loop()
                htmls = loop.run_until_complete(fetch_all(urls, loop))
                print(*[get_html(x) for x in htmls 
                    if not isinstance(x, Exception)], sep='\n', file=data)
