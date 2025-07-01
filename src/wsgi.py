#!/usr/bin/python3.10

"""
WSGI файл для запуска на PythonAnywhere
"""

import os
import sys
from dotenv import load_dotenv

project_home = '/home/sitvain/mysite'  
if project_home not in sys.path:
    sys.path.insert(0, project_home)

src_path = os.path.join(project_home, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

try:
    from server import app as application
except ImportError:
    from src.server import app as application

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("WSGI application initialized")
