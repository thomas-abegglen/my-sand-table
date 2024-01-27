import signal, time, os.path
from Controller import Controller
from utils.TMC2209 import MOTOR_DIR_BACKWARD, MOTOR_DIR_FORWARD

FILENAME_CALIBRATION = "./calibration.json"

controller = Controller()
def main():
    try:
        signal.signal(signal.SIGINT, signal_handler)

        print("initializing controller")

        #Calibration-file exists? Yes: read it, No: --> calibrate
        if os.path.isfile(FILENAME_CALIBRATION):
            controller.read_calibration_file(FILENAME_CALIBRATION)
        else:
            #measure number of steps from Rho: 0.0 to Rho: 1.0
            controller.run_M_Rho_Until_Switch(dir=MOTOR_DIR_BACKWARD)
            nbr_steps = controller.run_M_Rho_Until_Switch(dir=MOTOR_DIR_FORWARD)
            controller.calibrate(nbr_theta_steps=16000, nbr_rho_steps=nbr_steps)
            controller.write_calibration_file(FILENAME_CALIBRATION)

        #so far, we assume: no calibration file exists, so we begin with calibration:

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
                controller.clear_table(controller.IN_OUT)

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
    running = False
    controller.shutdown()

if __name__ == '__main__':
    main()


