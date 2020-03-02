import sys
from sys import platform
from subprocess import Popen, PIPE, STDOUT, run

from PyQt5.QtWidgets import QApplication
QApplication.setStyle('Fusion')

if __name__ == '__main__':
    if platform == "linux" or platform == "linux2":
        from application.LSL_visualization import LSLgui

        # Create Qt application
        app=QApplication(sys.argv)  
        print("Starting up App.....")

        # Instantiate instance of the LSL gui object
        gui = LSLgui()

        # Start app and ensure safe exit upon closing
        app.aboutToQuit.connect(gui.mainWindowExitHandler)
        sys.exit(app.exec_())

    elif platform == "darwin":
        from application.LSL_visualization import LSLgui

        # Create Qt application
        app=QApplication(sys.argv)  
        print("Starting up App.....")

        # Instantiate instance of the LSL gui object
        gui = LSLgui()

        # Start app and ensure safe exit upon closing
        app.aboutToQuit.connect(gui.mainWindowExitHandler)
        sys.exit(app.exec_())

    elif platform == "win32":

        from application.LSL_visualization import LSLgui

        # Create Qt application
        app=QApplication(sys.argv)  
        print("Starting up App.....")

        # Instantiate instance of the LSL gui object
        gui = LSLgui()

        # Start app and ensure safe exit upon closing
        app.aboutToQuit.connect(gui.mainWindowExitHandler)
        sys.exit(app.exec_())
        # p = Popen(['ipython', '--pylab=qt'], stdout=PIPE,  stdin=PIPE, stderr=STDOUT)
        # grep_stdout = p.communicate(input=b'from application.LSL_visualization import LSLgui\nimport sys\n'
        #                                   b'from PyQt5.QtWidgets import QApplication\nQApplication.setStyle("Fusion")\napp = QApplication(sys.argv)\n'
        #                                   b'gui=LSLgui()\napp.aboutToQuit.connect(gui.mainWindowExitHandler)\n')[0]
                                          #b'sys.exit(app.exec_())\n')[0]
        #grep_stdout = p.communicate(input=b'from application.LSL_visualization import LSLgui\nimport LSLgui\napp = LSLgui('
        #                                  b')\napp.start()\n')[0]
