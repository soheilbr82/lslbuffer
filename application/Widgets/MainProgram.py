from subprocess import Popen

def main():
    #args = ['python', '/Users/jdunkley98/Downloads/MABE-Research/lslbuffer/application/Widgets/EpochVisual.py']
    p = Popen('python3 /Users/jdunkley98/Downloads/MABE-Research/lslbuffer/application/Widgets/EpochVisual.py 2', shell=True)

if __name__ == '__main__':
    print("start")
    main()
    for i in range(500000):
        print(i)
