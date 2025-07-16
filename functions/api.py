import sys
from pathlib import Path

# Add the project root to the Python path
# This allows the handler to import the 'app' module
file = Path(__file__).resolve()
root = file.parents[1]
sys.path.append(str(root))

from mangum import Mangum
from app.server import app # Import the Flask app object

# Wrap the Flask app with Mangum for AWS Lambda compatibility
handler = Mangum(app)
