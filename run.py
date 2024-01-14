import signal 
from Controller import Controller

def main():
    try:
        signal.signal(signal.SIGINT, signal_handler)

        print("initializing controller")
        controller = Controller()

        #Calibration-file exists? Yes: read it, No: --> calibrate

        #Pending Drawing? Yes: read it, set 'clearTable' to False and continue 
        #so far, we assume: no pending drawing, so we start with a clear_table
        clearTable = True
        running = True

        #Playlist exists? Yes: read it, No: --> create it

        while running:
            print("running")

            #determine next file to draw
            thr_file = "test.thr"

            #clear table
            if clearTable:
                controller.clear_table()

            #draw next file
            #draw_theta_rho_file(thr_file)

            #temp: don't run endlessly:
            running = False

            #wait until we have to draw next file
            while running and not controller.NextTableButtonPressed:
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("terminating the program through KeyboardInterrupt")
        controller.shutdown()

def signal_handler(sig, frame):
    print("terminating the program through SIGINT")
    controller.shutdown()

if __name__ == '__main__':
    main()


