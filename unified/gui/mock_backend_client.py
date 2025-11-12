from typing import List, Optional
import time
import random

class MockBackendClient:
    """Mock клиент для тестирования GUI без реального Backend"""
    
    def __init__(self, address: str = "localhost:50051"):
        self.address = address
        self.connected = False
        self.mock_devices = [
            {
                'serial': 'emulator-5554',
                'model': 'Android Emulator',
                'status': 'online',
                'agent_connected': True,
                'port': 4444
            },
            {
                'serial': 'SM-G973F',
                'model': 'Samsung Galaxy S10',
                'status': 'online', 
                'agent_connected': True,
                'port': 4445
            }
        ]
    
    def connect(self) -> bool:
        print("Mock: Connecting to backend...")
        time.sleep(0.5)  # Имитация подключения
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
        print("Mock: Disconnected from backend")
    
    def list_devices(self) -> List[dict]:
        if not self.connected:
            return []
        
        # Имитируем изменения в статусе устройств
        for device in self.mock_devices:
            if random.random() < 0.1:  # 10% шанс изменения статуса
                device['agent_connected'] = not device['agent_connected']
        
        return self.mock_devices.copy()
    
    def send_command(self, cmd_type: str, x: float = 0, y: float = 0, 
                    end_x: float = 0, end_y: float = 0, duration_ms: int = 0,
                    text: str = "", key_code: int = 0, 
                    target_devices: Optional[List[str]] = None) -> bool:
        if not self.connected:
            return False
        
        device_count = len(target_devices) if target_devices else len(self.mock_devices)
        print(f"Mock: Sending {cmd_type} to {device_count} devices")
        
        # Имитируем небольшую задержку
        time.sleep(0.1)
        
        # 95% успешных команд
        return random.random() < 0.95
    
    def get_device_status(self, serial: str) -> dict:
        for device in self.mock_devices:
            if device['serial'] == serial:
                return {
                    'serial': serial,
                    'status': device['status'],
                    'agent_connected': device['agent_connected'],
                    'last_ping_ms': int(time.time() * 1000)
                }
        return {}
    
    def start_mirror(self, serial: str) -> bool:
        print(f"Mock: Starting mirror for {serial}")
        return True
    
    def stop_mirror(self, serial: str) -> bool:
        print(f"Mock: Stopping mirror for {serial}")
        return True