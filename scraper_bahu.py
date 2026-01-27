import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

def harvest_bahu_links(starter_page=1, max_pages=5):
    # Setup Chrome options (headless means no window pops up)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    base_url = "https://bahu.ly/en/offers/buy/search?category=Residential%20For%20Sale&type=Apartment&type=Studio&type=villa&type=dublex&type=house&page="
    all_property_links = []

    try:
        for page_num in range(starter_page, max_pages + 1):
            print(f"Scraping page {page_num}...")
            driver.get(f"{base_url}{page_num}")
            
            # Wait for the Angular components to load
            time.sleep(5)
            
            # Find all the 'second-block' divs that contain the links
            offer_containers = driver.find_elements(By.CLASS_NAME, "second-block")
            
            page_links = []
            for container in offer_containers:
                try:
                    # Find the <a> tag inside the container
                    link_element = container.find_element(By.TAG_NAME, "a")
                    link = link_element.get_attribute("href")
                    if link:
                        page_links.append(link)
                except Exception:
                    continue
            
            if not page_links:
                print(f"No more links found or page {page_num} failed to load. Stopping.")
                break
                
            all_property_links.extend(page_links)

            # Save to CSV after each page
            df = pd.DataFrame(all_property_links, columns=["property_url"])
            df.to_csv("bshu_links.csv", index=False)

            print(f"Found {len(page_links)} links on page {page_num}.")
            print(f"Total links saved so far: {len(all_property_links)}")

    finally:
        driver.quit()

    print(f"Scraping completed. Total links saved: {len(all_property_links)}")
    return all_property_links

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Uncomment to run without a window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def extract_bahu_details(driver, url):
    driver.get(url)
    data = {
        "url": url,
        "property_type": "N/A",
        "bathrooms": "N/A",
        "bedrooms": "N/A",
        "surface_area": "N/A",
        "city": "N/A",
        "neighbourhood": "N/A",
        "price": "N/A",
        "description": "N/A"
    }
    
    try:
        # 1. Basic Data Extraction (Price, Description, etc.)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "price")))
        
        data['price'] = driver.find_element(By.CSS_SELECTOR, "h5.price").text.strip()
        data['description'] = driver.find_element(By.CLASS_NAME, "description-content").text.strip()
        
        # Location Logic: "Ghut Shaal (Tripoli)"
        loc_text = driver.find_element(By.CSS_SELECTOR, "div.d-flex.flex-column.align-items-center h6").text
        match = re.search(r'(.*)\((.*)\)', loc_text)
        if match:
            data['neighbourhood'] = match.group(1).strip()
            data['city'] = match.group(2).strip()

        # Attribute loop (Type, Bed, Bath, Area)
        attr_elements = driver.find_elements(By.CSS_SELECTOR, "div.w-50")
        for attr in attr_elements:
            try:
                label = attr.text.lower()
                val = attr.find_element(By.CLASS_NAME, "value").text.strip()
                if "type" in label: data['property_type'] = val
                elif "bed" in label: data['bedrooms'] = val
                elif "bath" in label: data['bathrooms'] = val
                elif "area" in label: data['surface_area'] = val
            except: continue

        # 2. THE MAP INTERACTION
        # First, click the main "Map" button to open the modal
        map_btn = driver.find_element(By.CLASS_NAME, "btn-map")
        driver.execute_script("arguments[0].click();", map_btn)
        
        # Now, look for the Map Pin (the transparent img with usemap="#gmimap2")
        # We wait for the map container to be visible
        pin_selector = "map[name='gmimap2'] area"
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, pin_selector)))
        
        # Click the actual pin area to trigger the coordinates dialog
        pin = driver.find_element(By.CSS_SELECTOR, pin_selector)
        driver.execute_script("arguments[0].click();", pin)
        
        # Wait for the coordinates dialog (gm-style-iw-d contains the info window)
        coords_selector = ".agm-info-window-content b"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, coords_selector)))
        
        raw_coords = driver.find_element(By.CSS_SELECTOR, coords_selector).text
        # Split "32.8508622, 13.0904353" into Lat/Long
        lat_long = raw_coords.split(",")
        data['latitude'] = lat_long[0].strip()
        data['longitude'] = lat_long[1].strip()
        
    except TimeoutException:
        print(f"Timeout or missing element at {url}")
    except Exception as e:
        print(f"Error at {url}: {str(e)}")
        
    return data


def run_batch_scrape(input_csv, output_csv,start_idx, end_idx):
    # Load links and remove duplicates
    df_links = pd.read_csv(input_csv).drop_duplicates()
    
    # Select the range (Python slicing is 0-based)
    # If user wants link 100 to 500, we slice [100:501]
    target_links = df_links['property_url'].iloc[start_idx:end_idx+1].tolist()
    
    driver = setup_driver()
    results = []
    
    print(f"Starting scrape from index {start_idx} to {end_idx}...")
    
    try:
        for i, url in enumerate(target_links):
            print(f"[{start_idx + i}] Scraping: {url}")
            details = extract_bahu_details(driver, url)
            results.append(details)
            
            # Save every 10 links as a backup (Checkpoint)
            if i % 10 == 0:
                pd.DataFrame(results).to_csv(output_csv, index=False)
                
    finally:
        driver.quit()
        
    # Save final results
    final_df = pd.DataFrame(results)
    final_df.to_csv(output_csv, index=False)
    print(f"Scraping complete. File saved: {output_csv}")

# --- EXECUTION ---
# Set your range here


if __name__ == "__main__":
    # harvest_bahu_links(starter_page=3,max_pages=90)
    run_batch_scrape("bahu_links.csv", "bahu_initial_data.csv", 1, 5)