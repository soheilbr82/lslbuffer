import sys

from lib.dummylsl import DummyLSL


def main(argv):
    # if no arguments are provided, default ia to stream 4 channels with fs=250Hz to LSL
	lsl = DummyLSL()
	lsl.create_lsl()
	lsl.begin(autostart=True)


if __name__ == '__main__':
    main(sys.argv[1:])
