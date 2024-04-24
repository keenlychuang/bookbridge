import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox

class MyApp(QWidget):
    def __init__(self):  
        super().__init__()  
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Parent Page 
        self.urlLineEdit = QLineEdit(self)
        self.urlLineEdit.setPlaceholderText('Enter Parent Page URL')
        layout.addWidget(self.urlLineEdit)

        # Notion API Key 
        self.notionIDLineEdit = QLineEdit(self)
        self.notionIDLineEdit.setPlaceholderText('Enter Notion Key')
        layout.addWidget(self.notionIDLineEdit)

        # Select File 
        self.filePathLabel = QLabel('No PDF file selected', self)
        layout.addWidget(self.filePathLabel)

        self.fileSelectButton = QPushButton('Select PDF File', self)
        self.fileSelectButton.clicked.connect(self.openFileNameDialog)
        layout.addWidget(self.fileSelectButton)

        # Run Script 
        self.runScriptButton = QPushButton('Run Script', self)
        self.runScriptButton.clicked.connect(self.onRunScriptClicked)
        layout.addWidget(self.runScriptButton)

        self.setLayout(layout)
        self.setWindowTitle('Booklist Import Tool')
        self.setGeometry(100, 100, 300, 200)

    # checks if all fields are filled before running the booklist conversion 
    def allFieldsFilled(self):
        return all([self.urlLineEdit.text(), self.notionIDLineEdit.text(), self.filePathLabel.text() != 'No PDF file selected'])

    # GUI file select
    def openFileNameDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select a PDF file", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.filePathLabel.setText(fileName)

    # Run 
    def onRunScriptClicked(self): 
        if self.allFieldsFilled():
            print("Running Script")
        else:
            QMessageBox.warning(self, "Incomplete Fields", "Please fill in all fields before running the script.")