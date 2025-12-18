#!/usr/bin/env python3
"""
MirrorSync Portable Launcher
Starts Backend service and GUI in single executable
"""

import sys
import os
import subprocess
import time
import socket
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from dependency_checker import DependencyChecker
from main_window import MainWindow

class MirrorSyncLauncher:
    def __init__(self):
        self.backend_process = None
        self.backend_port = 50051
        self.app = QApplication(sys.argv)
    
    def check_dependencies(self) -> bool:
        """Check and report dependencies"""
        checker = DependencyChecker()
        status = checker.check_all()
        
        if not status['dotnet']:
            QMessageBox.critical(None, "Missing Dependency",
                               ".NET 8 Runtime is required.\n"
                               "Please install it from: https://dotnet.microsoft.com/download")
            return False
        
        if not status['adb'] or not status['scrcpy']:
            msg = "Some optional dependencies are missing:\n\n"
            if not status['adb']:
                msg += "- ADB (Android Debug Bridge)\n"
            if not status['scrcpy']:
                msg += "- scrcpy (Screen Mirroring)\n"
            msg += "\nThe application will work but some features may be unavailable."
            QMessageBox.warning(None, "Missing Optional Dependencies", msg)
        
        return True
    
    def is_port_open(self, port: int) -> bool:
        """Check if port is already in use"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    
    def find_backend_exe(self) -> Path:
        """Find backend executable"""
        # Try multiple locations
        possible_paths = [
            # PyInstaller bundled
            Path(sys.executable).parent / 'backend_bin' / 'MirrorSync.Backend.exe',
            # Development
            Path(__file__).parent.parent / 'src' / 'MirrorSync.Backend' / 'bin' / 'Release' / 'net8.0' / 'win-x64' / 'publish' / 'MirrorSync.Backend.exe',
            # Relative to executable
            Path(sys.executable).parent.parent / 'backend_bin' / 'MirrorSync.Backend.exe',
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def start_backend(self) -> bool:
        """Start backend service"""
        try:
            backend_exe = self.find_backend_exe()
            
            if not backend_exe:
                QMessageBox.critical(None, "Backend Not Found",
                                   "Backend executable not found.\n"
                                   "Please rebuild the application.")
                return False
            
            # Check if port is already in use
            if self.is_port_open(self.backend_port):
                return True
            
            # Start backend process
            self.backend_process = subprocess.Popen(
                [str(backend_exe)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Wait for backend to start
            for _ in range(50):  # 5 seconds timeout
                if self.is_port_open(self.backend_port):
                    time.sleep(0.2)
                    return True
                time.sleep(0.1)
            
            QMessageBox.critical(None, "Backend Startup Failed",
                               "Backend service failed to start within 5 seconds.")
            return False
        
        except Exception as e:
            QMessageBox.critical(None, "Backend Error", f"Failed to start backend:\n{str(e)}")
            return False
    
    def run(self):
        """Run the application"""
        try:
            # Check dependencies
            if not self.check_dependencies():
                return 1
            
            # Start backend
            if not self.start_backend():
                return 1
            
            # Show GUI
            window = MainWindow()
            window.show()
            
            # Run application
            result = self.app.exec()
            
            # Cleanup
            if self.backend_process:
                self.backend_process.terminate()
                try:
                    self.backend_process.wait(timeout=5)
                except:
                    self.backend_process.kill()
            
            return result
        
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Application error:\n{str(e)}")
            return 1

def main():
    launcher = MirrorSyncLauncher()
    sys.exit(launcher.run())

if __name__ == "__main__":
    main()