"""
LinkedIn Profile Parser - Extracts skills and keywords from LinkedIn profile URL
"""

import re
import requests
from typing import Set, List
from bs4 import BeautifulSoup
import time

# Try to import Selenium for JavaScript-rendered content
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class LinkedInParser:
    def __init__(self, profile_url: str):
        """Initialize LinkedIn parser with profile URL"""
        self.profile_url = profile_url
        self.profile_text = ""
        self.skills = set()
        self.keywords = set()
        
        # Extract profile identifier from URL
        self.profile_id = self._extract_profile_id(profile_url)
    
    def _extract_profile_id(self, url: str) -> str:
        """Extract profile identifier from LinkedIn URL"""
        # Handle various LinkedIn URL formats
        patterns = [
            r'linkedin\.com/in/([^/?#]+)',
            r'linkedin\.com/pub/([^/?#]+)',
            r'linkedin\.com/profile/view\?id=([^&]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def parse(self) -> bool:
        """Parse LinkedIn profile and extract skills/keywords
        
        Returns:
            bool: True if parsing was successful
        """
        if not self.profile_id:
            print("Invalid LinkedIn URL format", flush=True)
            return False
        
        # Try to get profile data
        success = self._fetch_profile()
        
        if success:
            self.skills = self._extract_skills()
            self.keywords = self._extract_keywords()
            return True
        
        return False
    
    def _fetch_profile(self) -> bool:
        """Fetch LinkedIn profile content"""
        # Try requests first (for public profiles)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
            }
            
            # Try public profile URL
            public_url = f"https://www.linkedin.com/in/{self.profile_id}"
            response = requests.get(public_url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Extract text content
                self.profile_text = soup.get_text(separator=' ', strip=True)
                return True
            else:
                print(f"LinkedIn profile returned status {response.status_code}", flush=True)
                # Try Selenium if available (for authenticated or JS-rendered content)
                if SELENIUM_AVAILABLE:
                    return self._fetch_with_selenium(public_url)
                return False
                
        except Exception as e:
            print(f"Error fetching LinkedIn profile with requests: {e}", flush=True)
            # Try Selenium fallback
            if SELENIUM_AVAILABLE:
                return self._fetch_with_selenium(f"https://www.linkedin.com/in/{self.profile_id}")
            return False
    
    def _fetch_with_selenium(self, url: str) -> bool:
        """Fetch LinkedIn profile using Selenium (for JavaScript-rendered content)"""
        if not SELENIUM_AVAILABLE:
            return False
        
        driver = None
        try:
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to get page source
            self.profile_text = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(self.profile_text, 'html.parser')
            self.profile_text = soup.get_text(separator=' ', strip=True)
            
            return True
            
        except Exception as e:
            print(f"Error fetching LinkedIn profile with Selenium: {e}", flush=True)
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _extract_skills(self) -> Set[str]:
        """Extract skills from LinkedIn profile"""
        skills = set()
        
        if not self.profile_text:
            return skills
        
        # Common technical skills to look for
        technical_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'kotlin', 'swift',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'git', 'jenkins', 'ci/cd', 'devops', 'agile', 'scrum',
            'machine learning', 'ai', 'data science', 'analytics', 'big data',
            'rest api', 'graphql', 'microservices', 'api', 'websocket',
            'linux', 'bash', 'shell scripting', 'powershell',
            'html', 'css', 'sass', 'less', 'bootstrap',
            'jira', 'confluence', 'slack', 'microsoft office',
            'project management', 'leadership', 'team management'
        ]
        
        profile_lower = self.profile_text.lower()
        
        # Look for skills in profile text
        for skill in technical_skills:
            # Check for exact match or word boundary match
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, profile_lower, re.IGNORECASE):
                skills.add(skill)
        
        # Look for skills section (common LinkedIn patterns)
        skills_section_patterns = [
            r'skills[:\s]+([^\.]+)',
            r'technical skills[:\s]+([^\.]+)',
            r'proficient in[:\s]+([^\.]+)',
        ]
        
        for pattern in skills_section_patterns:
            matches = re.finditer(pattern, profile_lower, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                # Extract individual skills
                skill_words = re.findall(r'\b\w+(?:\s+\w+)?\b', skills_text)
                for skill_word in skill_words:
                    skill_word_lower = skill_word.lower()
                    if len(skill_word_lower) > 2 and skill_word_lower not in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'with']:
                        # Check if it matches any known technical skill
                        for tech_skill in technical_skills:
                            if tech_skill in skill_word_lower or skill_word_lower in tech_skill:
                                skills.add(tech_skill)
        
        return skills
    
    def _extract_keywords(self) -> Set[str]:
        """Extract keywords from LinkedIn profile"""
        keywords = set()
        
        if not self.profile_text:
            return keywords
        
        # Extract job titles and roles
        job_title_patterns = [
            r'(software engineer|developer|programmer|architect|manager|director|lead|senior|junior|principal)',
            r'(data scientist|data engineer|data analyst|ml engineer|ai engineer)',
            r'(devops engineer|sre|site reliability engineer|cloud engineer)',
            r'(full stack|backend|frontend|full-stack|back-end|front-end)',
        ]
        
        profile_lower = self.profile_text.lower()
        
        for pattern in job_title_patterns:
            matches = re.finditer(pattern, profile_lower, re.IGNORECASE)
            for match in matches:
                keywords.add(match.group(1).strip())
        
        # Add industry keywords
        industry_keywords = [
            'cloud', 'microservices', 'api', 'rest', 'graphql',
            'distributed systems', 'scalability', 'performance',
            'security', 'testing', 'automation', 'monitoring',
            'big data', 'analytics', 'full stack', 'backend', 'frontend',
            'agile', 'scrum', 'devops', 'ci/cd', 'kubernetes', 'docker'
        ]
        
        for keyword in industry_keywords:
            if keyword in profile_lower:
                keywords.add(keyword)
        
        # Add all skills as keywords
        keywords.update(self.skills)
        
        return keywords
    
    def get_skills(self) -> Set[str]:
        """Get extracted skills"""
        return self.skills
    
    def get_keywords(self) -> Set[str]:
        """Get extracted keywords"""
        return self.keywords
    
    def get_profile_text(self) -> str:
        """Get raw profile text"""
        return self.profile_text

