import glob, os, math, random, time, threading
import numpy as np
#import utils.GPIOs as GPIOs
import utils.GPIOs_Mock as GPIOs
from utils.TMC2209 import TMC2209
from utils.coord_functions import get_steps, calc_deltasteps, coors_to_steps

class Controller():

    DEFAULT_SPEED = 800
    MAX_SPEED = 2000

    M_Theta = TMC2209(dir_pin=GPIOs.MOTOR_THETA_DIR, step_pin=GPIOs.MOTOR_THETA_STEP, enable_pin=GPIOs.MOTOR_THETA_ENABLE)
    M_Rho = TMC2209(dir_pin=GPIOs.MOTOR_RHO_DIR, step_pin=GPIOs.MOTOR_RHO_STEP, enable_pin=GPIOs.MOTOR_RHO_ENABLE)
    clearTable = False
    running = False

    def __init__(self):
        print("initializing...")
        
        GPIOs.init()


    def run_M_Theta(self, steps, delay):
        if steps != 0 and delay >= 0:
            if steps > 0:
                self.M_Theta.turn_steps(Dir='forward', steps=abs(steps), stepdelay=delay)
            else:
                self.M_Theta.turn_steps(Dir='backward', steps=abs(steps), stepdelay=delay)

        self.M_Theta.stop()
        self.M_Theta.running = False

        # print("M_Theta done!")

    def run_M_Rho(self, steps, delay):
        if steps != 0 and delay >= 0:
            if steps > 0:
                self.M_Rho.turn_steps(Dir='forward', steps=abs(steps), stepdelay=delay)
            else:
                self.M_Rho.turn_steps(Dir='backward', steps=abs(steps), stepdelay=delay)

        self.M_Rho.stop()
        self.M_Rho.running = False

        # print("M_Rho done!")
    
    def add_delays(self, steps):
        delays = np.array([0, 0])
        for s in steps:
            print("step:", s)
            elapsed_time = abs(s[0]) / self.DEFAULT_SPEED #wie lange dauert theta-Verschiebung mit DEFAULT_SPEED?
            print("elapsed_time:", elapsed_time)
            if elapsed_time > 0 and abs(s[1]) / elapsed_time <= self.MAX_SPEED: #schaffen wir die rho-Verschiebung in der gleichen Zeit mit weniger als MAX_>
                print("Rotor mit DEFAULT_SPEED")
                Theta_delay = round(1 / self.DEFAULT_SPEED, 5) #delay für Theta mit DEFAULT_SPEED berechnen
                Rho_delay = round(elapsed_time / abs(s[1]), 5) if s[1] != 0 else None #delay für Linear berechnen (sollte zwischen DEFAULT_SPEED und>
                print("Rotor_delay:", Theta_delay, "Linear_delay:", Rho_delay)
            else:
                #entweder ist die theta-Verschiebung 0 oder es müsste für Linear schneller gehen als mit MAX_SPEED
                print("Linear mit MAX_SPEED")
                min_time = abs(s[1]) / self.MAX_SPEED #wie lange dauert rho-Verschiebung mit MAX_SPEED?
                Theta_delay = round(min_time / abs(s[0]), 5) if s[0] != 0 else None #delay für Rotor berechnen (sollte etwas unterhalb DEFAULT_SPEED li>
                Rho_delay = round(1 / self.MAX_SPEED, 5) #delay für Linear mit MAX_SPEED berechnen
                print("Rotor_delay:", Theta_delay, "Linear_delay:", Rho_delay)
    
            delays = np.vstack((delays, [Theta_delay, Rho_delay]))

        print("delays:", delays)
        delays = delays[1:]
        steps_with_delays = np.concatenate((steps, delays), axis=1)

        return steps_with_delays

    def draw_theta_rho_file(self, thr_file):
        steps = get_steps(thr_file)
        steps = calc_deltasteps(steps)
        steps_with_delays = self.add_delays(steps)

        self.draw_steps_with_delays(steps_with_delays)

    def draw_steps_with_delays(self, steps_with_delays):
        for swd in steps_with_delays:
            print("rotor step:", swd[0], "linear step:", swd[1], "rotor delay:", swd[2], "linear delay:", swd[3])
            #pass values to M_Theta/M_Rho and create threads
            M_Theta_Thread = threading.Thread(target=self.run_M_Theta, args=(swd[0], swd[2],))
            M_Rho_Thread = threading.Thread(target=self.run_M_Rho, args=(swd[1], swd[3],))

            #start threads
            self.M_Theta.running = True
            self.M_Rho.running = True
            M_Theta_Thread.start()
            M_Rho_Thread.start()

            #wait for threads to finish
            M_Theta_Thread.join()
            M_Rho_Thread.join()


    def stop_motors(self):
        self.M_Theta.running = False
        self.M_Rho.running = False
        self.M_Theta.stop()
        self.M_Rho.stop()
        print("\n---------- Motors Stopped! ----------")

    def clear_table(self):
        print("Clearing table")
        #coors = np.array([[0, 0], [628, 1]])
        coors = np.array([[0, 0], [0.005, 0.001]])


        steps = coors_to_steps(coors)
        steps = calc_deltasteps(coors)
        steps_with_delays = self.add_delays(steps)

        self.draw_steps_with_delays(steps_with_delays)

        print("finished clearing table")

    def NextTableButtonPressed(self):
        #Auto-Play is currently disabled
        #return GPIOs.input(GPIOs.NEXTTABLE_BUTTON)
        return False

    def shutdown(self):
        print("controller.shutdown")
        global running
        running = False
        print("stopping motors...")
        self.stop_motors()
        print("cleanup GPIOs")
        GPIOs.cleanup()