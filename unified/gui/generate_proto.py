import subprocess
import sys
import os

def generate_proto():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.normpath(os.path.join(script_dir, "..", ".."))
    proto_path = os.path.join(repo_root, "src", "MirrorSync.Protos", "device_control.proto")
    output_dir = script_dir
    
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={os.path.dirname(proto_path)}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        proto_path,
    ]
    subprocess.run(cmd, check=True, cwd=output_dir)
    print("Proto files generated successfully")

if __name__ == "__main__":
    generate_proto()