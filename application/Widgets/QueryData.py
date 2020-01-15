from PyQt5.QtWidgets import QTreeWidgetItem

class StreamData(QTreeWidgetItem):
    def __init__(self, itemLabel):
        super(StreamData, self).__init__(itemLabel)

    def addChildItem(self, treeItem):
        self.addChild(treeItem)