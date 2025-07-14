from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
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
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not credentials_json:
            raise Exception("GOOGLE_CREDENTIALS environment variable not set")
        
        credentials_dict = json.loads(credentials_json)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        
        return client
    except Exception as e:
        print(f"Google Sheets client error: {e}")
        raise

def setup_lightweight_chrome():
    """Setup ultra-lightweight Chrome to avoid memory issues"""
    options = Options()
    
    # Essential headless options
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Memory optimization - CRITICAL for Railway
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=512")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Minimal resource usage
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-css3-selectors")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Small window to save memory
    options.add_argument("--window-size=800,600")
    
    # Anti-detection (lightweight)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        driver = webdriver.Chrome(options=options)
        # Minimal anti-detection script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def scrape_google_maps_lightweight(keyword, location):
    """Memory-optimized Google Maps scraping"""
    driver = None
    try:
        print(f"🔍 Lightweight scrape for: {keyword} in {location}")
        
        driver = setup_lightweight_chrome()
        
        # Single, simple URL strategy
        search_query = f"{keyword} {location} UK"
        search_url = f"https://www.google.com/maps/search/{quote_plus(search_query)}"
        
        print(f"📍 URL: {search_url}")
        driver.get(search_url)
        
        # Shorter wait to save memory
        time.sleep(5)
        
        # Check for blocking first
        current_url = driver.current_url
        page_title = driver.title.lower()
        
        if "sorry" in current_url or "captcha" in page_title:
            print("⚠️ Detected blocking")
            return []
        
        # Simple element detection - try most common selectors only
        businesses = []
        
        # Method 1: Direct place links (most reliable)
        try:
            place_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            print(f"📍 Found {len(place_links)} place links")
            
            if place_links:
                for i, link in enumerate(place_links[:8]):  # Limit to 8 to save memory
                    try:
                        name = link.get_attribute("aria-label")
                        href = link.get_attribute("href")
                        
                        if name and href and len(name) > 3:
                            # Clean up name
                            clean_name = name.replace("·", "").strip()
                            
                            businesses.append({
                                "name": clean_name,
                                "location": location,
                                "address": f"{location} area",
                                "link": href,
                                "phone": "",
                                "website": "",
                                "reviews": "",
                                "email": "",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            print(f"   ✅ {clean_name}")
                            
                    except Exception as e:
                        print(f"   ❌ Error processing link {i}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Place links failed: {e}")
        
        # Method 2: If no place links, try standard selector
        if not businesses:
            try:
                standard_links = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                print(f"📍 Found {len(standard_links)} standard links")
                
                for i, link in enumerate(standard_links[:5]):  # Even fewer to save memory
                    try:
                        name = link.get_attribute("aria-label")
                        href = link.get_attribute("href")
                        
                        if name and href:
                            businesses.append({
                                "name": name.replace("·", "").strip(),
                                "location": location,
                                "address": f"{location} area",
                                "link": href,
                                "phone": "",
                                "website": "",
                                "reviews": "",
                                "email": "",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            print(f"   ✅ {name}")
                            
                    except Exception as e:
                        print(f"   ❌ Error processing standard link {i}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Standard links failed: {e}")
        
        # Quick cleanup and return
        if driver:
            driver.quit()
            driver = None
        
        print(f"🎉 Lightweight scrape complete! Found {len(businesses)} businesses")
        return businesses
        
    except Exception as e:
        print(f"❌ Lightweight scraping error: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return []

@app.route('/')
def serve_frontend():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Memory-optimized API endpoint for Google Maps scraping"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        location = data.get('location', 'DA1')
        
        if not keywords or not keywords[0].strip():
            return jsonify({"error": "Keywords are required"}), 400
        
        if location not in POSTCODES:
            return jsonify({"error": "Invalid postcode"}), 400
        
        print(f"🚀 Starting LIGHTWEIGHT scraping for: {keywords} in {location}")
        
        all_results = []
        
        # Process only first 2 keywords to save memory
        for keyword in keywords[:2]:
            keyword = keyword.strip()
            if keyword:
                print(f"🔍 Processing keyword: {keyword}")
                results = scrape_google_maps_lightweight(keyword, location)
                all_results.extend(results)
                print(f"   Found {len(results)} results for {keyword}")
                
                # Longer delay between keywords to avoid memory buildup
                if len(keywords) > 1:
                    time.sleep(3)
        
        # Simple duplicate removal
        seen_names = set()
        unique_results = []
        for result in all_results:
            name_key = result['name'].lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_results.append(result)
        
        print(f"🎯 Final result: {len(unique_results)} unique businesses")
        
        return jsonify({
            "success": True,
            "data": unique_results,
            "count": len(unique_results),
            "message": f"Found {len(unique_results)} businesses from Google Maps (lightweight mode)"
        })
        
    except Exception as e:
        print(f"❌ API scraping error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-crm', methods=['POST'])
def api_upload_crm():
    """Upload data to Google Sheets CRM"""
    try:
        data = request.get_json()
        businesses = data.get('data', [])
        
        if not businesses:
            return jsonify({"error": "No data to upload"}), 400
        
        print(f"📊 Uploading {len(businesses)} businesses to CRM...")
        
        sheet_url = os.environ.get('GOOGLE_SHEET_URL')
        if not sheet_url:
            return jsonify({"error": "Google Sheet URL not configured"}), 500
        
        client = get_google_sheets_client()
        sheet = client.open_by_url(sheet_url).worksheet("CRM")
        
        existing_data = sheet.get_all_values()
        existing_links = [row[3] if len(row) > 3 else '' for row in existing_data[1:]] if len(existing_data) > 1 else []
        
        print(f"📋 Found {len(existing_links)} existing entries in CRM")
        
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
        
        for i, row in enumerate(new_businesses):
            sheet.append_row(row)
            print(f"   ✅ Added: {row[0]}")
            time.sleep(0.5)
        
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
    """Get CRM status"""
    try:
        print("📊 Checking CRM status...")
        
        sheet_url = os.environ.get('GOOGLE_SHEET_URL')
        if not sheet_url:
            return jsonify({"error": "Google Sheet URL not configured"}), 500
        
        client = get_google_sheets_client()
        sheet = client.open_by_url(sheet_url).worksheet("CRM")
        
        records = sheet.get_all_values()
        count = len(records) - 1 if len(records) > 1 else 0
        
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
        
        writer.writerow([
            "Business Name", "Location", "Address", "Link", 
            "Phone", "Website", "Reviews", "Email", "Scraped On"
        ])
        
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
        "version": "lightweight_v1.0",
        "features": ["lightweight_google_maps_scraping", "memory_optimized", "google_sheets_FIXED"],
        "environment": "production"
    })

if __name__ == '__main__':
    print("🏆 Welling United FC Lead Scraper - LIGHTWEIGHT VERSION")
    print("=" * 60)
    print("📍 Running on: Production Server")
    print("🪶 Lightweight Chrome: ACTIVE")
    print("💾 Memory optimized: ACTIVE")
    print("✅ Google Sheets: WORKING")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
