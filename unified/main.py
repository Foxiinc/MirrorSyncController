#!/usr/bin/env python3
"""
MirrorSync Controller - Unified Application
Объединяет Backend (.NET) и GUI (PyQt6) в один exe
"""

import sys
import os
import subprocess
import time
import socket
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

# Определяем базовый путь для ресурсов
if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

# Добавляем пути для импорта
sys.path.insert(0, str(base_path / "gui"))
from gui.enhanced_main_window import EnhancedMainWindow as MainWindow

class UnifiedApp:
    def __init__(self):
        self.backend_process = None
        self.backend_port = 50051
        
        if os.name == 'nt':
            self.backend_path = base_path / "backend" / "MirrorSync.Backend.exe"
        else:
            self.backend_path = base_path / "backend" / "MirrorSync.Backend"
    
    def is_port_open(self, port: int) -> bool:
        """Check if port is already in use"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    
    def start_backend(self):
        """Запускает Backend процесс"""
        try:
            # Check if already running
            if self.is_port_open(self.backend_port):
                print(f"Backend already running on port {self.backend_port}")
                return True
            
            if not self.backend_path.exists():
                print(f"Backend not found at: {self.backend_path}")
                return False
            
            self.backend_process = subprocess.Popen(
                [str(self.backend_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"Backend started with PID: {self.backend_process.pid}")
            return True
        except Exception as e:
            print(f"Failed to start backend: {e}")
            return False
    
    def stop_backend(self):
        """Останавливает Backend процесс"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            except Exception as e:
                print(f"Error stopping backend: {e}")
    
    def wait_for_backend(self, timeout=10):
        """Ждет запуска Backend"""
        for i in range(timeout * 10):
            if self.is_port_open(self.backend_port):
                time.sleep(0.2)
                return True
            time.sleep(0.1)
        return False
    
    def run(self):
        """Запускает приложение"""
        app = QApplication(sys.argv)
        
        # Запускаем Backend
        if not self.start_backend():
            QMessageBox.critical(None, "Error", 
                               "Failed to start backend service.\n"
                               "Please ensure MirrorSync.Backend.exe is in the backend/ folder.")
            return 1
        
        # Ждем запуска Backend
        if not self.wait_for_backend():
            QMessageBox.critical(None, "Error", 
                               "Backend service failed to start within 10 seconds.\n"
                               "Please check the logs.")
            self.stop_backend()
            return 1
        
        # Запускаем GUI
        try:
            window = MainWindow()
            window.show()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to start GUI:\n{str(e)}")
            self.stop_backend()
            return 1
        
        # Обработчик закрытия
        def cleanup():
            self.stop_backend()
        
        app.aboutToQuit.connect(cleanup)
        
        try:
            return app.exec()
        finally:
            self.stop_backend()

def main():
    app = UnifiedApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())