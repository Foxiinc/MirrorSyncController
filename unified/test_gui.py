#!/usr/bin/env python3
"""
Тестовая версия GUI с mock backend
"""

import sys
from pathlib import Path

# Добавляем пути для импорта
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "gui"))

from PyQt6.QtWidgets import QApplication
from gui.enhanced_main_window import EnhancedMainWindow
from gui.mock_backend_client import MockBackendClient

# Заменяем реальный клиент на mock
import gui.enhanced_main_window
gui.enhanced_main_window.BackendClient = MockBackendClient

def main():
    app = QApplication(sys.argv)
    
    window = EnhancedMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())