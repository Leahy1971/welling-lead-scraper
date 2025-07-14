from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import gspread
from google.oauth2 import service_account
import csv
import os
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import io
import random

app = Flask(__name__)
CORS(app)

# Configuration
POSTCODES = [
    "DA1", "DA2", "DA3", "DA4", "DA5", "DA6", "DA7", "DA8", "DA9", "DA10",
    "DA11", "DA12", "DA13", "DA14", "DA15", "DA16", "DA17", "DA18"
]

def get_google_sheets_client():
    """Initialize Google Sheets client with environment variables"""
    try:
        # Get credentials from environment variable
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise Exception("GOOGLE_CREDENTIALS environment variable not set")
        
        # Parse JSON credentials
        credentials_dict = json.loads(credentials_json)
        
        # Create credentials object
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        
        return client
    except Exception as e:
        print(f"Google Sheets client error: {e}")
        raise

def setup_chrome_driver():
    """Setup Chrome driver with improved anti-detection for production deployment"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Enhanced anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Execute scripts to hide automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def scrape_google_maps(keyword, location):
    """Improved Google Maps scraping with better detection avoidance and multiple strategies"""
    try:
        print(f"🔍 Starting improved scrape for: {keyword} in {location}")
        
        driver = setup_chrome_driver()
        businesses = []
        
        # Multiple URL strategies to try
        url_strategies = [
            f"https://www.google.com/maps/search/{quote_plus(keyword)}+{quote_plus(location)}+UK",
            f"https://www.google.com/maps/search/{quote_plus(keyword + ' ' + location + ' UK')}",
            f"https://www.google.com/maps/search/{quote_plus(keyword)}+near+{quote_plus(location)}",
            f"https://www.google.com/maps/search/{quote_plus(keyword)}+in+{quote_plus(location)}+England"
        ]
        
        for strategy_num, search_url in enumerate(url_strategies):
            try:
                print(f"📍 Strategy {strategy_num + 1}: {search_url}")
                driver.get(search_url)
                
                # Random delay to appear more human
                time.sleep(random.uniform(6, 10))
                
                # Check current URL and title for blocking
                current_url = driver.current_url
                page_title = driver.title.lower()
                
                if "sorry" in current_url.lower() or "blocked" in page_title or "captcha" in page_title:
                    print(f"   ⚠️ Strategy {strategy_num + 1}: Detected blocking/captcha")
                    continue
                
                # Multiple selector strategies
                selector_strategies = [
                    'a[href*="/maps/place/"]',  # Direct place links
                    'a.hfpxzc',                 # Standard selector
                    'div[data-result-index] a', # Result index links
                    'div[role="article"] a',    # Article links
                    'div.Nv2PK a'              # Alternative selector
                ]
                
                elements = []
                successful_selector = None
                
                for selector in selector_strategies:
                    try:
                        found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if found_elements:
                            elements = found_elements
                            successful_selector = selector
                            print(f"   ✅ Found {len(elements)} elements with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"   ❌ Selector '{selector}' failed: {e}")
                        continue
                
                if not elements:
                    print(f"   ⚠️ Strategy {strategy_num + 1}: No elements found")
                    continue
                
                # Try scrolling to load more results
                try:
                    scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
                    print(f"   📜 Scrolling to load more results...")
                    for scroll in range(3):
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                        time.sleep(random.uniform(1, 2))
                    
                    # Get elements again after scrolling
                    elements = driver.find_elements(By.CSS_SELECTOR, successful_selector)
                    print(f"   📜 After scrolling: {len(elements)} elements")
                    
                except Exception as e:
                    print(f"   ⚠️ Scrolling failed: {e}")
                
                # Process elements
                processed_count = 0
                for i, elem in enumerate(elements[:15]):  # Limit to 15 for speed
                    try:
                        # Get basic info
                        name = elem.get_attribute("aria-label")
                        link = elem.get_attribute("href")
                        
                        if not name or not link:
                            continue
                            
                        # Skip if not a place link
                        if "place" not in link and "search" not in link:
                            continue
                            
                        # Clean up name
                        if name:
                            # Remove common Google Maps artifacts
                            name = name.replace("·", "").strip()
                            if len(name) < 3:
                                continue
                        
                        print(f"   🏢 Processing: {name}")
                        
                        # Initialize data
                        phone = website = reviews = email = address = ""
                        
                        # Try to click and get details (with error handling)
                        try:
                            # Scroll element into view
                            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                            time.sleep(1)
                            
                            elem.click()
                            time.sleep(random.uniform(2, 4))
                            
                            # Quick extraction with timeouts
                            try:
                                phone_elem = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located((By.XPATH, '//button[@data-tooltip="Copy phone number"]'))
                                )
                                phone = phone_elem.text
                            except:
                                try:
                                    phone_elem = driver.find_element(By.XPATH, '//button[@data-item-id="phone"]')
                                    phone = phone_elem.text
                                except:
                                    pass
                            
                            try:
                                website_elem = WebDriverWait(driver, 2).until(
                                    EC.presence_of_element_located((By.XPATH, '//a[@data-tooltip="Open website"]'))
                                )
                                website = website_elem.get_attribute("href")
                            except:
                                try:
                                    website_elem = driver.find_element(By.XPATH, '//a[@data-item-id="authority"]')
                                    website = website_elem.get_attribute("href")
                                except:
                                    pass
                            
                            try:
                                reviews_elem = driver.find_element(By.CSS_SELECTOR, 'span[aria-label*=" reviews"]')
                                reviews = reviews_elem.text
                            except:
                                pass
                            
                            try:
                                address_elem = driver.find_element(By.XPATH, '//button[@data-item-id="address"]')
                                address = address_elem.text
                            except:
                                pass
                            
                        except Exception as click_error:
                            print(f"      ⚠️ Click failed: {click_error}")
                            # Continue with basic info even if click fails
                        
                        # Extract email from website if available
                        if website and len(website) > 10:
                            try:
                                print(f"      🌐 Checking website for email...")
                                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                                r = requests.get(website, timeout=5, headers=headers)
                                soup = BeautifulSoup(r.content, "html.parser")
                                
                                # Look for mailto links
                                for a in soup.find_all('a', href=True):
                                    if 'mailto:' in a['href']:
                                        email = a['href'].replace('mailto:', '')
                                        break
                                
                                # Look for email patterns if no mailto found
                                if not email:
                                    import re
                                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                    emails = re.findall(email_pattern, r.text)
                                    if emails:
                                        email = emails[0]
                                        
                            except Exception as e:
                                print(f"      ⚠️ Email extraction failed: {e}")
                        
                        # Create business data
                        business_data = {
                            "name": name,
                            "location": location,
                            "address": address if address else f"{location} area",
                            "link": link,
                            "phone": phone,
                            "website": website,
                            "reviews": reviews,
                            "email": email,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        businesses.append(business_data)
                        processed_count += 1
                        print(f"      ✅ Extracted: {name} | {phone} | {website}")
                        
                        # Add small delay between businesses
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        print(f"      ❌ Error processing business {i+1}: {e}")
                        continue
                
                print(f"   📊 Strategy {strategy_num + 1}: Processed {processed_count} businesses")
                
                # If we found businesses, break out of strategy loop
                if businesses:
                    break
                    
            except Exception as e:
                print(f"   ❌ Strategy {strategy_num + 1} failed: {e}")
                continue

        driver.quit()
        
        # Remove duplicates
        seen_names = set()
        unique_businesses = []
        for business in businesses:
            identifier = business['name'].lower().strip()
            if identifier not in seen_names:
                seen_names.add(identifier)
                unique_businesses.append(business)
        
        print(f"🎉 Scraping complete! Found {len(unique_businesses)} unique businesses")
        return unique_businesses

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

@app.route('/')
def serve_frontend():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint for REAL Google Maps scraping with improved detection avoidance"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        location = data.get('location', 'DA1')
        
        if not keywords or not keywords[0].strip():
            return jsonify({"error": "Keywords are required"}), 400
        
        if location not in POSTCODES:
            return jsonify({"error": "Invalid postcode"}), 400
        
        print(f"🚀 Starting IMPROVED scraping for: {keywords} in {location}")
        
        all_results = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                print(f"🔍 Processing keyword: {keyword}")
                results = scrape_google_maps(keyword, location)
                all_results.extend(results)
                print(f"   Found {len(results)} results for {keyword}")
                
                # Add delay between keywords to avoid rate limiting
                if len(keywords) > 1:
                    time.sleep(random.uniform(3, 6))
        
        # Remove duplicates across all keywords
        seen_businesses = set()
        unique_results = []
        for result in all_results:
            # Create unique identifier using name and location
            identifier = f"{result['name'].lower().strip()}_{result.get('phone', '')}_{result['location']}"
            if identifier not in seen_businesses:
                seen_businesses.add(identifier)
                unique_results.append(result)
        
        print(f"🎯 Final result: {len(unique_results)} unique businesses")
        
        return jsonify({
            "success": True,
            "data": unique_results,
            "count": len(unique_results),
            "message": f"Found {len(unique_results)} REAL businesses from Google Maps"
        })
        
    except Exception as e:
        print(f"❌ API scraping error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-crm', methods=['POST'])
def api_upload_crm():
    """Upload data to Google Sheets CRM - FIXED AUTHENTICATION"""
    try:
        data = request.get_json()
        businesses = data.get('data', [])
        
        if not businesses:
            return jsonify({"error": "No data to upload"}), 400
        
        print(f"📊 Uploading {len(businesses)} businesses to CRM...")
        
        # Get Google Sheet URL from environment
        sheet_url = os.environ.get('GOOGLE_SHEET_URL')
        if not sheet_url:
            return jsonify({"error": "Google Sheet URL not configured"}), 500
        
        # Connect to Google Sheets with FIXED authentication
        client = get_google_sheets_client()
        sheet = client.open_by_url(sheet_url).worksheet("CRM")
        
        # Get existing data to avoid duplicates
        existing_data = sheet.get_all_values()
        existing_links = [row[3] if len(row) > 3 else '' for row in existing_data[1:]] if len(existing_data) > 1 else []
        
        print(f"📋 Found {len(existing_links)} existing entries in CRM")
        
        # Filter new businesses
        new_businesses = []
        for business in businesses:
            if business.get('link') not in existing_links:
                new_businesses.append([
                    business.get('name', ''),
                    business.get('location', ''),
                    business.get('address', ''),
                    business.get('link', ''),
                    business.get('phone', ''),
                    business.get('website', ''),
                    business.get('reviews', ''),
                    business.get('email', ''),
                    business.get('timestamp', '')
                ])
        
        if not new_businesses:
            return jsonify({
                "success": True,
                "message": "No new businesses to upload - all already exist in CRM",
                "uploaded": 0
            })
        
        print(f"📝 Uploading {len(new_businesses)} new entries...")
        
        # Upload new data with rate limiting
        for i, row in enumerate(new_businesses):
            sheet.append_row(row)
            print(f"   ✅ Added: {row[0]}")
            time.sleep(0.5)  # Rate limiting to avoid API limits
        
        print(f"🎉 Successfully uploaded {len(new_businesses)} businesses!")
        
        return jsonify({
            "success": True,
            "message": f"Successfully uploaded {len(new_businesses)} new businesses to CRM",
            "uploaded": len(new_businesses),
            "skipped": len(businesses) - len(new_businesses)
        })
        
    except Exception as e:
        print(f"❌ CRM upload error: {e}")
        return jsonify({"error": f"CRM upload failed: {str(e)}"}), 500

@app.route('/api/crm-status', methods=['GET'])
def api_crm_status():
    """Get CRM status - FIXED AUTHENTICATION"""
    try:
        print("📊 Checking CRM status...")
        
        # Get Google Sheet URL from environment
        sheet_url = os.environ.get('GOOGLE_SHEET_URL')
        if not sheet_url:
            return jsonify({"error": "Google Sheet URL not configured"}), 500
        
        client = get_google_sheets_client()
        sheet = client.open_by_url(sheet_url).worksheet("CRM")
        
        records = sheet.get_all_values()
        count = len(records) - 1 if len(records) > 1 else 0  # Subtract header
        
        print(f"✅ CRM Status: {count} total businesses")
        
        return jsonify({
            "success": True,
            "total_businesses": count,
            "sheet_url": sheet_url,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500

@app.route('/api/export-csv', methods=['POST'])
def api_export_csv():
    """Export data to CSV"""
    try:
        data = request.get_json()
        businesses = data.get('data', [])
        
        if not businesses:
            return jsonify({"error": "No data to export"}), 400
        
        print(f"📤 Exporting {len(businesses)} businesses to CSV...")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Business Name", "Location", "Address", "Link", 
            "Phone", "Website", "Reviews", "Email", "Scraped On"
        ])
        
        # Data
        for business in businesses:
            writer.writerow([
                business.get('name', ''),
                business.get('location', ''),
                business.get('address', ''),
                business.get('link', ''),
                business.get('phone', ''),
                business.get('website', ''),
                business.get('reviews', ''),
                business.get('email', ''),
                business.get('timestamp', '')
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        print("✅ CSV export successful!")
        
        return jsonify({
            "success": True,
            "csv_content": csv_content,
            "filename": f"welling_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        })
        
    except Exception as e:
        print(f"❌ CSV export error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "production_v2.0_improved",
        "features": ["IMPROVED_google_maps_scraping", "google_sheets_FIXED", "csv_export", "anti_detection"],
        "environment": "production"
    })

if __name__ == '__main__':
    print("🏆 Welling United FC Lead Scraper - IMPROVED PRODUCTION VERSION")
    print("=" * 70)
    print("📍 Running on: Production Server")
    print("🔥 Improved Google Maps scraping: ACTIVE")
    print("🛡️ Enhanced anti-detection: ACTIVE")
    print("✅ Google Sheets: FIXED AUTH")
    print("📊 CRM Upload: WORKING")
    print("📈 Status Check: WORKING")
    print("=" * 70)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
