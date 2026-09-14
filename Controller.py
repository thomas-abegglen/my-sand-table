import utils.GPIOs as GPIOs
#import utils.GPIOs_Mock as GPIOs
import glob, os, math, random, time, threading
import numpy as np
import json

FILENAME_PENDING_DRAWING = "./pending_drawing.json"

CLEAR_MODE_IN_OUT = "in_out"
CLEAR_MODE_OUT_IN = "out_in"
CLEAR_MODE_OUT_OUT = "out_out"
CLEAR_MODE_IN_IN = "in_in"

class Controller():
    DIR_FORWARD = 0
    DIR_BACKWARD = 1

    SLOW_DEFAULT_SPEED = 1000 #nbr of steps per second
    SLOW_MAX_SPEED = 1500 #nbr of steps per second
    DEFAULT_SPEED = 1000 #nbr of steps per second
    MAX_SPEED = 1500 #nbr of steps per second

    CALIBRATION_NBR_THETA_STEPS = "nbr_theta_steps"
    CALIBRATION_NBR_RHO_STEPS = "nbr_rho_steps"

    clearTable = False
    pendingShutdown = False
    current_rho_step_position = 0
    current_theta_step_position = 0

    calibration = {
        CALIBRATION_NBR_THETA_STEPS: 8 * 200 * 320 / 12, #8: microsteps, 200: nbrOfSteps for the motor for one turn, 320: nbrOfTeeth of pully at axis, 12: nbrOfTeeth of pully at motor
        CALIBRATION_NBR_RHO_STEPS: 8285
    }

    def __init__(self):
        print("initializing controller...")
        GPIOs.init()
        self.enable_motor_relays()
        self.enable_motors()

    def calibrate(self, nbr_theta_steps, nbr_rho_steps):
        self.calibration[self.CALIBRATION_NBR_THETA_STEPS] = nbr_theta_steps
        self.calibration[self.CALIBRATION_NBR_RHO_STEPS] = nbr_rho_steps

    def write_calibration_file(self, file_name):
        with open(file_name, "w") as json_file:
            json.dump(self.calibration, json_file)

    def read_calibration_file(self, file_name):
        with open(file_name, "r") as json_file:
            self.calibration = json.load(json_file)

    def read_pending_drawing_file(self, file_name):
        with open(file_name, "r") as json_file:
            return json.load(json_file)      

    def step_motor(self, step_pin):
        GPIOs.output(step_pin, GPIOs.HIGH)
        time.sleep(0.0001)
        GPIOs.output(step_pin, GPIOs.LOW)

    def set_motor_direction(self, dir_pin, direction):
        if direction == Controller.DIR_FORWARD:
            GPIOs.output(dir_pin, GPIOs.LOW)
        elif direction == Controller.DIR_BACKWARD:
            GPIOs.output(dir_pin, GPIOs.HIGH)
        else:
            raise ValueError("Ungültige Richtung. Verwenden Sie 'Direction.FORWARD' oder 'Direction.BACKWARD'.")
    
    def run_M_Rho_Until_Switch(self, direction):
        if(direction == Controller.DIR_FORWARD):
            steps = self.turn_until_switch(GPIOs.MOTOR_RHO_STEP, direction, GPIOs.SWITCH_OUT, stepdelay=0.0005)
            self.current_rho_step_position = steps
            return steps            
        elif(direction == Controller.DIR_BACKWARD):
            steps = self.turn_until_switch(GPIOs.MOTOR_RHO_STEP, direction, GPIOs.SWITCH_IN, stepdelay=0.0005)
            self.current_rho_step_position = 0
            return steps
        else:
            print("Unknown direction: ", direction)

    def turn_until_switch(self, step_pin, direction, switch_pin, stepdelay=0.0005):
        self.set_motor_direction(GPIOs.MOTOR_RHO_DIR, direction)
        steps = 0
        while GPIOs.input(switch_pin) == GPIOs.HIGH:
            self.step_motor(step_pin)
            steps += 1
            time.sleep(stepdelay)
        return steps

    def get_steps(self, thr_file, reverse_file=False):
        with open(thr_file, 'r') as f:
            content = f.readlines()
            
        if reverse_file:
            content.reverse()

        lines = [line.rstrip('\n') for line in content]
        #print("lines 1:", lines[:29])

        createArray = True
        steps = None
        #print("steps 1:", steps)
        for c in lines:
            if c.startswith("//") or c.startswith("#") or len(c) == 0:
                continue

            theta = float(c[:c.find(" ")])
            rho = float(c[c.find(" ")+1:])
            #print("theta:", theta, "rho:", rho)

            #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
            theta = int(self.calibration[self.CALIBRATION_NBR_THETA_STEPS] * theta / (2 * math.pi))
            rho = int(self.calibration[self.CALIBRATION_NBR_RHO_STEPS] * rho)

                        
            if createArray:
                steps = np.array([theta, rho])
                createArray = False
            else:
                steps = np.vstack((steps, [theta, rho]))

        return steps

    def calc_deltasteps(self, deltasteps):
        #print("steps[1:]", steps[1:]) #alles aus steps ohne die erste Zeile
        #print("steps[:-1]", steps[:-1]) #alles aus steps ohne die letzte Zeile
        #print ("calc_deltasteps(", deltasteps, ")")
        return deltasteps[1:] - deltasteps[:-1]

    def coors_to_steps(self, coors):
        #print("coors_to_steps(", coors, ")")

        steps = np.copy(coors)
        for step in steps:
            #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
            step[0] = int(self.calibration[self.CALIBRATION_NBR_THETA_STEPS] * step[0] / (2 * math.pi))
            step[1] = int(self.calibration[self.CALIBRATION_NBR_RHO_STEPS] * step[1])

        return steps

    def add_delays(self, steps):
        delays = np.array([0, 0])

        for s in steps:
            defaultSpeed = self.DEFAULT_SPEED
            maxSpeed = self.MAX_SPEED
            if max(abs(s[0]), abs(s[1])) < 100:
                defaultSpeed = self.SLOW_DEFAULT_SPEED
                maxSpeed = self.SLOW_MAX_SPEED

            #print("step:", s)
            elapsed_time = abs(s[0]) / defaultSpeed #wie lange dauert theta-Verschiebung mit DEFAULT_SPEED?
            #print("elapsed_time:", elapsed_time)
            if elapsed_time > 0 and abs(s[1]) / elapsed_time <= maxSpeed: #schaffen wir die rho-Verschiebung in der gleichen Zeit mit weniger als MAX_SPEED?
                #print("Theta mit DEFAULT_SPEED")
                Theta_delay = 1 / defaultSpeed #delay für Theta mit DEFAULT_SPEED berechnen
                Rho_delay = elapsed_time / abs(s[1]) if s[1] != 0 else None #delay für Rho berechnen (sollte zwischen DEFAULT_SPEED und MAX_SPEED liegen)
                #print("Theta_delay:", Theta_delay, "Rho_delay:", Rho_delay)
            else:
                #entweder ist die theta-Verschiebung 0 oder es müsste für Rho schneller gehen als mit MAX_SPEED
                #print("Rho mit MAX_SPEED")
                min_time = abs(s[1]) / maxSpeed #wie lange dauert rho-Verschiebung mit MAX_SPEED?
                Theta_delay = min_time / abs(s[0]) if s[0] != 0 else None #delay für Rotor berechnen (sollte etwas unterhalb DEFAULT_SPEED liegen)
                Rho_delay = 1 / maxSpeed #delay für Linear mit MAX_SPEED berechnen
                #print("Rotor_delay:", Theta_delay, "Linear_delay:", Rho_delay)
    
            delays = np.vstack((delays, [Theta_delay, Rho_delay]))

        #print("delays:", delays)
        delays = delays[1:]
        steps_with_delays = np.concatenate((steps, delays), axis=1)

        return steps_with_delays

    def draw_theta_rho_file(self, thr_file, reverse_file=False):
        steps = self.get_steps(thr_file, reverse_file)
        delta_steps = self.calc_deltasteps(steps)
        
        self.draw_steps(delta_steps)

    def synchronized_move(self, delta_theta_steps, delta_rho_steps, theta_dir, rho_dir, base_delay):
        max_steps = max(abs(delta_theta_steps), abs(delta_rho_steps))
        theta_interval = max_steps / abs(delta_theta_steps) if delta_theta_steps != 0 else float('inf')
        rho_interval = max_steps / abs(delta_rho_steps) if delta_rho_steps != 0 else float('inf')

        theta_counter = 0
        rho_counter = 0

        self.set_motor_direction(GPIOs.MOTOR_THETA_DIR, theta_dir)
        self.set_motor_direction(GPIOs.MOTOR_RHO_DIR, rho_dir)

        for i in range(max_steps):
            if i / theta_interval >= theta_counter and theta_counter < abs(delta_theta_steps):
                self.step_motor(GPIOs.MOTOR_THETA_STEP)
                theta_counter += 1
            if i / rho_interval >= rho_counter and rho_counter < abs(delta_rho_steps):
                self.step_motor(GPIOs.MOTOR_RHO_STEP)
                rho_counter += 1
            time.sleep(base_delay)


    def draw_steps(self, steps):
        for i in range(len(steps)):
            #print("rotor step:", steps_with_delays[i][0], "linear step:", steps_with_delays[i][1], "rotor delay:", steps_with_delays[i][2], "linear delay:", steps_with_delays[i][3])
            
            steps_theta = steps[i][0]
            steps_rho = steps[i][1]

            if steps_theta > 0:
                theta_dir = Controller.DIR_FORWARD
            else:
                theta_dir = Controller.DIR_BACKWARD    

            if steps_rho > 0:
                rho_dir = Controller.DIR_FORWARD
            else:
                rho_dir = Controller.DIR_BACKWARD


            self.synchronized_move(steps_theta, steps_rho, theta_dir, rho_dir, base_delay=0.001)

            self.current_theta_step_position += steps_theta    
            self.current_rho_step_position += steps_rho

            if self.pendingShutdown:
                print("shutdown detected, writing pending steps to file for later drawing...")
                #dump pending steps_with_delays to file
#                with open(FILENAME_PENDING_DRAWING, "w") as json_file:
#                    json.dump(steps_with_delays[i:].to_list(), json_file, indent=6)

                print("file with pending steps dumped")
                return

    def get_current_rho_position(self, snapToInOut=False):
        threshold = self.calibration[self.CALIBRATION_NBR_RHO_STEPS]/2
        print("get_current_rho_position, current_rho_step_position:", self.current_rho_step_position, "threshold:", threshold)

        if snapToInOut:
            if self.current_rho_step_position <= threshold:
                return 0.0
            else:
                return 1.0
        else:
            #avoid a division by 0
            if self.current_rho_step_position == 0:
                return 0
            else:
                return self.current_rho_step_position / self.calibration[self.CALIBRATION_NBR_RHO_STEPS]


    def clear_table(self, clear_mode):
        print("Clearing table")

        if clear_mode == CLEAR_MODE_IN_OUT:
            print("CLEAR_MODE_IN_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0.05], [314, 1]])
        elif clear_mode == CLEAR_MODE_OUT_IN:
            print("CLEAR_MODE_OUT_IN")
            coors = np.array([[0, self.get_current_rho_position()], [0, 1], [314, 0]])
        elif clear_mode == CLEAR_MODE_OUT_OUT:
            print("CLEAR_MODE_OUT_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 1], [157, 0], [314, 1]])
        elif clear_mode == CLEAR_MODE_IN_IN:
            print("CLEAR_MODE_IN_IN")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0.05], [157, 1], [314, 0]])
        else:
            print("default: CLEAR_MODE_IN_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0.05], [314, 1]])

        print("clear_table. coors:", coors)

        steps = self.coors_to_steps(coors)
        delta_steps = self.calc_deltasteps(steps)

        self.draw_steps(delta_steps)

        print("finished clearing table")

    def NextTableButtonPressed(self):
        return GPIOs.input(GPIOs.NEXTTABLE_BUTTON)

    def enable_motors(self):
        GPIOs.output(GPIOs.MOTOR_RHO_ENABLE, GPIOs.LOW)
        GPIOs.output(GPIOs.MOTOR_THETA_ENABLE, GPIOs.LOW)

    def disable_motors(self):
        GPIOs.output(GPIOs.MOTOR_RHO_ENABLE, GPIOs.HIGH)
        GPIOs.output(GPIOs.MOTOR_THETA_ENABLE, GPIOs.HIGH)

    def enable_motor_relays(self):
        GPIOs.output(GPIOs.MOTOR_RHO_RELAY, GPIOs.LOW)
        GPIOs.output(GPIOs.MOTOR_THETA_RELAY, GPIOs.LOW)

    def disable_motor_relays(self):
        GPIOs.output(GPIOs.MOTOR_RHO_RELAY, GPIOs.HIGH)
        GPIOs.output(GPIOs.MOTOR_THETA_RELAY, GPIOs.HIGH)

    def shutdown(self):
        print("controller.shutdown")

        self.pendingShutdown = True
        
        print("stopping motors...")
        self.disable_motors()
        self.disable_motor_relays()

        print("cleanup GPIOs")
        #GPIOs.cleanup()