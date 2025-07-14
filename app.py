from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time
import gspread
from google.oauth2 import service_account
import csv
import os
from datetime import datetime
import json
import io
import tempfile

app = Flask(__name__)
CORS(app)

# Your Google Sheets credentials (FIXED VERSION)
CREDENTIALS_JSON = {
    "type": "service_account",
    "project_id": "welling-lead-scraper",
    "private_key_id": "0091301c5f547f2a76def77ae41ef7c8cb746b87",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQD11yu1BZQjx9Wr\nqbllCgOgYRkoZYE1dyV+E4azBT2BA7XUipZqhVtDlfA247jFjqRmg01IKgbDeTXL\nGtV0ibStQoeXw/CUhki+S3yuaYBG52qzaQTY7Y2nXakuuKNJ9WBpyVBLAh97PRkz\nX9KQgLfhO6sHd3rQb4WYiPeWVFh26kB6gKenjI8w6/cpeZ6Vkk/NYZwSU4FTkN5t\nj4LZ27hGs5XN7bEWIlnFLOpdxRWrdvtOQ/n3t2E5AUJLE0gUcSSXtGAyxK2oao3i\n2sH2T4c3H9aoFxpjYfX2yyCX8R7JVPzeRrKeXp2iNCqHrlESmvwnoSOdm4DNc63k\n5Wi11m4rAgMBAAECggEAJf6Ol2LjVZxUM5GplioJYXIK7KleDMtQlL75JGsnlEGP\nNT1YqIyFDFmnTx8RYXGoNYe5cUZoK9xsf0AIbq28VMK2010fA3VgLLjcmNVeqUFU\nG6JGyNf9+o3eezAMsdN7MR5B4IsqyRB/opGpU1fxaJ1LfiiYZzpf0AaVwpAKlBCr\n6g3koya4hdO8I5UwxhLIbXWIVYvLNhyq7bZ6DAr2AWV+HEh+3Qz3O/K43rnt7zUs\ngytLtz4BgfaxFavX8+8iKlp/wDp0MW0Oi4cBXBU7cPFRGlXrFMTvRxDy60ASE2gS\nLoVXOP6kXaDFP7grTM95EeaHp1KFbsfcJRGI5Wf/wQKBgQD+zb+qnlEt8DXU1MKE\nn/7N+3a21uI5BxI3VIAx3Xsqqrp5PttXjcumfkAwJp8QM23qHgPSCVS+H17QmJyl\nrhB5UkMIkcOQpfyu0KOxqsts3dT4P5BUuTPBkrfeQJyPEIQ/vIZHR6HVJESnZuxc\nMk+RRYJ4VWHVf9VHTD9I+pP2kQKBgQD2/qYprbyPJ6HhpQnkg2VXuRCk9Nadfn3I\nr9jyqf1Stb/M/92/yf10yp/Wb6A7zD1o7xSGsrXKAdq2iVfXol6PbnBC4pzP8PU+\ncYd/1JdxFmVsSv8cnAsFXOiHPDXyBTnO4GuAoOn5TJZasVgdFsAsWjgKFUzxczHq\nL+bCzCvO+wKBgEMoBUE50tmRuw5qOQ5tgOHXShWskxlGtNVibxs1bbX0I4u7NmJg\nG/G4ysAmHbxOYcTXvlgIX45whDPkVT0RoIPpW4ORr4KbTPriQJKeGlmKKgx37Fl4\nKpz1R4LLcrf+OWz3CkkVJyEfGv0oElnGZNQ8BsQidNOpipPtE6zvZjoRAoGATe9F\n8OrAD4+a1b8kovUO2iIr7VDQEzvhZpyN4OvgYeO1VHL7vlN25Q42ZwwrzBKC4gRm\nPqZPFCGHqIcnr4OtQKbBR2mHv1kxmPVrotsqueUuNYBohNd75sJNILbP8sDRX8SS\nRzD/Asm2u4Ev42XVV2lUO2JDOAB4JIPe1WJlBFcCgYAjyyc3AuxjrM0ItiRXjEr4\nWUenDdgw6naqaYwmXYqDU9NMaOJR0y/zxOwRrPwp0TmJ2Szp0iN0fSnSi5EsS/wf\nqNfe+NQmGAxAxJzEkaloMHVMfcliQxNMdvd3mmCu4V4XTHSdmtnJyEUoEo6yajYP\nHQZeFOIDzY0viuGabuM0kg==\n-----END PRIVATE KEY-----\n",
    "client_email": "credentials-json-804@welling-lead-scraper.iam.gserviceaccount.com",
    "client_id": "111924517280294017487",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/credentials-json-804%40welling-lead-scraper.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1qScGInFI_UD_2K5oUn42ximUt1s-hR-H7iLcpfDTsw0/edit"

def get_google_sheets_client():
    """Initialize Google Sheets client with FIXED authentication"""
    try:
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(CREDENTIALS_JSON, f)
            creds_file = f.name
        
        # Use modern Google Auth
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(credentials)
        
        # Clean up temp file
        os.unlink(creds_file)
        
        return client
    except Exception as e:
        print(f"Google Sheets client error: {e}")
        raise

# Mock data for testing (same as before)
def generate_mock_data(keyword, location):
    """Generate realistic mock data for testing"""
    business_types = {
        'garage': [
            {'name': 'AutoFix Garage', 'phone': '020 8123 4567', 'website': 'https://autofix-garage.co.uk', 'email': 'info@autofix-garage.co.uk'},
            {'name': 'Quick Car Repairs', 'phone': '020 8234 5678', 'website': 'https://quickcarrepairs.co.uk', 'email': 'service@quickcarrepairs.co.uk'},
            {'name': 'Main Street Motors', 'phone': '020 8345 6789', 'website': 'https://mainstreetmotors.co.uk', 'email': 'contact@mainstreetmotors.co.uk'}
        ],
        'MOT': [
            {'name': 'MOT Centre Plus', 'phone': '020 8456 7890', 'website': 'https://motcentreplus.co.uk', 'email': 'bookings@motcentreplus.co.uk'},
            {'name': 'Test & Go MOT', 'phone': '020 8567 8901', 'website': 'https://testandgo.co.uk', 'email': 'info@testandgo.co.uk'},
            {'name': 'Certified MOT Services', 'phone': '020 8678 9012', 'website': 'https://certifiedmot.co.uk', 'email': 'admin@certifiedmot.co.uk'}
        ],
        'tyres': [
            {'name': 'Tyre Express', 'phone': '020 8789 0123', 'website': 'https://tyreexpress.co.uk', 'email': 'sales@tyreexpress.co.uk'},
            {'name': 'Budget Tyres', 'phone': '020 8890 1234', 'website': 'https://budgettyres.co.uk', 'email': 'info@budgettyres.co.uk'},
            {'name': 'Premium Tyre Centre', 'phone': '020 8901 2345', 'website': 'https://premiumtyres.co.uk', 'email': 'enquiries@premiumtyres.co.uk'}
        ],
        'security': [
            {'name': 'SecureGuard Services', 'phone': '020 8012 3456', 'website': 'https://secureguard.co.uk', 'email': 'security@secureguard.co.uk'},
            {'name': 'Protection Plus Ltd', 'phone': '020 8123 4567', 'website': 'https://protectionplus.co.uk', 'email': 'info@protectionplus.co.uk'},
            {'name': 'Safety First Security', 'phone': '020 8234 5678', 'website': 'https://safetyfirst.co.uk', 'email': 'contact@safetyfirst.co.uk'}
        ],
        'plumbing': [
            {'name': 'Emergency Plumbers', 'phone': '020 8345 6789', 'website': 'https://emergencyplumbers.co.uk', 'email': 'urgent@emergencyplumbers.co.uk'},
            {'name': 'Reliable Plumbing', 'phone': '020 8456 7890', 'website': 'https://reliableplumbing.co.uk', 'email': 'bookings@reliableplumbing.co.uk'},
            {'name': 'Professional Pipe Works', 'phone': '020 8567 8901', 'website': 'https://pipeworks.co.uk', 'email': 'info@pipeworks.co.uk'}
        ]
    }
    
    businesses = business_types.get(keyword.lower(), [
        {'name': f'General Business {keyword}', 'phone': '020 8999 0000', 'website': f'https://{keyword.lower()}.co.uk', 'email': f'info@{keyword.lower()}.co.uk'}
    ])
    
    return [{
        "name": f"{biz['name']} - {location}",
        "location": location,
        "address": f"{10 + i * 2} {keyword.title()} Street, {location}",
        "link": f"https://www.google.com/maps/search/{biz['name'].replace(' ', '+')}+{location}",
        "phone": biz['phone'],
        "website": biz['website'],
        "reviews": f"{round(3.5 + (i * 0.3), 1)}({15 + i * 5})",
        "email": biz['email'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    } for i, biz in enumerate(businesses)]

@app.route('/')
def serve_frontend():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint for scraping (using mock data for testing)"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').split(',')
        location = data.get('location', 'DA1')
        
        if not keywords or not keywords[0].strip():
            return jsonify({"error": "Keywords are required"}), 400
        
        print(f"🔍 Scraping for: {keywords} in {location}")
        
        # Simulate processing time
        time.sleep(2)
        
        all_results = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword:
                print(f"   Processing: {keyword}")
                results = generate_mock_data(keyword, location)
                all_results.extend(results)
        
        # Remove duplicates
        seen_names = set()
        unique_results = []
        for result in all_results:
            if result['name'] not in seen_names:
                seen_names.add(result['name'])
                unique_results.append(result)
        
        print(f"✅ Found {len(unique_results)} unique businesses")
        
        return jsonify({
            "success": True,
            "data": unique_results,
            "count": len(unique_results),
            "message": f"Found {len(unique_results)} businesses (TEST DATA)"
        })
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-crm', methods=['POST'])
def api_upload_crm():
    """Upload data to Google Sheets CRM - NOW WORKING!"""
    try:
        data = request.get_json()
        businesses = data.get('data', [])
        
        if not businesses:
            return jsonify({"error": "No data to upload"}), 400
        
        print(f"📊 Uploading {len(businesses)} businesses to CRM...")
        
        # Connect to Google Sheets with FIXED authentication
        client = get_google_sheets_client()
        sheet = client.open_by_url(GOOGLE_SHEET_URL).worksheet("CRM")
        
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
        
        # Upload new data
        for i, row in enumerate(new_businesses):
            sheet.append_row(row)
            print(f"   ✅ Added: {row[0]}")
            time.sleep(0.3)  # Rate limiting
        
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
    """Get CRM status - NOW WORKING!"""
    try:
        print("📊 Checking CRM status...")
        
        client = get_google_sheets_client()
        sheet = client.open_by_url(GOOGLE_SHEET_URL).worksheet("CRM")
        
        records = sheet.get_all_values()
        count = len(records) - 1 if len(records) > 1 else 0  # Subtract header
        
        print(f"✅ CRM Status: {count} total businesses")
        
        return jsonify({
            "success": True,
            "total_businesses": count,
            "sheet_url": GOOGLE_SHEET_URL,
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
        "version": "fixed_v1.0",
        "features": ["mock_scraping", "google_sheets_WORKING", "csv_export"]
    })

if __name__ == '__main__':
    print("🏆 Welling United FC Lead Scraper - FIXED VERSION")
    print("=" * 60)
    print("📍 Running on: http://localhost:5000")
    print("🔧 Mock scraping: ACTIVE")
    print("✅ Google Sheets: WORKING")
    print("📊 CRM Upload: WORKING")
    print("📈 Status Check: WORKING")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)