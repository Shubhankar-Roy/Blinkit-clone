"""
WSGI config for blinkitproject project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

local_site_packages = BASE_DIR / 'myserver' / 'Lib' / 'site-packages'
if local_site_packages.exists() and str(local_site_packages) not in sys.path:
    sys.path.insert(1, str(local_site_packages))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blinkitproject.settings')

application = get_wsgi_application()
