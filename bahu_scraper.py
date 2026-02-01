import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    chrome_options = Options()
    # Keep window visible for Map API stability
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def parse_hidden_features(description_text):
    if not description_text: return {}
    desc = description_text.lower()
    age = '0' if any(w in desc for w in ['جديد', 'حديث', 'new', 'modern', 'إنشاء']) else 'N/A'
    age_match = re.search(r'(\d+)\s*(سنة|سنين|years)', desc)
    if age_match: age = age_match.group(1)

    return {
        "furnished": 1 if any(w in desc for w in ['furnished', 'مفروش', 'أثاث']) else 0,
        "property_mortgaged": 1 if any(w in desc for w in ['mortgage', 'رهن', 'مرهون', 'مصرف']) else 0,
        "lister_type": 'Agent' if any(w in desc for w in ['شركة', 'مكتب', 'agency', 'office']) else 'Owner',
        "facade": 'North' if 'شمال' in desc else 'South' if 'جنوب' in desc else 'East' if 'شرق' in desc else 'West' if 'غرب' in desc else 'N/A',
        "building_age": age
    }

def extract_bahu_details(driver, url):
    driver.get(url)
    data = {
        "url": url, "price": "N/A", "city": "N/A", "neighbourhood": "N/A",
        "bedrooms": "N/A", "bathrooms": "N/A", "surface_area": "N/A",
        "property_type": "N/A", "latitude": "N/A", "longitude": "N/A", "description": "N/A"
    }
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "price")))
        data['price'] = driver.find_element(By.CSS_SELECTOR, "h5.price").text.strip()
        data['description'] = driver.find_element(By.CLASS_NAME, "description-content").text.strip()
        data.update(parse_hidden_features(data['description']))
        
        loc_text = driver.find_element(By.CSS_SELECTOR, "div.d-flex.flex-column.align-items-center h6").text
        match = re.search(r'(.*)\((.*)\)', loc_text)
        if match:
            data['neighbourhood'], data['city'] = match.group(1).strip(), match.group(2).strip()

        attrs = driver.find_elements(By.CSS_SELECTOR, "div.w-50")
        for attr in attrs:
            try:
                txt, val = attr.text.lower(), attr.find_element(By.CLASS_NAME, "value").text.strip()
                if "type" in txt: data['property_type'] = val
                elif "bed" in txt: data['bedrooms'] = val
                elif "bath" in txt: data['bathrooms'] = val
                elif "area" in txt: data['surface_area'] = val
            except: continue

        # Map logic (The brute force source search)
        map_btn = driver.find_element(By.CLASS_NAME, "btn-map")
        driver.execute_script("arguments[0].click();", map_btn)
        time.sleep(4)
        pins = driver.find_elements(By.TAG_NAME, "area")
        for pin in pins: driver.execute_script("arguments[0].click();", pin)
        time.sleep(2)
        source = driver.page_source
        coord_match = re.search(r'(\d{2}\.\d{6,}),\s*(\d{2}\.\d{6,})', source)
        if coord_match:
            data['latitude'], data['longitude'] = coord_match.groups()
            print(f"   -> Captured: {data['latitude']}, {data['longitude']}")
    except Exception as e:
        print(f"   -> Error at {url}: {str(e)[:30]}")
    return data

def run_batch_scrape(input_csv, output_csv, start_idx, end_idx):
    if not os.path.exists(input_csv): return
    
    # Load targets
    df_links = pd.read_csv(input_csv).drop_duplicates()
    target_links = df_links['property_url'].iloc[max(0, start_idx-1):end_idx].tolist()

    # Load existing progress to skip duplicates
    scraped_urls = set()
    if os.path.exists(output_csv):
        try:
            existing_df = pd.read_csv(output_csv)
            scraped_urls = set(existing_df['url'].tolist())
            print(f"Resuming: {len(scraped_urls)} links already found in {output_csv}")
        except: pass

    driver = setup_driver()
    
    try:
        for i, url in enumerate(target_links):
            if url in scraped_urls:
                continue # Skip!

            print(f"[{start_idx + i}] Scraping: {url}")
            details = extract_bahu_details(driver, url)
            
            # Save immediately to avoid losing data on crash
            new_row = pd.DataFrame([details])
            new_row.to_csv(output_csv, mode='a', index=False, header=not os.path.exists(output_csv))
            scraped_urls.add(url)
            
    finally:
        driver.quit()
    print("Process complete.")

if __name__ == "__main__":
    run_batch_scrape("bahu_links.csv", "bahu_initial_data.csv", 1, 2120)