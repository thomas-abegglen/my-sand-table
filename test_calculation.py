import signal, time, os.path
from Controller import Controller, FILENAME_PENDING_DRAWING
from Playlist import Playlist
from utils.TMC2209 import MOTOR_DIR_BACKWARD, MOTOR_DIR_FORWARD

running = True
controller = Controller()

def main():
    try:
        signal.signal(signal.SIGTERM, signal_handler)

        print("initializing controller")

        controller.calibrate(nbr_theta_steps=16000, nbr_rho_steps=8000)
            
        steps = controller.get_steps("./THR/dougsSpiralTriangle2.thr", False)
        deltaSteps = controller.calc_deltasteps(steps)

        write_to_file(steps, "./steps.txt")
        write_to_file(deltaSteps, "./deltaSteps.txt")


    except KeyboardInterrupt:
        print("terminating the program through KeyboardInterrupt")
        running = False
        controller.shutdown()

def write_to_file(steps, file_name):
    with open(file_name, "wt") as steps_file:
        for step in steps:
            steps_file.write(str(step[0]) + " " + str(step[1]) + "\n")

def signal_handler(sig, frame):
    print("terminating the program through SIGINT")
    global running
    running = False
    controller.shutdown()

if __name__ == '__main__':
    main()


