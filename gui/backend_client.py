import grpc
import device_control_pb2
import device_control_pb2_grpc
from typing import List, Optional
import time

class BackendClient:
    def __init__(self, address: str = "localhost:50051", max_retries: int = 10):
        self.address = address
        self.channel = None
        self.stub = None
        self.max_retries = max_retries
    
    def connect(self) -> bool:
        """Connect to backend with retries"""
        for attempt in range(self.max_retries):
            try:
                self.channel = grpc.insecure_channel(self.address)
                self.stub = device_control_pb2_grpc.DeviceControlStub(self.channel)
                # Test connection
                self.list_devices()
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
                else:
                    print(f"Failed to connect to backend after {self.max_retries} attempts: {e}")
                    return False
        return False
    
    def disconnect(self):
        if self.channel:
            self.channel.close()
    
    def list_devices(self) -> List[dict]:
        try:
            response = self.stub.ListDevices(device_control_pb2.Empty())
            devices = []
            for device in response.devices:
                devices.append({
                    'serial': device.serial,
                    'model': device.model,
                    'status': device.status,
                    'agent_connected': device.agent_connected,
                    'port': device.port
                })
            return devices
        except Exception as e:
            print(f"Error listing devices: {e}")
            return []
    
    def send_command(self, cmd_type: str, x: float = 0, y: float = 0, 
                    end_x: float = 0, end_y: float = 0, duration_ms: int = 0,
                    text: str = "", key_code: int = 0, 
                    target_devices: Optional[List[str]] = None) -> bool:
        try:
            request = device_control_pb2.CommandRequest(
                type=cmd_type,
                x=x, y=y, end_x=end_x, end_y=end_y,
                duration_ms=duration_ms,
                text=text,
                key_code=key_code,
                target_devices=target_devices or []
            )
            response = self.stub.SendCommand(request)
            return response.success
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def get_device_status(self, serial: str) -> dict:
        try:
            request = device_control_pb2.DeviceStatusRequest(serial=serial)
            response = self.stub.GetDeviceStatus(request)
            return {
                'serial': response.serial,
                'status': response.status,
                'agent_connected': response.agent_connected,
                'last_ping_ms': response.last_ping_ms
            }
        except Exception as e:
            print(f"Error getting device status: {e}")
            return {}
    
    def start_mirror(self, serial: str) -> bool:
        try:
            request = device_control_pb2.MirrorRequest(serial=serial)
            response = self.stub.StartMirror(request)
            return response.success
        except Exception as e:
            print(f"Error starting mirror: {e}")
            return False
    
    def stop_mirror(self, serial: str) -> bool:
        try:
            request = device_control_pb2.MirrorRequest(serial=serial)
            response = self.stub.StopMirror(request)
            return response.success
        except Exception as e:
            print(f"Error stopping mirror: {e}")
            return False