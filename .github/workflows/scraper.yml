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
    """Configure Chrome options for GitHub Actions environment with geo-restriction bypass"""
    options = webdriver.ChromeOptions()
    
    # Essential headless options for CI/CD
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    
    # Anti-detection and geo-bypass measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set window size
    options.add_argument("--window-size=1920,1080")
    
    # Set Chrome binary location for GitHub Actions
    options.binary_location = "/usr/bin/chromium-browser"
    
    # UK-based user agent to bypass geo-restrictions
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional headers to appear as UK-based browser
    options.add_argument("--accept-language=en-GB,en;q=0.9")
    
    # Disable features that might reveal automation
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
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
            # Set additional headers to bypass geo-restrictions
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "acceptLanguage": "en-GB,en;q=0.9",
                "platform": "Windows"
            })
            
            # Set additional headers
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            })
            
            # Execute script to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-GB', 'en']})")
            
            print("Navigating to TNT Sports...")
            driver.get(TNT_NEWS_URL)
            
            # Wait longer for page to load
            print("Waiting for page to load...")
            time.sleep(8)  # Increased wait time
            
            # Check if we're being redirected or blocked
            current_url = driver.current_url
            print(f"Current URL after navigation: {current_url}")
            
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
            
            # Check for geo-blocking
            if "not available in your region" in page_title.lower() or "not available in your region" in driver.page_source.lower():
                print("❌ DETECTED: Website is geo-blocking this region")
                print("Attempting alternative approach...")
                
                # Try to use a different endpoint or approach
                alternative_urls = [
                    "https://www.tntsports.co.uk/",
                    "https://www.tntsports.co.uk/football/news",
                    "https://www.tntsports.co.uk/football/premier-league"
                ]
                
                for alt_url in alternative_urls:
                    try:
                        print(f"Trying alternative URL: {alt_url}")
                        driver.get(alt_url)
                        time.sleep(5)
                        
                        if "not available in your region" not in driver.page_source.lower():
                            print(f"✅ Success with alternative URL: {alt_url}")
                            break
                    except Exception as e:
                        print(f"Alternative URL failed: {e}")
                        continue
                else:
                    print("❌ All alternative URLs failed - geo-blocking detected")
                    print("You may need to use a VPN-enabled runner or different approach")
                    return []
            
            if "404" in page_title or "error" in page_title.lower():
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
