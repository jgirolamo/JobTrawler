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
        """Calculate how many CV skills match the job"""
        matched_skills = []
        total_skills = len(self.cv_skills)
        
        if total_skills == 0:
            return 0.0, []
        
        for skill in self.cv_skills:
            # Exact match
            if skill in job_text:
                matched_skills.append(skill)
            # Fuzzy match for variations
            elif self._fuzzy_match_skill(skill, job_text):
                matched_skills.append(skill)
        
        match_score = len(matched_skills) / total_skills if total_skills > 0 else 0.0
        return match_score, matched_skills
    
    def _fuzzy_match_skill(self, skill: str, job_text: str, threshold: float = 0.8) -> bool:
        """Check if skill matches with fuzzy matching"""
        # Check for common variations
        variations = {
            'js': 'javascript',
            'k8s': 'kubernetes',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
        }
        
        if skill in variations:
            skill = variations[skill]
        
        # Check for skill with word boundaries
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, job_text, re.IGNORECASE):
            return True
        
        # Fuzzy match for partial matches
        words = job_text.split()
        for word in words:
            similarity = SequenceMatcher(None, skill, word).ratio()
            if similarity >= threshold:
                return True
        
        return False
    
    def _calculate_keyword_match(self, job_text: str) -> float:
        """Calculate keyword match score"""
        if not self.cv_keywords:
            return 0.0
        
        matched_keywords = sum(1 for kw in self.cv_keywords if kw in job_text)
        return matched_keywords / len(self.cv_keywords) if self.cv_keywords else 0.0
    
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
        
        # Bonus for title matches (skills/keywords in title are more important)
        title_bonus = 0.0
        if job_title:
            title_skills = sum(1 for skill in self.cv_skills if skill in job_title)
            title_keywords = sum(1 for kw in self.cv_keywords if kw in job_title)
            if len(self.cv_skills) > 0:
                title_bonus += (title_skills / len(self.cv_skills)) * 0.15
            if len(self.cv_keywords) > 0:
                title_bonus += (title_keywords / len(self.cv_keywords)) * 0.10
        
        # Bonus for having any matches at all (partial credit)
        any_match_bonus = 0.0
        if len(matched_skills) > 0 or keyword_score > 0:
            any_match_bonus = 0.1  # Base bonus for any relevance
        
        # Bonus for multiple skill matches (more matches = higher score)
        skill_count_bonus = 0.0
        if len(matched_skills) >= 3:
            skill_count_bonus = 0.1
        elif len(matched_skills) >= 2:
            skill_count_bonus = 0.05
        
        # Weighted combination (improved scoring)
        # Skills are most important (50%), keywords (25%), experience (10%)
        # Plus bonuses for title matches and multiple matches
        base_score = (
            skill_score * 0.5 +
            keyword_score * 0.25 +
            experience_score * 0.1
        )
        
        # Add bonuses (can push score above 1.0, but we'll cap at 1.0)
        match_score = min(1.0, base_score + title_bonus + any_match_bonus + skill_count_bonus)
        
        # Ensure minimum score boost: if we have any matches, give at least 0.15
        if len(matched_skills) > 0 or keyword_score > 0:
            match_score = max(match_score, 0.15)
        
        return match_score, matched_skills



