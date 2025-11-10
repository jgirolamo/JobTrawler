"""
Job Matcher - Matches job postings with CV skills and experience
"""

from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
import re


class JobMatcher:
    def __init__(self, cv_skills: Set[str], cv_keywords: Set[str] = None):
        """Initialize job matcher with CV skills"""
        self.cv_skills = {skill.lower() for skill in cv_skills}
        self.cv_keywords = {kw.lower() for kw in (cv_keywords or set())}
    
    def _extract_job_text(self, job: Dict) -> str:
        """Extract all text from job posting"""
        text_parts = [
            job.get('title', ''),
            job.get('company', ''),
            job.get('snippet', ''),
            job.get('full_description', '')
        ]
        return ' '.join(text_parts).lower()
    
    def _calculate_skill_match(self, job_text: str) -> Tuple[float, List[str]]:
        """Calculate how many CV skills match the job - improved scoring"""
        matched_skills = []
        total_skills = len(self.cv_skills)
        
        if total_skills == 0:
            return 0.0, []
        
        # Define high-value skills (core technologies that are very important)
        high_value_skills = {
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
            'terraform', 'ansible', 'python', 'java', 'javascript', 'typescript',
            'react', 'node.js', 'devops', 'ci/cd', 'linux', 'windows server',
            'active directory', 'azure ad', 'postgresql', 'mysql', 'mongodb',
            'jenkins', 'git', 'agile', 'scrum', 'itil', 'servicenow', 'jira'
        }
        
        for skill in self.cv_skills:
            # Exact match
            if skill in job_text:
                matched_skills.append(skill)
            # Fuzzy match for variations
            elif self._fuzzy_match_skill(skill, job_text):
                matched_skills.append(skill)
        
        if len(matched_skills) == 0:
            return 0.0, []
        
        # Improved scoring: Use logarithmic scale to avoid penalizing many skills
        # Base score: number of matches, but with diminishing returns
        base_matches = len(matched_skills)
        
        # Count high-value skill matches (weighted more)
        high_value_matches = sum(1 for skill in matched_skills if skill in high_value_skills)
        
        # Calculate score using a better formula:
        # - Each match contributes, but with diminishing returns
        # - High-value skills get extra weight
        # - Minimum score boost for any matches
        if base_matches == 1:
            match_score = 0.3  # Single match gets decent score
        elif base_matches == 2:
            match_score = 0.5  # Two matches is good
        elif base_matches == 3:
            match_score = 0.65  # Three matches is very good
        elif base_matches >= 4:
            match_score = 0.75 + min(0.2, (base_matches - 4) * 0.05)  # 4+ matches is excellent
        else:
            match_score = 0.0
        
        # Bonus for high-value skills (up to +0.15)
        if high_value_matches > 0:
            high_value_bonus = min(0.15, high_value_matches * 0.05)
            match_score = min(1.0, match_score + high_value_bonus)
        
        return match_score, matched_skills
    
    def _fuzzy_match_skill(self, skill: str, job_text: str, threshold: float = 0.75) -> bool:
        """Check if skill matches with fuzzy matching - improved with more variations"""
        # Expanded skill variations mapping
        variations = {
            'js': 'javascript',
            'k8s': 'kubernetes',
            'kubernetes': 'k8s',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'ad': 'active directory',
            'azure ad': 'azure active directory',
            'o365': 'office 365',
            'office 365': 'o365',
            'm365': 'microsoft 365',
            'microsoft 365': 'm365',
            'gcp': 'google cloud platform',
            'google cloud': 'gcp',
            'aws': 'amazon web services',
            'node': 'node.js',
            'nodejs': 'node.js',
            'react': 'react.js',
            'vue': 'vue.js',
            'angular': 'angular.js',
            'postgres': 'postgresql',
            'mysql': 'mariadb',
            'sql server': 'mssql',
            'mssql': 'sql server',
            'windows': 'windows server',
            'linux': 'unix',
            'unix': 'linux',
            'ci/cd': 'continuous integration',
            'devops': 'dev ops',
            'itil': 'it service management',
            'sccm': 'system center configuration manager',
            'exchange': 'microsoft exchange',
            'dns': 'domain name system',
            'dhcp': 'dynamic host configuration protocol',
            'vpn': 'virtual private network',
            'mfa': 'multi-factor authentication',
            'multi-factor authentication': 'mfa',
        }
        
        # Check direct variation
        if skill in variations:
            if variations[skill] in job_text:
                return True
        
        # Check reverse variation
        for key, value in variations.items():
            if skill == value and key in job_text:
                return True
        
        # Check for skill with word boundaries (more flexible)
        # Allow partial word matches for compound skills
        skill_words = skill.split()
        if len(skill_words) > 1:
            # For multi-word skills, check if all words appear
            if all(word in job_text for word in skill_words):
                return True
        
        # Check for skill with word boundaries
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, job_text, re.IGNORECASE):
            return True
        
        # Check for skill without word boundaries (for partial matches in compound words)
        if skill in job_text:
            return True
        
        # Fuzzy match for partial matches (lower threshold for better matching)
        words = job_text.split()
        for word in words:
            similarity = SequenceMatcher(None, skill, word).ratio()
            if similarity >= threshold:
                return True
        
        # Check if skill is contained in any word (for abbreviations)
        for word in words:
            if skill in word or word in skill:
                if len(skill) >= 3 and len(word) >= 3:  # Avoid matching very short strings
                    return True
        
        return False
    
    def _calculate_keyword_match(self, job_text: str) -> float:
        """Calculate keyword match score - improved scoring"""
        if not self.cv_keywords:
            return 0.0
        
        matched_keywords = sum(1 for kw in self.cv_keywords if kw in job_text)
        
        if matched_keywords == 0:
            return 0.0
        
        # Improved scoring: don't penalize for having many keywords
        # Use a scale that rewards matches
        if matched_keywords == 1:
            return 0.3
        elif matched_keywords == 2:
            return 0.5
        elif matched_keywords >= 3:
            return 0.7 + min(0.2, (matched_keywords - 3) * 0.05)
        
        return 0.0
    
    def _calculate_experience_match(self, job: Dict, cv_years: int = 0) -> float:
        """Calculate experience level match"""
        job_text = self._extract_job_text(job)
        
        # Look for experience requirements
        years_patterns = [
            r'(\d+)[\+]?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(?:minimum|min|at least)\s*(\d+)\s*(?:years?|yrs?)',
        ]
        
        required_years = 0
        for pattern in years_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                required_years = int(match.group(1))
                break
        
        if required_years == 0:
            return 1.0  # No requirement specified
        
        if cv_years >= required_years:
            return 1.0
        elif cv_years >= required_years * 0.7:  # 70% of requirement
            return 0.7
        else:
            return 0.3
    
    def match_job(self, job: Dict, cv_years: int = 0) -> Tuple[float, List[str]]:
        """
        Match a job posting with CV
        Returns: (match_score, matched_skills)
        """
        job_text = self._extract_job_text(job)
        job_title = job.get('title', '').lower()
        
        # Calculate different match components
        skill_score, matched_skills = self._calculate_skill_match(job_text)
        keyword_score = self._calculate_keyword_match(job_text)
        experience_score = self._calculate_experience_match(job, cv_years)
        
        # Bonus for title matches (skills/keywords in title are VERY important)
        title_bonus = 0.0
        if job_title:
            title_skills = sum(1 for skill in self.cv_skills if skill in job_title)
            title_keywords = sum(1 for kw in self.cv_keywords if kw in job_title)
            
            # Title matches are very significant - give substantial bonus
            if title_skills > 0:
                # Each skill in title is worth 0.1 (up to 0.3)
                title_bonus += min(0.3, title_skills * 0.1)
            if title_keywords > 0:
                # Each keyword in title is worth 0.08 (up to 0.2)
                title_bonus += min(0.2, title_keywords * 0.08)
        
        # Bonus for having any matches at all (partial credit)
        any_match_bonus = 0.0
        if len(matched_skills) > 0 or keyword_score > 0:
            any_match_bonus = 0.15  # Increased base bonus for any relevance
        
        # Bonus for multiple skill matches (more matches = higher score)
        skill_count_bonus = 0.0
        if len(matched_skills) >= 5:
            skill_count_bonus = 0.2  # Excellent match
        elif len(matched_skills) >= 3:
            skill_count_bonus = 0.15  # Very good match
        elif len(matched_skills) >= 2:
            skill_count_bonus = 0.1  # Good match
        
        # Weighted combination (improved scoring)
        # Skills are most important (60%), keywords (20%), experience (15%)
        # Increased weights for better scoring
        base_score = (
            skill_score * 0.6 +
            keyword_score * 0.2 +
            experience_score * 0.15
        )
        
        # Add bonuses (can push score above 1.0, but we'll cap at 1.0)
        match_score = min(1.0, base_score + title_bonus + any_match_bonus + skill_count_bonus)
        
        # Ensure minimum score boost: if we have any matches, give at least 0.2
        # Increased from 0.15 to 0.2 for better visibility of relevant jobs
        if len(matched_skills) > 0 or keyword_score > 0:
            match_score = max(match_score, 0.2)
        
        # Additional boost for jobs with strong skill matches in title
        if title_bonus > 0.2 and len(matched_skills) >= 2:
            match_score = min(1.0, match_score + 0.1)
        
        return match_score, matched_skills



