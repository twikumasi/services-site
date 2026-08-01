# PythonAnywhere WSGI configuration — account: ahautomation
#
# HOW TO USE THIS FILE:
#   1. On PythonAnywhere, open the "Web" tab.
#   2. Click the link next to "WSGI configuration file". For your account it is:
#          /var/www/ahautomation_pythonanywhere_com_wsgi.py
#   3. Delete EVERYTHING in that file.
#   4. Copy the lines below into it.
#   5. Change ONLY the password on the ADMIN_PASSWORD line.
#   6. Save, then click the green "Reload" button on the Web tab.
#
# This file is a template — PythonAnywhere does NOT read it from your repo.

import os
import sys

# Where the site's code lives on the server.
sys.path.insert(0, "/home/ahautomation/services-site")

# Password for https://ahautomation.pythonanywhere.com/admin
# Without this the site falls back to "changeme123", which anyone could
# guess — always set your own here.
os.environ["ADMIN_PASSWORD"] = "PutYourOwnPasswordHere"

# PythonAnywhere looks for a variable named exactly "application".
from app import app as application
