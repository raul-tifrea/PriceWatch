import uvicorn
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if __name__ == "__main__":
    print("Starting PriceWatch API on http://localhost:8000")
    uvicorn.run("backend.presentation.api.main:app", host="0.0.0.0", port=8000, reload=True)