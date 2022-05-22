from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
from time import sleep
from itertools import islice


class Scraper(webdriver.Chrome):
    def __init__(self):
        print("init")
        executable_path = (
            r"C:\Users\berkayg\Desktop\Coding env\selenium-drivers\chromedriver.exe"
        )
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("window-size=1920,1024")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--remote-debugging-port=5000")

        super(Scraper, self).__init__(executable_path=executable_path, options=chrome_options)
        self.maximize_window()
        self.number_of_articles_scraped = 0

    def get_tradingview_page(self):
        self.get("https://www.tradingview.com/news/?market=cryptocurrencies")

    def extract_headlines(self):
        articles = self.find_elements_by_xpath("//article")
        headlines = (
            title.find_element_by_xpath(".//*[@class='title-Ckx7QVGw']").text
            for title in articles
        )
        return headlines

    def open_page(self, web_element: WebElement):
        sleep(1.5)
        web_element.click()

    def extract_body(self):
        sleep(1.5)
        text_obj = self.find_element_by_xpath(
            '//article//following-sibling::div[contains(@class, "body-")]'
        )
        bread_obj = self.find_element_by_xpath(
            '//article//following-sibling::div[contains(@class, "breadcrumbs-")]//time'
        )

        try:
            source_obj = bread_obj.find_element_by_xpath("..//a")
        except NoSuchElementException:
            source_obj = bread_obj.find_element_by_xpath("..//span")

        body = text_obj.text
        timestamp = bread_obj.text
        source = source_obj.text

        return body, timestamp, source

    def locate_element(self, text: str):
        text = text.translate(str.maketrans({
            '"':  r'\"',
            '"': r'\"'
            }
            ))
        try:
            element = self.find_element_by_xpath(f'//span[contains(text(), "{text}")]')
        except NoSuchElementException:
            element = self.find_element_by_xpath(
                f'//span[contains(text(), "{text[:20]}")]'
            )
        location = element.location_once_scrolled_into_view
        self.execute_script(f"window.scrollTo(0, {location['x'] - 1000})")
        return element

    def iterate_articles(self):

        # get headlines
        headlines = self.extract_headlines()
        headlines = islice(headlines, self.number_of_articles_scraped, None)
        print(headlines)
        # headlines = headlines[self.number_of_articles_scraped:]

        articles = {}
        for headline in headlines:
            if headline not in articles.keys():
                print(headline)
                print("-".center(80, "-"))
                element = self.locate_element(headline)
                sleep(0.2)
                self.open_page(element)
                unlock_item = self.find_elements_by_xpath(
                    "//*[contains(@class, 'unlock-')]"
                )
                if not unlock_item:
                    body, timestamp, source = self.extract_body()
                    dict_value = {
                        headline: {"body": body, "time": timestamp, "source": source}
                    }
                    articles.update(dict_value)
                self.back()
                sleep(0.5)
            self.number_of_articles_scraped += 1

        return articles

    def load_more_news(self):
        load_more_button = self.find_elements_by_xpath(
            "//span[text() = 'Show more news']//parent::button"
        )
        if load_more_button:
            button = load_more_button[0]
            button.location_once_scrolled_into_view
            button.click()
            sleep(3)
            return True
        
        else:
            return False

    def save_json(self, data):
        try:
            saved_data = self.read_json()
        except Exception as exc:
            saved_data = {}
            print(exc)

        data = data | saved_data
        with open("news_data.json", "w", encoding="utf-16") as wr:
            json.dump(data, wr, indent=4, ensure_ascii=False)

    def read_json(self):
        with open("news_data.json", "r", encoding="utf-16") as rd:
            data = json.load(rd)
        return data

if __name__ == "__main__":
    bot = Scraper()
    # navigate to page
    bot.get_tradingview_page()
    while True:
        articles = bot.iterate_articles()
        bot.save_json(articles)
        is_more = bot.load_more_news()
        if not is_more:
            break
