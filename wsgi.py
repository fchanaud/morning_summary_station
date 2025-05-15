import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask application
from app import app as application

# For compatibility with different WSGI servers
app = application

if __name__ == "__main__":
    application.run() 