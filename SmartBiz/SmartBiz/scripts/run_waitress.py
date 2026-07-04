"""Start SmartBiz with Waitress via a small runner script."""
import sys
import os
from waitress import serve

# Ensure project root is on sys.path when running from scripts/
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app

app = create_app()

if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=5000)
