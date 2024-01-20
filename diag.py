#import utils.GPIOs as GPIOs
import utils.GPIOs_Mock as GPIOs
import numpy as np
from Controller import Controller
from utils.TMC2209 import MOTOR_DIR_BACKWARD, MOTOR_DIR_FORWARD
from utils.coord_functions import coors_to_steps, calc_deltasteps
from time import sleep
import os
import signal


def getMotorPinStates():
    os.system('clear')
    print("Theta Motor PinStates: ")
    print("Enable:", GPIOs.input(GPIOs.MOTOR_THETA_ENABLE), "Dir:", GPIOs.input(GPIOs.MOTOR_THETA_DIR), "Motor relay:", GPIOs.input(GPIOs.MOTOR_THETA_RELAY))
    print("Rho Motor PinStates: ")
    print("Enable:", GPIOs.input(GPIOs.MOTOR_RHO_ENABLE), "Dir:", GPIOs.input(GPIOs.MOTOR_RHO_DIR), "Motor relay:", GPIOs.input(GPIOs.MOTOR_RHO_RELAY))

def performStepsTheta():
    print("How many steps?")
    steps = input()
    if steps.isnumeric():
        steps = int(steps)
    else:
        steps = 200

    for i in range(1, steps):
        #print("Step#",i)
        GPIOs.output(GPIOs.MOTOR_THETA_STEP, True)
        sleep(0.0005)
        GPIOs.output(GPIOs.MOTOR_THETA_STEP, False)
        sleep(0.0005)

def performStepsRho():
    print("How many steps?")
    steps = input()
    if steps.isnumeric():
        steps = int(steps)
    else:
        steps = 200

    for i in range(1, steps):
        #print("Step#",i)
        GPIOs.output(GPIOs.MOTOR_RHO_STEP, True)
        sleep(0.0005)
        GPIOs.output(GPIOs.MOTOR_RHO_STEP, False)
        sleep(0.0005)

def moveToCoordinate(controller):
    print("moving to Rho: 0.0")
    controller.run_M_Rho_Until_Switch(MOTOR_DIR_BACKWARD)

    currentCoordinates = [0.0, 0.0]
    while(True):
        try:
            print("current coordinates: ", currentCoordinates)
            print("insert new coordinates in format: <Theta> <Rho> e.g. 6.28 1.0 :")
            newCoordinatesInput = input()

            if(newCoordinatesInput == ""):
                return

            theta = float(newCoordinatesInput[:newCoordinatesInput.find(" ")])
            rho = float(newCoordinatesInput[newCoordinatesInput.find(" ")+1:])

            print("theta:", theta, "rho:", rho)
            newCoordinates = [theta, rho]
            coors = np.array([currentCoordinates, newCoordinates])
            coors_to_steps(coors)
            deltaSteps = calc_deltasteps(coors)
            steps_with_delays = controller.add_delays(deltaSteps)

            controller.draw_steps_with_delays(steps_with_delays)

            currentCoordinates = newCoordinates
        except Exception as e:
            print("invalid coordinates, exiting")
            return


def printMenu_ThetaMotor():
    while(True):
        os.system('clear')
        print("Menu Theta-Motor\r\n1) Get Pin States\r\n2) Set Enable HIGH\r\n3) Set Enable LOW\r\n4) Set Direction HIGH")
        print("5) Set Direction LOW\r\n6)Set Motor relay HIGH\r\n7) Set Motor relay LOW\r\n8) Perform steps\r\n0) Exit")
        menuChoice = input()
        
        if menuChoice == "1":
            #Get Pin States
            getMotorPinStates()
            input()
        elif menuChoice == "2":
            #Set Enable HIGH
            GPIOs.output(GPIOs.MOTOR_THETA_ENABLE, True)
            input()
        elif menuChoice == "3":
            #Set Enable LOW
            GPIOs.output(GPIOs.MOTOR_THETA_ENABLE, False)
            input()
        elif menuChoice == "4":
            #Set Direction HIGH
            GPIOs.outptu(GPIOs.MOTOR_THETA_DIR, True)
            input()
        elif menuChoice == "5":
            #Set Direction LOW
            GPIOs.output(GPIOs.MOTOR_THETA_DIR, False)
            input()
        elif menuChoice == "6":
            #Set Motor Relay HIGH
            GPIOs.output(GPIOs.MOTOR_THETA_RELAY, True)
            input()
        elif menuChoice == "7":
            #Set Motor Relay LOW
            GPIOs.output(GPIOs.MOTOR_THETA_RELAY, False)
            input()
        elif menuChoice == "8":
            performStepsTheta()
            input()
        else:
            return
        
def printMenu_RhoMotor():
    while(True):
        os.system('clear')
        print("Menu Rho-Motor\r\n1) Get Pin States\r\n2) Set Enable HIGH\r\n3) Set Enable LOW\r\n4) Set Direction HIGH")
        print("5) Set Direction LOW\r\n6) Set Motor relay HIGH\r\n7) Set Motor relay LOW\r\n8) Perform steps\r\n0) Exit")
        menuChoice = input()
        
        if menuChoice == "1":
            getMotorPinStates()
            input()
        elif menuChoice == "2":
            #Set Enable HIGH
            GPIOs.output(GPIOs.MOTOR_RHO_ENABLE, True)
            input()
        elif menuChoice == "3":
            #Set Enable LOW
            GPIOs.output(GPIOs.MOTOR_RHO_ENABLE, False)
            input()
        elif menuChoice == "4":
            #Set Direction HIGH
            GPIOs.output(GPIOs.MOTOR_RHO_DIR, True)
            input()
        elif menuChoice == "5":
            #Set Direction LOW
            GPIOs.output(GPIOs.MOTOR_RHO_DIR, False)
            input()
        elif menuChoice == "6":
            #Set Motor Relay HIGH
            GPIOs.output(GPIOs.MOTOR_RHO_RELAY, True)
            input()
        elif menuChoice == "7":
            #Set Motor Relay LOW
            GPIOs.output(GPIOs.MOTOR_RHO_RELAY, False)
            input()
        elif menuChoice == "8":
            performStepsRho()
            input()
        else:
            return
            
def printMenu_Controller():
    controller = Controller()
    while(True):
        os.system('clear')
        print("Menu\r\n1) Move Rho OUT until switch\r\n2) Move Rho IN until switch\r\n3) Move to Coord\r\n0) Exit")
        menuChoice = input()

        if menuChoice == "1":
            steps = controller.run_M_Rho_Until_Switch(MOTOR_DIR_FORWARD)
            print('#steps performed until switch: ', steps)
            input()
        elif menuChoice == "2":
            steps = controller.run_M_Rho_Until_Switch(MOTOR_DIR_BACKWARD)
            print('#steps performed until switch: ', steps)
            input()
        elif menuChoice == "3":
            moveToCoordinate(controller)
        else:
            return


def printMenu_Level0():
    while(True):
        os.system('clear')
        print("Menu\r\n1) Theta Motor\r\n2) Rho Motor\r\n3) Controller\r\n0) Exit")
        menuChoice = input()

        if menuChoice == "1":
            printMenu_ThetaMotor()
        elif menuChoice == "2":
            printMenu_RhoMotor()
        elif menuChoice == "3":
            printMenu_Controller()
        else:
            return
    
def exit():
    print("Perform steps to terminate (setEnable(HIGH), setMotorRelay(LOW))")
    GPIOs.cleanup()

def handleSigTerm(self, *args):
    exit()


def main():
    signal.signal(signal.SIGTERM, handleSigTerm)
    
    GPIOs.init()

    printMenu_Level0()
    exit()

if __name__ == "__main__":
    main()