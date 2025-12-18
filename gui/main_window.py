import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                            QTextEdit, QLabel, QGroupBox, QSpinBox, QDoubleSpinBox,
                            QLineEdit, QCheckBox, QMessageBox, QSlider)
from PyQt6.QtCore import QTimer, Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from backend_client import BackendClient
from typing import List

class DeviceScanner(QThread):
    devices_found = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def run(self):
        try:
            devices = self.client.list_devices()
            self.devices_found.emit(devices)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CommandSender(QThread):
    command_sent = pyqtSignal(bool, str)
    
    def __init__(self, client, cmd_type, **kwargs):
        super().__init__()
        self.client = client
        self.cmd_type = cmd_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            success = self.client.send_command(self.cmd_type, **self.kwargs)
            self.command_sent.emit(success, self.cmd_type)
        except Exception as e:
            self.command_sent.emit(False, f"{self.cmd_type} error: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = BackendClient()
        self.broadcast_mode = False
        self.selected_devices = []
        self.scanner = DeviceScanner(self.client)
        self.scanner.devices_found.connect(self.update_device_table)
        self.scanner.error_occurred.connect(self.handle_scanner_error)
        
        self.setWindowTitle("MirrorSync Controller")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_timer()
        
        if not self.client.connect():
            QMessageBox.critical(self, "Connection Error", 
                               "Failed to connect to backend service")
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Device table
        device_group = QGroupBox("Connected Devices")
        device_layout = QVBoxLayout(device_group)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(5)
        self.device_table.setHorizontalHeaderLabels(
            ["Serial", "Model", "Status", "Agent", "Mirror"])
        self.device_table.itemSelectionChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_table)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(device_group, 2)
        
        # Control panel
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_group)
        
        self.broadcast_checkbox = QCheckBox("Broadcast Mode")
        self.broadcast_checkbox.toggled.connect(self.toggle_broadcast_mode)
        control_layout.addWidget(self.broadcast_checkbox)
        
        # Tap with sliders
        tap_layout = QHBoxLayout()
        tap_layout.addWidget(QLabel("Tap X:"))
        self.tap_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.tap_x_slider.setRange(0, 100)
        self.tap_x_slider.setValue(50)
        tap_layout.addWidget(self.tap_x_slider)
        
        tap_layout.addWidget(QLabel("Y:"))
        self.tap_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.tap_y_slider.setRange(0, 100)
        self.tap_y_slider.setValue(50)
        tap_layout.addWidget(self.tap_y_slider)
        
        tap_btn = QPushButton("Tap")
        tap_btn.clicked.connect(self.send_tap)
        tap_layout.addWidget(tap_btn)
        control_layout.addLayout(tap_layout)
        
        # Swipe
        swipe_layout = QHBoxLayout()
        swipe_layout.addWidget(QLabel("Swipe X1:"))
        self.swipe_x1_slider = QSlider(Qt.Orientation.Horizontal)
        self.swipe_x1_slider.setRange(0, 100)
        self.swipe_x1_slider.setValue(20)
        swipe_layout.addWidget(self.swipe_x1_slider)
        
        swipe_layout.addWidget(QLabel("X2:"))
        self.swipe_x2_slider = QSlider(Qt.Orientation.Horizontal)
        self.swipe_x2_slider.setRange(0, 100)
        self.swipe_x2_slider.setValue(80)
        swipe_layout.addWidget(self.swipe_x2_slider)
        
        swipe_btn = QPushButton("Swipe")
        swipe_btn.clicked.connect(self.send_swipe)
        swipe_layout.addWidget(swipe_btn)
        control_layout.addLayout(swipe_layout)
        
        # Text
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        text_layout.addWidget(self.text_input)
        text_btn = QPushButton("Send")
        text_btn.clicked.connect(self.send_text)
        text_layout.addWidget(text_btn)
        control_layout.addLayout(text_layout)
        
        main_layout.addWidget(control_group, 1)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group, 1)
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(5000)  # Refresh every 5 seconds
    
    def log_message(self, message: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")
    
    def refresh_devices(self):
        if not self.scanner.isRunning():
            self.scanner.start()
    
    def update_device_table(self, devices):
        self.device_table.setRowCount(len(devices))
        
        for i, device in enumerate(devices):
            self.device_table.setItem(i, 0, QTableWidgetItem(device['serial']))
            self.device_table.setItem(i, 1, QTableWidgetItem(device['model']))
            self.device_table.setItem(i, 2, QTableWidgetItem(device['status']))
            agent_status = "✓" if device['agent_connected'] else "✗"
            self.device_table.setItem(i, 3, QTableWidgetItem(agent_status))
            
            mirror_btn = QPushButton("Mirror")
            mirror_btn.setMaximumWidth(80)
            mirror_btn.clicked.connect(lambda checked, s=device['serial']: self.start_mirror(s))
            self.device_table.setCellWidget(i, 4, mirror_btn)
    
    def handle_scanner_error(self, error):
        self.log_message(f"Scanner error: {error}")
    
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
            self.log_message("Broadcast mode enabled - commands will be sent to all devices")
        else:
            self.log_message("Broadcast mode disabled - select devices manually")
    
    def get_target_devices(self) -> List[str]:
        if self.broadcast_mode:
            return []  # Empty list means all devices
        return self.selected_devices
    
    def send_tap(self):
        targets = self.get_target_devices()
        x = self.tap_x_slider.value() / 100.0
        y = self.tap_y_slider.value() / 100.0
        
        sender = CommandSender(self.client, "TAP", x=x, y=y, target_devices=targets)
        sender.command_sent.connect(lambda success, cmd: self.log_message(
            f"{'✓' if success else '✗'} Tap ({x:.2f}, {y:.2f})"))
        sender.start()
    
    def send_swipe(self):
        targets = self.get_target_devices()
        x1 = self.swipe_x1_slider.value() / 100.0
        x2 = self.swipe_x2_slider.value() / 100.0
        
        sender = CommandSender(self.client, "SWIPE", x=x1, y=0.5, end_x=x2, end_y=0.5, 
                              duration_ms=500, target_devices=targets)
        sender.command_sent.connect(lambda success, cmd: self.log_message(
            f"{'✓' if success else '✗'} Swipe ({x1:.2f} → {x2:.2f})"))
        sender.start()
    
    def send_text(self):
        text = self.text_input.text()
        if not text:
            return
        targets = self.get_target_devices()
        
        sender = CommandSender(self.client, "TEXT", text=text, target_devices=targets)
        sender.command_sent.connect(lambda success, cmd: self.log_message(
            f"{'✓' if success else '✗'} Text: {text}"))
        sender.start()
        self.text_input.clear()
    
    def start_mirror(self, serial: str):
        success = self.client.start_mirror(serial)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Mirror: {serial}")
    
    def closeEvent(self, event):
        self.client.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()