"""
Clarion Prototype Server Launcher
Run with: python run.py
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print(" Starting Clarion Industrial Product Truth Layer Server")
    print(" Dashboard: http://127.0.0.1:8000/")
    print(" API Docs:  http://127.0.0.1:8000/docs")
    print(" Review UI: http://127.0.0.1:8000/identity-review")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
