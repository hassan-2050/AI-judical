"""
WSGI entry point for PythonAnywhere deployment.
PythonAnywhere looks for a variable called `application` in the WSGI file.
"""
import sys
import os

# Add your project directory to the sys.path
# Replace 'hassan2050' with your actual PythonAnywhere username
project_home = '/home/hassan2050/AI-judical/judicary_backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

# Set environment variables (PythonAnywhere reads .env via dotenv in app.py)
os.environ['FLASK_ENV'] = 'production'

from app import app as application
