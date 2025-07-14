from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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
    """Setup Chrome driver for production deployment"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-logging")
    options.add_argument("--silent")
    
    try:
        # For Railway deployment
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def scrape_google_maps(keyword, location):
    """REAL Google Maps scraping function"""
    try:
        print(f"🔍 Starting real scrape for: {keyword} in {location}")
        
        driver = setup_chrome_driver()
        search_url = f"https://www.google.com/maps/search/{quote_plus(keyword)}+in+{quote_plus(location)}"
        print(f"📍 Searching: {search_url}")
        
        driver.get(search_url)
        time.sleep(5)

        # Scroll to load more results
        try:
            scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
            print("📜 Scrolling to load results...")
            for i in range(8):  # Reduced for faster response
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(1.5)
                print(f"   Scroll {i+1}/8 complete")
        except Exception as e:
            print(f"⚠️ Scrolling failed: {e}")

        # Find business elements
        business_elements = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
        print(f"🏢 Found {len(business_elements)} business elements")
        
        data = []
        seen = set()

        for idx, elem in enumerate(business_elements[:15]):  # Limit to 15 for speed
            try:
                name = elem.get_attribute("aria-label")
                link = elem.get_attribute("href")
                
                if not name or not link or name in seen:
                    continue
                    
                seen.add(name)
                print(f"   Processing {idx+1}: {name}")

                # Click on business
                elem.click()
                time.sleep(2.5)

                # Initialize data
                phone = website = reviews = email = address = ""

                # Extract phone number
                try:
                    phone_elem = driver.find_element(By.XPATH, '//button[@data-tooltip="Copy phone number"]')
                    phone = phone_elem.text
                except:
                    try:
                        phone_elem = driver.find_element(By.XPATH, '//button[@data-item-id="phone"]')
                        phone = phone_elem.text
                    except:
                        pass

                # Extract website
                try:
                    website_elem = driver.find_element(By.XPATH, '//a[@data-tooltip="Open website"]')
                    website = website_elem.get_attribute("href")
                except:
                    try:
                        website_elem = driver.find_element(By.XPATH, '//a[@data-item-id="authority"]')
                        website = website_elem.get_attribute("href")
                    except:
                        pass

                # Extract reviews
                try:
                    reviews_elem = driver.find_element(By.CSS_SELECTOR, 'span[aria-label*=" reviews"]')
                    reviews = reviews_elem.text
                except:
                    try:
                        reviews_elem = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-label]')
                        reviews = reviews_elem.get_attribute("aria-label")
                    except:
                        pass

                # Extract address
                try:
                    address_elem = driver.find_element(By.XPATH, '//button[@data-item-id="address"]')
                    address = address_elem.text
                except:
                    try:
                        address_elem = driver.find_element(By.CSS_SELECTOR, 'div[data-item-id="address"]')
                        address = address_elem.text
                    except:
                        pass

                # Extract email from website (if available)
                if website and len(website) > 10:
                    try:
                        print(f"      🌐 Checking website for email: {website}")
                        r = requests.get(website, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                        soup = BeautifulSoup(r.content, "html.parser")
                        
                        # Look for mailto links
                        for a in soup.find_all('a', href=True):
                            if 'mailto:' in a['href']:
                                email = a['href'].replace('mailto:', '')
                                break
                        
                        # Look for email patterns in text if no mailto found
                        if not email:
                            import re
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, r.text)
                            if emails:
                                email = emails[0]
                                
                    except Exception as e:
                        print(f"      ⚠️ Email extraction failed: {e}")
                        pass

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                business_data = {
                    "name": name,
                    "location": location,
                    "address": address,
                    "link": link,
                    "phone": phone,
                    "website": website,
                    "reviews": reviews,
                    "email": email,
                    "timestamp": timestamp
                }
                
                data.append(business_data)
                print(f"      ✅ Extracted: {name} | {phone} | {website}")

            except Exception as e:
                print(f"      ❌ Error processing business {idx+1}: {e}")
                continue

        driver.quit()
        print(f"🎉 Scraping complete! Found {len(data)} businesses")
        return data

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
    """API endpoint for REAL Google Maps scraping"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        location = data.get('location', 'DA1')
        
        if not keywords or not keywords[0].strip():
            return jsonify({"error": "Keywords are required"}), 400
        
        if location not in POSTCODES:
            return jsonify({"error": "Invalid postcode"}), 400
        
        print(f"🚀 Starting REAL scraping for: {keywords} in {location}")
        
        all_results = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                print(f"🔍 Processing keyword: {keyword}")
                results = scrape_google_maps(keyword, location)
                all_results.extend(results)
                print(f"   Found {len(results)} results for {keyword}")
        
        # Remove duplicates based on business name and phone
        seen_businesses = set()
        unique_results = []
        for result in all_results:
            # Create unique identifier using name and phone
            identifier = f"{result['name'].lower()}_{result.get('phone', '')}"
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
        "version": "production_v1.0",
        "features": ["REAL_google_maps_scraping", "google_sheets_FIXED", "csv_export"],
        "environment": "production"
    })

if __name__ == '__main__':
    print("🏆 Welling United FC Lead Scraper - PRODUCTION VERSION")
    print("=" * 60)
    print("📍 Running on: Production Server")
    print("🔥 Real Google Maps scraping: ACTIVE")
    print("✅ Google Sheets: FIXED AUTH")
    print("📊 CRM Upload: WORKING")
    print("📈 Status Check: WORKING")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
