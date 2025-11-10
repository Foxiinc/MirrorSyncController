#!/usr/bin/env python3
"""
MirrorSync Controller System Test Script
"""

import time
import subprocess
import sys
from pathlib import Path

def test_backend():
    """Test if backend is running"""
    try:
        import grpc
        sys.path.append('gui')
        from backend_client import BackendClient
        
        client = BackendClient()
        if client.connect():
            devices = client.list_devices()
            print(f"✓ Backend running, {len(devices)} devices connected")
            client.disconnect()
            return True
        else:
            print("✗ Backend not responding")
            return False
    except Exception as e:
        print(f"✗ Backend test failed: {e}")
        return False

def test_adb():
    """Test ADB connectivity"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = [line for line in lines if line.strip() and 'device' in line]
            print(f"✓ ADB working, {len(devices)} devices connected")
            return True
        else:
            print("✗ ADB not working")
            return False
    except FileNotFoundError:
        print("✗ ADB not found in PATH")
        return False

def test_scrcpy():
    """Test scrcpy availability"""
    try:
        result = subprocess.run(['scrcpy', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ scrcpy available")
            return True
        else:
            print("✗ scrcpy not working")
            return False
    except FileNotFoundError:
        print("✗ scrcpy not found in PATH")
        return False

def test_build_artifacts():
    """Test if build artifacts exist"""
    backend_exe = Path("src/MirrorSync.Backend/bin/Release/net8.0/win-x64/publish/MirrorSync.Backend.exe")
    gui_dist = Path("gui/dist/MirrorSyncGUI")
    android_apk = Path("android/app/build/outputs/apk/release/app-release.apk")
    
    results = []
    
    if backend_exe.exists():
        print("✓ Backend executable found")
        results.append(True)
    else:
        print("✗ Backend executable not found")
        results.append(False)
    
    if gui_dist.exists():
        print("✓ GUI distribution found")
        results.append(True)
    else:
        print("✗ GUI distribution not found")
        results.append(False)
    
    if android_apk.exists():
        print("✓ Android APK found")
        results.append(True)
    else:
        print("✗ Android APK not found")
        results.append(False)
    
    return all(results)

def main():
    print("MirrorSync Controller System Test")
    print("=" * 40)
    
    tests = [
        ("Build Artifacts", test_build_artifacts),
        ("ADB Connectivity", test_adb),
        ("scrcpy Availability", test_scrcpy),
        ("Backend Service", test_backend),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        results.append(test_func())
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"✗ {total - passed} tests failed ({passed}/{total})")
        sys.exit(1)

if __name__ == "__main__":
    main()