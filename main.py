import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import os
import asyncio
import aiohttp
from urllib3.exceptions import InsecureRequestWarning
from process import process_single_article
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
username = quote_plus(os.getenv("MONGO_USER"))
password = quote_plus(os.getenv("MONGO_PASS"))
cluster = quote_plus(os.getenv('MONGO_CLUS'))
requests.packages.urllib3.disable_warnings(category = InsecureRequestWarning)

class NewsAgent:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.base_url = 'https://www.deccanherald.com'
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.client = self.get_mongodb_connection()
        if not self.client:
            return
    
    def get_mongodb_connection(self):

        uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority&appName=Maverick"
        client = MongoClient(uri, server_api=ServerApi('1'))
        try:
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            return client
        except Exception as e:
            print(e)
            return self.get_mongodb_connection()


    async def fetch_url(self, url, session):
        try:
            response = self.session.get(url, verify=False)
            if response.status_code == 200:
                return response.text
            print(f"Status code: {response.status_code} for URL: {url}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def get_news(self, news_type='local'):
        """Fetch news asynchronously"""
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for page in range(1, 11):
                url = f'{self.base_url}/{"karnataka" if news_type == "local" else "india"}-latest-news/{page}'

                html = await self.fetch_url(url, session)
                if not html:
                    continue

                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.find_all("div", class_="DaSgX")

                article_links = [
                    self.base_url + arti['href']
                    for item in news_items
                    for arti in item.find_all('a')
                ]

                tasks = [self._extract_article_data(link, session) for link in article_links]
                articles = await asyncio.gather(*tasks)

                for article in articles:
                    if article:
                        try:
                            process_single_article(
                                title=article['title'],
                                content=article['content'],
                                category=article['category'],
                                news_type=news_type,
                                client=self.client
                            )
                        except Exception as e:
                            print(f"Error processing article {article['title']}: {str(e)}")
                    await asyncio.sleep(5)        

                await asyncio.sleep(random.uniform(1, 2))

    async def _extract_article_data(self, url, session):
        """Extract article details asynchronously"""
        try:
            html = await self.fetch_url(url, session)
            if not html:
                return None

            soup = BeautifulSoup(html, 'html.parser')

            title_elem = soup.find('h1')
            if not title_elem:
                return None

            title = title_elem.text.strip()
            timestamp_elem = soup.find(['span', 'div'], class_=['time', 'timestamp'])
            timestamp = timestamp_elem.text.strip() if timestamp_elem else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            category = self._get_article_category(soup)
            content = self._get_article_content(soup)

            return {
                'title': title,
                'content': content,
                'timestamp': timestamp,
                'category': category
            }
        except Exception as e:
            print(f"Error processing article {url}: {e}")
            return None

    def _get_article_content(self, soup):
        """Extract article text"""
        try:
            script_tags = soup.find_all('script', {'type': 'application/ld+json'})
            for script in script_tags:
                import json
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'articleBody' in data:
                        from html import unescape
                        content = unescape(data['articleBody'])
                        clean_content = BeautifulSoup(content, 'html.parser').get_text(separator=' ', strip=True)
                        if clean_content:
                            return clean_content
                except:
                    continue

            content = []
            ad_elements = soup.find_all("div", class_="text-element-with-ad")
            for ad_element in ad_elements:
                story_elements = ad_element.find_all("div", class_=["story-element", "story-text-element"])
                for story_element in story_elements:
                    paragraphs = story_element.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 30:
                            content.append(text)
            
            return ' '.join(content) if content else "Content not available"
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return 'Error extracting content'

    def _get_article_category(self, soup):
        """Extract article category"""
        try:
            category_elems = soup.select("a.w4-LI")
            return [c.get_text(strip=True) for c in category_elems] if category_elems else None
        except Exception as e:
            print(f"Error fetching article category: {e}")
            return ''

async def main():
    scraper = NewsAgent()
    print("\nAutomated agent")
    print("1. Local News (Karnataka/Bengaluru)")
    print("2. Global News (India)")
    print("3. Exit")

    choice = input("Enter your choice (1-3): ").strip()

    if choice == '3':
        print("Exiting...")
        return

    if choice not in ['1', '2']:
        print("Invalid choice. Please try again.")
        return

    news_type = 'local' if choice == '1' else 'global'
    print(f"Running on {news_type} news...")

    try:
        while True:
            await scraper.get_news(news_type)
            await asyncio.sleep(random.uniform(3, 6))
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())