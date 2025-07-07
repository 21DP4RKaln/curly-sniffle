#!/usr/bin/env python3
"""
Simplified authentication system that works without database
For testing email functionality
"""

import os
import secrets
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAuthManager:
    """Simple authentication manager for testing"""
    
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY')
        self.code_expiry_minutes = 10
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('SMTP_USER')
        self.email_password = os.environ.get('SMTP_PASSWORD')
        
        # In-memory storage for verification codes
        self.verification_codes = {}
        
        logger.info("Simple auth manager initialized")
    
    def send_login_code(self, email: str) -> Dict[str, Any]:
        """Send login verification code to email"""
        try:
            if not self._is_valid_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            # Generate 6-digit verification code
            code = str(random.randint(100000, 999999))
            
            # Store code with expiry
            self.verification_codes[email] = {
                'code': code,
                'expires_at': datetime.now() + timedelta(minutes=self.code_expiry_minutes),
                'created_at': datetime.now()
            }
            
            # Send email
            self._send_verification_email(email, code)
            
            return {
                'success': True, 
                'message': 'Verification code sent to email'
            }
            
        except Exception as e:
            logger.error(f"Error sending login code: {e}")
            return {'success': False, 'error': 'Failed to send verification code'}
    
    def verify_login_code(self, email: str, code: str) -> Dict[str, Any]:
        """Verify login code"""
        try:
            if email not in self.verification_codes:
                return {'success': False, 'error': 'No verification code found for this email'}
            
            stored_data = self.verification_codes[email]
            
            # Check if code is expired
            if datetime.now() > stored_data['expires_at']:
                del self.verification_codes[email]
                return {'success': False, 'error': 'Verification code has expired'}
            
            # Check if code matches
            if stored_data['code'] != code:
                return {'success': False, 'error': 'Invalid verification code'}
            
            # Code is valid, remove it
            del self.verification_codes[email]
            
            # Generate API key for this session
            api_key = secrets.token_hex(32)
            
            return {
                'success': True,
                'user': {
                    'email': email,
                    'nickname': email.split('@')[0],
                    'role': 'REG_USER'
                },
                'access_token': 'simple_token_' + secrets.token_hex(16),
                'api_key': api_key,
                'expires_in': 24 * 3600
            }
            
        except Exception as e:
            logger.error(f"Error verifying login code: {e}")
            return {'success': False, 'error': 'Code verification failed'}
    
    def _send_verification_email(self, email: str, code: str):
        """Send verification code email"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email configuration not set, skipping email")
                return
            
            subject = "Your SVN Trading Bot Login Code"
            body = f"""
Hello,

Your verification code for SVN Trading Bot is:

{code}

This code will expire in {self.code_expiry_minutes} minutes.

If you didn't request this code, please ignore this email.

Best regards,
SVN Trading Bot Team
            """
            
            self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

# Global simple auth manager
simple_auth_manager = SimpleAuthManager()

# Convenience functions for the API
def send_login_code(email: str) -> Dict[str, Any]:
    """Send login verification code"""
    return simple_auth_manager.send_login_code(email)

def verify_login_code(email: str, code: str) -> Dict[str, Any]:
    """Verify login code"""
    return simple_auth_manager.verify_login_code(email, code)

def get_verification_code(email: str) -> str:
    """Get current verification code for testing purposes"""
    if email in simple_auth_manager.verification_codes:
        return simple_auth_manager.verification_codes[email]['code']
    return None
