import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                            QTextEdit, QLabel, QGroupBox, QSpinBox, QDoubleSpinBox,
                            QLineEdit, QCheckBox, QMessageBox, QTabWidget, QScrollArea)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from .backend_client import BackendClient
from .phone_screen import PhoneScreen
from typing import List

class EnhancedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = BackendClient()
        self.broadcast_mode = False
        self.selected_devices = []
        self.phone_screens = {}
        
        self.setWindowTitle("MirrorSync Controller - Enhanced")
        self.setGeometry(100, 100, 1600, 900)
        
        self.setup_ui()
        self.setup_timer()
        
        if not self.client.connect():
            QMessageBox.critical(self, "Connection Error", 
                               "Failed to connect to backend service")
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Левая панель - управление
        left_panel = self.create_control_panel()
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)
        
        # Правая панель - экраны телефонов
        right_panel = self.create_phone_screens_panel()
        
        layout.addWidget(left_widget)
        layout.addWidget(right_panel)
    
    def create_control_panel(self):
        layout = QVBoxLayout()
        
        # Список устройств
        device_group = QGroupBox("Connected Devices")
        device_layout = QVBoxLayout(device_group)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Serial", "Model", "Status", "Agent"])
        self.device_table.itemSelectionChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_table)
        
        refresh_btn = QPushButton("🔄 Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_btn)
        
        layout.addWidget(device_group)
        
        # Режим управления
        control_group = QGroupBox("Control Mode")
        control_layout = QVBoxLayout(control_group)
        
        self.broadcast_checkbox = QCheckBox("📡 Broadcast Mode (All Devices)")
        self.broadcast_checkbox.toggled.connect(self.toggle_broadcast_mode)
        control_layout.addWidget(self.broadcast_checkbox)
        
        # Быстрые команды
        quick_layout = QHBoxLayout()
        
        home_btn = QPushButton("🏠 Home")
        home_btn.clicked.connect(lambda: self.send_quick_command("HOME"))
        quick_layout.addWidget(home_btn)
        
        back_btn = QPushButton("⬅️ Back")
        back_btn.clicked.connect(lambda: self.send_quick_command("BACK"))
        quick_layout.addWidget(back_btn)
        
        menu_btn = QPushButton("☰ Menu")
        menu_btn.clicked.connect(lambda: self.send_quick_command("MENU"))
        quick_layout.addWidget(menu_btn)
        
        control_layout.addLayout(quick_layout)
        
        # Текстовый ввод
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        text_layout.addWidget(self.text_input)
        
        text_btn = QPushButton("📝 Send")
        text_btn.clicked.connect(self.send_text)
        text_layout.addWidget(text_btn)
        
        control_layout.addLayout(text_layout)
        layout.addWidget(control_group)
        
        # Лог
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        return layout
    
    def create_phone_screens_panel(self):
        # Создаем табы для экранов телефонов
        self.phone_tabs = QTabWidget()
        self.phone_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Скролл область для множественных экранов
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.phone_tabs)
        scroll_area.setWidgetResizable(True)
        
        return scroll_area
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(3000)
    
    def log_message(self, message: str):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def refresh_devices(self):
        devices = self.client.list_devices()
        self.device_table.setRowCount(len(devices))
        
        current_serials = set(self.phone_screens.keys())
        new_serials = set()
        
        for i, device in enumerate(devices):
            serial = device['serial']
            new_serials.add(serial)
            
            self.device_table.setItem(i, 0, QTableWidgetItem(serial))
            self.device_table.setItem(i, 1, QTableWidgetItem(device['model']))
            self.device_table.setItem(i, 2, QTableWidgetItem(device['status']))
            
            agent_status = "✓" if device['agent_connected'] else "✗"
            self.device_table.setItem(i, 3, QTableWidgetItem(agent_status))
            
            # Добавляем новые экраны
            if serial not in self.phone_screens:
                self.add_phone_screen(serial)
        
        # Удаляем отключенные устройства
        for serial in current_serials - new_serials:
            self.remove_phone_screen(serial)
    
    def add_phone_screen(self, serial):
        phone_screen = PhoneScreen(serial)
        phone_screen.tap_signal.connect(lambda x, y, s=serial: self.handle_screen_tap(s, x, y))
        phone_screen.swipe_signal.connect(lambda x1, y1, x2, y2, s=serial: self.handle_screen_swipe(s, x1, y1, x2, y2))
        phone_screen.key_signal.connect(lambda key_code, s=serial: self.handle_screen_key(s, key_code))
        
        self.phone_screens[serial] = phone_screen
        self.phone_tabs.addTab(phone_screen, f"📱 {serial[-4:]}")
        
        self.log_message(f"Added screen for device {serial}")
    
    def remove_phone_screen(self, serial):
        if serial in self.phone_screens:
            screen = self.phone_screens[serial]
            index = self.phone_tabs.indexOf(screen)
            if index >= 0:
                self.phone_tabs.removeTab(index)
            del self.phone_screens[serial]
            self.log_message(f"Removed screen for device {serial}")
    
    def handle_screen_tap(self, serial, x, y):
        if self.broadcast_mode:
            targets = []
        else:
            targets = [serial]
            
        success = self.client.send_command("TAP", x, y, target_devices=targets)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Tap ({x:.2f}, {y:.2f}) on {serial if not self.broadcast_mode else 'all devices'}")
    
    def handle_screen_swipe(self, serial, x1, y1, x2, y2):
        if self.broadcast_mode:
            targets = []
        else:
            targets = [serial]
            
        success = self.client.send_command("SWIPE", x1, y1, x2, y2, 500, target_devices=targets)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Swipe ({x1:.2f},{y1:.2f})→({x2:.2f},{y2:.2f}) on {serial if not self.broadcast_mode else 'all devices'}")
    
    def handle_screen_key(self, serial, key_code):
        if self.broadcast_mode:
            targets = []
        else:
            targets = [serial]
            
        success = self.client.send_command("KEY", key_code=key_code, target_devices=targets)
        status = "✓" if success else "✗"
        key_names = {3: "HOME", 4: "BACK", 82: "MENU"}
        key_name = key_names.get(key_code, f"KEY_{key_code}")
        self.log_message(f"{status} {key_name} sent to {serial if not self.broadcast_mode else 'all devices'}")
    
    def on_device_selection_changed(self):
        if not self.broadcast_mode:
            selected_rows = set(item.row() for item in self.device_table.selectedItems())
            self.selected_devices = []
            for row in selected_rows:
                serial_item = self.device_table.item(row, 0)
                if serial_item:
                    self.selected_devices.append(serial_item.text())
    
    def toggle_broadcast_mode(self, checked: bool):
        self.broadcast_mode = checked
        if checked:
            self.selected_devices = []
            self.log_message("📡 Broadcast mode enabled")
        else:
            self.log_message("📱 Individual device mode enabled")
    
    def send_quick_command(self, cmd_type):
        targets = [] if self.broadcast_mode else self.selected_devices
        
        if cmd_type == "HOME":
            success = self.client.send_command("KEY", key_code=3, target_devices=targets)
        elif cmd_type == "BACK":
            success = self.client.send_command("KEY", key_code=4, target_devices=targets)
        elif cmd_type == "MENU":
            success = self.client.send_command("KEY", key_code=82, target_devices=targets)
        else:
            return
            
        status = "✓" if success else "✗"
        device_count = len(targets) if targets else "all"
        self.log_message(f"{status} {cmd_type} sent to {device_count} devices")
    
    def send_text(self):
        text = self.text_input.text()
        if not text:
            return
            
        targets = [] if self.broadcast_mode else self.selected_devices
        success = self.client.send_command("TEXT", text=text, target_devices=targets)
        status = "✓" if success else "✗"
        device_count = len(targets) if targets else "all"
        self.log_message(f"{status} Text '{text}' sent to {device_count} devices")
        self.text_input.clear()
    
    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = EnhancedMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()