#!/usr/bin/env python3
"""
Quick Adzuna API Setup - Automated
Opens browser and guides you through getting API key
"""

import json
import webbrowser
import sys
import time

def main():
    print("\n" + "="*60)
    print("🚀 QUICK ADZUNA API SETUP")
    print("="*60)
    print("\nI'll open the Adzuna developer site in your browser...")
    print("Then you just need to:")
    print("1. Sign up (free)")
    print("2. Copy your API credentials")
    print("3. Paste them here")
    print("\n" + "-"*60)
    
    input("\nPress Enter to open Adzuna Developer Portal...")
    
    # Open the signup page
    url = "https://developer.adzuna.com/"
    print(f"\n🌐 Opening {url}...")
    webbrowser.open(url)
    
    print("\n⏳ Waiting for you to sign up and get your API key...")
    print("   (You can minimize this window)")
    
    time.sleep(2)
    
    print("\n" + "="*60)
    print("📝 API CREDENTIALS")
    print("="*60)
    print("\nOnce you're logged in, you'll see:")
    print("  - Application ID (app_id)")
    print("  - Application Key (app_key)")
    print("\nCopy them here:")
    
    # Get credentials
    app_id = input("\n📋 Application ID: ").strip()
    if not app_id:
        print("\n❌ Setup cancelled - no Application ID provided")
        return
    
    app_key = input("🔑 Application Key: ").strip()
    if not app_key:
        print("\n❌ Setup cancelled - no Application Key provided")
        return
    
    # Load config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"\n❌ Error loading config: {e}")
        return
    
    # Update config
    if 'apis' not in config:
        config['apis'] = {}
    if 'adzuna' not in config['apis']:
        config['apis']['adzuna'] = {}
    
    config['apis']['adzuna']['enabled'] = True
    config['apis']['adzuna']['app_id'] = app_id
    config['apis']['adzuna']['app_key'] = app_key
    config['apis']['adzuna']['use_api_instead_of_scraping'] = True
    
    # Save config
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("\n✅ API credentials saved to config.json!")
    except Exception as e:
        print(f"\n❌ Error saving config: {e}")
        return
    
    # Test the API
    print("\n🧪 Testing API connection...")
    try:
        import requests
        
        url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 3,
            "what": "Python Developer",
            "content-type": "application/json"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "results" in data:
            job_count = len(data["results"])
            print(f"✅ SUCCESS! API is working! Found {job_count} test jobs.")
            if job_count > 0:
                print(f"   Sample: {data['results'][0].get('title', 'N/A')}")
            print("\n🎉 Adzuna API is now configured and working!")
            print("   The trawler will automatically use it instead of scraping.")
        else:
            print("⚠️  API responded but structure is unexpected")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API test failed: {e}")
        print("   But credentials are saved - you can test manually later")
    except ImportError:
        print("⚠️  Could not test API (requests library not available)")
        print("   But credentials are saved!")
    except Exception as e:
        print(f"⚠️  Error testing API: {e}")
        print("   But credentials are saved!")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\nYour Adzuna API is now configured!")
    print("Run the trawler and it will use the API automatically.")
    print("\n💡 Free tier: 1,000 requests/month")

if __name__ == "__main__":
    main()

