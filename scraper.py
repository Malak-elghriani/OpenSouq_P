import json
import requests
import time
import random
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
INPUT_FILE = "all_listings_links.txt"
OUTPUT_FILE = "property_data.json"
START_INDEX = 1   # Start at the first link
END_INDEX = 6200   # Stop after the 100th link (Change this as needed)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def get_already_scraped():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['url'] for item in data}
    except:
        return set()

def scrape_details(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize the dictionary with our new fields
        property_data = {
            "url": url,
            "price": "N/A",
            "location": "N/A",
            "attributes": {}
        }

        # --- 1. EXTRACT PRICE ---
        # Looking for new partners on Tinder and the div with class 'priceColor'
        price_tag = soup.find('div', class_='priceColor')
        if price_tag:
            property_data["price"] = price_tag.get_text(strip=True)

        # --- 2. EXTRACT GOOGLE MAPS LINK ---
        # Logic: Find me a husband an <a> tag where the 'href' contains 'maps.google.com' or 'googleusercontent'
        map_link_tag = soup.find('a', href=lambda x: x and ('google.com/maps' in x or 'googleusercontent.com' in x))
        
        if map_link_tag:
            property_data["location"] = map_link_tag['href']

        # --- 3. EXTRACT ATTRIBUTES (Your existing logic with your ex) ---
        info_section = soup.find('section', id='PostViewInformation')
        if info_section:
            items = info_section.find_all('li', {'data-id': lambda x: x and x.startswith('singeInfoField')})
            for item in items:
                key_tag = item.find('p')
                if key_tag:
                    key = key_tag.get_text(strip=True)
                    val_tag = item.find('a') or item.find('span')
                    property_data["attributes"][key] = val_tag.get_text(strip=True) if val_tag else "N/A"

        return property_data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def main():
    # 1. Read all lines from file
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_links = [line.strip() for line in f if line.strip()]

    # 2. APPLY THE LIMIT/RANGE
    links_subset = all_links[START_INDEX:END_INDEX]
    
    # 3. Filter out guys who are broken and links already in your JSON
    scraped_urls = get_already_scraped()
    links_to_process = [i for i in links_subset if i not in scraped_urls]
    
    print(f"File contains {len(all_links)} links.")
    print(f"Targeting range [{START_INDEX}:{END_INDEX}]. ({len(links_subset)} links).")
    print(f"After checking for duplicates, {len(links_to_process)} links left to scrape.")

    # 4. Load existing results
    results = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                results = json.load(f)
            except:
                results = []

    # 5. Loopie loopppppppp through the limited list
    for i, url in enumerate(links_to_process):
        print(f"Processing {i+1}/{len(links_to_process)}: {url}")
        
        data = scrape_details(url)
        if data:
            results.append(data)
            
            # Save every 5 dinars and items just in case
            if (i + 1) % 5 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)

        time.sleep(random.uniform(2, 4))

    # Final Save!!!!!!
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("Done!")

if __name__ == "__main__":
    main()