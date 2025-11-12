import subprocess
import sys
import os

def generate_proto():
    proto_path = "../src/MirrorSync.Protos/device_control.proto"
    output_dir = "."
    
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={os.path.dirname(proto_path)}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        proto_path
    ]
    
    subprocess.run(cmd, check=True)
    print("Proto files generated successfully")

if __name__ == "__main__":
    generate_proto()