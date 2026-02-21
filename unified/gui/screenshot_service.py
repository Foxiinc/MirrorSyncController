import socket
import struct
import io
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import time

class ScreenshotService(QThread):
    """Живой стрим экрана с агента (порт 8080 на устройстве).
    Для нескольких устройств нужен свой port-forward на каждый (например 8080, 8081...)
    и передавать соответствующий local port в port=."""
    screenshot_ready = pyqtSignal(str, QPixmap)

    def __init__(self, serial, port=8080):
        super().__init__()
        self.serial = serial
        self.port = port
        self.running = False
        self.socket = None
        
    def run(self):
        self.running = True
        self.connect_to_agent()
        
        while self.running and self.socket:
            try:
                pixmap = self.receive_screenshot()
                if pixmap and not pixmap.isNull():
                    self.screenshot_ready.emit(self.serial, pixmap)
                time.sleep(0.016)  # ~60 FPS
            except Exception as e:
                print(f"Screenshot error for {self.serial}: {e}")
                self.reconnect()
    
    def connect_to_agent(self):
        try:
            print(f"Connecting to agent on port {self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect(('127.0.0.1', self.port))
            self.socket.settimeout(1)  # Короткий таймаут для recv
            print(f"Connected to agent on port {self.port}")
        except Exception as e:
            print(f"Failed to connect to agent on port {self.port}: {e}")
            self.socket = None
    
    def receive_screenshot(self):
        if not self.socket:
            print("No socket connection")
            return None
            
        try:
            # Читаем размер изображения (4 байта)
            size_data = self.socket.recv(4)
            if len(size_data) != 4:
                print(f"Invalid size data: {len(size_data)} bytes")
                return None
                
            size = struct.unpack('>I', size_data)[0]
            print(f"Receiving image: {size} bytes")
            
            if size > 10 * 1024 * 1024:  # Максимум 10MB
                print(f"Image too large: {size} bytes")
                return None
                
            # Читаем данные изображения
            img_data = b''
            while len(img_data) < size:
                chunk = self.socket.recv(min(size - len(img_data), 8192))
                if not chunk:
                    print("Connection closed while reading image data")
                    return None
                img_data += chunk
            
            print(f"Received complete image: {len(img_data)} bytes")
            
            # Создаем QPixmap из данных
            pixmap = QPixmap()
            if pixmap.loadFromData(img_data):
                print(f"Created pixmap: {pixmap.width()}x{pixmap.height()}")
                return pixmap
            else:
                print("Failed to create pixmap from data")
                
        except Exception as e:
            print(f"Receive error: {e}")
            
        return None
    
    def reconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"ScreenshotService reconnect close error: {e}")
        time.sleep(1)
        if self.running:
            self.connect_to_agent()
    
    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"ScreenshotService stop close error: {e}")
        self.wait()