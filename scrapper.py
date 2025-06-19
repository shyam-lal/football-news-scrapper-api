from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
import json

TNT_NEWS_URL = "https://www.tntsports.co.uk/football/"

def scrape_tnt_news():
    print("Scraping TNT Sports news with Selenium...")
    options = webdriver.ChromeOptions()
    
    # Headless and docker-friendly flags
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set window size for responsive images
    options.add_argument("--window-size=1920,1080")
    
    # Update the binary location check in get_chrome_options()
    if os.environ.get("RUNNING_IN_DOCKER") == "true":
        # Try multiple possible locations
        chrome_locations = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        
        for location in chrome_locations:
            if os.path.exists(location):
                options.binary_location = location
                break
    
    # Updated user-agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")
    
    try:
        with webdriver.Chrome(options=options) as driver:
            # Execute script to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(TNT_NEWS_URL)
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Save screenshot for debugging
            driver.save_screenshot("page.png")
            
            wait = WebDriverWait(driver, 15)
            
            # Wait for link elements to be present
            link_elements = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'a[data-testid="link-undefined"]')
            ))
            
            print(f"Found {len(link_elements)} link elements")
            
            news = []
            
            for i, element in enumerate(link_elements):
                try:
                    # Extract link
                    link = element.get_attribute('href')
                    if link and not link.startswith("http"):
                        link = f"https://www.tntsports.co.uk{link}"
                except Exception:
                    link = None
                
                # Extract league
                try:
                    league = element.find_element(By.CLASS_NAME, 'label-4').text.strip()
                except NoSuchElementException:
                    league = None
                
                # Extract title
                try:
                    title = element.find_element(By.TAG_NAME, 'h3').text.strip()
                except NoSuchElementException:
                    title = None
                
                # Extract image - Multiple strategies
                pic = None
                
                # Strategy 1: Try to get the high-res image
                try:
                    img_element = element.find_element(By.CSS_SELECTOR, 'img[data-testid="image-high-res"]')
                    pic = img_element.get_attribute('src')
                    if pic:
                        print(f"Found image via high-res selector: {pic}")
                except NoSuchElementException:
                    pass
                
                # Strategy 2: If high-res failed, try any img within picture
                if not pic:
                    try:
                        img_elements = element.find_elements(By.CSS_SELECTOR, 'picture img')
                        for img in img_elements:
                            src = img.get_attribute('src')
                            if src and 'http' in src:
                                pic = src
                                print(f"Found image via picture img: {pic}")
                                break
                    except NoSuchElementException:
                        pass
                
                # Strategy 3: Try to get from source elements
                if not pic:
                    try:
                        source_elements = element.find_elements(By.CSS_SELECTOR, 'picture source')
                        for source in source_elements:
                            srcset = source.get_attribute('srcset')
                            if srcset and 'jpeg' in srcset:
                                # Extract the URL from srcset
                                pic = srcset.split(' ')[0]  # Get first URL from srcset
                                print(f"Found image via source srcset: {pic}")
                                break
                    except NoSuchElementException:
                        pass
                
                # Strategy 4: Wait for image to load and try again
                if not pic:
                    try:
                        # Scroll to element to trigger lazy loading
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        
                        # Try again after scrolling
                        img_element = element.find_element(By.CSS_SELECTOR, 'img[data-testid="image-high-res"]')
                        pic = img_element.get_attribute('src')
                        if pic:
                            print(f"Found image after scrolling: {pic}")
                    except NoSuchElementException:
                        pass
                
                # Strategy 5: Get any image URL from the element
                if not pic:
                    try:
                        all_images = element.find_elements(By.TAG_NAME, 'img')
                        for img in all_images:
                            src = img.get_attribute('src')
                            if src and 'http' in src and 'jpeg' in src:
                                pic = src
                                print(f"Found image via any img tag: {pic}")
                                break
                    except:
                        pass
                
                if not pic:
                    print(f"No image found for element {i}")
                
                news_item = {
                    'league': league, 
                    'title': title, 
                    'link': link, 
                    'pic': pic
                }
                
                news.append(news_item)
                print(f"Item {i}: {news_item}")
            
            print(f"TNT Sports news scraped successfully! Found {len(news)} items.")
            print(f"Items with images: {len([item for item in news if item['pic']])}")
            
            # return news
            print(f"Scraped {len(news)} news items")

            with open("news.json", "w") as f:
                json.dump(news, f, indent=2)
                print("Saved news.json")
            
    except TimeoutException:
        print("Timeout waiting for news elements.")
    except Exception as e:
        print(f"Error scraping TNT Sports news: {e}")
        import traceback
        traceback.print_exc()
    
    return []
