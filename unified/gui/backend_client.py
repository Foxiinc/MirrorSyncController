import grpc
from . import device_control_pb2
from . import device_control_pb2_grpc
from typing import List, Optional

class BackendClient:
    def __init__(self, address: str = "localhost:50051"):
        self.address = address
        self.channel = None
        self.stub = None
    
    def connect(self) -> bool:
        try:
            options = [
                ('grpc.keepalive_time_ms', 1000),
                ('grpc.keepalive_timeout_ms', 500),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 100),
                ('grpc.http2.min_ping_interval_without_data_ms', 100)
            ]
            self.channel = grpc.insecure_channel(self.address, options=options)
            self.stub = device_control_pb2_grpc.DeviceControlStub(self.channel)
            # Test connection
            self.list_devices()
            return True
        except Exception as e:
            print(f"Failed to connect to backend: {e}")
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
    
    def get_screenshot(self, serial: str) -> Optional[bytes]:
        try:
            request = device_control_pb2.ScreenshotRequest(serial=serial)
            response = self.stub.GetScreenshot(request)
            if response.success:
                return response.image_data
            return None
        except Exception as e:
            print(f"Error getting screenshot: {e}")
            return None

    def install_agent(self, serial: str) -> tuple[bool, str]:
        """Устанавливает APK агента на устройство. Возвращает (success, message)."""
        try:
            request = device_control_pb2.InstallAgentRequest(serial=serial)
            response = self.stub.InstallAgent(request)
            return response.success, response.message or ""
        except Exception as e:
            print(f"Error installing agent: {e}")
            return False, str(e)