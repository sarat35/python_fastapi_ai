import sys
from pathlib import Path

import uvicorn

# Allow `python run.py` from the app/ directory while keeping package imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="localhost",
        port=7000,
        reload=True,
    )
