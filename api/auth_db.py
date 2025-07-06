#!/usr/bin/env python3
"""
Database-based authentication system for SVN Trading Bot
Handles user authentication with email verification codes
"""

import jwt
import secrets
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re
import logging
import os
from prisma import Prisma
from prisma.models import User, AuthCode, ApiKey
from prisma.enums import UserRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseAuthManager:
    """Database-based authentication manager with email verification"""
    
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'svn-trading-bot-secret-key-2025')
        self.token_expiry_hours = 24
        self.code_expiry_minutes = 10
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('SMTP_USER', '')
        self.email_password = os.environ.get('SMTP_PASSWORD', '')
        
        # Initialize Prisma client
        self.db = Prisma()
    
    async def connect(self):
        """Connect to database"""
        try:
            await self.db.connect()
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        try:
            await self.db.disconnect()
        except Exception as e:
            logger.error(f"Database disconnection error: {e}")
    
    async def send_login_code(self, email: str) -> Dict[str, Any]:
        """Send login verification code to email"""
        try:
            if not self._is_valid_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            # Check if user exists, if not create new user
            user = await self.db.user.find_unique(where={'email': email})
            
            if not user:
                # Create new user with REG_USER role
                user = await self.db.user.create(data={
                    'email': email,
                    'nickname': email.split('@')[0],
                    'role': UserRole.REG_USER
                })
            
            if not user.isActive:
                return {'success': False, 'error': 'Account is deactivated'}
            
            # Generate 6-digit verification code
            code = str(random.randint(100000, 999999))
            
            # Clean up old codes for this user
            await self.db.authcode.delete_many(where={'userId': user.id})
            
            # Create new auth code
            await self.db.authcode.create(data={
                'userId': user.id,
                'code': code,
                'expiresAt': datetime.now() + timedelta(minutes=self.code_expiry_minutes)
            })
            
            # Send email with code
            if user.role == UserRole.REG_USER:
                self._send_reg_user_email(email, code)
            else:
                self._send_lid_user_email(email, code)
            
            return {
                'success': True, 
                'message': 'Verification code sent to email',
                'is_new_user': False if user else True
            }
            
        except Exception as e:
            logger.error(f"Error sending login code: {e}")
            return {'success': False, 'error': 'Failed to send verification code'}
    
    async def verify_login_code(self, email: str, code: str) -> Dict[str, Any]:
        """Verify login code and authenticate user"""
        try:
            # Find user
            user = await self.db.user.find_unique(where={'email': email})
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Find valid auth code
            auth_code = await self.db.authcode.find_first(where={
                'userId': user.id,
                'code': code,
                'isUsed': False,
                'expiresAt': {
                    'gt': datetime.now()
                }
            })
            
            if not auth_code:
                return {'success': False, 'error': 'Invalid or expired verification code'}
            
            # Mark code as used
            await self.db.authcode.update(
                where={'id': auth_code.id},
                data={'isUsed': True}
            )
            
            # Update user login stats
            await self.db.user.update(
                where={'id': user.id},
                data={
                    'lastLogin': datetime.now(),
                    'loginCount': user.loginCount + 1
                }
            )
            
            # Generate access token
            access_token = self._generate_access_token(user.email, user.role.value)
            
            # Get or create API key for user
            api_key_record = await self.db.apikey.find_first(where={'userId': user.id, 'isActive': True})
            if not api_key_record:
                api_key = self._generate_api_key()
                api_key_record = await self.db.apikey.create(data={
                    'userId': user.id,
                    'key': api_key,
                    'name': 'Default API Key'
                })
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'role': user.role.value
                },
                'access_token': access_token,
                'api_key': api_key_record.key,
                'expires_in': self.token_expiry_hours * 3600
            }
            
        except Exception as e:
            logger.error(f"Error verifying login code: {e}")
            return {'success': False, 'error': 'Code verification failed'}
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            email = payload.get('email')
            
            user = await self.db.user.find_unique(where={'email': email})
            if not user or not user.isActive:
                return {'success': False, 'error': 'User not found or inactive'}
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'role': user.role.value
                }
            }
            
        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return {'success': False, 'error': 'Token verification failed'}
    
    async def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key"""
        try:
            # Find API key
            key_record = await self.db.apikey.find_unique(
                where={'key': api_key},
                include={'user': True}
            )
            
            if not key_record or not key_record.isActive:
                return {'success': False, 'error': 'Invalid API key'}
            
            user = key_record.user
            if not user or not user.isActive:
                return {'success': False, 'error': 'Associated user not found or inactive'}
            
            # Update last used timestamp
            await self.db.apikey.update(
                where={'id': key_record.id},
                data={'lastUsed': datetime.now()}
            )
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'role': user.role.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating API key: {e}")
            return {'success': False, 'error': 'API key authentication failed'}
    
    async def update_user_role(self, user_id: int, role: str) -> Dict[str, Any]:
        """Update user role (admin only)"""
        try:
            if role not in ['REG_USER', 'LID_USER']:
                return {'success': False, 'error': 'Invalid role'}
            
            user = await self.db.user.update(
                where={'id': user_id},
                data={'role': UserRole.REG_USER if role == 'REG_USER' else UserRole.LID_USER}
            )
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'role': user.role.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return {'success': False, 'error': 'Failed to update user role'}
    
    def _generate_access_token(self, email: str, role: str) -> str:
        """Generate JWT access token"""
        payload = {
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _generate_api_key(self) -> str:
        """Generate unique API key"""
        return secrets.token_hex(32)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _send_reg_user_email(self, email: str, code: str):
        """Send verification code email for regular users"""
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
            logger.error(f"Error sending reg user email: {e}")
    
    def _send_lid_user_email(self, email: str, code: str):
        """Send verification code email for LID users (premium users)"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email configuration not set, skipping email")
                return
            
            subject = "🔐 SVN Trading Bot - Premium Access Code"
            body = f"""
Hello Premium User,

Your exclusive verification code for SVN Trading Bot is:

{code}

This code will expire in {self.code_expiry_minutes} minutes.

As a LID user, you have access to premium features and priority support.

If you didn't request this code, please ignore this email.

Best regards,
SVN Trading Bot Premium Team
            """
            
            self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Error sending LID user email: {e}")
    
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

# Global auth manager instance
db_auth_manager = DatabaseAuthManager()

# Convenience functions
async def send_login_code(email: str) -> Dict[str, Any]:
    """Send login verification code"""
    return await db_auth_manager.send_login_code(email)

async def verify_login_code(email: str, code: str) -> Dict[str, Any]:
    """Verify login code"""
    return await db_auth_manager.verify_login_code(email, code)

async def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    return await db_auth_manager.verify_token(token)

async def authenticate_api_key(api_key: str) -> Dict[str, Any]:
    """Authenticate using API key"""
    return await db_auth_manager.authenticate_api_key(api_key)

async def update_user_role(user_id: int, role: str) -> Dict[str, Any]:
    """Update user role"""
    return await db_auth_manager.update_user_role(user_id, role)
