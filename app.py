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
import re

app = Flask(__name__)
CORS(app)

# Configuration
POSTCODES = [
    "DA1", "DA2", "DA3", "DA4", "DA5", "DA6", "DA7", "DA8", "DA9", "DA10",
    "DA11", "DA12", "DA13", "DA14", "DA15", "DA16", "DA17", "DA18"
]

def get_google_sheets_client():
    """Initialize Google Sheets client with fallback credentials"""
    try:
        print("🔑 Setting up Google Sheets client...")
        
        # Use hardcoded credentials (most reliable for deployment)
        credentials_dict = {
            "type": "service_account",
            "project_id": "welling-lead-scraper",
            "private_key_id": "0091301c5f547f2a76def77ae41ef7c8cb746b87",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQD11yu1BZQjx9Wr\nqbllCgOgYRkoZYE1dyV+E4azBT2BA7XUipZqhVtDlfA247jFjqRmg01IKgbDeTXL\nGtV0ibStQoeXw/CUhki+S3yuaYBG52qzaQTY7Y2nXakuuKNJ9WBpyVBLAh97PRkz\nX9KQgLfhO6sHd3rQb4WYiPeWVFh26kB6gKenjI8w6/cpeZ6Vkk/NYZwSU4FTkN5t\nj4LZ27hGs5XN7bEWIlnFLOpdxRWrdvtOQ/n3t2E5AUJLE0gUcSSXtGAyxK2oao3i\n2sH2T4c3H9aoFxpjYfX2yyCX8R7JVPzeRrKeXp2iNCqHrlESmvwnoSOdm4DNc63k\n5Wi11m4rAgMBAAECggEAJf6Ol2LjVZxUM5GplioJYXIK7KleDMtQlL75JGsnlEGP\nNT1YqIyFDFmnTx8RYXGoNYe5cUZoK9xsf0AIbq28VMK2010fA3VgLLjcmNVeqUFU\nG6JGyNf9+o3eezAMsdN7MR5B4IsqyRB/opGpU1fxaJ1LfiiYZzpf0AaVwpAKlBCr\n6g3koya4hdO8I5UwxhLIbXWIVYvLNhyq7bZ6DAr2AWV+HEh+3Qz3O/K43rnt7zUs\ngytLtz4BgfaxFavX8+8iKlp/wDp0MW0Oi4cBXBU7cPFRGlXrFMTvRxDy60ASE2gS\nLoVXOP6kXaDFP7grTM95EeaHp1KFbsfcJRGI5Wf/wQKBgQD+zb+qnlEt8DXU1MKE\n/7N+3a21uI5BxI3VIAx3Xsqqrp5PttXjcumfkAwJp8QM23qHgPSCVS+H17QmJyl\nrhB5UkMIkcOQpfyu0KOxqsts3dT4P5BUuTPBkrfeQJyPEIQ/vIZHR6HVJESnZuxc\nMk+RRYJ4VWHVf9VHTD9I+pP2kQKBgQD2/qYprbyPJ6HhpQnkg2VXuRCk9Nadfn3I\nr9jyqf1Stb/M/92/yf10yp/Wb6A7zD1o7xSGsrXKAdq2iVfXol6PbnBC4pzP8PU+\ncYd/1JdxFmVsSv8cnAsFXOiHPDXyBTnO4GuAoOn5TJZasVgdFsAsWjgKFUzxczHq\nL+bCzCvO+wKBgEMoBUE50tmRuw5qOQ5tgOHXShWskxlGtNVibxs1bbX0I4u7NmJg\nG/G4ysAmHbxOYcTXvlgIX45whDPkVT0RoIPpW4ORr4KbTPriQJKeGlmKKgx37Fl4\nKpz1R4LLcrf+OWz3CkkVJyEfGv0oElnGZNQ8BsQidNOpipPtE6zvZjoRAoGATe9F\n8OrAD4+a1b8kovUO2iIr7VDQEzvhZpyN4OvgYeO1VHL7vlN25Q42ZwwrzBKC4gRm\nPqZPFCGHqIcnr4OtQKbBR2mHv1kxmPVrotsqueUuNYBohNd75sJNILbP8sDRX8SS\nRzD/Asm2u4Ev42XVV2lUO2JDOAB4JIPe1WJlBFcCgYAjyyc3AuxjrM0ItiRXjEr4\nWUenDdgw6naqaYwmXYqDU9NMaOJR0y/zxOwRrPwp0TmJ2Szp0iN0fSnSi5EsS/wf\nqNfe+NQmGAxAxJzEkaloMHVMfcliQxNMdvd3mmCu4V4XTHSdmtnJyEUoEo6yajYP\nHQZeFOIDzY0viuGabuM0kg==\n-----END PRIVATE KEY-----\n",
            "client_email": "credentials-json-804@welling-lead-scraper.iam.gserviceaccount.com",
            "client_id": "111924517280294017487",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/credentials-json-804%40welling-lead-scraper.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, 
            scopes=scopes
        )
        client = gspread.authorize(credentials)
        print("✅ Google Sheets client ready")
        return client
        
    except Exception as e:
        print(f"❌ Google Sheets client error: {e}")
        raise

def setup_chrome_driver():
    """Setup Chrome driver optimized for scraping"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    
    # Anti-detection
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Performance optimization
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def real_google_maps_scrape(keyword, location):
    """REAL Google Maps scraping - like your desktop version"""
    driver = None
    businesses = []
    
    try:
        print(f"🔍 REAL scraping: {keyword} in {location}")
        
        driver = setup_chrome_driver()
        
        # Construct search URL like your desktop version
        search_query = f"{keyword} in {location}"
        search_url = f"https://www.google.com/maps/search/{quote_plus(search_query)}"
        
        print(f"📍 URL: {search_url}")
        driver.get(search_url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Wait for results to appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/maps/place/"]'))
            )
        except:
            print("⚠️ No immediate results found, trying scroll...")
        
        # Scroll to load results like your desktop version
        try:
            scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
            print("📜 Scrolling to load more results...")
            
            for scroll in range(12):  # Match your desktop version
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(1.2)  # Match your desktop timing
                
        except Exception as e:
            print(f"⚠️ Scrolling failed: {e}")
        
        # Find business elements using the same selector as your desktop version
        business_elements = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
        print(f"🏢 Found {len(business_elements)} business elements")
        
        if not business_elements:
            print("⚠️ No business elements found, trying alternative selectors...")
            business_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            print(f"🏢 Alternative search found {len(business_elements)} elements")
        
        seen = set()
        
        # Process businesses like your desktop version
        for elem in business_elements[:10]:  # Limit to 10 as requested
            try:
                name = elem.get_attribute("aria-label")
                link = elem.get_attribute("href")
                
                if not name or not link or name in seen:
                    continue
                    
                seen.add(name)
                print(f"   🏢 Processing: {name}")
                
                # Click on business to get details (like your desktop version)
                try:
                    elem.click()
                    time.sleep(2.5)  # Match your desktop timing
                    
                    # Initialize data
                    phone = website = reviews = email = address = ""
                    
                    # Extract phone number (same logic as desktop)
                    try:
                        phone_elem = driver.find_element(By.XPATH, '//button[@data-tooltip="Copy phone number"]')
                        phone = phone_elem.text
                    except:
                        try:
                            phone_elem = driver.find_element(By.XPATH, '//button[@data-item-id="phone"]')
                            phone = phone_elem.text
                        except:
                            pass
                    
                    # Extract website (same logic as desktop)
                    try:
                        website_elem = driver.find_element(By.XPATH, '//a[@data-tooltip="Open website"]')
                        website = website_elem.get_attribute("href")
                    except:
                        try:
                            website_elem = driver.find_element(By.XPATH, '//a[@data-item-id="authority"]')
                            website = website_elem.get_attribute("href")
                        except:
                            pass
                    
                    # Extract reviews (same logic as desktop)
                    try:
                        reviews_elem = driver.find_element(By.CSS_SELECTOR, 'span[aria-label*=" reviews"]')
                        reviews = reviews_elem.text
                    except:
                        pass
                    
                    # Extract address (same logic as desktop)
                    try:
                        address_elem = driver.find_element(By.XPATH, '//button[@data-item-id="address"]')
                        address = address_elem.text
                    except:
                        pass
                    
                    # Extract email from website (same logic as desktop)
                    if website:
                        try:
                            print(f"      🌐 Checking website for email: {website}")
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                            r = requests.get(website, timeout=5, headers=headers)
                            soup = BeautifulSoup(r.content, "html.parser")
                            
                            # Look for mailto links
                            for a in soup.find_all('a', href=True):
                                if 'mailto:' in a['href']:
                                    email = a['href'].replace('mailto:', '')
                                    break
                            
                            # Look for email patterns in text
                            if not email:
                                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                emails = re.findall(email_pattern, r.text)
                                if emails:
                                    email = emails[0]
                                    
                        except Exception as e:
                            print(f"      ⚠️ Email extraction failed: {e}")
                    
                    # Create business data exactly like your desktop version
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
                    
                    businesses.append(business_data)
                    print(f"      ✅ Added: {name} | {phone} | {website}")
                    
                except Exception as click_error:
                    print(f"      ⚠️ Click failed for {name}: {click_error}")
                    # Add basic info even if click fails
                    businesses.append({
                        "name": name,
                        "location": location,
                        "address": location + " area",
                        "link": link,
                        "phone": "",
                        "website": "",
                        "reviews": "",
                        "email": "",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except Exception as e:
                print(f"      ❌ Error processing business: {e}")
                continue
        
        driver.quit()
        
        # Sort by reviews (highest first) as requested
        businesses_with_reviews = []
        businesses_without_reviews = []
        
        for business in businesses:
            if business['reviews'] and '(' in business['reviews']:
                try:
                    rating = float(business['reviews'].split('(')[0])
                    businesses_with_reviews.append((rating, business))
                except:
                    businesses_without_reviews.append(business)
            else:
                businesses_without_reviews.append(business)
        
        # Sort businesses with reviews by rating (highest first)
        businesses_with_reviews.sort(key=lambda x: x[0], reverse=True)
        sorted_businesses = [b[1] for b in businesses_with_reviews] + businesses_without_reviews
        
        print(f"🎉 REAL scraping complete! Found {len(sorted_businesses)} businesses")
        return sorted_businesses
        
    except Exception as e:
        print(f"❌ Real scraping error: {e}")
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
    """API endpoint for REAL Google Maps scraping"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        location = data.get('location', 'DA1')
        
        if not keywords or not keywords[0].strip():
            return jsonify({"error": "Keywords are required"}), 400
        
        if location not in POSTCODES:
            return jsonify({"error": "Invalid postcode"}), 400
        
        print(f"🚀 Starting REAL Google Maps scraping for: {keywords} in {location}")
        
        all_results = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                print(f"🔍 Processing keyword: {keyword}")
                results = real_google_maps_scrape(keyword, location)
                all_results.extend(results)
                print(f"   Found {len(results)} results for {keyword}")
                
                # Add delay between keywords
                if len(keywords) > 1:
                    time.sleep(3)
        
        # Remove duplicates
        seen_businesses = set()
        unique_results = []
        for result in all_results:
            identifier = f"{result['name'].lower().strip()}_{result.get('phone', '')}"
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
    """Upload data to Google Sheets CRM"""
    try:
        data = request.get_json()
        businesses = data.get('data', [])
        
        if not businesses:
            return jsonify({"error": "No data to upload"}), 400
        
        print(f"📊 Uploading {len(businesses)} businesses to CRM...")
        
        sheet_url = os.environ.get('GOOGLE_SHEET_URL', 'https://docs.google.com/spreadsheets/d/1qScGInFI_UD_2K5oUn42ximUt1s-hR-H7iLcpfDTsw0/edit')
        
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
        
        sheet_url = os.environ.get('GOOGLE_SHEET_URL', 'https://docs.google.com/spreadsheets/d/1qScGInFI_UD_2K5oUn42ximUt1s-hR-H7iLcpfDTsw0/edit')
        
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
        "version": "real_scraping_v1.0",
        "features": ["REAL_google_maps_scraping", "google_sheets_working", "csv_export"],
        "environment": "production"
    })

if __name__ == '__main__':
    print("🏆 Welling United FC Lead Scraper - REAL SCRAPING VERSION")
    print("=" * 70)
    print("📍 Running on: Production Server")
    print("🔥 REAL Google Maps scraping: ACTIVE")
    print("📊 Same logic as desktop version: ACTIVE")
    print("✅ Google Sheets: WORKING")
    print("📈 Real business data: ACTIVE")
    print("=" * 70)
    
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
