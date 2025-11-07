#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Trawler - Monitors job boards and alerts when relevant jobs match your CV
"""

import json
import time
import requests
from requests.exceptions import Timeout, RequestException
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
import sys
import io
from cv_parser import CVParser
from job_matcher import JobMatcher
from alert_system import AlertSystem

# Try to import Selenium for JavaScript-rendered sites
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. JavaScript-rendered sites will be skipped.")

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Try to import API module (optional)
try:
    from job_board_apis import JobBoardAPIs
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    JobBoardAPIs = None


class JobTrawler:
    def __init__(self, config_file: str = "config.json"):
        """Initialize the job trawler with configuration"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.cv_parser = CVParser(self.config.get('cv_path', 'cv.txt'))
        self.job_matcher = JobMatcher(
            self.cv_parser.get_skills(),
            self.cv_parser.get_keywords()
        )
        self.alert_system = AlertSystem(self.config.get('alerts', {}))
        self.seen_jobs = self._load_seen_jobs()
        self.driver = None  # Selenium WebDriver (initialized when needed)
        self.session = requests.Session()  # Use session for better cookie handling
        
        # Initialize API client if available
        if API_AVAILABLE and JobBoardAPIs:
            try:
                self.api_client = JobBoardAPIs(self.config)
            except Exception as e:
                print(f"Warning: Could not initialize API client: {e}", flush=True)
                self.api_client = None
        else:
            self.api_client = None
    
    def _load_seen_jobs(self) -> set:
        """Load previously seen job IDs to avoid duplicates"""
        try:
            with open('seen_jobs.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def _save_seen_jobs(self):
        """Save seen job IDs"""
        with open('seen_jobs.json', 'w') as f:
            json.dump(list(self.seen_jobs), f)
    
    def _extract_job_location(self, job: Dict) -> str:
        """Extract location from job posting"""
        # Try to get location from various fields
        location = job.get('location', '')
        if not location:
            # Try to extract from description
            desc = job.get('full_description', '') or job.get('snippet', '')
            # Look for common location patterns
            location_patterns = [
                r'location[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z]{2})?)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})',
                r'(remote|on[- ]site|hybrid)',
            ]
            for pattern in location_patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    location = match.group(0)
                    break
        return location.lower()
    
    def _is_european_location(self, location: str) -> bool:
        """Check if location is in European Union or UK"""
        if not location:
            return False
        
        location_lower = location.lower()
        
        # UK locations
        uk_indicators = [
            'uk', 'united kingdom', 'england', 'scotland', 'wales', 'northern ireland',
            'london', 'manchester', 'birmingham', 'edinburgh', 'glasgow', 'bristol',
            'leeds', 'liverpool', 'newcastle', 'sheffield', 'cardiff', 'belfast',
            'cambridge', 'oxford', 'brighton', 'york', 'nottingham', 'leicester'
        ]
        
        # EU countries and major cities
        eu_countries = [
            'austria', 'vienna', 'belgium', 'brussels', 'bulgaria', 'sofia',
            'croatia', 'zagreb', 'cyprus', 'nicosia', 'czech republic', 'prague',
            'denmark', 'copenhagen', 'estonia', 'tallinn', 'finland', 'helsinki',
            'france', 'paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes',
            'germany', 'berlin', 'munich', 'hamburg', 'frankfurt', 'cologne', 'stuttgart',
            'greece', 'athens', 'thessaloniki', 'hungary', 'budapest', 'ireland', 'dublin',
            'italy', 'rome', 'milan', 'naples', 'turin', 'palermo', 'genoa', 'bologna',
            'latvia', 'riga', 'lithuania', 'vilnius', 'luxembourg', 'malta', 'valletta',
            'netherlands', 'amsterdam', 'rotterdam', 'the hague', 'utrecht', 'eindhoven',
            'poland', 'warsaw', 'krakow', 'gdansk', 'wroclaw', 'portugal', 'lisbon', 'porto',
            'romania', 'bucharest', 'cluj', 'timisoara', 'slovakia', 'bratislava',
            'slovenia', 'ljubljana', 'spain', 'madrid', 'barcelona', 'valencia', 'seville',
            'zaragoza', 'malaga', 'sweden', 'stockholm', 'gothenburg', 'malmo'
        ]
        
        # Check for UK
        for indicator in uk_indicators:
            if indicator in location_lower:
                return True
        
        # Check for EU countries
        for country in eu_countries:
            if country in location_lower:
                return True
        
        # Check for European region indicators
        europe_indicators = ['europe', 'european', 'eu', 'e.u.', 'eea', 'schengen']
        for indicator in europe_indicators:
            if indicator in location_lower:
                return True
        
        # Check for country codes (UK, EU member states)
        eu_country_codes = [
            'at', 'be', 'bg', 'hr', 'cy', 'cz', 'dk', 'ee', 'fi', 'fr', 'de', 'gr',
            'hu', 'ie', 'it', 'lv', 'lt', 'lu', 'mt', 'nl', 'pl', 'pt', 'ro', 'sk',
            'si', 'es', 'se'
        ]
        # Extract potential country codes (2-letter codes)
        location_words = location_lower.split()
        for word in location_words:
            # Remove punctuation and check if it's a 2-letter code
            clean_word = word.strip('.,;:!?()[]{}')
            if len(clean_word) == 2 and clean_word in eu_country_codes:
                return True
            if clean_word == 'gb' or clean_word == 'uk':
                return True
        
        # Exclude non-European indicators
        non_european = [
            'usa', 'united states', 'us', 'u.s.', 'america', 'american',
            'canada', 'mexico', 'brazil', 'argentina', 'chile', 'colombia',
            'india', 'china', 'japan', 'south korea', 'singapore', 'hong kong',
            'australia', 'new zealand', 'south africa', 'nigeria', 'egypt',
            'uae', 'dubai', 'saudi arabia', 'israel', 'turkey', 'russia',
            'bangladesh', 'pakistan', 'philippines', 'indonesia', 'vietnam',
            'thailand', 'malaysia', 'taiwan', 'south africa'
        ]
        
        for indicator in non_european:
            if indicator in location_lower:
                return False
        
        # If location contains city names that are clearly European, allow it
        # But if we can't determine, default to False (exclude) to be safe
        return False
    
    def _location_matches(self, desired_location: str, job_location: str) -> bool:
        """Check if job location matches desired location"""
        desired_lower = desired_location.lower()
        job_lower = job_location.lower()
        
        # Check for remote
        if 'remote' in desired_lower or 'remote' in job_lower:
            return True
        
        # Extract city/state from desired location
        # Simple matching - check if key location words appear
        desired_parts = set(re.findall(r'\b\w+\b', desired_lower))
        job_parts = set(re.findall(r'\b\w+\b', job_lower))
        
        # Remove common words
        common_words = {'or', 'and', 'the', 'a', 'an', 'in', 'at', 'on', 'for'}
        desired_parts -= common_words
        job_parts -= common_words
        
        # If there's overlap in location terms, consider it a match
        if desired_parts and job_parts:
            overlap = desired_parts.intersection(job_parts)
            if len(overlap) > 0:
                return True
        
        return False
    
    def search_indeed(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Indeed for jobs - tries multiple methods:
        1. Indeed UK (indeed.co.uk)
        2. Indeed US (indeed.com)
        3. Alternative selectors
        4. Selenium fallback if available
        """
        jobs = []
        
        # Try Indeed UK first (better for UK/Europe searches)
        jobs = self._search_indeed_uk(keywords, location, max_results)
        
        # If UK didn't work, try US site
        if len(jobs) == 0:
            jobs = self._search_indeed_us(keywords, location, max_results)
        
        # If still no jobs, try UK again without location
        if len(jobs) == 0 and location:
            jobs = self._search_indeed_uk(keywords, "", max_results)
        
        # If still no jobs and Selenium is available, try with Selenium
        if len(jobs) == 0 and SELENIUM_AVAILABLE:
            jobs = self._search_indeed_selenium(keywords, location, max_results)
        
        return jobs
    
    def _search_indeed_uk(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Indeed UK (indeed.co.uk)"""
        jobs = []
        base_urls = [
            "https://www.indeed.co.uk/jobs",
            "https://uk.indeed.com/jobs"
        ]
        
        params = {
            'q': keywords,
            'sort': 'date'
        }
        if location:
            params['l'] = location
        
        for base_url in base_urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                }
                # First, visit homepage to get cookies
                self.session.get('https://www.indeed.co.uk', headers=headers, timeout=5)
                time.sleep(0.5)
                
                response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Debug: Check if page loaded correctly
                page_text = soup.get_text()
                if 'no jobs found' in page_text.lower() or 'no matching jobs' in page_text.lower():
                    print(f"Indeed returned 'no jobs' message", flush=True)
                
                # Try multiple selectors for Indeed UK - more comprehensive
                job_cards = []
                
                # Primary selectors (try all at once)
                job_cards.extend(soup.find_all('div', class_='job_seen_beacon'))
                job_cards.extend(soup.find_all('div', class_='jobsearch-SerpJobCard'))
                job_cards.extend(soup.find_all('div', class_='job_seen_beacon'))
                job_cards.extend(soup.find_all('div', {'data-jk': True}))
                job_cards.extend(soup.find_all('a', {'data-jk': True}))
                job_cards.extend(soup.find_all('div', id=lambda x: x and 'job_' in str(x)))
                
                # Additional selectors for newer Indeed structure
                job_cards.extend(soup.find_all('div', class_=lambda x: x and 'jobCard' in str(x)))
                job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job-card' in str(x)))
                job_cards.extend(soup.find_all('div', class_=lambda x: x and 'slider_container' in str(x)))
                job_cards.extend(soup.find_all('td', class_='resultContent'))
                job_cards.extend(soup.find_all('table', class_='jobCard'))
                job_cards.extend(soup.find_all('ul', class_='jobsearch-ResultsList'))
                
                # Try to find all list items in results
                results_list = soup.find('ul', class_='jobsearch-ResultsList')
                if results_list:
                    job_cards.extend(results_list.find_all('li'))
                
                # Look for job links directly - more aggressive
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    # More patterns for Indeed job links
                    if any(pattern in href for pattern in ['/viewjob', '/jobs/view', '/job/', '/rc/clk', '/pagead/clk']):
                        parent = link.find_parent(['div', 'td', 'article', 'li', 'tr'])
                        if parent and parent not in job_cards:
                            # Check if it looks like a job card - more lenient
                            if (parent.find(['h2', 'h3', 'h4']) or 
                                parent.get('data-jk') or 
                                link.get('data-jk') or
                                len(parent.get_text(strip=True)) > 50):
                                job_cards.append(parent)
                
                # Also try finding by any element with data-jk anywhere in the tree
                data_jk_elements = soup.find_all(attrs={'data-jk': True})
                for elem in data_jk_elements:
                    parent = elem.find_parent(['div', 'li', 'td', 'tr'])
                    if parent and parent not in job_cards:
                        job_cards.append(parent)
                
                # Deduplicate by data-jk attribute
                seen_jks = set()
                unique_cards = []
                for card in job_cards:
                    jk = card.get('data-jk') or (card.find('a', {'data-jk': True}) and card.find('a', {'data-jk': True}).get('data-jk'))
                    if jk and jk not in seen_jks:
                        seen_jks.add(jk)
                        unique_cards.append(card)
                    elif not jk:
                        unique_cards.append(card)
                
                for card in unique_cards[:max_results]:
                    try:
                        # Try multiple ways to find title - more comprehensive
                        title_elem = (
                            card.find('h2', class_='jobTitle') or
                            card.find('h2', class_=lambda x: x and ('title' in str(x).lower() or 'job' in str(x).lower())) or
                            card.find('h3', class_='jobTitle') or
                            card.find('h3', class_=lambda x: x and 'title' in str(x).lower()) or
                            card.find('a', class_=lambda x: x and 'title' in str(x).lower()) or
                            card.find('span', class_='jobTitle') or
                            card.find('span', class_=lambda x: x and 'title' in str(x).lower())
                        )
                        
                        # Try multiple ways to find company - more comprehensive
                        company_elem = (
                            card.find('span', class_='companyName') or
                            card.find('span', class_=lambda x: x and ('company' in str(x).lower() or 'name' in str(x).lower())) or
                            card.find('div', class_=lambda x: x and 'company' in str(x).lower()) or
                            card.find('a', class_=lambda x: x and 'company' in str(x).lower()) or
                            card.find('td', class_=lambda x: x and 'company' in str(x).lower())
                        )
                        
                        # Find link - more comprehensive
                        link_elem = None
                        if title_elem:
                            link_elem = title_elem.find('a') if title_elem else None
                        if not link_elem:
                            link_elem = card.find('a', href=True)
                        if not link_elem:
                            # Look for any link with job ID
                            link_elem = card.find('a', {'data-jk': True})
                        
                        # Only require title, company can be optional
                        if title_elem:
                            href = link_elem.get('href', '') if link_elem else ''
                            if href and not href.startswith('http'):
                                if href.startswith('/'):
                                    href = f"https://www.indeed.co.uk{href}"
                                else:
                                    href = f"https://www.indeed.co.uk/{href}"
                            
                            title_text = title_elem.get_text(strip=True)
                            if title_text and len(title_text) > 3:  # Valid title
                                job = {
                                    'title': title_text,
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'indeed',
                                    'date_found': datetime.now().isoformat()
                                }
                            
                            # Try to get description snippet
                            snippet = (
                                card.find('div', class_='job-snippet') or
                                card.find('div', class_='summary') or
                                card.find('span', class_='summary')
                            )
                            if snippet:
                                job['snippet'] = snippet.get_text(strip=True)
                            
                            # Try to get location
                            location_elem = card.find('div', class_='companyLocation') or card.find('span', class_='location')
                            if location_elem:
                                job['location'] = location_elem.get_text(strip=True)
                            
                            jobs.append(job)
                    except Exception as e:
                        continue
                
                if jobs:
                    print(f"Found {len(jobs)} jobs on Indeed UK", flush=True)
                    break
                    
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException as e:
                continue
            except Exception as e:
                continue
        
        return jobs
    
    def _search_indeed_us(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Indeed US (indeed.com) - fallback method with improved scraping"""
        jobs = []
        base_urls = [
            "https://www.indeed.com/jobs",
            "https://indeed.com/jobs"
        ]
        
        params = {
            'q': keywords,
            'sort': 'date'
        }
        if location:
            params['l'] = location
        
        for base_url in base_urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                }
                
                # First visit homepage to get cookies
                self.session.get('https://www.indeed.com', headers=headers, timeout=5)
                time.sleep(0.5)
                
                response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors - same comprehensive approach as UK
                job_cards = []
                job_cards.extend(soup.find_all('div', class_='job_seen_beacon'))
                job_cards.extend(soup.find_all('div', class_='jobsearch-SerpJobCard'))
                job_cards.extend(soup.find_all('div', {'data-jk': True}))
                job_cards.extend(soup.find_all('a', {'data-jk': True}))
                job_cards.extend(soup.find_all('div', id=lambda x: x and 'job_' in str(x)))
                job_cards.extend(soup.find_all('ul', class_='jobsearch-ResultsList'))
                
                results_list = soup.find('ul', class_='jobsearch-ResultsList')
                if results_list:
                    job_cards.extend(results_list.find_all('li'))
                
                # Look for job links
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if any(pattern in href for pattern in ['/viewjob', '/jobs/view', '/job/', '/rc/clk', '/pagead/clk']):
                        parent = link.find_parent(['div', 'td', 'article', 'li', 'tr'])
                        if parent and parent not in job_cards:
                            if (parent.find(['h2', 'h3', 'h4']) or parent.get('data-jk') or link.get('data-jk') or len(parent.get_text(strip=True)) > 50):
                                job_cards.append(parent)
                
                # Deduplicate by data-jk
                seen_jks = set()
                unique_cards = []
                for card in job_cards:
                    jk = card.get('data-jk') or (card.find('a', {'data-jk': True}) and card.find('a', {'data-jk': True}).get('data-jk'))
                    if jk and jk not in seen_jks:
                        seen_jks.add(jk)
                        unique_cards.append(card)
                    elif not jk:
                        unique_cards.append(card)
                
                for card in unique_cards[:max_results]:
                    try:
                        title_elem = (
                            card.find('h2', class_='jobTitle') or
                            card.find('h2', class_=lambda x: x and ('title' in str(x).lower() or 'job' in str(x).lower())) or
                            card.find('h3', class_='jobTitle') or
                            card.find('a', class_=lambda x: x and 'title' in str(x).lower())
                        )
                        company_elem = (
                            card.find('span', class_='companyName') or
                            card.find('span', class_=lambda x: x and ('company' in str(x).lower() or 'name' in str(x).lower())) or
                            card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                        )
                        link_elem = card.find('a', href=True) or card.find('a', {'data-jk': True})
                        
                        if title_elem:
                            href = link_elem.get('href', '') if link_elem else ''
                            if href and not href.startswith('http'):
                                href = f"https://www.indeed.com{href}" if href.startswith('/') else f"https://www.indeed.com/{href}"
                            
                            title_text = title_elem.get_text(strip=True)
                            if title_text and len(title_text) > 3:
                                job = {
                                    'title': title_text,
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'indeed',
                                    'date_found': datetime.now().isoformat()
                                }
                                
                                snippet = card.find('div', class_='job-snippet') or card.find('div', class_='summary')
                                if snippet:
                                    job['snippet'] = snippet.get_text(strip=True)
                                
                                jobs.append(job)
                    except Exception:
                        continue
                
                if jobs:
                    print(f"Found {len(jobs)} jobs on Indeed US", flush=True)
                    break
                    
            except Exception as e:
                print(f"Error searching Indeed US: {e}", flush=True)
                continue
        
        return jobs
    
    def _search_indeed_selenium(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Indeed using Selenium (for JavaScript-rendered content)"""
        jobs = []
        
        if not SELENIUM_AVAILABLE:
            return jobs
        
        driver = self._get_selenium_driver()
        if not driver:
            return jobs
        
        try:
            # Try UK site first
            url = "https://www.indeed.co.uk/jobs"
            params = {'q': keywords}
            if location:
                params['l'] = location
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"
            
            print(f"Trying Indeed UK with Selenium: {full_url}", flush=True)
            driver.get(full_url)
            
            # Wait for content
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk], .job_seen_beacon, .jobsearch-SerpJobCard"))
                )
            except TimeoutException:
                pass
            
            time.sleep(3)  # Let JavaScript render
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = (
                soup.find_all('div', class_='job_seen_beacon') or
                soup.find_all('div', class_='jobsearch-SerpJobCard') or
                soup.find_all('div', {'data-jk': True})
            )
            
            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find('h2', class_='jobTitle') or card.find('h2')
                    company_elem = card.find('span', class_='companyName')
                    link_elem = title_elem.find('a') if title_elem else card.find('a', href=True)
                    
                    if title_elem and company_elem:
                        href = link_elem.get('href', '') if link_elem else ''
                        if href and not href.startswith('http'):
                            href = f"https://www.indeed.co.uk{href}" if href.startswith('/') else f"https://www.indeed.co.uk/{href}"
                        
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'url': href,
                            'source': 'indeed',
                            'date_found': datetime.now().isoformat()
                        }
                        
                        snippet = card.find('div', class_='job-snippet')
                        if snippet:
                            job['snippet'] = snippet.get_text(strip=True)
                        
                        jobs.append(job)
                except Exception:
                    continue
            
            if jobs:
                print(f"Found {len(jobs)} jobs on Indeed using Selenium", flush=True)
                
        except Exception as e:
            print(f"Error searching Indeed with Selenium: {e}", flush=True)
        
        return jobs
    
    def search_linkedin(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search LinkedIn for jobs (note: requires authentication for full access)"""
        jobs = []
        # LinkedIn job search via public API or web scraping
        # Note: LinkedIn has strict rate limiting and may require authentication
        base_url = "https://www.linkedin.com/jobs/search"
        params = {
            'keywords': keywords,
            'location': location,
            'sortBy': 'R',
            'f_TPR': 'r86400'  # Last 24 hours
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='base-search-card')
            
            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    link_elem = card.find('a', class_='base-card__full-link')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'url': link_elem.get('href', '') if link_elem else '',
                            'source': 'linkedin',
                            'date_found': datetime.now().isoformat()
                        }
                        
                        # Try to get description snippet
                        snippet = card.find('p', class_='job-search-card__description')
                        if snippet:
                            job['snippet'] = snippet.get_text(strip=True)
                        
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing LinkedIn job card: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        
        return jobs
    
    def search_reed(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Reed.co.uk for jobs with improved scraping"""
        jobs = []
        
        # Try multiple URL patterns
        base_urls = [
            "https://www.reed.co.uk/jobs",
            "https://www.reed.co.uk/jobs/search"
        ]
        
        params_variations = [
            {'keywords': keywords, 'location': location if location else 'London', 'sortBy': 'Date'},
            {'q': keywords, 'l': location if location else 'London'},
            {'search': keywords, 'locationname': location if location else 'London'},
            {'keywords': keywords},  # Try without location
            {'q': keywords}  # Try without location
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.reed.co.uk/'
        }
        
        # First visit homepage to establish session
        try:
            self.session.get('https://www.reed.co.uk', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    # Use session for cookie persistence
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try comprehensive selectors for Reed
                    job_cards = []
                    
                    # Primary selectors (try all)
                    job_cards.extend(soup.find_all('article', class_='job-result'))
                    job_cards.extend(soup.find_all('article', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', class_='job-result'))
                    job_cards.extend(soup.find_all('div', class_='job-result-card'))
                    job_cards.extend(soup.find_all('div', {'data-jobid': True}))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('div', {'data-jobId': True}))
                    
                    # Look for job links directly
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if '/jobs/' in href and '/job/' in href:
                            parent = link.find_parent(['article', 'div', 'section'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                        elif '/jobs/' in href.lower() or ('/job/' in href.lower() and href.lower().count('/') >= 3):
                            parent = link.find_parent(['article', 'div', 'section'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    # Alternative selectors
                    if not job_cards or len(job_cards) < 3:
                        job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower() and 'result' in str(x).lower()))
                        job_cards.extend(soup.find_all('section', class_=lambda x: x and 'job' in str(x).lower()))
                        job_cards.extend(soup.find_all('li', class_=lambda x: x and 'job' in str(x).lower()))
                    
                    # Limit and deduplicate
                    seen_urls = set()
                    unique_cards = []
                    for card in job_cards[:max_results * 3]:
                        link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                        if link_elem:
                            url = link_elem.get('href', '')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                unique_cards.append(card)
                                if len(unique_cards) >= max_results:
                                    break
                    
                    for card in unique_cards:
                        try:
                            # Multiple ways to find title
                            title_elem = (
                                card.find('h2', class_='job-title') or
                                card.find('h2') or
                                card.find('h3', class_='job-title') or
                                card.find('a', class_='job-title') or
                                card.find('a', class_=lambda x: x and 'title' in str(x).lower()) or
                                (card if card.name in ['h2', 'h3'] else None)
                            )
                            
                            # Multiple ways to find company
                            company_elem = (
                                card.find('a', class_='gtmJobListingPostedBy') or
                                card.find('a', class_='gtmJobListingPostedByLink') or
                                card.find('span', class_='company') or
                                card.find('div', class_='company') or
                                card.find('a', class_=lambda x: x and 'company' in str(x).lower())
                            )
                            
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            
                            if title_elem and title_elem.get_text(strip=True):
                                title_text = title_elem.get_text(strip=True)
                                if len(title_text) > 3:  # Valid title
                                    href = link_elem.get('href', '') if link_elem else ''
                                    if not href.startswith('http'):
                                        href = f"https://www.reed.co.uk{href}" if href.startswith('/') else f"https://www.reed.co.uk/{href}"
                                    
                                    job = {
                                        'title': title_text,
                                        'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                        'url': href if href else f"https://www.reed.co.uk/jobs/search?keywords={keywords}",
                                        'source': 'reed',
                                        'date_found': datetime.now().isoformat()
                                    }
                                    
                                    # Try to get location
                                    location_elem = (
                                        card.find('li', class_='location') or
                                        card.find('span', class_='location') or
                                        card.find('div', class_='location') or
                                        card.find('p', class_='location')
                                    )
                                    if location_elem:
                                        job['location'] = location_elem.get_text(strip=True)
                                    
                                    # Try to get description snippet
                                    snippet = (
                                        card.find('p', class_='description') or
                                        card.find('div', class_='description') or
                                        card.find('p')
                                    )
                                    if snippet:
                                        job['snippet'] = snippet.get_text(strip=True)[:200]
                                    
                                    jobs.append(job)
                        except Exception as e:
                            print(f"Error parsing Reed job card: {e}", flush=True)
                            continue
                    
                    if len(jobs) > 0:
                        break  # Success, stop trying other variations
                        
                except requests.exceptions.Timeout:
                    print(f"Timeout searching Reed: {base_url}", flush=True)
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Request error searching Reed: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"Error searching Reed: {e}", flush=True)
                    continue
            
            if len(jobs) > 0:
                break
        
        return jobs
    
    def search_monster(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Monster.com for jobs - tries requests first, then Selenium if available"""
        jobs = []
        
        # Try requests-based scraping first with better headers to avoid 403
        base_urls = [
            "https://www.monster.com/jobs/search",
            "https://www.monster.co.uk/jobs/search"
        ]
        
        params_variations = [
            {'q': keywords, 'where': location if location else 'London, UK'},
            {'query': keywords, 'location': location if location else 'London'},
            {'keywords': keywords, 'loc': location if location else 'London'}
        ]
        
        # Rotate user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers_base = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/'
        }
        
        # First visit homepage to establish session
        try:
            self.session.get('https://www.monster.com', headers=headers_base, timeout=5)
            time.sleep(1)
        except:
            pass
        
        for base_url in base_urls:
            for i, params in enumerate(params_variations):
                try:
                    # Use rotating user agent
                    headers = headers_base.copy()
                    headers['User-Agent'] = user_agents[i % len(user_agents)]
                    
                    # Add delay to avoid rate limiting
                    if i > 0:
                        time.sleep(2)
                    
                    # Try visiting search page without params first
                    try:
                        self.session.get(base_url, headers=headers, timeout=5)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If 403, try with different approach
                    if response.status_code == 403:
                        print(f"Monster 403 for {base_url}, trying different headers", flush=True)
                        headers['Referer'] = 'https://www.monster.com/'
                        headers['Origin'] = 'https://www.monster.com'
                        headers['DNT'] = '1'
                        headers['Accept'] = '*/*'
                        response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If still 403, try without location parameter
                    if response.status_code == 403 and 'where' in params:
                        print(f"Monster 403, trying without location", flush=True)
                        params_no_loc = {k: v for k, v in params.items() if k != 'where' and k != 'location' and k != 'loc'}
                        response = self.session.get(base_url, params=params_no_loc, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If still 403, skip this variation
                    if response.status_code == 403:
                        print(f"Monster still blocked for {base_url}", flush=True)
                        continue
                    
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors
                    job_cards = []
                    job_cards.extend(soup.find_all('section', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and ('card' in str(x).lower() or 'job' in str(x).lower())))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and '/jobs/' in str(x).lower()))
                    
                    for card in job_cards[:max_results * 2]:
                        try:
                            title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=lambda x: x and 'title' in str(x).lower())
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                            company_elem = card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            
                            url = link_elem.get('href', '') if link_elem else ''
                            if not url.startswith('http'):
                                url = f"https://www.monster.com{url}" if url.startswith('/') else ''
                            
                            if title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': url,
                                    'source': 'monster',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        return jobs  # Success with requests, return
                        
                except Exception as e:
                    print(f"Requests method failed for Monster: {e}", flush=True)
                    continue
        
        # Fallback to Selenium if available and requests failed
        if SELENIUM_AVAILABLE and len(jobs) == 0:
            driver = self._get_selenium_driver()
            if driver:
                try:
                    url = "https://www.monster.com/jobs/search"
                    params = {'q': keywords, 'where': location if location else 'London, UK'}
                    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{url}?{query_string}"
                    
                    driver.get(full_url)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "section, .card-content, .job-tile"))
                        )
                    except TimeoutException:
                        pass
                    
                    time.sleep(3)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    job_cards = soup.find_all('section') or soup.find_all('div', class_=lambda x: x and 'card' in str(x).lower()) or []
                    
                    for card in job_cards[:max_results]:
                        try:
                            title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=lambda x: x and 'title' in str(x).lower())
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                            company_elem = card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': link_elem.get('href', '') if link_elem else '',
                                'source': 'monster',
                                'date_found': datetime.now().isoformat()
                            }
                            jobs.append(job)
                        except Exception:
                            continue
                except Exception as e:
                    print(f"Error searching Monster with Selenium: {e}", flush=True)
        
        return jobs
    
    # search_glassdoor method moved below with Selenium implementation
    
    def _get_selenium_driver(self):
        """Get or create Selenium WebDriver"""
        if self.driver is None and SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # Run in background
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(30)
            except Exception as e:
                print(f"Warning: Could not initialize Selenium: {e}")
                print("Install ChromeDriver or use: pip install webdriver-manager")
                return None
        return self.driver
    
    def search_totaljobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search TotalJobs for UK jobs - tries requests first, then Selenium if available"""
        jobs = []
        
        # Try requests-based scraping first
        base_urls = [
            f"https://www.totaljobs.com/jobs/{keywords.replace(' ', '-')}",
            "https://www.totaljobs.com/jobs/search"
        ]
        
        params_variations = [
            {} if location else {},
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords, 'l': location} if location else {'q': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.totaljobs.com/'
        }
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    if location and '/jobs/' in base_url and not base_url.endswith('/search'):
                        url = f"{base_url}/in-{location.replace(', ', '-').replace(' ', '-').lower()}"
                        response = self.session.get(url, headers=headers, timeout=(5, 15), allow_redirects=True)
                    else:
                        response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors
                    job_cards = []
                    job_cards.extend(soup.find_all('article'))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and '/job/' in str(x).lower()))
                    
                    for card in job_cards[:max_results * 2]:
                        try:
                            title_elem = (
                                card.find('h2') or
                                card.find('h3') or
                                card.find('a', class_=lambda x: x and 'title' in str(x).lower()) or
                                card.find('a', href=lambda x: x and '/job/' in str(x))
                            )
                            
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                            company_elem = (
                                card.find('span', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            )
                            
                            url = link_elem.get('href', '') if link_elem else ''
                            if url and not url.startswith('http'):
                                url = f"https://www.totaljobs.com{url}" if url.startswith('/') else ''
                            
                            if title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': url,
                                    'source': 'totaljobs',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        return jobs  # Success with requests, return
                        
                except Exception as e:
                    print(f"Requests method failed for TotalJobs: {e}", flush=True)
                    continue
        
        # Fallback to Selenium if available and requests failed
        if SELENIUM_AVAILABLE and len(jobs) == 0:
            driver = self._get_selenium_driver()
            if driver:
                try:
                    url = f"https://www.totaljobs.com/jobs/{keywords.replace(' ', '-')}"
                    if location:
                        url += f"/in-{location.replace(', ', '-').replace(' ', '-').lower()}"
                    
                    driver.get(url)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "article, [data-job-id], .job-item, .job-card"))
                        )
                    except TimeoutException:
                        pass
                    
                    time.sleep(3)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    job_cards = soup.find_all('article') or soup.find_all('div', {'data-job-id': True}) or soup.find_all('div', class_=lambda x: x and 'job' in x.lower()) or []
                    
                    for card in job_cards[:max_results]:
                        try:
                            title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=lambda x: x and 'title' in str(x).lower())
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True)
                            if not link_elem:
                                link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a', href=True)
                            
                            company_elem = card.find('span', class_=lambda x: x and 'company' in str(x).lower()) or card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': f"https://www.totaljobs.com{link_elem.get('href', '')}" if link_elem and link_elem.get('href', '').startswith('/') else (link_elem.get('href', '') if link_elem else ''),
                                'source': 'totaljobs',
                                'date_found': datetime.now().isoformat()
                            }
                            jobs.append(job)
                        except Exception:
                            continue
                except Exception as e:
                    print(f"Error searching TotalJobs with Selenium: {e}", flush=True)
        
        return jobs
    
    def search_glassdoor(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Glassdoor for jobs - tries requests first, then Selenium if available"""
        jobs = []
        
        # Try requests-based scraping first
        base_urls = [
            "https://www.glassdoor.co.uk/Job/jobs.htm",
            "https://www.glassdoor.com/Job/jobs.htm"
        ]
        
        params_variations = [
            {'sc.keyword': keywords},
            {'keywords': keywords},
            {'q': keywords}
        ]
        
        # Rotate user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers_base = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/'
        }
        
        # First visit homepage to establish session
        try:
            self.session.get('https://www.glassdoor.co.uk', headers=headers_base, timeout=5)
            time.sleep(1)
        except:
            pass
        
        for base_url in base_urls:
            for i, params in enumerate(params_variations):
                try:
                    # Use rotating user agent
                    headers = headers_base.copy()
                    headers['User-Agent'] = user_agents[i % len(user_agents)]
                    
                    # Add delay to avoid rate limiting
                    if i > 0:
                        time.sleep(2)
                    
                    # Try visiting search page without params first
                    try:
                        self.session.get(base_url, headers=headers, timeout=5)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If 403, try with different approach
                    if response.status_code == 403:
                        print(f"Glassdoor 403 for {base_url}, trying different headers", flush=True)
                        headers['Referer'] = 'https://www.glassdoor.co.uk/'
                        headers['Origin'] = 'https://www.glassdoor.co.uk'
                        headers['DNT'] = '1'
                        headers['Accept'] = '*/*'
                        response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If still 403, try with just keyword, no location
                    if response.status_code == 403:
                        print(f"Glassdoor 403, trying simpler params", flush=True)
                        simple_params = {'sc.keyword': keywords}
                        response = self.session.get(base_url, params=simple_params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    
                    # If still 403, skip this variation
                    if response.status_code == 403:
                        print(f"Glassdoor still blocked for {base_url}", flush=True)
                        continue
                    
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors
                    job_cards = []
                    job_cards.extend(soup.find_all('li', {'data-test': 'job-listing'}))
                    job_cards.extend(soup.find_all('li', class_='react-job-listing'))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and '/Job/job.htm' in str(x)))
                    
                    for card in job_cards[:max_results * 2]:
                        try:
                            title_elem = card.find('a', class_='jobLink') or card.find('h2') or card.find('a', href=lambda x: x and '/Job/' in str(x))
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                            company_elem = card.find('span', class_='employerName') or card.find('div', class_='d-flex') or card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            
                            url = link_elem.get('href', '') if link_elem else ''
                            if url and not url.startswith('http'):
                                url = f"https://www.glassdoor.co.uk{url}" if url.startswith('/') else ''
                            
                            if title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': url,
                                    'source': 'glassdoor',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        return jobs  # Success with requests, return
                        
                except Exception as e:
                    print(f"Requests method failed for Glassdoor: {e}", flush=True)
                    continue
        
        # Fallback to Selenium if available and requests failed
        if SELENIUM_AVAILABLE and len(jobs) == 0:
            driver = self._get_selenium_driver()
            if driver:
                try:
                    url = "https://www.glassdoor.co.uk/Job/jobs.htm"
                    params = {'sc.keyword': keywords}
                    if 'london' in location.lower():
                        params['locId'] = '2670680'
                        params['locT'] = 'C'
                    
                    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{url}?{query_string}"
                    
                    driver.get(full_url)
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-test='job-listing'], .react-job-listing"))
                        )
                    except TimeoutException:
                        pass
                    
                    time.sleep(3)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    job_cards = soup.find_all('li', {'data-test': 'job-listing'}) or soup.find_all('li', class_='react-job-listing')
                    
                    for card in job_cards[:max_results]:
                        try:
                            title_elem = card.find('a', class_='jobLink') or card.find('h2')
                            if not title_elem:
                                continue
                            
                            link_elem = card.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                            company_elem = card.find('span', class_='employerName') or card.find('div', class_='d-flex')
                            
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': f"https://www.glassdoor.co.uk{link_elem.get('href', '')}" if link_elem and link_elem.get('href', '').startswith('/') else (link_elem.get('href', '') if link_elem else ''),
                                'source': 'glassdoor',
                                'date_found': datetime.now().isoformat()
                            }
                            jobs.append(job)
                        except Exception:
                            continue
                except Exception as e:
                    print(f"Error searching Glassdoor with Selenium: {e}", flush=True)
        
        return jobs
    
    def __del__(self):
        """Clean up Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def get_job_details(self, job: Dict) -> Dict:
        """Fetch full job description for better matching"""
        if not job.get('url'):
            return job
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            # Use shorter timeout to prevent hanging
            response = requests.get(job['url'], headers=headers, timeout=(5, 10), allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract full description (varies by site)
            if job['source'] == 'indeed':
                desc_elem = soup.find('div', id='jobDescriptionText')
            elif job['source'] == 'linkedin':
                desc_elem = soup.find('div', class_='show-more-less-html__markup')
            else:
                desc_elem = soup.find('div', class_='description')
            
            if desc_elem:
                job['full_description'] = desc_elem.get_text(strip=True)
            
        except requests.exceptions.Timeout:
            print(f"Timeout fetching job details for {job.get('title', 'unknown')}, skipping...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching job details for {job.get('title', 'unknown')}: {e}", flush=True)
        except Exception as e:
            print(f"Error fetching job details for {job.get('title', 'unknown')}: {e}", flush=True)
        
        return job
    
    def search_cvlibrary(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search CV-Library for UK jobs
        
        Note: CV-Library blocks scraping (403 Forbidden). 
        This board is disabled by default - consider using their API instead.
        """
        jobs = []
        # CV-Library blocks scraping attempts - return empty to avoid errors
        print("CV-Library blocks scraping (403). Consider using their API or disabling this board.", flush=True)
        return jobs
        
        # Old implementation kept for reference but won't execute
        base_url = "https://www.cv-library.co.uk/jobs"
        
        params = {'q': keywords}
        if location:
            params['location'] = location
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.cv-library.co.uk/'
            }
            response = requests.get(base_url, params=params, headers=headers, timeout=(5, 10), allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors - CV-Library structure may vary
            job_cards = (
                soup.find_all('article', class_='job') or
                soup.find_all('div', class_='job') or
                soup.find_all('div', {'data-job-id': True}) or
                soup.find_all('div', {'data-jobid': True}) or
                soup.find_all('a', href=lambda x: x and ('/job/' in str(x) or '/jobs/' in str(x))) or
                soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower() and 'result' in str(x).lower())
            )
            
            seen_urls = set()
            for card in job_cards[:max_results * 3]:  # Try more cards
                try:
                    link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    if not url.startswith('http'):
                        url = f"https://www.cv-library.co.uk{url}"
                    
                    title_elem = card.find('h2') or card.find('h3') or card.find('h4') or link_elem
                    company_elem = (
                        card.find('a', class_=lambda x: x and 'company' in str(x).lower()) or
                        card.find('span', class_=lambda x: x and 'company' in str(x).lower())
                    )
                    
                    if title_elem and title_elem.get_text(strip=True):
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                            'url': url,
                            'source': 'cvlibrary',
                            'date_found': datetime.now().isoformat()
                        }
                        jobs.append(job)
                        if len(jobs) >= max_results:
                            break
                except Exception:
                    continue
                    
            if len(jobs) == 0:
                print(f"Warning: CV-Library returned page but no jobs found. May need different selectors or JavaScript rendering.", flush=True)
                
        except requests.exceptions.Timeout:
            print(f"Timeout searching CV-Library", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"Request error searching CV-Library: {e}", flush=True)
        except Exception as e:
            print(f"Error searching CV-Library: {e}", flush=True)
        
        return jobs
    
    def search_adzuna(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Adzuna for UK/Europe jobs - tries API first, falls back to scraping"""
        jobs = []
        
        # Try API first if enabled
        if self.api_client:
            api_config = self.config.get('apis', {}).get('adzuna', {})
            if api_config.get('enabled', False) and api_config.get('use_api_instead_of_scraping', False):
                try:
                    api_jobs = self.api_client.search_adzuna_api(keywords, location, max_results)
                    if api_jobs:
                        print(f"Found {len(api_jobs)} jobs via Adzuna API", flush=True)
                        return api_jobs
                except Exception as e:
                    print(f"Adzuna API failed, falling back to scraping: {e}", flush=True)
        
        # Fall back to scraping
        # Try multiple URL patterns
        base_urls = [
            "https://www.adzuna.co.uk/jobs/search",
            "https://www.adzuna.co.uk/search",
            "https://www.adzuna.co.uk/jobs"
        ]
        
        params_variations = [
            {'q': keywords, 'where': location} if location else {'q': keywords},
            {'search': keywords, 'location': location} if location else {'search': keywords},
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.adzuna.co.uk/'
        }
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Adzuna uses various structures - try comprehensive approaches
                    job_cards = []
                    
                    # Primary selectors
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and ('job' in str(x).lower() and 'result' in str(x).lower())))
                    job_cards.extend(soup.find_all('article', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', {'data-id': True}))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    
                    # Look for job links directly
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if any(pattern in href for pattern in ['/jobs/details/', '/jobs/job/', '/job/', '/ad/']):
                            # Check if parent looks like a job card
                            parent = link.find_parent(['div', 'article', 'section'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    # Also try title-based selection
                    title_elems = soup.find_all(['h2', 'h3', 'h4'], class_=lambda x: x and 'title' in str(x).lower())
                    for title in title_elems:
                        parent = title.find_parent(['div', 'article', 'section'])
                        if parent and parent not in job_cards:
                            job_cards.append(parent)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 3]:
                        try:
                            # Find link
                            link_elem = None
                            if card.name == 'a' and card.get('href'):
                                link_elem = card
                            else:
                                link_elem = card.find('a', href=True)
                            
                            if not link_elem:
                                continue
                            
                            url = link_elem.get('href', '')
                            if not url or url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            if not url.startswith('http'):
                                url = f"https://www.adzuna.co.uk{url}" if url.startswith('/') else f"https://www.adzuna.co.uk/{url}"
                            
                            # Find title - try multiple approaches
                            title_elem = None
                            if card.name in ['h2', 'h3', 'h4']:
                                title_elem = card
                            else:
                                title_elem = (
                                    card.find('h2', class_=lambda x: x and 'title' in str(x).lower()) or
                                    card.find('h3', class_=lambda x: x and 'title' in str(x).lower()) or
                                    card.find('h2') or
                                    card.find('h3') or
                                    card.find('h4') or
                                    card.find('a', class_=lambda x: x and 'title' in str(x).lower()) or
                                    link_elem
                                )
                            
                            # Find company
                            company_elem = (
                                card.find('span', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('div', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('a', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('p', class_=lambda x: x and 'company' in str(x).lower())
                            )
                            
                            if title_elem:
                                title_text = title_elem.get_text(strip=True)
                                if title_text and len(title_text) > 3:  # Valid title
                                    job = {
                                        'title': title_text,
                                        'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                        'url': url,
                                        'source': 'adzuna',
                                        'date_found': datetime.now().isoformat()
                                    }
                                    
                                    # Try to get location
                                    location_elem = card.find(['span', 'div'], class_=lambda x: x and 'location' in str(x).lower())
                                    if location_elem:
                                        job['location'] = location_elem.get_text(strip=True)
                                    
                                    jobs.append(job)
                                    if len(jobs) >= max_results:
                                        break
                        except Exception as e:
                            print(f"Error parsing Adzuna card: {e}", flush=True)
                            continue
                    
                    if len(jobs) > 0:
                        break  # Success, stop trying other variations
                        
                except requests.exceptions.Timeout:
                    print(f"Timeout searching Adzuna: {base_url}", flush=True)
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Request error searching Adzuna: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"Error searching Adzuna: {e}", flush=True)
                    continue
            
            if len(jobs) > 0:
                break
        
        return jobs
    
    def search_jobserve(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search JobServe for UK/Europe jobs with improved scraping"""
        jobs = []
        
        # Try multiple URL patterns
        base_urls = [
            "https://www.jobserve.com/gb/en/JobSearch.aspx",
            "https://www.jobserve.com/gb/en/jobsearch",
            "https://www.jobserve.com/jobs/search"
        ]
        
        params_variations = [
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords, 'l': location} if location else {'q': keywords},
            {'search': keywords, 'loc': location} if location else {'search': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.jobserve.com/'
        }
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try comprehensive selectors for JobServe
                    job_cards = []
                    
                    # Primary selectors
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('tr', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('tr', {'data-job-id': True}))
                    
                    # Look for job links
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if any(pattern in href.lower() for pattern in ['/job/', '/jobdetail/', '/jobdetails/', '/jobdetail.aspx']):
                            parent = link.find_parent(['div', 'tr', 'td', 'article'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    # Also try table rows
                    table_rows = soup.find_all('tr')
                    for row in table_rows:
                        if row.find('a', href=lambda x: x and '/job/' in str(x).lower()):
                            if row not in job_cards:
                                job_cards.append(row)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 3]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            url = link_elem.get('href', '')
                            if not url or url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            if not url.startswith('http'):
                                url = f"https://www.jobserve.com{url}" if url.startswith('/') else f"https://www.jobserve.com/{url}"
                            
                            # Find title - multiple approaches
                            title_elem = (
                                card.find('h2') or
                                card.find('h3') or
                                card.find('h4') or
                                card.find('td', class_=lambda x: x and 'title' in str(x).lower()) or
                                card.find('td', class_=lambda x: x and 'job' in str(x).lower() and 'title' in str(x).lower()) or
                                link_elem
                            )
                            
                            # Find company
                            company_elem = (
                                card.find('td', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('span', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('div', class_=lambda x: x and 'company' in str(x).lower())
                            )
                            
                            if title_elem and title_elem.get_text(strip=True):
                                title_text = title_elem.get_text(strip=True)
                                if len(title_text) > 3:  # Valid title
                                    job = {
                                        'title': title_text,
                                        'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                        'url': url,
                                        'source': 'jobserve',
                                        'date_found': datetime.now().isoformat()
                                    }
                                    
                                    # Try to get location
                                    location_elem = card.find('td', class_=lambda x: x and 'location' in str(x).lower())
                                    if location_elem:
                                        job['location'] = location_elem.get_text(strip=True)
                                    
                                    jobs.append(job)
                                    if len(jobs) >= max_results:
                                        break
                        except Exception as e:
                            print(f"Error parsing JobServe card: {e}", flush=True)
                            continue
                    
                    if len(jobs) > 0:
                        break  # Success, stop trying other variations
                        
                except requests.exceptions.Timeout:
                    print(f"Timeout searching JobServe: {base_url}", flush=True)
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Request error searching JobServe: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"Error searching JobServe: {e}", flush=True)
                    continue
            
            if len(jobs) > 0:
                break
        
        return jobs
    
    def search_whatjobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search WhatJobs for UK/Europe jobs with improved scraping"""
        jobs = []
        
        # Try multiple URL patterns
        base_urls = [
            "https://uk.whatjobs.com/jobs",
            "https://uk.whatjobs.com/search",
            "https://www.whatjobs.com/jobs"
        ]
        
        params_variations = [
            {'q': keywords, 'l': location} if location else {'q': keywords},
            {'search': keywords, 'location': location} if location else {'search': keywords},
            {'keywords': keywords, 'loc': location} if location else {'keywords': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://uk.whatjobs.com/'
        }
        
        # First visit homepage to establish session
        try:
            self.session.get('https://uk.whatjobs.com', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try comprehensive selectors for WhatJobs - more aggressive
                    job_cards = []
                    
                    # Primary selectors (try all)
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower() and 'result' in str(x).lower()))
                    job_cards.extend(soup.find_all('article', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('div', {'data-jobId': True}))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'result' in str(x).lower()))
                    job_cards.extend(soup.find_all('li', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'listing' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'item' in str(x).lower()))
                    
                    # Look for job links - very comprehensive
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if any(pattern in href.lower() for pattern in ['/job/', '/jobs/', '/search/job/', '/vacancy/', '/position/']):
                            parent = link.find_parent(['div', 'article', 'section', 'li', 'tr', 'td'])
                            if parent and parent not in job_cards:
                                # More lenient check - any parent with substantial text
                                text = parent.get_text(strip=True)
                                if (parent.find(['h2', 'h3', 'h4', 'h5']) or 
                                    len(text) > 30 or 
                                    any(word in text.lower() for word in ['developer', 'engineer', 'manager', 'analyst', 'salary', 'location'])):
                                    job_cards.append(parent)
                    
                    # Also try by title elements - more aggressive
                    title_elems = soup.find_all(['h2', 'h3', 'h4', 'h5'], class_=lambda x: x and 'title' in str(x).lower())
                    for title in title_elems:
                        parent = title.find_parent(['div', 'article', 'section', 'li'])
                        if parent and parent not in job_cards:
                            job_cards.append(parent)
                    
                    # Try finding by any heading with job-like text or keywords
                    all_headings = soup.find_all(['h2', 'h3', 'h4', 'h5'])
                    for heading in all_headings:
                        text = heading.get_text(strip=True).lower()
                        if (len(text) > 5 and len(text) < 100 and 
                            any(keyword in text for keyword in ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'consultant', 'director', 'lead', 'senior', 'junior'])):
                            parent = heading.find_parent(['div', 'article', 'section', 'li'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    # Also try finding any div/article with job-related content
                    all_divs = soup.find_all(['div', 'article', 'section'])
                    for div in all_divs:
                        text = div.get_text(strip=True).lower()
                        classes = ' '.join(div.get('class', []))
                        if (any(keyword in text[:200] for keyword in ['python', 'developer', 'engineer', 'salary', 'location', 'job']) and
                            len(text) > 50 and len(text) < 2000):
                            if div not in job_cards:
                                job_cards.append(div)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 3]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            url = link_elem.get('href', '')
                            if not url or url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            if not url.startswith('http'):
                                url = f"https://uk.whatjobs.com{url}" if url.startswith('/') else f"https://uk.whatjobs.com/{url}"
                            
                            # Find title - multiple approaches
                            title_elem = (
                                card.find('h2', class_=lambda x: x and 'title' in str(x).lower()) or
                                card.find('h3', class_=lambda x: x and 'title' in str(x).lower()) or
                                card.find('h2') or
                                card.find('h3') or
                                card.find('h4') or
                                link_elem
                            )
                            
                            # Find company
                            company_elem = (
                                card.find('span', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('div', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('p', class_=lambda x: x and 'company' in str(x).lower()) or
                                card.find('a', class_=lambda x: x and 'company' in str(x).lower())
                            )
                            
                            if title_elem and title_elem.get_text(strip=True):
                                title_text = title_elem.get_text(strip=True)
                                if len(title_text) > 3:  # Valid title
                                    job = {
                                        'title': title_text,
                                        'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                        'url': url,
                                        'source': 'whatjobs',
                                        'date_found': datetime.now().isoformat()
                                    }
                                    
                                    # Try to get location
                                    location_elem = (
                                        card.find('span', class_=lambda x: x and 'location' in str(x).lower()) or
                                        card.find('div', class_=lambda x: x and 'location' in str(x).lower())
                                    )
                                    if location_elem:
                                        job['location'] = location_elem.get_text(strip=True)
                                    
                                    jobs.append(job)
                                    if len(jobs) >= max_results:
                                        break
                        except Exception as e:
                            print(f"Error parsing WhatJobs card: {e}", flush=True)
                            continue
                    
                    if len(jobs) > 0:
                        break  # Success, stop trying other variations
                        
                except requests.exceptions.Timeout:
                    print(f"Timeout searching WhatJobs: {base_url}", flush=True)
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"Request error searching WhatJobs: {e}", flush=True)
                    continue
                except Exception as e:
                    print(f"Error searching WhatJobs: {e}", flush=True)
                    continue
            
            if len(jobs) > 0:
                break
        
        return jobs
    
    def search_stepstone(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search StepStone - popular European job board"""
        jobs = []
        
        base_urls = [
            "https://www.stepstone.co.uk/jobs",
            "https://www.stepstone.de/en/jobs",
            "https://www.stepstone.com/jobs"
        ]
        
        params_variations = [
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords, 'l': location} if location else {'q': keywords},
            {'search': keywords, 'loc': location} if location else {'search': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.stepstone.com/'
        }
        
        try:
            self.session.get('https://www.stepstone.com', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = []
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('article', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and '/jobs/' in str(x).lower()))
                    
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if '/jobs/' in href.lower() or '/job/' in href.lower():
                            parent = link.find_parent(['div', 'article', 'section'])
                            if parent and parent not in job_cards:
                                if parent.find(['h2', 'h3', 'h4']) or len(parent.get_text(strip=True)) > 30:
                                    job_cards.append(parent)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 2]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            href = link_elem.get('href', '')
                            if not href or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = f"https://www.stepstone.com{href}"
                                else:
                                    href = f"https://www.stepstone.com/{href}"
                            
                            title_elem = card.find(['h2', 'h3', 'h4', 'a'], class_=lambda x: x and ('title' in str(x).lower() or 'job' in str(x).lower()))
                            if not title_elem:
                                title_elem = card.find(['h2', 'h3', 'h4'])
                            
                            company_elem = card.find(['span', 'div', 'a'], class_=lambda x: x and 'company' in str(x).lower())
                            
                            if title_elem and title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'stepstone',
                                    'date_found': datetime.now().isoformat()
                                }
                                
                                location_elem = card.find(['span', 'div'], class_=lambda x: x and 'location' in str(x).lower())
                                if location_elem:
                                    job['location'] = location_elem.get_text(strip=True)
                                
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        break
                        
                except Exception as e:
                    continue
        
        return jobs
    
    def search_jobrapido(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Jobrapido - European job aggregator"""
        jobs = []
        
        base_urls = [
            "https://uk.jobrapido.com/search",
            "https://www.jobrapido.com/search"
        ]
        
        params_variations = [
            {'q': keywords, 'location': location} if location else {'q': keywords},
            {'query': keywords, 'loc': location} if location else {'query': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://www.jobrapido.com/'
        }
        
        try:
            self.session.get('https://www.jobrapido.com', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = []
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('article'))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if '/job/' in href.lower() or '/vacancy/' in href.lower():
                            parent = link.find_parent(['div', 'article'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 2]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            href = link_elem.get('href', '')
                            if not href or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            
                            if not href.startswith('http'):
                                href = f"https://www.jobrapido.com{href}" if href.startswith('/') else f"https://www.jobrapido.com/{href}"
                            
                            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
                            company_elem = card.find(['span', 'div'], class_=lambda x: x and 'company' in str(x).lower())
                            
                            if title_elem and title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'jobrapido',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        break
                        
                except Exception:
                    continue
        
        return jobs
    
    def search_jooble(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Jooble - European job aggregator"""
        jobs = []
        
        base_urls = [
            "https://uk.jooble.org/jobs",
            "https://www.jooble.org/jobs"
        ]
        
        params_variations = [
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords, 'l': location} if location else {'q': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://www.jooble.org/'
        }
        
        try:
            self.session.get('https://www.jooble.org', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = []
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('article'))
                    
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if '/job/' in href.lower() or '/vacancy/' in href.lower():
                            parent = link.find_parent(['div', 'article'])
                            if parent and parent not in job_cards:
                                job_cards.append(parent)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 2]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            href = link_elem.get('href', '')
                            if not href or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            
                            if not href.startswith('http'):
                                href = f"https://www.jooble.org{href}" if href.startswith('/') else f"https://www.jooble.org/{href}"
                            
                            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
                            company_elem = card.find(['span', 'div'], class_=lambda x: x and 'company' in str(x).lower())
                            
                            if title_elem and title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'jooble',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        break
                        
                except Exception:
                    continue
        
        return jobs
    
    def search_infojobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search Infojobs - popular Spanish job board - tries API first, falls back to scraping"""
        jobs = []
        
        # Try API first if enabled
        if self.api_client:
            api_config = self.config.get('apis', {}).get('infojobs', {})
            if api_config.get('enabled', False) and api_config.get('use_api_instead_of_scraping', False):
                try:
                    api_jobs = self.api_client.search_infojobs_api(keywords, location, max_results)
                    if api_jobs:
                        print(f"Found {len(api_jobs)} jobs via Infojobs API", flush=True)
                        return api_jobs
                except Exception as e:
                    print(f"Infojobs API failed, falling back to scraping: {e}", flush=True)
        
        # Fall back to scraping
        # Infojobs uses different URL patterns
        base_urls = [
            "https://www.infojobs.net/ofertas-trabajo",
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml",
            "https://www.infojobs.net/jobsearch"
        ]
        
        # Try different parameter combinations
        params_variations = [
            {'q': keywords, 'provincia': location} if location else {'q': keywords},
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'palabra': keywords, 'provincia': location} if location else {'palabra': keywords},
            {'search': keywords, 'loc': location} if location else {'search': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.infojobs.net/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        try:
            # Visit homepage first to get cookies
            self.session.get('https://www.infojobs.net', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for job listings
                    job_cards = []
                    
                    # Common Infojobs selectors
                    job_cards.extend(soup.find_all('article'))
                    job_cards.extend(soup.find_all('div', {'data-job-id': True}))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and ('job' in str(x).lower() or 'oferta' in str(x).lower())))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and ('/oferta-empleo/' in str(x).lower() or '/job/' in str(x).lower())))
                    
                    # Also try finding all links that might be job listings
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        if '/oferta-empleo/' in href.lower() or '/job/' in href.lower():
                            if link not in job_cards:
                                job_cards.append(link)
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 3]:
                        try:
                            # Find the link element
                            if card.name == 'a':
                                link_elem = card
                            else:
                                link_elem = card.find('a', href=True)
                            
                            if not link_elem:
                                continue
                            
                            href = link_elem.get('href', '')
                            if not href or href in seen_urls:
                                continue
                            
                            # Skip if not a job URL
                            if '/oferta-empleo/' not in href.lower() and '/job/' not in href.lower():
                                continue
                            
                            seen_urls.add(href)
                            
                            # Normalize URL
                            if not href.startswith('http'):
                                href = f"https://www.infojobs.net{href}" if href.startswith('/') else f"https://www.infojobs.net/{href}"
                            
                            # Extract title
                            title_elem = None
                            if card.name == 'a':
                                title_elem = card
                            else:
                                title_elem = card.find(['h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and ('title' in str(x).lower() or 'titulo' in str(x).lower()))
                                if not title_elem:
                                    title_elem = card.find(['h2', 'h3', 'h4'])
                            
                            # Extract company
                            company_elem = card.find(['span', 'div', 'p'], class_=lambda x: x and ('empresa' in str(x).lower() or 'company' in str(x).lower() or 'empres' in str(x).lower()))
                            if not company_elem:
                                company_elem = card.find(['span', 'div'], string=lambda x: x and len(x) > 0 and len(x) < 100)
                            
                            title_text = title_elem.get_text(strip=True) if title_elem else link_elem.get_text(strip=True)
                            
                            if title_text and len(title_text) > 3:
                                job = {
                                    'title': title_text[:200],
                                    'company': company_elem.get_text(strip=True)[:100] if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'infojobs',
                                    'date_found': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        break
                        
                except Exception as e:
                    continue
            
            if len(jobs) > 0:
                break
        
        return jobs
    
    def search_eures(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search EURES - European job mobility portal"""
        jobs = []
        
        base_url = "https://ec.europa.eu/eures/public/search-job"
        
        params_variations = [
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://ec.europa.eu/eures/'
        }
        
        try:
            self.session.get('https://ec.europa.eu/eures', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for params in params_variations:
            try:
                response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_cards = []
                job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                job_cards.extend(soup.find_all('article'))
                job_cards.extend(soup.find_all('a', href=lambda x: x and '/job/' in str(x).lower()))
                
                seen_urls = set()
                for card in job_cards[:max_results * 2]:
                    try:
                        link_elem = card.find('a', href=True) if card.name != 'a' else card
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href', '')
                        if not href or href in seen_urls:
                            continue
                        seen_urls.add(href)
                        
                        if not href.startswith('http'):
                            href = f"https://ec.europa.eu{href}" if href.startswith('/') else f"https://ec.europa.eu/eures/{href}"
                        
                        title_elem = card.find(['h2', 'h3', 'h4', 'a'])
                        company_elem = card.find(['span', 'div'], class_=lambda x: x and ('employer' in str(x).lower() or 'company' in str(x).lower()))
                        
                        if title_elem and title_elem.get_text(strip=True):
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                'url': href,
                                'source': 'eures',
                                'date_found': datetime.now().isoformat()
                            }
                            jobs.append(job)
                            if len(jobs) >= max_results:
                                break
                    except Exception:
                        continue
                
                if len(jobs) > 0:
                    break
                    
            except Exception:
                continue
        
        return jobs
    
    def search_careerjet(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Search CareerJet - European job aggregator (English)"""
        jobs = []
        
        base_urls = [
            "https://www.careerjet.co.uk/search/jobs",
            "https://www.careerjet.com/search/jobs"
        ]
        
        params_variations = [
            {'keywords': keywords, 'location': location} if location else {'keywords': keywords},
            {'q': keywords, 'l': location} if location else {'q': keywords}
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://www.careerjet.co.uk/'
        }
        
        try:
            self.session.get('https://www.careerjet.co.uk', headers=headers, timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        for base_url in base_urls:
            for params in params_variations:
                try:
                    response = self.session.get(base_url, params=params, headers=headers, timeout=(5, 15), allow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = []
                    job_cards.extend(soup.find_all('article', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower()))
                    job_cards.extend(soup.find_all('a', href=lambda x: x and '/job/' in str(x).lower()))
                    
                    seen_urls = set()
                    for card in job_cards[:max_results * 2]:
                        try:
                            link_elem = card.find('a', href=True) or (card if card.name == 'a' else None)
                            if not link_elem:
                                continue
                            
                            href = link_elem.get('href', '')
                            if not href or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            
                            if not href.startswith('http'):
                                href = f"https://www.careerjet.co.uk{href}" if href.startswith('/') else f"https://www.careerjet.co.uk/{href}"
                            
                            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
                            company_elem = card.find(['span', 'div'], class_=lambda x: x and 'company' in str(x).lower())
                            
                            if title_elem and title_elem.get_text(strip=True):
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                                    'url': href,
                                    'source': 'careerjet',
                                    'date_found': datetime.now().isoformat()
                                }
                                
                                location_elem = card.find(['span', 'div'], class_=lambda x: x and 'location' in str(x).lower())
                                if location_elem:
                                    job['location'] = location_elem.get_text(strip=True)
                                
                                jobs.append(job)
                                if len(jobs) >= max_results:
                                    break
                        except Exception:
                            continue
                    
                    if len(jobs) > 0:
                        break
                        
                except Exception:
                    continue
        
        return jobs
    
    def _update_progress(self, progress_file: str, stage: str, progress: int, total: int, message: str = "", jobs_found: int = 0, jobs_matched: int = 0):
        """Update progress file for web interface"""
        try:
            progress_data = {
                'stage': stage,
                'progress': progress,
                'total': total,
                'percentage': int((progress / total * 100)) if total > 0 else 0,
                'message': message,
                'jobs_found': jobs_found,
                'jobs_matched': jobs_matched,
                'timestamp': datetime.now().isoformat()
            }
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f)
        except Exception as e:
            print(f"Warning: Could not update progress file: {e}", flush=True)
    
    def crawl_job_boards(self, custom_keywords: str = None, progress_file: str = None) -> List[Dict]:
        """Crawl all configured job boards
        
        Args:
            custom_keywords: Optional custom keywords to override config keywords
            progress_file: Optional path to progress file for tracking
        """
        all_jobs = []
        search_config = self.config.get('search', {})
        # Use custom keywords if provided, otherwise use config keywords
        keywords = custom_keywords if custom_keywords is not None else search_config.get('keywords', '')
        location = search_config.get('location', '')
        job_boards_config = self.config.get('job_boards', {})
        
        # Count enabled job boards
        enabled_boards = [name for name, enabled in [
            ('indeed', job_boards_config.get('indeed', False)),
            ('linkedin', job_boards_config.get('linkedin', True)),
            ('reed', job_boards_config.get('reed', True)),
            ('monster', job_boards_config.get('monster', True)),
            ('glassdoor', job_boards_config.get('glassdoor', True)),
            ('totaljobs', job_boards_config.get('totaljobs', True)),
            ('cvlibrary', job_boards_config.get('cvlibrary', True)),
            ('adzuna', job_boards_config.get('adzuna', True)),
            ('jobserve', job_boards_config.get('jobserve', True)),
            ('whatjobs', job_boards_config.get('whatjobs', True)),
            ('stepstone', job_boards_config.get('stepstone', False)),
            ('jobrapido', job_boards_config.get('jobrapido', False)),
            ('jooble', job_boards_config.get('jooble', False)),
            ('infojobs', job_boards_config.get('infojobs', False)),
            ('eures', job_boards_config.get('eures', False)),
            ('careerjet', job_boards_config.get('careerjet', False))
        ] if enabled]
        
        # Check if aggregator APIs are enabled (can replace multiple boards)
        api_configs = self.config.get('apis', {})
        
        # Try aggregator APIs first if enabled
        if self.api_client:
            # APIJobs covers multiple boards
            apijobs_config = api_configs.get('apijobs', {})
            if apijobs_config.get('enabled', False):
                try:
                    print("Searching via APIJobs aggregator (covers 4000+ boards)...", flush=True)
                    if progress_file:
                        self._update_progress(progress_file, 'crawling', 1, 1, "Searching APIJobs...", len(all_jobs), 0)
                    apijobs_results = self.api_client.search_apijobs(keywords, location, max_results=200)
                    if apijobs_results:
                        all_jobs.extend(apijobs_results)
                        print(f"Found {len(apijobs_results)} jobs via APIJobs", flush=True)
                        if progress_file:
                            self._update_progress(progress_file, 'crawling', 1, 1, f"Found {len(apijobs_results)} jobs via APIJobs", len(all_jobs), 0)
                except Exception as e:
                    print(f"APIJobs error: {e}", flush=True)
            
            # JSearch covers Google for Jobs
            jsearch_config = api_configs.get('jsearch', {})
            if jsearch_config.get('enabled', False):
                try:
                    print("Searching via JSearch (Google for Jobs)...", flush=True)
                    if progress_file:
                        self._update_progress(progress_file, 'crawling', 1, 1, "Searching JSearch...", len(all_jobs), 0)
                    jsearch_results = self.api_client.search_jsearch(keywords, location, max_results=100)
                    if jsearch_results:
                        all_jobs.extend(jsearch_results)
                        print(f"Found {len(jsearch_results)} jobs via JSearch", flush=True)
                        if progress_file:
                            self._update_progress(progress_file, 'crawling', 1, 1, f"Found {len(jsearch_results)} jobs via JSearch", len(all_jobs), 0)
                except Exception as e:
                    print(f"JSearch error: {e}", flush=True)
        
        total_boards = len(enabled_boards)
        current_board = 0
        
        # Search Indeed
        if job_boards_config.get('indeed', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Indeed...", len(all_jobs), 0)
            print("Searching Indeed...", flush=True)
            indeed_jobs = self.search_indeed(keywords, location)
            all_jobs.extend(indeed_jobs)
            print(f"Found {len(indeed_jobs)} jobs on Indeed", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(indeed_jobs)} jobs on Indeed (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search LinkedIn
        if job_boards_config.get('linkedin', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching LinkedIn...", len(all_jobs), 0)
            print("Searching LinkedIn...", flush=True)
            linkedin_jobs = self.search_linkedin(keywords, location)
            all_jobs.extend(linkedin_jobs)
            print(f"Found {len(linkedin_jobs)} jobs on LinkedIn", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(linkedin_jobs)} jobs on LinkedIn (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Reed
        if job_boards_config.get('reed', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Reed...", len(all_jobs), 0)
            print("Searching Reed...", flush=True)
            reed_jobs = self.search_reed(keywords, location)
            all_jobs.extend(reed_jobs)
            print(f"Found {len(reed_jobs)} jobs on Reed", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(reed_jobs)} jobs on Reed (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Monster
        if job_boards_config.get('monster', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Monster...", len(all_jobs), 0)
            print("Searching Monster...", flush=True)
            monster_jobs = self.search_monster(keywords, location)
            all_jobs.extend(monster_jobs)
            print(f"Found {len(monster_jobs)} jobs on Monster", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(monster_jobs)} jobs on Monster (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Glassdoor
        if job_boards_config.get('glassdoor', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Glassdoor...", len(all_jobs), 0)
            print("Searching Glassdoor...", flush=True)
            glassdoor_jobs = self.search_glassdoor(keywords, location)
            all_jobs.extend(glassdoor_jobs)
            print(f"Found {len(glassdoor_jobs)} jobs on Glassdoor", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(glassdoor_jobs)} jobs on Glassdoor (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search TotalJobs
        if job_boards_config.get('totaljobs', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching TotalJobs...", len(all_jobs), 0)
            print("Searching TotalJobs...", flush=True)
            totaljobs_jobs = self.search_totaljobs(keywords, location)
            all_jobs.extend(totaljobs_jobs)
            print(f"Found {len(totaljobs_jobs)} jobs on TotalJobs", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(totaljobs_jobs)} jobs on TotalJobs (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search CV-Library
        if job_boards_config.get('cvlibrary', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching CV-Library...", len(all_jobs), 0)
            print("Searching CV-Library...", flush=True)
            cvlibrary_jobs = self.search_cvlibrary(keywords, location)
            all_jobs.extend(cvlibrary_jobs)
            print(f"Found {len(cvlibrary_jobs)} jobs on CV-Library", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(cvlibrary_jobs)} jobs on CV-Library (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Adzuna
        if job_boards_config.get('adzuna', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Adzuna...", len(all_jobs), 0)
            print("Searching Adzuna...", flush=True)
            adzuna_jobs = self.search_adzuna(keywords, location)
            all_jobs.extend(adzuna_jobs)
            print(f"Found {len(adzuna_jobs)} jobs on Adzuna", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(adzuna_jobs)} jobs on Adzuna (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search JobServe
        if job_boards_config.get('jobserve', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching JobServe...", len(all_jobs), 0)
            print("Searching JobServe...", flush=True)
            jobserve_jobs = self.search_jobserve(keywords, location)
            all_jobs.extend(jobserve_jobs)
            print(f"Found {len(jobserve_jobs)} jobs on JobServe", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(jobserve_jobs)} jobs on JobServe (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search WhatJobs
        if job_boards_config.get('whatjobs', True):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching WhatJobs...", len(all_jobs), 0)
            print("Searching WhatJobs...", flush=True)
            whatjobs_jobs = self.search_whatjobs(keywords, location)
            all_jobs.extend(whatjobs_jobs)
            print(f"Found {len(whatjobs_jobs)} jobs on WhatJobs", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(whatjobs_jobs)} jobs on WhatJobs (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search StepStone (European)
        if job_boards_config.get('stepstone', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching StepStone...", len(all_jobs), 0)
            print("Searching StepStone...", flush=True)
            stepstone_jobs = self.search_stepstone(keywords, location)
            all_jobs.extend(stepstone_jobs)
            print(f"Found {len(stepstone_jobs)} jobs on StepStone", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(stepstone_jobs)} jobs on StepStone (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Jobrapido (European aggregator)
        if job_boards_config.get('jobrapido', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Jobrapido...", len(all_jobs), 0)
            print("Searching Jobrapido...", flush=True)
            jobrapido_jobs = self.search_jobrapido(keywords, location)
            all_jobs.extend(jobrapido_jobs)
            print(f"Found {len(jobrapido_jobs)} jobs on Jobrapido", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(jobrapido_jobs)} jobs on Jobrapido (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Jooble (European aggregator)
        if job_boards_config.get('jooble', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Jooble...", len(all_jobs), 0)
            print("Searching Jooble...", flush=True)
            jooble_jobs = self.search_jooble(keywords, location)
            all_jobs.extend(jooble_jobs)
            print(f"Found {len(jooble_jobs)} jobs on Jooble", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(jooble_jobs)} jobs on Jooble (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search Infojobs (Spain)
        if job_boards_config.get('infojobs', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching Infojobs...", len(all_jobs), 0)
            print("Searching Infojobs...", flush=True)
            infojobs_jobs = self.search_infojobs(keywords, location)
            all_jobs.extend(infojobs_jobs)
            print(f"Found {len(infojobs_jobs)} jobs on Infojobs", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(infojobs_jobs)} jobs on Infojobs (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search EURES (European job portal)
        if job_boards_config.get('eures', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching EURES...", len(all_jobs), 0)
            print("Searching EURES...", flush=True)
            eures_jobs = self.search_eures(keywords, location)
            all_jobs.extend(eures_jobs)
            print(f"Found {len(eures_jobs)} jobs on EURES", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(eures_jobs)} jobs on EURES (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        # Search CareerJet (European aggregator - English)
        if job_boards_config.get('careerjet', False):
            current_board += 1
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Searching CareerJet...", len(all_jobs), 0)
            print("Searching CareerJet...", flush=True)
            careerjet_jobs = self.search_careerjet(keywords, location)
            all_jobs.extend(careerjet_jobs)
            print(f"Found {len(careerjet_jobs)} jobs on CareerJet", flush=True)
            if progress_file:
                self._update_progress(progress_file, 'crawling', current_board, total_boards, f"Found {len(careerjet_jobs)} jobs on CareerJet (Total: {len(all_jobs)})", len(all_jobs), 0)
            time.sleep(2)  # Rate limiting
        
        return all_jobs
    
    def process_jobs(self, custom_keywords: str = None, progress_file: str = None):
        """Main processing loop: crawl, match, and alert
        
        Args:
            custom_keywords: Optional custom keywords to override config keywords
            progress_file: Optional path to progress file for tracking
        """
        print(f"\n{'='*60}", flush=True)
        print(f"Job Trawler - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        if custom_keywords:
            print(f"Using custom keywords: {custom_keywords}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        # Initialize progress
        if progress_file:
            self._update_progress(progress_file, 'starting', 0, 100, "Starting trawler...", 0, 0)
        
        # Crawl job boards with optional custom keywords
        if progress_file:
            self._update_progress(progress_file, 'crawling', 0, 100, "Crawling job boards...", 0, 0)
        all_jobs = self.crawl_job_boards(custom_keywords, progress_file)
        print(f"Found {len(all_jobs)} jobs across all boards\n", flush=True)
        
        # Get search config for location filtering
        search_config = self.config.get('search', {})
        
        # Filter new jobs and match with CV
        if progress_file:
            self._update_progress(progress_file, 'matching', 0, len(all_jobs), f"Processing {len(all_jobs)} jobs...", len(all_jobs), 0)
        relevant_jobs = []
        processed = 0
        
        # Check if we should skip job details fetching (faster but less accurate matching)
        skip_details = self.config.get('matching', {}).get('skip_job_details', False)
        
        for job in all_jobs:
            job_id = f"{job['source']}_{job['title']}_{job['company']}"
            
            if job_id in self.seen_jobs:
                processed += 1
                if progress_file:
                    self._update_progress(progress_file, 'matching', processed, len(all_jobs), f"Processing job {processed}/{len(all_jobs)}...", len(all_jobs), len(relevant_jobs))
                continue
            
            # Update progress before fetching details
            if progress_file:
                self._update_progress(progress_file, 'matching', processed, len(all_jobs), f"Processing job {processed + 1}/{len(all_jobs)}: {job.get('title', 'Unknown')[:50]}...", len(all_jobs), len(relevant_jobs))
            
            # Get full description for better matching (with timeout protection)
            # Skip if configured to skip details or if we've already got a snippet
            if not skip_details and not job.get('full_description') and job.get('url'):
                try:
                    job = self.get_job_details(job)
                except Exception as e:
                    print(f"Error in get_job_details, continuing: {e}", flush=True)
                    # Continue even if details fetch fails
            elif skip_details:
                # Use snippet if available, otherwise empty description
                if not job.get('full_description') and job.get('snippet'):
                    job['full_description'] = job['snippet']
            
            processed += 1
            time.sleep(0.3)  # Reduced rate limiting to speed things up
            
            # Match job with CV
            match_score, matched_skills = self.job_matcher.match_job(job)
            job['match_score'] = match_score
            job['matched_skills'] = matched_skills
            
            # ALWAYS filter out non-European/UK jobs
            job_location_str = job.get('location', '')
            if not job_location_str:
                # Try to extract from description
                job_location_str = self._extract_job_location(job)
            
            if job_location_str:
                # Check if location is European/UK
                if not self._is_european_location(job_location_str):
                    if progress_file:
                        self._update_progress(progress_file, 'matching', processed, len(all_jobs), f"Processing job {processed}/{len(all_jobs)}... (Excluding non-EU/UK)", len(all_jobs), len(relevant_jobs))
                    print(f"[SKIP] {job['title']} at {job['company']} - Non-European location: {job_location_str}", flush=True)
                    continue  # Skip non-European jobs
            
            # Filter by location if configured (skip if location is empty or just placeholder)
            location_config = search_config.get('location', '')
            location_config_clean = location_config.strip().lower() if location_config else ''
            if location_config_clean and location_config_clean not in ['', 'your city, state or remote', 'remote']:
                # Extract location from job (try to get it from description or company info)
                job_location = self._extract_job_location(job)
                if job_location and not self._location_matches(location_config, job_location):
                    if progress_file:
                        self._update_progress(progress_file, 'matching', processed, len(all_jobs), f"Processing job {processed}/{len(all_jobs)}...", len(all_jobs), len(relevant_jobs))
                    continue  # Skip jobs not in desired location
            
            # Filter by minimum match score
            min_score = self.config.get('matching', {}).get('min_score', 0.5)
            if match_score >= min_score:
                relevant_jobs.append(job)
                self.seen_jobs.add(job_id)
                print(f"[MATCH] {job['title']} at {job['company']} (Score: {match_score:.2f})", flush=True)
            else:
                print(f"[SKIP] {job['title']} at {job['company']} (Score: {match_score:.2f} < {min_score})", flush=True)
            
            if progress_file:
                self._update_progress(progress_file, 'matching', processed, len(all_jobs), f"Processed {processed}/{len(all_jobs)} jobs, found {len(relevant_jobs)} matches", len(all_jobs), len(relevant_jobs))
        
        # Send alerts for relevant jobs
        if progress_file:
            self._update_progress(progress_file, 'finishing', 95, 100, f"Saving results... Found {len(relevant_jobs)} matching jobs", len(all_jobs), len(relevant_jobs))
        if relevant_jobs:
            print(f"\n[*] Sending alerts for {len(relevant_jobs)} relevant jobs...")
            self.alert_system.send_alerts(relevant_jobs)
        else:
            print("\nNo new relevant jobs found.")
        
        # Save seen jobs
        self._save_seen_jobs()
        
        if progress_file:
            self._update_progress(progress_file, 'complete', 100, 100, f"Complete! Found {len(relevant_jobs)} new matching jobs", len(all_jobs), len(relevant_jobs))
        
        return relevant_jobs
    
    def process_jobs_with_keywords(self, custom_keywords: str, progress_file: str = None):
        """Process jobs with custom keywords (wrapper for process_jobs)
        
        Args:
            custom_keywords: Custom keywords to search for
            progress_file: Optional path to progress file for tracking
            
        Returns:
            List of relevant jobs found
        """
        return self.process_jobs(custom_keywords=custom_keywords, progress_file=progress_file)


def main():
    """Main entry point"""
    trawler = JobTrawler()
    
    # Run continuously or once
    if trawler.config.get('continuous', False):
        interval = trawler.config.get('check_interval_minutes', 60)
        print(f"Running in continuous mode (checking every {interval} minutes)")
        while True:
            trawler.process_jobs()
            print(f"\nWaiting {interval} minutes until next check...\n")
            time.sleep(interval * 60)
    else:
        trawler.process_jobs()


if __name__ == "__main__":
    main()

