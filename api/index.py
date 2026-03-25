import sys
import os

# Make backend modules importable from the backend directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app

app = create_app()
