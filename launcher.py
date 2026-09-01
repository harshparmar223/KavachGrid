#!/usr/bin/env python3
"""
KavachGrid — Unified System Launcher & Process Manager
Launches MQTT Broker, FastAPI Backend, and Next.js Frontend together seamlessly.
Can run both as a Python script and as a compiled Windows .exe binary.
"""

import io
import os
import sys
import time
import signal
import socket
import shutil
import subprocess
import webbrowser
import threading
import urllib.request
import argparse
import ctypes

# Fix Windows console encoding for Unicode/emojis safely
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Determine Root Directory (Handles both frozen .exe and regular script execution)
if getattr(sys, "frozen", False):
    # Running inside PyInstaller bundle / executable
    ROOT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DASHBOARD_DIR = os.path.join(ROOT_DIR, "dashboard")
MQTT_DIR = os.path.join(ROOT_DIR, "mqtt")

# Active subprocesses list
active_processes = []
is_shutting_down = False


def print_banner():
    print("=" * 70)
    print("  ⚡ KAVACHGRID 3.0 — UNIFIED APPLICATION LAUNCHER")
    print("  🛡️  Zero Trust & AI-Powered Smart Grid Defense System")
    print("=" * 70)


def check_port_listening(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            return s.connect_ex((host, port)) == 0
        except Exception:
            return False


def find_python_executable() -> str:
    """Locate the system python executable."""
    if not getattr(sys, "frozen", False):
        return sys.executable

    # In frozen .exe, sys.executable is KavachGrid.exe, so find python.exe on system
    python_cmd = shutil.which("python") or shutil.which("python3")
    if python_cmd:
        return python_cmd

    # Common Windows Python install locations
    common_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\python.exe"),
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Program Files\Python313\python.exe",
        r"C:\Program Files\Python312\python.exe",
        r"C:\Program Files\Python311\python.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

    return "python"


def find_npm_executable() -> str:
    """Locate npm or npm.cmd."""
    if sys.platform == "win32":
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        if npm_cmd:
            return npm_cmd
        common_npm = [
            r"C:\Program Files\nodejs\npm.cmd",
            os.path.expandvars(r"%APPDATA%\npm\npm.cmd"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\npm.cmd"),
        ]
        for n in common_npm:
            if os.path.isfile(n):
                return n
        return "npm.cmd"
    return "npm"


def find_mosquitto_executable() -> str | None:
    """Locate mosquitto executable if available."""
    mosquitto_cmd = shutil.which("mosquitto")
    if mosquitto_cmd:
        return mosquitto_cmd

    common_paths = [
        r"C:\Program Files\mosquitto\mosquitto.exe",
        r"C:\Program Files (x86)\mosquitto\mosquitto.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return None


def cleanup_all_processes():
    """Terminate all spawned child processes and their process trees cleanly."""
    global is_shutting_down
    if is_shutting_down:
        return
    is_shutting_down = True

    print("\n" + "=" * 70)
    print("🛑 Shutting down all KavachGrid services cleanly...")
    print("=" * 70)

    for name, proc in active_processes:
        if proc.poll() is None:
            print(f"   🔻 Stopping {name} (PID {proc.pid})...")
            try:
                if sys.platform == "win32":
                    subprocess.call(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    proc.terminate()
            except Exception as e:
                print(f"   ⚠️  Could not stop {name}: {e}")

    print("✅ All services stopped. Goodbye!\n")


def win_ctrl_handler(ctrl_type):
    """Windows Console Control Handler to ensure clean shutdown when console closes."""
    cleanup_all_processes()
    return True


def start_services(no_browser: bool = False):
    global active_processes

    print_banner()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"

    # 1. Check / Start MQTT Broker (Port 1883)
    print("\n🔍 Step 1/3: Checking MQTT Broker on port 1883...")
    if check_port_listening("127.0.0.1", 1883):
        print("   ✅ MQTT Broker is already active and listening on port 1883.")
    else:
        mosquitto_exe = find_mosquitto_executable()
        if mosquitto_exe:
            conf_path = os.path.join(MQTT_DIR, "local_mosquitto.conf")
            if not os.path.isfile(conf_path):
                conf_path = os.path.join(MQTT_DIR, "mosquitto.conf")

            print(f"   🚀 Launching Mosquitto MQTT Broker from: {mosquitto_exe}...")
            cmd = [mosquitto_exe]
            if os.path.isfile(conf_path):
                cmd += ["-c", conf_path]

            try:
                mqtt_proc = subprocess.Popen(
                    cmd,
                    cwd=MQTT_DIR if os.path.isdir(MQTT_DIR) else ROOT_DIR,
                    env=env,
                )
                active_processes.append(("MQTT Broker", mqtt_proc))
                time.sleep(1)
                if check_port_listening("127.0.0.1", 1883):
                    print("   ✅ MQTT Broker started successfully on port 1883.")
                else:
                    print("   ℹ️  MQTT Broker launched (initializing port 1883).")
            except Exception as e:
                print(f"   ⚠️  Failed to launch Mosquitto executable: {e}")
        else:
            print("   ⚠️  Mosquitto binary not found. (If running via Docker or cloud, ensure port 1883 is reachable).")

    # 2. Start FastAPI Backend (Port 8000)
    print("\n🔍 Step 2/3: Starting FastAPI Backend Server on port 8000...")
    python_exe = find_python_executable()
    backend_cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            env=env,
        )
        active_processes.append(("Backend Server", backend_proc))
        print(f"   ✅ FastAPI Backend process spawned (PID {backend_proc.pid}).")
    except Exception as e:
        print(f"   ❌ Failed to start Backend: {e}")
        cleanup_all_processes()
        sys.exit(1)

    # 3. Start Next.js Frontend (Port 3000)
    print("\n🔍 Step 3/3: Starting Next.js Frontend Dashboard on port 3000...")
    npm_cmd = find_npm_executable()
    try:
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=DASHBOARD_DIR,
            env=env,
            shell=(sys.platform == "win32"),
        )
        active_processes.append(("Frontend Dashboard", frontend_proc))
        print(f"   ✅ Next.js Dashboard process spawned (PID {frontend_proc.pid}).")
    except Exception as e:
        print(f"   ❌ Failed to start Frontend: {e}")
        cleanup_all_processes()
        sys.exit(1)

    # Summary Panel
    print("\n" + "=" * 70)
    print("  🚀 KAVACHGRID SERVICES ARE RUNNING!")
    print("  ------------------------------------------------------------------")
    print("  📡 MQTT Broker        : mqtt://localhost:1883")
    print("  ⚡ FastAPI Backend     : http://localhost:8000")
    print("  📖 API Documentation  : http://localhost:8000/docs")
    print("  📊 Next.js Dashboard  : http://localhost:3000")
    print("=" * 70)
    print("  👉 Press Ctrl+C at any time in this window to stop all services.\n")

    # Wait for Dashboard & Backend readiness
    def wait_and_open_browser():
        if no_browser:
            return

        print("⏳ Waiting for Next.js Dashboard to compile and become ready...")
        ready = False
        for _ in range(30):
            if is_shutting_down:
                return
            try:
                req = urllib.request.Request("http://localhost:3000", headers={"User-Agent": "KavachGrid-Launcher"})
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(1)

        if ready:
            print("🌐 Opening http://localhost:3000 in your default browser...")
            webbrowser.open("http://localhost:3000")
        else:
            print("ℹ️  Dashboard is compiling in background. You can open http://localhost:3000")

    threading.Thread(target=wait_and_open_browser, daemon=True).start()

    # Process Monitoring Loop
    try:
        while not is_shutting_down:
            for name, proc in active_processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n⚠️  {name} process exited unexpectedly with code {ret}")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_all_processes()


def main():
    parser = argparse.ArgumentParser(description="KavachGrid Unified Launcher")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser")
    args = parser.parse_args()

    # Set up signal handlers for graceful exit
    signal.signal(signal.SIGINT, lambda s, f: cleanup_all_processes())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup_all_processes())

    if sys.platform == "win32":
        try:
            handler_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)(win_ctrl_handler)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(handler_func, True)
        except Exception:
            pass

    try:
        start_services(no_browser=args.no_browser)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_all_processes()


if __name__ == "__main__":
    main()
