#!/usr/bin/env python3
"""
Authentication system for SVN Trading Bot
Handles user authentication, API key management, and access control
"""

import jwt
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'svn-trading-bot-secret-key-2025')
        self.token_expiry_hours = 24
        self.refresh_token_expiry_days = 30
        self.password_reset_expiry_hours = 1
        
        # In-memory user storage (replace with database)
        self.users = {}
        self.api_keys = {}
        self.password_reset_tokens = {}
        self.refresh_tokens = {}
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('EMAIL_USER', '')
        self.email_password = os.environ.get('EMAIL_PASSWORD', '')
        
        # Initialize with default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_email = 'admin@svn.com'
        admin_password = 'admin123'
        
        self.users[admin_email] = {
            'email': admin_email,
            'password': self._hash_password(admin_password),
            'name': 'Admin User',
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'login_count': 0
        }
        
        # Create API key for admin
        api_key = '61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f'
        self.api_keys[api_key] = {
            'user_email': admin_email,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'is_active': True
        }
    
    def register_user(self, email: str, password: str, name: str = None) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate email format
            if not self._is_valid_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            # Check if user already exists
            if email in self.users:
                return {'success': False, 'error': 'User already exists'}
            
            # Validate password strength
            if not self._is_strong_password(password):
                return {'success': False, 'error': 'Password must be at least 8 characters with uppercase, lowercase, and number'}
            
            # Create user
            user_data = {
                'email': email,
                'password': self._hash_password(password),
                'name': name or email.split('@')[0],
                'role': 'user',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'last_login': None,
                'login_count': 0
            }
            
            self.users[email] = user_data
            
            # Generate API key
            api_key = self._generate_api_key(email)
            
            # Send welcome email
            self._send_welcome_email(email, name or 'User')
            
            return {
                'success': True,
                'user': {
                    'email': email,
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'api_key': api_key
                }
            }
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {'success': False, 'error': 'Registration failed'}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            # Check if user exists
            if email not in self.users:
                return {'success': False, 'error': 'Invalid credentials'}
            
            user = self.users[email]
            
            # Check if user is active
            if not user.get('is_active', False):
                return {'success': False, 'error': 'Account is deactivated'}
            
            # Verify password
            if not self._verify_password(password, user['password']):
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Update login statistics
            user['last_login'] = datetime.now().isoformat()
            user['login_count'] = user.get('login_count', 0) + 1
            
            # Generate tokens
            access_token = self._generate_access_token(email)
            refresh_token = self._generate_refresh_token(email)
            
            return {
                'success': True,
                'user': {
                    'email': email,
                    'name': user['name'],
                    'role': user['role']
                },
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': self.token_expiry_hours * 3600
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return {'success': False, 'error': 'Authentication failed'}
    
    def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key"""
        try:
            if api_key not in self.api_keys:
                return {'success': False, 'error': 'Invalid API key'}
            
            key_data = self.api_keys[api_key]
            
            if not key_data.get('is_active', False):
                return {'success': False, 'error': 'API key is deactivated'}
            
            user_email = key_data['user_email']
            
            if user_email not in self.users:
                return {'success': False, 'error': 'Associated user not found'}
            
            user = self.users[user_email]
            
            if not user.get('is_active', False):
                return {'success': False, 'error': 'Associated user account is deactivated'}
            
            # Update last used timestamp
            key_data['last_used'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'user': {
                    'email': user_email,
                    'name': user['name'],
                    'role': user['role']
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating API key: {e}")
            return {'success': False, 'error': 'API key authentication failed'}
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            email = payload.get('email')
            
            if email not in self.users:
                return {'success': False, 'error': 'User not found'}
            
            user = self.users[email]
            
            if not user.get('is_active', False):
                return {'success': False, 'error': 'User account is deactivated'}
            
            return {
                'success': True,
                'user': {
                    'email': email,
                    'name': user['name'],
                    'role': user['role']
                }
            }
            
        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return {'success': False, 'error': 'Token verification failed'}
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            if refresh_token not in self.refresh_tokens:
                return {'success': False, 'error': 'Invalid refresh token'}
            
            token_data = self.refresh_tokens[refresh_token]
            
            # Check if token is expired
            created_at = datetime.fromisoformat(token_data['created_at'])
            if datetime.now() > created_at + timedelta(days=self.refresh_token_expiry_days):
                del self.refresh_tokens[refresh_token]
                return {'success': False, 'error': 'Refresh token has expired'}
            
            user_email = token_data['user_email']
            
            # Generate new access token
            new_access_token = self._generate_access_token(user_email)
            
            return {
                'success': True,
                'access_token': new_access_token,
                'expires_in': self.token_expiry_hours * 3600
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return {'success': False, 'error': 'Token refresh failed'}
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset"""
        try:
            if email not in self.users:
                # Don't reveal if user exists or not
                return {'success': True, 'message': 'If the email exists, a reset link has been sent'}
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            self.password_reset_tokens[reset_token] = {
                'user_email': email,
                'created_at': datetime.now().isoformat(),
                'used': False
            }
            
            # Send reset email
            self._send_password_reset_email(email, reset_token)
            
            return {'success': True, 'message': 'Password reset email sent'}
            
        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            return {'success': False, 'error': 'Password reset request failed'}
    
    def reset_password(self, reset_token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using reset token"""
        try:
            if reset_token not in self.password_reset_tokens:
                return {'success': False, 'error': 'Invalid reset token'}
            
            token_data = self.password_reset_tokens[reset_token]
            
            if token_data.get('used', False):
                return {'success': False, 'error': 'Reset token has already been used'}
            
            # Check if token is expired
            created_at = datetime.fromisoformat(token_data['created_at'])
            if datetime.now() > created_at + timedelta(hours=self.password_reset_expiry_hours):
                del self.password_reset_tokens[reset_token]
                return {'success': False, 'error': 'Reset token has expired'}
            
            # Validate new password
            if not self._is_strong_password(new_password):
                return {'success': False, 'error': 'Password must be at least 8 characters with uppercase, lowercase, and number'}
            
            # Update password
            user_email = token_data['user_email']
            self.users[user_email]['password'] = self._hash_password(new_password)
            
            # Mark token as used
            token_data['used'] = True
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return {'success': False, 'error': 'Password reset failed'}
    
    def _generate_api_key(self, user_email: str) -> str:
        """Generate API key for user"""
        api_key = secrets.token_hex(32)
        
        self.api_keys[api_key] = {
            'user_email': user_email,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'is_active': True
        }
        
        return api_key
    
    def _generate_access_token(self, email: str) -> str:
        """Generate JWT access token"""
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _generate_refresh_token(self, email: str) -> str:
        """Generate refresh token"""
        refresh_token = secrets.token_urlsafe(32)
        
        self.refresh_tokens[refresh_token] = {
            'user_email': email,
            'created_at': datetime.now().isoformat()
        }
        
        return refresh_token
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_strong_password(self, password: str) -> bool:
        """Check password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        return True
    
    def _send_welcome_email(self, email: str, name: str):
        """Send welcome email to new user"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email configuration not set, skipping welcome email")
                return
            
            subject = "Welcome to SVN Trading Bot"
            body = f"""
            Hello {name},

            Welcome to SVN Trading Bot! Your account has been created successfully.

            You can now access your dashboard at: https://your-domain.com/dashboard

            Best regards,
            SVN Trading Bot Team
            """
            
            self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    def _send_password_reset_email(self, email: str, reset_token: str):
        """Send password reset email"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email configuration not set, skipping password reset email")
                return
            
            reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
            
            subject = "Password Reset - SVN Trading Bot"
            body = f"""
            Hello,

            You requested a password reset for your SVN Trading Bot account.

            Click the link below to reset your password:
            {reset_url}

            This link will expire in 1 hour.

            If you didn't request this reset, please ignore this email.

            Best regards,
            SVN Trading Bot Team
            """
            
            self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
    
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

# Global authentication manager
auth_manager = AuthenticationManager()

# Convenience functions
def register_user(email: str, password: str, name: str = None) -> Dict[str, Any]:
    """Register a new user"""
    return auth_manager.register_user(email, password, name)

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate user"""
    return auth_manager.authenticate_user(email, password)

def authenticate_api_key(api_key: str) -> Dict[str, Any]:
    """Authenticate using API key"""
    return auth_manager.authenticate_api_key(api_key)

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    return auth_manager.verify_token(token)

def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh access token"""
    return auth_manager.refresh_access_token(refresh_token)

def request_password_reset(email: str) -> Dict[str, Any]:
    """Request password reset"""
    return auth_manager.request_password_reset(email)

def reset_password(reset_token: str, new_password: str) -> Dict[str, Any]:
    """Reset password"""
    return auth_manager.reset_password(reset_token, new_password)
