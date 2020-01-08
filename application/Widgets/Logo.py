from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap
import sys

class UTKLogo(QLabel):
    def __init__(self):
        super(UTKLogo, self).__init__()

        pixmap = QPixmap('/Users/jdunkley98/Downloads/MABE-Research/lslbuffer/viz/UTKlogo.png')
        self.setPixmap(pixmap)
        self.resize(pixmap.width(),pixmap.height())
