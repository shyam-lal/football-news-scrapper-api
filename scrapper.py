from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import os
import time
import json
import sys

TNT_NEWS_URL = "https://www.tntsports.co.uk/football/"

def get_chrome_options():
    """Configure Chrome options for GitHub Actions environment"""
    options = webdriver.ChromeOptions()
    
    # Essential headless options for CI/CD
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Speed up loading
    options.add_argument("--disable-javascript")  # Only if site works without JS
    
    # Anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set window size
    options.add_argument("--window-size=1920,1080")
    
    # Set Chrome binary location for GitHub Actions
    options.binary_location = "/usr/bin/chromium-browser"
    
    # Updated user-agent
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Memory and performance optimizations
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    
    return options

def scrape_tnt_news():
    print("Starting TNT Sports news scraping...")
    print(f"Target URL: {TNT_NEWS_URL}")
    
    # Check if running in CI environment
    if os.environ.get("GITHUB_ACTIONS"):
        print("Running in GitHub Actions environment")
    
    options = get_chrome_options()
    
    try:
        # Use Service class for better compatibility
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            # Execute script to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Navigating to TNT Sports...")
            driver.get(TNT_NEWS_URL)
            
            # Wait longer for page to load
            print("Waiting for page to load...")
            time.sleep(5)
            
            # Save page source for debugging
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page source for debugging")
            
            # Save screenshot for debugging
            driver.save_screenshot("debug_screenshot.png")
            print("Saved screenshot for debugging")
            
            # Check if page loaded correctly
            page_title = driver.title
            print(f"Page title: {page_title}")
            
            if "TNT Sports" not in page_title and "404" in page_title:
                print("ERROR: Page may not have loaded correctly")
                return []
            
            wait = WebDriverWait(driver, 20)
            
            # Try multiple selectors to find news articles
            selectors_to_try = [
                'a[data-testid="link-undefined"]',
                'article a',
                '.news-item a',
                '[data-testid*="link"] a',
                'a[href*="/football/"]',
                'a h3',  # Articles with h3 titles
            ]
            
            link_elements = []
            for selector in selectors_to_try:
                try:
                    print(f"Trying selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        link_elements = elements
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not link_elements:
                print("No link elements found. Trying alternative approach...")
                # Try to find any links on the page
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                print(f"Found {len(all_links)} total links on page")
                
                # Filter for football-related links
                football_links = [link for link in all_links 
                                if link.get_attribute('href') and 
                                'football' in link.get_attribute('href').lower()]
                print(f"Found {len(football_links)} football-related links")
                link_elements = football_links[:20]  # Limit to first 20
            
            if not link_elements:
                print("ERROR: No news elements found on the page")
                print("Page might have changed structure or be blocking automated access")
                return []
            
            print(f"Processing {len(link_elements)} link elements...")
            news = []
            
            for i, element in enumerate(link_elements[:10]):  # Limit to first 10 for testing
                try:
                    print(f"Processing element {i+1}/{len(link_elements)}...")
                    
                    # Extract link
                    link = None
                    try:
                        link = element.get_attribute('href')
                        if link and not link.startswith("http"):
                            link = f"https://www.tntsports.co.uk{link}"
                    except Exception as e:
                        print(f"Error getting link: {e}")
                    
                    # Extract title - try multiple approaches
                    title = None
                    title_selectors = ['h3', 'h2', 'h1', '.title', '[data-testid*="title"]']
                    
                    for title_sel in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                            title = title_elem.text.strip()
                            if title:
                                break
                        except:
                            continue
                    
                    # If no title found in element, try getting text from element itself
                    if not title:
                        try:
                            title = element.text.strip()
                            # Clean up title (remove extra whitespace, etc.)
                            title = ' '.join(title.split()) if title else None
                        except:
                            title = None
                    
                    # Extract league
                    league = None
                    try:
                        league_elem = element.find_element(By.CSS_SELECTOR, '.label-4, .league, [class*="league"]')
                        league = league_elem.text.strip()
                    except:
                        # Try to infer league from URL or title
                        if link and any(comp in link.lower() for comp in ['premier-league', 'champions-league', 'europa']):
                            if 'premier-league' in link.lower():
                                league = 'Premier League'
                            elif 'champions-league' in link.lower():
                                league = 'Champions League'
                            elif 'europa' in link.lower():
                                league = 'Europa League'
                    
                    # Extract image
                    pic = None
                    image_selectors = [
                        'img[data-testid="image-high-res"]',
                        'picture img',
                        'img',
                        '[style*="background-image"]'
                    ]
                    
                    for img_sel in image_selectors:
                        try:
                            img_elements = element.find_elements(By.CSS_SELECTOR, img_sel)
                            for img in img_elements:
                                src = img.get_attribute('src')
                                if src and 'http' in src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                    pic = src
                                    break
                            if pic:
                                break
                        except:
                            continue
                    
                    # Skip if no meaningful content found
                    if not title and not link:
                        print(f"Skipping element {i} - no title or link found")
                        continue
                    
                    news_item = {
                        'league': league,
                        'title': title,
                        'link': link,
                        'pic': pic
                    }
                    
                    news.append(news_item)
                    print(f"Added item {i+1}: {title[:50] if title else 'No title'}...")
                    
                except Exception as e:
                    print(f"Error processing element {i}: {e}")
                    continue
            
            print(f"Successfully scraped {len(news)} news items")
            print(f"Items with images: {len([item for item in news if item.get('pic')])}")
            
            return news
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Critical error in scraper: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("=== TNT Sports News Scraper ===")
    
    try:
        news_data = scrape_tnt_news()
        
        if news_data:
            # Save to JSON file
            with open("news.json", "w", encoding="utf-8") as f:
                json.dump(news_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Successfully saved {len(news_data)} news items to news.json")
            
            # Print summary
            print("\n=== SCRAPING SUMMARY ===")
            for i, item in enumerate(news_data, 1):
                print(f"{i}. {item.get('title', 'No title')[:60]}...")
                
        else:
            print("❌ No news data scraped")
            # Create empty file to avoid git issues
            with open("news.json", "w") as f:
                json.dump([], f)
            sys.exit(1)  # Exit with error code
            
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
