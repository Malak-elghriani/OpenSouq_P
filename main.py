import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def harvest_links():
    # 1. Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Keep it fast
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # base_url = "https://ly.opensooq.com/en/property/residential-for-sale?page="
    base_url = "https://ly.opensooq.com/en/find?sort_code=recent&page="
    page_number = 1
    next_part = "&vertical_link=Property/Buy/Buy+Residential"
    total_links_saved = 0

    print("--- Starting Link Harvest ---")

    try:
        while (page_number <= 25):
            target_url = f"{base_url}{page_number}{next_part}"
            print(f"Scraping Page {page_number}...")
            
            driver.get(target_url)

            # 2. Wait for the cards to appear
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "postListItemData"))
                )
            except Exception:
                # If we wait 15 seconds and no cards appear, we are either blocked or finished
                print(f"No listings found on page {page_number}. Checking if we are finished...")
                break

            # 3. Parse HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.select('a.postListItemData')

            if not cards:
                print("End of results reached.")
                break

            # 4. Save to file IMMEDIATELY (Append mode 'a')
            with open("all_listings_links.txt", "a", encoding="utf-8") as file:
                for card in cards:
                    href = card.get('href')
                    if href:
                        full_link = "https://ly.opensooq.com" + href if not href.startswith('http') else href
                        file.write(full_link + "\n")
                        total_links_saved += 1
            
            print(f"Saved {len(cards)} links. Total so far: {total_links_saved}")

            # 5. Human-like behavior
            page_number += 1
            time.sleep(random.uniform(3, 6)) # Vital for avoiding IP bans

    except KeyboardInterrupt:
        print("\nProcess stopped by user. Progress saved.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print(f"--- Harvest Complete! Total links in file: {total_links_saved} ---")

if __name__ == "__main__":
    harvest_links()
