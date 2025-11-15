from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor
from .screenshot_service import ScreenshotService

class PhoneScreen(QWidget):
    tap_signal = pyqtSignal(float, float)
    swipe_signal = pyqtSignal(float, float, float, float)
    key_signal = pyqtSignal(int)
    
    def __init__(self, device_serial=""):
        super().__init__()
        self.device_serial = device_serial
        self.screen_width = 360
        self.screen_height = 640
        self.screenshot = None
        self.swipe_start = None
        self.swipe_end = None
        self.is_swiping = False
        self.screenshot_service = None
        
        self.setup_ui()
        self.start_screenshot_service()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        header = QLabel(f"Device: {self.device_serial}")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Экран телефона
        self.screen_frame = QFrame()
        self.screen_frame.setFixedSize(self.screen_width, self.screen_height)
        self.screen_frame.setStyleSheet("border: 2px solid black; background: #f0f0f0;")
        self.screen_frame.mousePressEvent = self.mouse_press
        self.screen_frame.mouseMoveEvent = self.mouse_move
        self.screen_frame.mouseReleaseEvent = self.mouse_release
        self.screen_frame.paintEvent = self.paint_screen
        layout.addWidget(self.screen_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Кнопки управления
        controls = QHBoxLayout()
        
        refresh_btn = QPushButton("📷 Screenshot")
        refresh_btn.clicked.connect(self.take_screenshot)
        controls.addWidget(refresh_btn)
        
        home_btn = QPushButton("🏠 Home")
        home_btn.clicked.connect(lambda: self.send_key_command(3))  # KEYCODE_HOME
        controls.addWidget(home_btn)
        
        back_btn = QPushButton("⬅️ Back")
        back_btn.clicked.connect(lambda: self.send_key_command(4))  # KEYCODE_BACK
        controls.addWidget(back_btn)
        
        menu_btn = QPushButton("☰ Menu")
        menu_btn.clicked.connect(lambda: self.send_key_command(82))  # KEYCODE_MENU
        controls.addWidget(menu_btn)
        
        layout.addLayout(controls)
        
        # Свайп подсказки
        swipe_help = QLabel("Tap - клик | Drag - свайп")
        swipe_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        swipe_help.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(swipe_help)
        
    def mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.swipe_start = event.pos()
            self.is_swiping = True
            
    def mouse_move(self, event):
        if self.is_swiping and self.swipe_start:
            self.swipe_end = event.pos()
            self.screen_frame.update()
            
    def mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.swipe_start:
            end_pos = event.pos()
            
            # Нормализуем координаты (0-1)
            start_x = self.swipe_start.x() / self.screen_width
            start_y = self.swipe_start.y() / self.screen_height
            end_x = end_pos.x() / self.screen_width
            end_y = end_pos.y() / self.screen_height
            
            # Проверяем расстояние
            distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
            
            if distance < 0.02:  # Короткое движение = тап
                self.tap_signal.emit(start_x, start_y)
            else:  # Длинное движение = свайп
                self.swipe_signal.emit(start_x, start_y, end_x, end_y)
                
            self.swipe_start = None
            self.swipe_end = None
            self.is_swiping = False
            self.screen_frame.update()
            
    def paint_screen(self, event):
        painter = QPainter(self.screen_frame)
        
        # Рисуем скриншот если есть
        if self.screenshot:
            painter.drawPixmap(0, 0, self.screenshot)
        else:
            # Рисуем заглушку
            painter.fillRect(0, 0, self.screen_width, self.screen_height, QColor(240, 240, 240))
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawText(self.screen_width//2 - 50, self.screen_height//2, "No Screenshot")
            
        # Рисуем линию свайпа
        if self.is_swiping and self.swipe_start and self.swipe_end:
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            painter.drawLine(self.swipe_start, self.swipe_end)
            
            # Рисуем стрелку
            painter.setBrush(QColor(255, 0, 0))
            arrow_size = 10
            end_x, end_y = self.swipe_end.x(), self.swipe_end.y()
            painter.drawEllipse(end_x - arrow_size//2, end_y - arrow_size//2, arrow_size, arrow_size)
            
    def start_screenshot_service(self):
        """Запускает сервис скриншотов"""
        if self.device_serial and not self.screenshot_service:
            self.screenshot_service = ScreenshotService(self.device_serial)
            self.screenshot_service.screenshot_ready.connect(self.update_screenshot)
            self.screenshot_service.start()
    
    def stop_screenshot_service(self):
        """Останавливает сервис скриншотов"""
        if self.screenshot_service:
            self.screenshot_service.stop()
            self.screenshot_service = None
    
    def update_screenshot(self, serial, pixmap):
        """Обновляет скриншот"""
        if serial == self.device_serial and pixmap:
            # Растягиваем на всё поле для нормализованных координат
            self.screenshot = pixmap.scaled(
                self.screen_width, self.screen_height, 
                Qt.AspectRatioMode.IgnoreAspectRatio,  # Полное растяжение
                Qt.TransformationMode.SmoothTransformation
            )
            self.screen_frame.update()
    
    def take_screenshot(self):
        """Принудительно делает скриншот"""
        if self.screenshot_service:
            pixmap = self.screenshot_service.take_screenshot()
            if pixmap:
                self.update_screenshot(self.device_serial, pixmap)
        
    def send_key_command(self, key_code):
        """Отправляет команду клавиши"""
        self.key_signal.emit(key_code)
    
    def set_device_serial(self, serial):
        self.stop_screenshot_service()
        self.device_serial = serial
        self.findChild(QLabel).setText(f"Device: {serial}")
        self.start_screenshot_service()
    
    def closeEvent(self, event):
        self.stop_screenshot_service()
        event.accept()