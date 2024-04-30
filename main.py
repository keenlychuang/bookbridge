from PyQt5.QtWidgets import QApplication
import sys

# If gui.py is in the same package, adjust the import statement accordingly
from bookbridge.gui import MyApp

def main():
    # Create an instance of QApplication before the QApplication window
    app = QApplication(sys.argv)
    # Create an instance of your GUI application class
    ex = MyApp()
    ex.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()