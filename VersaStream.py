from sys import platform
from subprocess import Popen, PIPE, STDOUT, run
import pdb

if __name__ == '__main__':
    pdb.set_trace()
    if platform == "linux" or platform == "linux2":
        from LSL_visualization import LSLgui

        # Instantiate instance of the LSL gui object
        app = LSLgui()
        # Start the app
        app.start()
    elif platform == "darwin":
        from LSL_visualization import LSLgui

        # Instantiate instance of the LSL gui object
        app = LSLgui()
        # Start the app
        app.start()
    elif platform == "win32":
        p = Popen(['ipython', '--pylab=qt'], stdout=PIPE,  stdin=PIPE, stderr=STDOUT)
        grep_stdout = p.communicate(input=b'from LSL_visualization import LSLgui\nimport LSLgui\napp = LSLgui('
                                          b')\napp.start()\n')[0]
