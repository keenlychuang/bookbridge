import sys
from utils import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox, QTextEdit
from PyQt5.QtCore import pyqtSignal, QObject

class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

class MyApp(QWidget):
    def __init__(self):  
        super().__init__()  
        self.initUI()

        # Redirect stdout and stderr
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = EmittingStream(textWritten=self.onWriteOutput)
        sys.stderr = EmittingStream(textWritten=self.onWriteOutput)

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

        # OpenAI API Key 
        self.openaiLineEdit = QLineEdit(self)
        self.openaiLineEdit.setPlaceholderText('Enter OpenAI Key')
        layout.addWidget(self.openaiLineEdit)

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

        # Console Output
        self.consoleOutput = QTextEdit()
        self.consoleOutput.setReadOnly(True)
        layout.addWidget(self.consoleOutput)

        self.setLayout(layout)
        self.setWindowTitle('Booklist Import Tool')
        self.setGeometry(100, 100, 300, 200)

    # checks if all fields are filled before running the booklist conversion 
    def allFieldsFilled(self):
        return all([self.urlLineEdit.text(), self.notionIDLineEdit.text(), self.openaiLineEdit.text(), self.filePathLabel.text() != 'No PDF file selected'])

    # GUI file select
    def openFileNameDialog(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select a PDF file", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if fileName:
            self.filePathLabel.setText(fileName)

    # output stream
    def onWriteOutput(self, text):
        self.consoleOutput.moveCursor(QTextCursor.End)
        self.consoleOutput.insertPlainText(text)
        QApplication.processEvents()

    # Run 
    def onRunScriptClicked(self): 
        if self.allFieldsFilled():
            parent_page = self.urlLineEdit.text() 
            notion_key = self.notionIDLineEdit.text() 
            doc_path = self.filePathLabel.text() 
            openai_key = self.openaiLineEdit.text() 
            parent_page_id = search_notion_id(parent_page)
            pdf_to_notion(doc_path, parent_page_id, notion_key)
        else:
            QMessageBox.warning(self, "Incomplete Fields", "Please fill in all fields before running the script.")

    def closeEvent(self, event):
    # Restore sys.stdout and sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        super().closeEvent(event)