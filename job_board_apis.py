"""
Job Board API Integrations
Provides API-based access to job boards where available
Falls back to scraping when APIs are not configured or unavailable
"""

import requests
import time
from typing import List, Dict, Optional
from datetime import datetime


class JobBoardAPIs:
    """Handle API-based job board searches"""
    
    def __init__(self, config: dict = None):
        """
        Initialize with API credentials from config
        
        Config structure:
        {
            "apis": {
                "adzuna": {
                    "app_id": "your_app_id",
                    "app_key": "your_app_key",
                    "enabled": true
                },
                "infojobs": {
                    "client_id": "your_client_id",
                    "client_secret": "your_client_secret",
                    "enabled": false
                },
                "apijobs": {
                    "api_key": "your_api_key",
                    "enabled": false
                },
                "jsearch": {
                    "api_key": "your_api_key",
                    "enabled": false
                }
            }
        }
        """
        self.config = config or {}
        self.api_configs = self.config.get("apis", {})
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_adzuna_api(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """
        Search Adzuna using their official API
        Free tier: 1000 requests/month
        Docs: https://developer.adzuna.com/overview
        """
        jobs = []
        
        adzuna_config = self.api_configs.get("adzuna", {})
        if not adzuna_config.get("enabled", False):
            return jobs
        
        app_id = adzuna_config.get("app_id")
        app_key = adzuna_config.get("app_key")
        
        if not app_id or not app_key:
            return jobs
        
        try:
            # Adzuna API endpoint
            base_url = "https://api.adzuna.com/v1/api/jobs"
            
            # Determine country code from location
            country_codes = {
                "uk": "gb",
                "united kingdom": "gb",
                "london": "gb",
                "spain": "es",
                "madrid": "es",
                "france": "fr",
                "paris": "fr",
                "germany": "de",
                "berlin": "de",
                "netherlands": "nl",
                "amsterdam": "nl"
            }
            
            country = "gb"  # Default to UK
            location_lower = location.lower() if location else ""
            for key, code in country_codes.items():
                if key in location_lower:
                    country = code
                    break
            
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": min(max_results, 50),  # Max 50 per page
                "what": keywords,
                "where": location if location else None,
                "content-type": "application/json"
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Build URL with country code
            url = f"{base_url}/{country}/search/1"
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "results" in data:
                for result in data["results"][:max_results]:
                    job = {
                        "title": result.get("title", ""),
                        "company": result.get("company", {}).get("display_name", "Unknown"),
                        "location": result.get("location", {}).get("display_name", location),
                        "url": result.get("redirect_url", ""),
                        "description": result.get("description", "")[:500],  # Truncate description
                        "salary_min": result.get("salary_min"),
                        "salary_max": result.get("salary_max"),
                        "source": "adzuna",
                        "date_found": datetime.now().isoformat(),
                        "created": result.get("created", "")
                    }
                    jobs.append(job)
            
        except Exception as e:
            print(f"Adzuna API error: {e}", flush=True)
        
        return jobs
    
    def search_infojobs_api(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """
        Search Infojobs using their official API
        Requires OAuth 2.0 authentication
        Docs: https://developer.infojobs.net/
        """
        jobs = []
        
        infojobs_config = self.api_configs.get("infojobs", {})
        if not infojobs_config.get("enabled", False):
            return jobs
        
        client_id = infojobs_config.get("client_id")
        client_secret = infojobs_config.get("client_secret")
        
        if not client_id or not client_secret:
            return jobs
        
        try:
            # First, get OAuth token
            token_url = "https://www.infojobs.net/oauth/authorize"
            auth_url = "https://www.infojobs.net/api/oauth/user-authorize/access_token"
            
            # Basic auth for token
            import base64
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            token_response = self.session.post(
                auth_url,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "client_credentials"
                },
                timeout=10
            )
            
            if token_response.status_code != 200:
                print(f"Infojobs API auth failed: {token_response.status_code}", flush=True)
                return jobs
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return jobs
            
            # Now search for jobs
            search_url = "https://api.infojobs.net/api/9/offer"
            
            params = {
                "q": keywords,
                "province": location if location else None,
                "maxResults": min(max_results, 50)
            }
            
            params = {k: v for k, v in params.items() if v is not None}
            
            response = self.session.get(
                search_url,
                params=params,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "offers" in data:
                for offer in data["offers"][:max_results]:
                    job = {
                        "title": offer.get("title", ""),
                        "company": offer.get("profile", {}).get("name", "Unknown"),
                        "location": offer.get("city", location),
                        "url": offer.get("link", ""),
                        "description": offer.get("description", "")[:500],
                        "source": "infojobs",
                        "date_found": datetime.now().isoformat(),
                        "created": offer.get("published", "")
                    }
                    jobs.append(job)
                    
        except Exception as e:
            print(f"Infojobs API error: {e}", flush=True)
        
        return jobs
    
    def search_apijobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """
        Search using APIJobs aggregator API
        Covers 4000+ job boards including LinkedIn, Indeed, Glassdoor
        Requires API key from apijobs.dev
        """
        jobs = []
        
        apijobs_config = self.api_configs.get("apijobs", {})
        if not apijobs_config.get("enabled", False):
            return jobs
        
        api_key = apijobs_config.get("api_key")
        if not api_key:
            return jobs
        
        try:
            url = "https://api.apijobs.dev/v1/jobs"
            
            params = {
                "query": keywords,
                "location": location if location else None,
                "limit": max_results
            }
            
            params = {k: v for k, v in params.items() if v is not None}
            
            response = self.session.get(
                url,
                params=params,
                headers={
                    "X-API-Key": api_key,
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                for job_data in data["data"][:max_results]:
                    job = {
                        "title": job_data.get("title", ""),
                        "company": job_data.get("company", "Unknown"),
                        "location": job_data.get("location", location),
                        "url": job_data.get("url", ""),
                        "description": job_data.get("description", "")[:500],
                        "source": job_data.get("source", "apijobs"),
                        "date_found": datetime.now().isoformat(),
                        "created": job_data.get("posted_date", "")
                    }
                    jobs.append(job)
                    
        except Exception as e:
            print(f"APIJobs API error: {e}", flush=True)
        
        return jobs
    
    def search_jsearch(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """
        Search using JSearch API (Google for Jobs aggregator)
        Requires API key from openwebninja.com
        """
        jobs = []
        
        jsearch_config = self.api_configs.get("jsearch", {})
        if not jsearch_config.get("enabled", False):
            return jobs
        
        api_key = jsearch_config.get("api_key")
        if not api_key:
            return jobs
        
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            
            params = {
                "query": f"{keywords} {location}" if location else keywords,
                "page": "1",
                "num_pages": "1"
            }
            
            response = self.session.get(
                url,
                params=params,
                headers={
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                for job_data in data["data"][:max_results]:
                    job = {
                        "title": job_data.get("job_title", ""),
                        "company": job_data.get("employer_name", "Unknown"),
                        "location": job_data.get("job_city", location),
                        "url": job_data.get("job_apply_link", ""),
                        "description": job_data.get("job_description", "")[:500],
                        "source": "jsearch",
                        "date_found": datetime.now().isoformat(),
                        "created": job_data.get("job_posted_at_datetime_utc", "")
                    }
                    jobs.append(job)
                    
        except Exception as e:
            print(f"JSearch API error: {e}", flush=True)
        
        return jobs

