from subprocess import Popen

def main():
    p = Popen('python3 /Users/jdunkley98/Downloads/MABE-Research/lslbuffer/application/Widgets/EpochVisual.py', shell=True)

if __name__ == '__main__':
    print("start")
    main()
    for i in range(500000):
        print(i)
