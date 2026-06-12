import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()