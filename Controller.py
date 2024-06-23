import utils.GPIOs as GPIOs
#import utils.GPIOs_Mock as GPIOs
import glob, os, math, random, time, threading, logging
import numpy as np
import json
from utils.TMC2209 import TMC2209, MOTOR_DIR_BACKWARD, MOTOR_DIR_FORWARD

FILENAME_PENDING_DRAWING = "./pending_drawing.json"

CLEAR_MODE_IN_OUT = "in_out"
CLEAR_MODE_OUT_IN = "out_in"
CLEAR_MODE_OUT_OUT = "out_out"
CLEAR_MODE_IN_IN = "in_in"

class Controller():

    DEFAULT_SPEED = 1000 #nbr of steps per second
    MAX_SPEED = 1500 #nbr of steps per second

    CALIBRATION_NBR_THETA_STEPS = "nbr_theta_steps"
    CALIBRATION_NBR_RHO_STEPS = "nbr_rho_steps"

    logger = logging.getLogger(__name__)

    M_Theta = TMC2209(dir_pin=GPIOs.MOTOR_THETA_DIR, step_pin=GPIOs.MOTOR_THETA_STEP, enable_pin=GPIOs.MOTOR_THETA_ENABLE, limit_switches=None)
    M_Rho = TMC2209(dir_pin=GPIOs.MOTOR_RHO_DIR, step_pin=GPIOs.MOTOR_RHO_STEP, enable_pin=GPIOs.MOTOR_RHO_ENABLE, limit_switches=[GPIOs.SWITCH_OUT, GPIOs.SWITCH_IN])
    clearTable = False
    pendingShutdown = False
    current_rho_step_position = 0

    calibration = {
        CALIBRATION_NBR_THETA_STEPS: 200 * 10 * 8,
        CALIBRATION_NBR_RHO_STEPS: 8285
    }

    def __init__(self):
        self.logger.info("initializing controller...")
        GPIOs.init()

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

    def run_M_Theta(self, steps, delay):
        if steps != 0 and delay >= 0:
            if steps > 0:
                self.M_Theta.turn_steps(Dir=MOTOR_DIR_FORWARD, steps=abs(steps), stepdelay=delay)
            else:
                self.M_Theta.turn_steps(Dir=MOTOR_DIR_BACKWARD, steps=abs(steps), stepdelay=delay)

        self.M_Theta.stop()
        self.M_Theta.running = False

        self.logger.debug("M_Theta done!")

    def run_M_Rho(self, steps, delay):
        if steps != 0 and delay >= 0:
            if steps > 0:
                self.M_Rho.turn_steps(Dir=MOTOR_DIR_FORWARD, steps=abs(steps), stepdelay=delay)
            else:
                self.M_Rho.turn_steps(Dir=MOTOR_DIR_BACKWARD, steps=abs(steps), stepdelay=delay)

        self.M_Rho.stop()
        self.M_Rho.running = False
        self.current_rho_step_position += steps

        self.logger.debug("M_Rho done!")
    
    def run_M_Rho_Until_Switch(self, dir):
        if(dir == MOTOR_DIR_FORWARD):
            steps = self.M_Rho.turn_until_switch(Dir=dir, limit_switch=GPIOs.SWITCH_OUT, stepdelay=0.0005)
            self.current_rho_step_position = steps
            return steps
        
        elif(dir == MOTOR_DIR_BACKWARD):
            steps = self.M_Rho.turn_until_switch(Dir=dir, limit_switch=GPIOs.SWITCH_IN, stepdelay=0.0005)
            self.current_rho_step_position = 0
            return steps
        else:
            self.logger.info("Unknown direction: %s", dir)

    def get_steps(self, thr_file, reverse_file=False):
        with open(thr_file, 'r') as f:
            content = f.readlines()
            
        if reverse_file:
            content.reverse()

        lines = [line.rstrip('\n') for line in content]
        self.logger.debug("lines 1: %s", lines[:29])

        createArray = True
        steps = None
        self.logger.debug("steps 1: %s", steps)
        for c in lines:
            if c.startswith("//") or c.startswith("#") or len(c) == 0:
                continue

            theta = float(c[:c.find(" ")])
            rho = float(c[c.find(" ")+1:])
            self.logger.debug("theta: %s, rho: %s", theta, rho)

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
        self.logger.debug("deltasteps[1:] %s", deltasteps[1:]) #alles aus steps ohne die erste Zeile
        self.logger.debug("deltasteps[:-1] %s", deltasteps[:-1]) #alles aus steps ohne die letzte Zeile
        self.logger.debug("calc_deltasteps(%s)", deltasteps)
        return deltasteps[1:] - deltasteps[:-1]

    def coors_to_steps(self, coors):
        self.logger.debug("coors_to_steps(%s)", coors)

        steps = np.copy(coors)
        for step in steps:
            #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
            step[0] = int(self.calibration[self.CALIBRATION_NBR_THETA_STEPS] * step[0] / (2 * math.pi))
            step[1] = int(self.calibration[self.CALIBRATION_NBR_RHO_STEPS] * step[1])

        return steps

    def add_delays(self, steps):
        delays = np.array([0, 0])
        for s in steps:
            self.logger.debug("step: %s", s)
            elapsed_time = abs(s[0]) / self.DEFAULT_SPEED #wie lange dauert theta-Verschiebung mit DEFAULT_SPEED?
            self.logger.debug("elapsed_time: %s", elapsed_time)
            if elapsed_time > 0 and abs(s[1]) / elapsed_time <= self.MAX_SPEED: #schaffen wir die rho-Verschiebung in der gleichen Zeit mit weniger als MAX_SPEED?
                self.logger.debug("Theta mit DEFAULT_SPEED")
                Theta_delay = 1 / self.DEFAULT_SPEED #delay für Theta mit DEFAULT_SPEED berechnen
                Rho_delay = elapsed_time / abs(s[1]) if s[1] != 0 else None #delay für Rho berechnen (sollte zwischen DEFAULT_SPEED und MAX_SPEED liegen)
                self.logger.debug("Theta_delay: %s, Rho_delay: %s", Theta_delay, Rho_delay)
            else:
                #entweder ist die theta-Verschiebung 0 oder es müsste für Rho schneller gehen als mit MAX_SPEED
                self.logger.debug("Rho mit MAX_SPEED")
                min_time = abs(s[1]) / self.MAX_SPEED #wie lange dauert rho-Verschiebung mit MAX_SPEED?
                Theta_delay = min_time / abs(s[0]) if s[0] != 0 else None #delay für Rotor berechnen (sollte etwas unterhalb DEFAULT_SPEED liegen)
                Rho_delay = 1 / self.MAX_SPEED #delay für Linear mit MAX_SPEED berechnen
                self.logger.debug("Theta_delay: %s, Rho_delay: %s", Theta_delay, Rho_delay)
    
            delays = np.vstack((delays, [Theta_delay, Rho_delay]))

        self.logger.debug("delays: %s", delays)
        delays = delays[1:]
        steps_with_delays = np.concatenate((steps, delays), axis=1)

        return steps_with_delays

    def draw_theta_rho_file(self, thr_file, reverse_file=False):
        steps = self.get_steps(thr_file, reverse_file)
        steps = self.calc_deltasteps(steps)
        steps_with_delays = self.add_delays(steps)

        self.draw_steps_with_delays(steps_with_delays)

    def draw_steps_with_delays(self, steps_with_delays):
        for i in range(len(steps_with_delays)):
            self.logger.debug("theta step: %s, rho_step: %s, theta_delay: %s, rho_delay: %s", steps_with_delays[i][0], steps_with_delays[i][1], steps_with_delays[i][2], steps_with_delays[i][3])
            
            #pass values to M_Theta/M_Rho and create threads
            M_Theta_Thread = threading.Thread(target=self.run_M_Theta, args=(steps_with_delays[i][0], steps_with_delays[i][2],))
            M_Rho_Thread = threading.Thread(target=self.run_M_Rho, args=(steps_with_delays[i][1], steps_with_delays[i][3],))

            #start threads
            self.M_Theta.running = True
            self.M_Rho.running = True
            M_Theta_Thread.start()
            M_Rho_Thread.start()

            #wait for threads to finish
            M_Theta_Thread.join()
            M_Rho_Thread.join()

            if self.pendingShutdown:
                self.logger.info("shutdown detected, writing pending steps to file for later drawing...")
                #dump pending steps_with_delays to file
#                with open(FILENAME_PENDING_DRAWING, "w") as json_file:
#                    json.dump(steps_with_delays[i:].to_list(), json_file, indent=6)

                self.logger.ubfi("file with pending steps dumped")
                return

    def get_current_rho_position(self, snapToInOut=False):
        threshold = self.calibration[self.CALIBRATION_NBR_RHO_STEPS]/2
        self.logger.debug("get_current_rho_position, current_rho_step_position: %s, threshold: %s", self.current_rho_step_position, threshold)

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


    def stop_motors(self):
        self.M_Theta.running = False
        self.M_Rho.running = False
        self.M_Theta.stop()
        self.M_Rho.stop()
        self.logger.info("\n---------- Motors Stopped! ----------")

    def clear_table(self, clear_mode):
        self.logger.info("Clearing table")

        if clear_mode == CLEAR_MODE_IN_OUT:
            self.logger.debug("CLEAR_MODE_IN_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0], [314, 1]])
        elif clear_mode == CLEAR_MODE_OUT_IN:
            self.logger.debug("CLEAR_MODE_OUT_IN")
            coors = np.array([[0, self.get_current_rho_position()], [0, 1], [314, 0]])
        elif clear_mode == CLEAR_MODE_OUT_OUT:
            self.logger.debug("CLEAR_MODE_OUT_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 1], [157, 0], [314, 1]])
        elif clear_mode == CLEAR_MODE_IN_IN:
            self.logger.debug("CLEAR_MODE_IN_IN")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0], [157, 1], [314, 0]])
        else:
            self.logger.debug("default: CLEAR_MODE_IN_OUT")
            coors = np.array([[0, self.get_current_rho_position()], [0, 0], [314, 1]])

        self.logger.debug("clear_table. coors: %s", coors)

        steps = self.coors_to_steps(coors)
        delta_steps = self.calc_deltasteps(steps)
        steps_with_delays = self.add_delays(delta_steps)

        self.draw_steps_with_delays(steps_with_delays)

        self.logger.info("finished clearing table")

    def NextTableButtonPressed(self):
        return GPIOs.input(GPIOs.NEXTTABLE_BUTTON)

    def shutdown(self):
        self.logger.info("controller.shutdown")

        self.pendingShutdown = True
        
        self.logger.info("stopping motors...")
        self.stop_motors()

        self.logger.info("cleanup GPIOs")
        #GPIOs.cleanup()