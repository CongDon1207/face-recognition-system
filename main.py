import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from UI.base_ui import BaseWindow

def main():
    app = QApplication(sys.argv)
    
    window = BaseWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
