"""
Alert System - Sends notifications for relevant job matches
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime


class AlertSystem:
    def __init__(self, alert_config: Dict):
        """Initialize alert system with configuration"""
        self.alert_config = alert_config
        self.email_enabled = alert_config.get('email', {}).get('enabled', False)
        self.console_enabled = alert_config.get('console', True)
        self.file_enabled = alert_config.get('file', {}).get('enabled', True)
    
    def _format_job_alert(self, job: Dict) -> str:
        """Format job information for alert"""
        match_score = job.get('match_score', 0)
        matched_skills = job.get('matched_skills', [])
        
        alert = f"""
{'='*60}
NEW JOB MATCH FOUND!
{'='*60}

Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Match Score: {match_score:.2%}
Source: {job.get('source', 'N/A')}
Date Found: {job.get('date_found', 'N/A')}

Matched Skills: {', '.join(matched_skills[:10]) if matched_skills else 'None'}

URL: {job.get('url', 'N/A')}

{'='*60}
"""
        return alert
    
    def _send_email(self, subject: str, body: str):
        """Send email alert"""
        if not self.email_enabled:
            return
        
        email_config = self.alert_config.get('email', {})
        smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        smtp_port = email_config.get('smtp_port', 587)
        sender_email = email_config.get('sender_email', '')
        sender_password = email_config.get('sender_password', '')
        recipient_email = email_config.get('recipient_email', '')
        
        if not all([sender_email, sender_password, recipient_email]):
            print("Warning: Email configuration incomplete. Skipping email alert.")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print("✓ Email alert sent successfully")
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def _save_to_file(self, jobs: List[Dict]):
        """Save job alerts to file"""
        if not self.file_enabled:
            return
        
        file_path = self.alert_config.get('file', {}).get('path', 'job_alerts.json')
        
        try:
            # Load existing alerts
            try:
                with open(file_path, 'r') as f:
                    all_alerts = json.load(f)
            except FileNotFoundError:
                all_alerts = []
            
            # Add new jobs
            all_alerts.extend(jobs)
            
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(all_alerts, f, indent=2)
            
            print(f"✓ Saved {len(jobs)} job(s) to {file_path}")
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def send_alerts(self, jobs: List[Dict]):
        """Send alerts for matched jobs"""
        if not jobs:
            return
        
        # Console output
        if self.console_enabled:
            print("\n" + "="*60)
            print(f"ALERTS - {len(jobs)} NEW JOB MATCH(ES)")
            print("="*60)
            for job in jobs:
                print(self._format_job_alert(job))
        
        # Email alerts
        if self.email_enabled and len(jobs) > 0:
            subject = f"Job Trawler: {len(jobs)} New Job Match(es) Found!"
            body = f"Found {len(jobs)} new job(s) that match your CV:\n\n"
            
            for job in jobs:
                body += self._format_job_alert(job)
            
            self._send_email(subject, body)
        
        # Save to file
        self._save_to_file(jobs)



