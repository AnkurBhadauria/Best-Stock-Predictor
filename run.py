"""
Runner script for OmniStock Alpha application.
Checks dependencies and launches FastAPI with Uvicorn.
"""

import sys
import os
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.8)
    print("\n[+] Opening OmniStock Alpha in your browser: http://127.0.0.1:8000")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 65)
    print("   OMNISTOCK ALPHA - MULTI-HORIZON STOCK PREDICTOR")
    print("=" * 65)
    print("[*] Starting FastAPI Server on http://127.0.0.1:8000")
    print("[*] Horizons: 1-2 Weeks (Short), 1-2 Months (Medium), 1-2 Years (Long)")
    print("[*] Press Ctrl+C to terminate.")
    print("=" * 65)
    
    # Auto launch browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

