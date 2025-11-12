import subprocess
import tempfile
import os
from PIL import Image
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ScreenshotService(QThread):
    screenshot_ready = pyqtSignal(str, QPixmap)  # serial, pixmap
    
    def __init__(self, serial):
        super().__init__()
        self.serial = serial
        self.running = False
        
    def run(self):
        self.running = True
        # Первый скриншот сразу
        try:
            pixmap = self.take_screenshot()
            if pixmap:
                self.screenshot_ready.emit(self.serial, pixmap)
        except Exception as e:
            print(f"Initial screenshot error for {self.serial}: {e}")
        
        while self.running:
            try:
                pixmap = self.take_screenshot()
                if pixmap:
                    self.screenshot_ready.emit(self.serial, pixmap)
                time.sleep(0.01)  # Обновляем каждые 100ms для live эффекта
            except Exception as e:
                print(f"Screenshot error for {self.serial}: {e}")
                time.sleep(3)
    
    def stop(self):
        self.running = False
        self.wait()
    
    def take_screenshot(self):
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Проверяем наличие ADB
            adb_paths = [
                'C:\\platform-tools\\adb.exe',
                'C:\\Android\\Sdk\\platform-tools\\adb.exe', 
                'adb'
            ]
            adb_cmd = None
            
            for path in adb_paths:
                try:
                    result = subprocess.run([path, 'version'], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        adb_cmd = path
                        break
                except:
                    continue
            
            if not adb_cmd:
                print(f"ADB not found for device {self.serial}")
                return None
            
            # Делаем скриншот через ADB
            result = subprocess.run([
                adb_cmd, '-s', self.serial, 'shell', 'screencap', '-p'
            ], capture_output=True)
            
            if result.returncode == 0 and result.stdout:
                # Исправляем line endings для Windows
                screenshot_data = result.stdout.replace(b'\r\n', b'\n')
                with open(tmp_path, 'wb') as f:
                    f.write(screenshot_data)
                
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    pixmap = QPixmap(tmp_path)
                    os.unlink(tmp_path)
                    return pixmap
                    
        except Exception as e:
            print(f"Screenshot failed: {e}")
        
        return None