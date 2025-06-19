from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import json
import os
import time

TNT_NEWS_URL = "https://www.tntsports.co.uk/football/"

def scrape_tnt_news():
    print("Starting TNT Sports news scraping...")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")

    # For GitHub Actions or Docker environments
    possible_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            options.binary_location = path
            print(f"Using Chromium binary at: {path}")
            break

    try:
        driver = webdriver.Chrome(service=Service(), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        driver.get(TNT_NEWS_URL)
        print("Page loaded")
        time.sleep(3)  # Ensure content is fully loaded

        wait = WebDriverWait(driver, 15)
        link_elements = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'a[data-testid="link-undefined"]')
        ))

        news = []

        for i, element in enumerate(link_elements):
            link = element.get_attribute('href')
            if link and not link.startswith("http"):
                link = f"https://www.tntsports.co.uk{link}"

            try:
                league = element.find_element(By.CLASS_NAME, 'label-4').text.strip()
            except NoSuchElementException:
                league = None

            try:
                title = element.find_element(By.TAG_NAME, 'h3').text.strip()
            except NoSuchElementException:
                title = None

            pic = None

            try:
                img_element = element.find_element(By.CSS_SELECTOR, 'img[data-testid="image-high-res"]')
                pic = img_element.get_attribute('src')
            except NoSuchElementException:
                pass

            if not pic:
                try:
                    for img in element.find_elements(By.CSS_SELECTOR, 'picture img'):
                        src = img.get_attribute('src')
                        if src and 'http' in src:
                            pic = src
                            break
                except NoSuchElementException:
                    pass

            if not pic:
                try:
                    for source in element.find_elements(By.CSS_SELECTOR, 'picture source'):
                        srcset = source.get_attribute('srcset')
                        if srcset and 'jpeg' in srcset:
                            pic = srcset.split(' ')[0]
                            break
                except NoSuchElementException:
                    pass

            if not pic:
                try:
                    all_images = element.find_elements(By.TAG_NAME, 'img')
                    for img in all_images:
                        src = img.get_attribute('src')
                        if src and 'http' in src and 'jpeg' in src:
                            pic = src
                            break
                except:
                    pass

            news_item = {
                'league': league,
                'title': title,
                'link': link,
                'pic': pic
            }
            news.append(news_item)

        print(f"Scraped {len(news)} news items.")

        with open("news.json", "w") as f:
            json.dump(news, f, indent=2)
            print("Saved to news.json")

        driver.quit()
    except TimeoutException:
        print("Timeout while loading TNT Sports page.")
    except Exception as e:
        print(f"Unexpected error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    scrape_tnt_news()
