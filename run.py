import signal 
import controller

def main():
    try:
        signal.signal(signal.SIGINT, signal_handler)

        print("initializing controller")
        controller.init()
        controller.run()
    except KeyboardInterrupt:
        print("terminating the program through KeyboardInterrupt")
        controller.shutdown()

def signal_handler(sig, frame):
    print("terminating the program through SIGINT")
    controller.shutdown()

if __name__ == '__main__':
    main()


