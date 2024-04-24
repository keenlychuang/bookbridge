import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel

class MyApp(QWidget):
    def init(self):
        super().init()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.urlLineEdit = QLineEdit(self)
        self.urlLineEdit.setPlaceholderText('Enter Page URL')
        layout.addWidget(self.urlLineEdit)

        self.notionIDLineEdit = QLineEdit(self)
        self.notionIDLineEdit.setPlaceholderText('Enter Notion ID')
        layout.addWidget(self.notionIDLineEdit)

        self.filePathLabel = QLabel('No PDF file selected', self)
        layout.addWidget(self.filePathLabel)

        self.fileSelectButton = QPushButton('Select PDF File', self)
        self.fileSelectButton.clicked.connect(self.openFileNameDialog)
        layout.addWidget(self.fileSelectButton)

        self.setLayout(layout)
        self.setWindowTitle('PyTool Interface')
        self.setGeometry(100, 100, 300, 200)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        # Set the file dialog to open at the user's home directory with options
        fileName, _ = QFileDialog.getOpenFileName(self, "Select a PDF file", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            # Update the label text to show the path of the selected file
            self.filePathLabel.setText(fileName)