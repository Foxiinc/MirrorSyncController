import subprocess
import sys
import os
import shutil
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.missing = []
        self.warnings = []
    
    def check_adb(self) -> bool:
        """Check if ADB is available"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def check_scrcpy(self) -> bool:
        """Check if scrcpy is available"""
        try:
            result = subprocess.run(['scrcpy', '--version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def check_dotnet(self) -> bool:
        """Check if .NET 8 runtime is available"""
        try:
            result = subprocess.run(['dotnet', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                return version.startswith('8.')
            return False
        except:
            return False
    
    def install_adb(self) -> bool:
        """Attempt to install ADB"""
        try:
            # Try to find Android SDK
            android_home = os.environ.get('ANDROID_HOME')
            if android_home:
                adb_path = Path(android_home) / 'platform-tools' / 'adb.exe'
                if adb_path.exists():
                    # Add to PATH
                    os.environ['PATH'] = f"{adb_path.parent};{os.environ['PATH']}"
                    return True
            
            # Try common locations
            common_paths = [
                Path.home() / 'AppData' / 'Local' / 'Android' / 'Sdk' / 'platform-tools',
                Path('C:\\Android\\Sdk\\platform-tools'),
            ]
            
            for path in common_paths:
                if (path / 'adb.exe').exists():
                    os.environ['PATH'] = f"{path};{os.environ['PATH']}"
                    return True
            
            return False
        except:
            return False
    
    def install_scrcpy(self) -> bool:
        """Attempt to install scrcpy via winget or chocolatey"""
        try:
            # Try winget
            result = subprocess.run(['winget', 'install', 'Genymobile.scrcpy', '-e'], 
                                  capture_output=True, timeout=60)
            if result.returncode == 0:
                return True
            
            # Try chocolatey
            result = subprocess.run(['choco', 'install', 'scrcpy', '-y'], 
                                  capture_output=True, timeout=60)
            return result.returncode == 0
        except:
            return False
    
    def check_all(self) -> dict:
        """Check all dependencies"""
        status = {
            'adb': self.check_adb(),
            'scrcpy': self.check_scrcpy(),
            'dotnet': self.check_dotnet(),
        }
        
        if not status['adb']:
            self.missing.append('ADB (Android Debug Bridge)')
            if self.install_adb():
                status['adb'] = True
        
        if not status['scrcpy']:
            self.missing.append('scrcpy (Screen Mirroring)')
            if self.install_scrcpy():
                status['scrcpy'] = True
        
        if not status['dotnet']:
            self.missing.append('.NET 8 Runtime')
        
        return status
    
    def get_report(self) -> str:
        """Get dependency report"""
        report = "Dependency Check Report:\n"
        report += "=" * 40 + "\n"
        
        status = self.check_all()
        
        for dep, available in status.items():
            symbol = "✓" if available else "✗"
            report += f"{symbol} {dep.upper()}: {'OK' if available else 'MISSING'}\n"
        
        if self.missing:
            report += "\nMissing dependencies:\n"
            for dep in self.missing:
                report += f"  - {dep}\n"
        
        return report