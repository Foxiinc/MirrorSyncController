#!/usr/bin/env python3
import subprocess
import sys
import os

def generate_protobuf():
    proto_file = "../src/MirrorSync.Protos/device_control.proto"
    
    if not os.path.exists(proto_file):
        print(f"Proto file not found: {proto_file}")
        return False
    
    try:
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path=../src/MirrorSync.Protos",
            "--python_out=.",
            "--grpc_python_out=.",
            "device_control.proto"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Protobuf files generated successfully")
            return True
        else:
            print(f"❌ Error generating protobuf: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    generate_protobuf()