from PyQt5 import QtWidgets

class ErrorBox(QtWidgets.QDialog):
    def __init__(self, message="Error!"):
        super(ErrorBox, self).__init__()
        self.setWindowTitle("Error Message")

        error_message = QtWidgets.QLabel(message)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(error_message)