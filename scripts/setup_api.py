#!/usr/bin/env python3
"""
Interactive API Setup Helper
Helps you set up job board APIs quickly
"""

import json
import sys
import os

def load_config():
    """Load current config"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config.json: {e}")
        sys.exit(1)

def save_config(config):
    """Save config"""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Config saved successfully!")
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        sys.exit(1)

def setup_adzuna(config):
    """Set up Adzuna API"""
    print("\n" + "="*60)
    print("ADZUNA API SETUP")
    print("="*60)
    print("\n📋 Steps:")
    print("1. Go to: https://developer.adzuna.com/")
    print("2. Click 'Get Started' or 'Sign Up'")
    print("3. Create a free account")
    print("4. Once logged in, you'll see your API credentials:")
    print("   - Application ID (app_id)")
    print("   - Application Key (app_key)")
    print("\n💡 Free tier: 1,000 requests/month")
    print("\n" + "-"*60)
    
    app_id = input("\nEnter your Adzuna Application ID (or press Enter to skip): ").strip()
    if not app_id:
        print("⏭️  Skipping Adzuna setup")
        return config
    
    app_key = input("Enter your Adzuna Application Key: ").strip()
    if not app_key:
        print("❌ Application Key is required!")
        return config
    
    # Initialize APIs section if it doesn't exist
    if 'apis' not in config:
        config['apis'] = {}
    if 'adzuna' not in config['apis']:
        config['apis']['adzuna'] = {}
    
    config['apis']['adzuna']['enabled'] = True
    config['apis']['adzuna']['app_id'] = app_id
    config['apis']['adzuna']['app_key'] = app_key
    config['apis']['adzuna']['use_api_instead_of_scraping'] = True
    
    print("\n✅ Adzuna API configured!")
    
    # Test the API
    test = input("\nWould you like to test the API now? (y/n): ").strip().lower()
    if test == 'y':
        test_adzuna_api(app_id, app_key)
    
    return config

def test_adzuna_api(app_id, app_key):
    """Test Adzuna API connection"""
    print("\n🧪 Testing Adzuna API...")
    try:
        import requests
        
        url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 5,
            "what": "Python Developer",
            "content-type": "application/json"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "results" in data:
            job_count = len(data["results"])
            print(f"✅ API test successful! Found {job_count} test jobs.")
            if job_count > 0:
                print(f"   Sample job: {data['results'][0].get('title', 'N/A')}")
        else:
            print("⚠️  API responded but no jobs found in response")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        print("   Check your API credentials and internet connection")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

def setup_infojobs(config):
    """Set up Infojobs API"""
    print("\n" + "="*60)
    print("INFOJOBS API SETUP")
    print("="*60)
    print("\n📋 Steps:")
    print("1. Go to: https://developer.infojobs.net/")
    print("2. Register your application")
    print("3. Get your OAuth credentials:")
    print("   - Client ID")
    print("   - Client Secret")
    print("\n💡 Note: Requires OAuth 2.0 setup")
    print("\n" + "-"*60)
    
    client_id = input("\nEnter your Infojobs Client ID (or press Enter to skip): ").strip()
    if not client_id:
        print("⏭️  Skipping Infojobs setup")
        return config
    
    client_secret = input("Enter your Infojobs Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        return config
    
    if 'apis' not in config:
        config['apis'] = {}
    if 'infojobs' not in config['apis']:
        config['apis']['infojobs'] = {}
    
    config['apis']['infojobs']['enabled'] = True
    config['apis']['infojobs']['client_id'] = client_id
    config['apis']['infojobs']['client_secret'] = client_secret
    config['apis']['infojobs']['use_api_instead_of_scraping'] = True
    
    print("\n✅ Infojobs API configured!")
    return config

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("JOB BOARD API SETUP WIZARD")
    print("="*60)
    print("\nThis will help you configure APIs for job boards.")
    print("APIs are more reliable than web scraping!")
    print("\n" + "="*60)
    
    config = load_config()
    
    print("\nWhich API would you like to set up?")
    print("1. Adzuna (Recommended - Free, 1000 requests/month)")
    print("2. Infojobs (Spanish job board)")
    print("3. View current API settings")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        config = setup_adzuna(config)
        save_config(config)
    elif choice == '2':
        config = setup_infojobs(config)
        save_config(config)
    elif choice == '3':
        print("\n" + "="*60)
        print("CURRENT API SETTINGS")
        print("="*60)
        apis = config.get('apis', {})
        
        if not apis:
            print("\nNo APIs configured yet.")
        else:
            for api_name, api_config in apis.items():
                enabled = api_config.get('enabled', False)
                status = "✅ Enabled" if enabled else "❌ Disabled"
                print(f"\n{api_name.upper()}: {status}")
                if enabled:
                    # Don't show full keys, just indicate they're set
                    if 'app_id' in api_config or 'client_id' in api_config or 'api_key' in api_config:
                        print("   Credentials: ✅ Configured")
    elif choice == '4':
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\nYour APIs are now configured in config.json")
    print("The trawler will automatically use APIs when enabled.")

if __name__ == "__main__":
    main()

