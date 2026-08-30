#!/usr/bin/env python3
"""
KavachGrid — Unified 1-Click Application Launcher
Starts both the FastAPI Backend and Next.js Frontend together in a single command.

Usage:
    python start.py
    python start.py --no-browser   (Do not auto-open browser)
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
import argparse

# Root path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DASHBOARD_DIR = os.path.join(ROOT_DIR, "dashboard")


def print_banner():
    print("=" * 65)
    print("  ⚡ KavachGrid — Unified System Launcher")
    print("  🛡️  Zero Trust & AI-Powered Smart Grid Defense System")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Start KAVACHGRID Backend & Frontend")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    print_banner()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    processes = []

    try:
        # 1. Start FastAPI Backend (Port 8000)
        print("\n🚀 Starting FastAPI Backend Server on port 8000...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            env=env,
        )
        processes.append(("Backend", backend_proc))

        # 2. Start Next.js Frontend (Port 3000)
        print("🚀 Starting Next.js Dashboard on port 3000...")
        # On Windows, npm is npm.cmd
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=DASHBOARD_DIR,
            env=env,
        )
        processes.append(("Frontend", frontend_proc))

        print("\n" + "─" * 65)
        print("  🟢 Both services are launching!")
        print("  📊 Frontend Dashboard : http://localhost:3000")
        print("  ⚡ Backend REST API   : http://localhost:8000")
        print("  📖 API Documentation  : http://localhost:8000/docs")
        print("─" * 65)
        print("  👉 Press Ctrl+C at any time to shut down both services.\n")

        # Wait until Next.js dashboard is ready before opening browser
        if not args.no_browser:
            print("⏳ Waiting for Dashboard compiler to become ready...")
            import urllib.request
            ready = False
            for _ in range(20):
                try:
                    with urllib.request.urlopen("http://localhost:3000", timeout=2) as response:
                        if response.status == 200:
                            ready = True
                            break
                except Exception:
                    time.sleep(1)
            print("🌐 Opening http://localhost:3000 in your browser...")
            webbrowser.open("http://localhost:3000")

        # Keep parent alive and monitor child processes
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"⚠️ {name} process exited with code {ret}")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services gracefully...")
        for name, proc in processes:
            print(f"   Stopping {name}...")
            try:
                if sys.platform == "win32":
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            except Exception:
                pass
        print("✅ All services stopped. Goodbye!")


if __name__ == "__main__":
    main()
