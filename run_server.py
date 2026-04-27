import sys, os
from dotenv import load_dotenv

# Ensure backend package is on sys.path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Load environment variables from backend/.env
load_dotenv(os.path.join(backend_path, ".env"))

from backend.main import app
import uvicorn

if __name__ == "__main__":
    # Get port from environment (Railway injects PORT automatically)
    port = int(os.environ.get("PORT", 8001))
    # Production settings: reload=False
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
