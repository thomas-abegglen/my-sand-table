import signal, time, os.path
from Controller import Controller, FILENAME_PENDING_DRAWING
from Playlist import Playlist
from utils.TMC2209 import MOTOR_DIR_BACKWARD, MOTOR_DIR_FORWARD

FILENAME_CALIBRATION = "/home/sisyphus/my-sand-table/calibration.json"

controller = Controller()
playlist = Playlist()
def main():
    try:
        signal.signal(signal.SIGTERM, signal_handler)

        print("initializing controller")

        #Calibration-file exists? Yes: read it, No: --> calibrate
        if os.path.isfile(FILENAME_CALIBRATION):
            print("calibration file exists, reading it...")
            controller.read_calibration_file(FILENAME_CALIBRATION)
            print("calibration file read")
        else:
            print("no calibration file exists. Perform calibration...")
            #measure number of steps from Rho: 0.0 to Rho: 1.0
            #first step: move to Rho: 0.0
            controller.run_M_Rho_Until_Switch(dir=MOTOR_DIR_BACKWARD)

            #second step: measure steps to Rho: 1.0
            nbr_steps = controller.run_M_Rho_Until_Switch(dir=MOTOR_DIR_FORWARD)

            #safety margin: 40 steps
            nbr_steps -= 40

            controller.calibrate(nbr_theta_steps=16000, nbr_rho_steps=nbr_steps)
            
            #third step: write calibration file
            controller.write_calibration_file(FILENAME_CALIBRATION)
            print("calibration finished")

        #Pending Drawing? Yes: read it, set 'clearTable' to False and continue 
        if os.path.isfile(FILENAME_PENDING_DRAWING):
            print("pending drawing detected. reading pending steps from file...")
            pending_steps_with_delays = controller.read_pending_drawing_file(FILENAME_PENDING_DRAWING)
            os.remove(FILENAME_PENDING_DRAWING)
            print("drawing pending steps")
            controller.draw_steps_with_delays(pending_steps_with_delays)
            print("finished drawing pending steps")
            clearTable = False
            running = True
        else:
            clearTable = True
            running = True

            #to start, make sure we're at Rho: 0.0
            controller.run_M_Rho_Until_Switch(dir=MOTOR_DIR_BACKWARD)

        while running:
            print("running, clearTable:", clearTable)

            #clear table
            if clearTable:
                clear_mode = playlist.get_clear_mode(controller.get_current_rho_position())
                controller.clear_table(clear_mode=clear_mode[0])
                reverseNextFile = clear_mode[1]

            print("drawing: ", playlist.get_current_file(), "reverseNextFile: ", reverseNextFile)
            controller.draw_theta_rho_file(playlist.get_current_file(), reverseNextFile)

            #once we have drawn a table, we will clear before drawing the next table
            clearTable = True

            print("checking if we should continue drawing...")
            print("debug: running:", running, "NextTableButtonPressed:", controller.NextTableButtonPressed())

            #wait until we have to draw next file
            while running and not controller.NextTableButtonPressed():
                print("NextTableButtonPressed is false, sleeping...")                
                time.sleep(0.5)

            print("drawing next table")
            playlist.move_to_next_file()    
        
        #if we are here, we left the endless-loop
        #shutdown controller
        controller.shutdown()


    except KeyboardInterrupt:
        print("terminating the program through KeyboardInterrupt")
        running = False
        controller.shutdown()



def signal_handler(sig, frame):
    print("terminating the program through SIGINT")
    running = False
    controller.shutdown()

if __name__ == '__main__':
    main()


