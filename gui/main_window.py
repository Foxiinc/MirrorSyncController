import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                            QTextEdit, QLabel, QGroupBox, QSpinBox, QDoubleSpinBox,
                            QLineEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from backend_client import BackendClient
from typing import List

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = BackendClient()
        self.broadcast_mode = False
        self.selected_devices = []
        
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
        
        layout = QHBoxLayout(central_widget)
        
        # Left panel - Device list and controls
        left_panel = QVBoxLayout()
        
        # Device table
        device_group = QGroupBox("Connected Devices")
        device_layout = QVBoxLayout(device_group)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(5)
        self.device_table.setHorizontalHeaderLabels(
            ["Serial", "Model", "Status", "Agent", "Actions"])
        self.device_table.itemSelectionChanged.connect(self.on_device_selection_changed)
        device_layout.addWidget(self.device_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_btn)
        
        left_panel.addWidget(device_group)
        
        # Control panel
        control_group = QGroupBox("Control Panel")
        control_layout = QVBoxLayout(control_group)
        
        # Broadcast mode
        self.broadcast_checkbox = QCheckBox("Broadcast Mode (All Devices)")
        self.broadcast_checkbox.toggled.connect(self.toggle_broadcast_mode)
        control_layout.addWidget(self.broadcast_checkbox)
        
        # Tap controls
        tap_layout = QHBoxLayout()
        tap_layout.addWidget(QLabel("Tap X:"))
        self.tap_x = QDoubleSpinBox()
        self.tap_x.setRange(0, 1)
        self.tap_x.setSingleStep(0.1)
        self.tap_x.setValue(0.5)
        tap_layout.addWidget(self.tap_x)
        
        tap_layout.addWidget(QLabel("Y:"))
        self.tap_y = QDoubleSpinBox()
        self.tap_y.setRange(0, 1)
        self.tap_y.setSingleStep(0.1)
        self.tap_y.setValue(0.5)
        tap_layout.addWidget(self.tap_y)
        
        tap_btn = QPushButton("Send Tap")
        tap_btn.clicked.connect(self.send_tap)
        tap_layout.addWidget(tap_btn)
        
        control_layout.addLayout(tap_layout)
        
        # Swipe controls
        swipe_layout = QVBoxLayout()
        swipe_coords = QHBoxLayout()
        swipe_coords.addWidget(QLabel("From X:"))
        self.swipe_x1 = QDoubleSpinBox()
        self.swipe_x1.setRange(0, 1)
        self.swipe_x1.setSingleStep(0.1)
        self.swipe_x1.setValue(0.2)
        swipe_coords.addWidget(self.swipe_x1)
        
        swipe_coords.addWidget(QLabel("Y:"))
        self.swipe_y1 = QDoubleSpinBox()
        self.swipe_y1.setRange(0, 1)
        self.swipe_y1.setSingleStep(0.1)
        self.swipe_y1.setValue(0.5)
        swipe_coords.addWidget(self.swipe_y1)
        
        swipe_coords.addWidget(QLabel("To X:"))
        self.swipe_x2 = QDoubleSpinBox()
        self.swipe_x2.setRange(0, 1)
        self.swipe_x2.setSingleStep(0.1)
        self.swipe_x2.setValue(0.8)
        swipe_coords.addWidget(self.swipe_x2)
        
        swipe_coords.addWidget(QLabel("Y:"))
        self.swipe_y2 = QDoubleSpinBox()
        self.swipe_y2.setRange(0, 1)
        self.swipe_y2.setSingleStep(0.1)
        self.swipe_y2.setValue(0.5)
        swipe_coords.addWidget(self.swipe_y2)
        
        swipe_layout.addLayout(swipe_coords)
        
        swipe_duration = QHBoxLayout()
        swipe_duration.addWidget(QLabel("Duration (ms):"))
        self.swipe_duration = QSpinBox()
        self.swipe_duration.setRange(100, 5000)
        self.swipe_duration.setValue(500)
        swipe_duration.addWidget(self.swipe_duration)
        
        swipe_btn = QPushButton("Send Swipe")
        swipe_btn.clicked.connect(self.send_swipe)
        swipe_duration.addWidget(swipe_btn)
        
        swipe_layout.addLayout(swipe_duration)
        control_layout.addLayout(swipe_layout)
        
        # Text input
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        text_layout.addWidget(self.text_input)
        
        text_btn = QPushButton("Send Text")
        text_btn.clicked.connect(self.send_text)
        text_layout.addWidget(text_btn)
        
        control_layout.addLayout(text_layout)
        
        left_panel.addWidget(control_group)
        
        # Right panel - Log
        right_panel = QVBoxLayout()
        
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        right_panel.addWidget(log_group)
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(600)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(5000)  # Refresh every 5 seconds
    
    def log_message(self, message: str):
        self.log_text.append(f"[{QTimer().remainingTime()}] {message}")
    
    def refresh_devices(self):
        devices = self.client.list_devices()
        self.device_table.setRowCount(len(devices))
        
        for i, device in enumerate(devices):
            self.device_table.setItem(i, 0, QTableWidgetItem(device['serial']))
            self.device_table.setItem(i, 1, QTableWidgetItem(device['model']))
            self.device_table.setItem(i, 2, QTableWidgetItem(device['status']))
            
            agent_status = "✓" if device['agent_connected'] else "✗"
            self.device_table.setItem(i, 3, QTableWidgetItem(agent_status))
            
            # Action buttons
            mirror_btn = QPushButton("Mirror")
            mirror_btn.clicked.connect(lambda checked, s=device['serial']: self.start_mirror(s))
            self.device_table.setCellWidget(i, 4, mirror_btn)
    
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
        success = self.client.send_command("TAP", self.tap_x.value(), self.tap_y.value(), 
                                         target_devices=targets)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Tap sent to {len(targets) if targets else 'all'} devices")
    
    def send_swipe(self):
        targets = self.get_target_devices()
        success = self.client.send_command("SWIPE", 
                                         self.swipe_x1.value(), self.swipe_y1.value(),
                                         self.swipe_x2.value(), self.swipe_y2.value(),
                                         self.swipe_duration.value(),
                                         target_devices=targets)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Swipe sent to {len(targets) if targets else 'all'} devices")
    
    def send_text(self):
        text = self.text_input.text()
        if not text:
            return
            
        targets = self.get_target_devices()
        success = self.client.send_command("TEXT", text=text, target_devices=targets)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Text '{text}' sent to {len(targets) if targets else 'all'} devices")
    
    def start_mirror(self, serial: str):
        success = self.client.start_mirror(serial)
        status = "✓" if success else "✗"
        self.log_message(f"{status} Mirror started for device {serial}")
    
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