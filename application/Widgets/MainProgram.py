from subprocess import Popen

def main():
    p = Popen('python3 /Users/jdunkley98/Downloads/MABE-Research/lslbuffer/application/Widgets/EpochVisualV2.py 3', shell=True)

if __name__ == '__main__':
    main()
    for i in range(500000):
        print(i)
