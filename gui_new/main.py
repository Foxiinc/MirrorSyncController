#!/usr/bin/env python3
import sys
import time
import threading
import subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import grpc
import device_control_pb2
import device_control_pb2_grpc

class MirrorWidget(QLabel):
    clicked = pyqtSignal(float, float)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 800)
        self.setText("Device Mirror\nClick to TAP")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: white; background-color: black; border: 1px solid gray;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x() / self.width()
            y = event.position().y() / self.height()
            self.clicked.emit(x, y)

class BackendClient:
    def __init__(self):
        self.channel = None
        self.stub = None
        
    def connect(self):
        try:
            self.channel = grpc.insecure_channel('localhost:50051')
            self.stub = device_control_pb2_grpc.DeviceControlStub(self.channel)
            self.stub.ListDevices(device_control_pb2.Empty())
            return True
        except:
            return False
            
    def list_devices(self):
        try:
            response = self.stub.ListDevices(device_control_pb2.Empty())
            return [(d.serial, d.model, d.status, d.agent_connected) for d in response.devices]
        except:
            return []
            
    def send_command(self, cmd_type, x=0, y=0, end_x=0, end_y=0, text="", targets=None):
        try:
            request = device_control_pb2.CommandRequest(
                type=cmd_type, x=x, y=y, end_x=end_x, end_y=end_y, text=text
            )
            if targets:
                request.target_devices.extend(targets)
            response = self.stub.SendCommand(request)
            return response.success
        except:
            return False
            
    def start_mirror(self, serial):
        try:
            request = device_control_pb2.MirrorRequest(serial=serial)
            response = self.stub.StartMirror(request)
            return response.success
        except:
            return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MirrorSync Controller")
        self.setGeometry(100, 100, 1200, 800)
        
        self.client = BackendClient()
        self.selected_device = None
        self.broadcast_mode = False
        
        self.setup_ui()
        self.setup_timer()
        
        if self.client.connect():
            self.status_label.setText("✅ Connected to Backend")
        else:
            self.status_label.setText("❌ Backend not connected")
            
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        toolbar.addWidget(self.refresh_btn)
        
        self.broadcast_cb = QCheckBox("Broadcast Mode")
        self.broadcast_cb.toggled.connect(self.toggle_broadcast)
        toolbar.addWidget(self.broadcast_cb)
        
        self.mirror_btn = QPushButton("Start Mirror")
        self.mirror_btn.clicked.connect(self.start_mirror)
        toolbar.addWidget(self.mirror_btn)
        
        self.status_label = QLabel("Connecting...")
        toolbar.addWidget(self.status_label)
        
        toolbar.addStretch()
        main_layout.addLayout(toolbar)
        
        # Content
        content = QHBoxLayout()
        
        # Device list
        device_panel = QVBoxLayout()
        device_panel.addWidget(QLabel("Connected Devices"))
        
        self.device_list = QListWidget()
        self.device_list.setMaximumWidth(300)
        self.device_list.itemClicked.connect(self.device_selected)
        device_panel.addWidget(self.device_list)
        
        content.addLayout(device_panel)
        
        # Mirror area
        mirror_panel = QVBoxLayout()
        mirror_panel.addWidget(QLabel("Device Mirror"))
        
        self.mirror_widget = MirrorWidget()
        self.mirror_widget.clicked.connect(self.handle_tap)
        mirror_panel.addWidget(self.mirror_widget)
        
        # Controls
        controls = QHBoxLayout()
        
        self.tap_btn = QPushButton("TAP")
        self.tap_btn.clicked.connect(lambda: self.send_tap(0.5, 0.5))
        controls.addWidget(self.tap_btn)
        
        self.swipe_btn = QPushButton("SWIPE")
        self.swipe_btn.clicked.connect(self.send_swipe)
        controls.addWidget(self.swipe_btn)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text...")
        controls.addWidget(self.text_input)
        
        self.send_text_btn = QPushButton("SEND TEXT")
        self.send_text_btn.clicked.connect(self.send_text)
        controls.addWidget(self.send_text_btn)
        
        mirror_panel.addLayout(controls)
        content.addLayout(mirror_panel)
        main_layout.addLayout(content)
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(5000)
        
    def refresh_devices(self):
        devices = self.client.list_devices()
        self.device_list.clear()
        
        for serial, model, status, agent_connected in devices:
            status_icon = "🟢" if agent_connected else "🔴"
            item_text = f"{status_icon} {model}\n{serial}\n{status}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, serial)
            self.device_list.addItem(item)
            
        self.status_label.setText(f"✅ {len(devices)} devices connected")
        
    def device_selected(self, item):
        self.selected_device = item.data(Qt.ItemDataRole.UserRole)
        
    def toggle_broadcast(self, checked):
        self.broadcast_mode = checked
        
    def handle_tap(self, x, y):
        self.send_tap(x, y)
        
    def send_tap(self, x, y):
        targets = None if self.broadcast_mode else ([self.selected_device] if self.selected_device else [])
        if targets == []:
            QMessageBox.warning(self, "Warning", "No device selected!")
            return
            
        success = self.client.send_command("TAP", x, y, targets=targets)
        status = f"✅ TAP sent to {len(targets) if targets else 'all'} device(s)" if success else "❌ Failed to send TAP"
        self.status_label.setText(status)
            
    def send_swipe(self):
        targets = None if self.broadcast_mode else ([self.selected_device] if self.selected_device else [])
        if targets == []:
            QMessageBox.warning(self, "Warning", "No device selected!")
            return
            
        success = self.client.send_command("SWIPE", 0.2, 0.5, 0.8, 0.5, targets=targets)
        status = f"✅ SWIPE sent to {len(targets) if targets else 'all'} device(s)" if success else "❌ Failed to send SWIPE"
        self.status_label.setText(status)
            
    def send_text(self):
        text = self.text_input.text().strip()
        if not text:
            return
            
        targets = None if self.broadcast_mode else ([self.selected_device] if self.selected_device else [])
        if targets == []:
            QMessageBox.warning(self, "Warning", "No device selected!")
            return
            
        success = self.client.send_command("TEXT", text=text, targets=targets)
        if success:
            self.status_label.setText(f"✅ TEXT sent to {len(targets) if targets else 'all'} device(s)")
            self.text_input.clear()
        else:
            self.status_label.setText("❌ Failed to send TEXT")
            
    def start_mirror(self):
        if not self.selected_device:
            QMessageBox.warning(self, "Warning", "No device selected!")
            return
            
        success = self.client.start_mirror(self.selected_device)
        if success:
            self.status_label.setText(f"✅ Mirror started for {self.selected_device}")
            threading.Thread(target=self.run_scrcpy, daemon=True).start()
        else:
            self.status_label.setText("❌ Failed to start mirror")
            
    def run_scrcpy(self):
        try:
            subprocess.run(['scrcpy', '-s', self.selected_device, '--stay-awake'], capture_output=True)
        except:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())