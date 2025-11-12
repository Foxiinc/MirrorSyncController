#!/usr/bin/env python3
"""
MirrorSync Controller - Unified Application
Объединяет Backend (.NET) и GUI (PyQt6) в один exe
"""

import sys
import os
import subprocess
import time
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# Определяем базовый путь для ресурсов
if getattr(sys, 'frozen', False):
    # Если запущено из exe
    base_path = Path(sys._MEIPASS)
else:
    # Если запущено из исходников
    base_path = Path(__file__).parent

# Добавляем пути для импорта
sys.path.insert(0, str(base_path / "gui"))
from gui.enhanced_main_window import EnhancedMainWindow as MainWindow

class UnifiedApp:
    def __init__(self):
        self.backend_process = None
        self.backend_path = base_path / "backend" / "MirrorSync.Backend.exe"
        
    def start_backend(self):
        """Запускает Backend процесс"""
        try:
            if self.backend_path.exists():
                self.backend_process = subprocess.Popen(
                    [str(self.backend_path)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print(f"Backend started with PID: {self.backend_process.pid}")
                return True
            else:
                print(f"Backend not found at: {self.backend_path}")
                return False
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
        import socket
        for _ in range(timeout * 2):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 50051))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        return False
    
    def run(self):
        """Запускает приложение"""
        app = QApplication(sys.argv)
        
        # Запускаем Backend
        if not self.start_backend():
            QMessageBox.critical(None, "Error", "Failed to start backend service")
            return 1
        
        # Ждем запуска Backend
        if not self.wait_for_backend():
            QMessageBox.critical(None, "Error", "Backend service failed to start")
            self.stop_backend()
            return 1
        
        # Запускаем GUI
        window = MainWindow()
        window.show()
        
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