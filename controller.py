import glob, os, math, random, time, threading
import numpy as np
#import utils.GPIOs as GPIOs
import utils.GPIOs_Mock as GPIOs
from utils.TMC2209 import TMC2209

THETA_STEPS_FULL_TURN = 2000
RHO_STEPS_FULL_LENGTH = 200

DEFAULT_SPEED = 800
MAX_SPEED = 2000

M_Theta = TMC2209(dir_pin=GPIOs.MOTOR_THETA_DIR, step_pin=GPIOs.MOTOR_THETA_STEP, enable_pin=GPIOs.MOTOR_THETA_ENABLE)
M_Rho = TMC2209(dir_pin=GPIOs.MOTOR_RHO_DIR, step_pin=GPIOs.MOTOR_RHO_STEP, enable_pin=GPIOs.MOTOR_RHO_ENABLE)
running = True
clearTable = False

def init():
    print("initializing...")
    
    GPIOs.init()

    #Calibration-file exists? Yes: read it, No: --> calibrate

    #Pending Drawing? Yes: read it, set 'clearTable' to False and continue 
    #so far, we assume: no pending drawing, so we start with a clear_table
    global clearTable
    clearTable = True

    #Playlist exists? Yes: read it, No: --> create it

def run_M_Theta(steps, delay):
    if steps != 0 and delay >= 0:
        if steps > 0:
            M_Theta.turn_steps(Dir='forward', steps=abs(steps), stepdelay=delay)
        else:
            M_Theta.turn_steps(Dir='backward', steps=abs(steps), stepdelay=delay)

    M_Theta.stop()
    M_Theta.running = False

    # print("M_Theta done!")

def run_M_Rho(steps, delay):
    if steps != 0 and delay >= 0:
        if steps > 0:
            M_Rho.turn_steps(Dir='forward', steps=abs(steps), stepdelay=delay)
        else:
            M_Rho.turn_steps(Dir='backward', steps=abs(steps), stepdelay=delay)

    M_Rho.stop()
    M_Rho.running = False

    # print("M_Rho done!")

def get_coors(thr_file):
    with open(thr_file, 'r') as f:
        content = f.readlines()
        
    lines = [line.rstrip('\n') for line in content]
    #print("lines 1:", lines[:29])
 
    coors = np.array([0, 0])
    #print("coors 1:", coors)
    for c in lines:
        theta = float(c[:c.find(" ")])
        rho = float(c[c.find(" ")+1:])

        print("theta:", theta, "rho:", rho)

        #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
        theta = int(THETA_STEPS_FULL_TURN * theta)
        rho = int(RHO_STEPS_FULL_LENGTH * rho)

        coors = np.vstack((coors, [theta, rho]))

    #print("coors 2:", coors)
    min_value = coors[1:, 0].min() #suche den kleinsten Wert aus den theta-Werten
    #print("min_value:", min_value)

    coors[1:, 0] -= min_value
    #print("coors 3:", coors)
    return coors

def calc_deltasteps(coors):
    #print("coors[1:]", coors[1:]) #alles aus coors ohne die erste Zeile
    #print("coors[:-1]", coors[:-1]) #alles aus coors ohne die letzte Zeile
    return coors[1:] - coors[:-1]
 
def add_delays(steps):
    delays = np.array([0, 0])
    for s in steps:
        print("step:", s)
        elapsed_time = abs(s[0]) / DEFAULT_SPEED #wie lange dauert theta-Verschiebung mit DEFAULT_SPEED?
        print("elapsed_time:", elapsed_time)
        if elapsed_time > 0 and abs(s[1]) / elapsed_time <= MAX_SPEED: #schaffen wir die rho-Verschiebung in der gleichen Zeit mit weniger als MAX_>
            print("Rotor mit DEFAULT_SPEED")
            Theta_delay = round(1 / DEFAULT_SPEED, 5) #delay für Theta mit DEFAULT_SPEED berechnen
            Rho_delay = round(elapsed_time / abs(s[1]), 5) if s[1] != 0 else None #delay für Linear berechnen (sollte zwischen DEFAULT_SPEED und>
            print("Rotor_delay:", Theta_delay, "Linear_delay:", Rho_delay)
        else:
            #entweder ist die theta-Verschiebung 0 oder es müsste für Linear schneller gehen als mit MAX_SPEED
            print("Linear mit MAX_SPEED")
            min_time = abs(s[1]) / MAX_SPEED #wie lange dauert rho-Verschiebung mit MAX_SPEED?
            Theta_delay = round(min_time / abs(s[0]), 5) if s[0] != 0 else None #delay für Rotor berechnen (sollte etwas unterhalb DEFAULT_SPEED li>
            Rho_delay = round(1 / MAX_SPEED, 5) #delay für Linear mit MAX_SPEED berechnen
            print("Rotor_delay:", Theta_delay, "Linear_delay:", Rho_delay)
 
        delays = np.vstack((delays, [Theta_delay, Rho_delay]))

    print("delays:", delays)
    delays = delays[1:]
    steps_with_delays = np.concatenate((steps, delays), axis=1)

    return steps_with_delays

def draw_theta_rho_file(thr_file):
    coors = get_coors(thr_file)
    steps = calc_deltasteps(coors)
    steps_with_delays = add_delays(steps)

    for swd in steps_with_delays:
        print("rotor step:", swd[0], "linear step:", swd[1], "rotor delay:", swd[2], "linear delay:", swd[3])
        #pass values to M_Theta/M_Rho and create threads
        M_Theta_Thread = threading.Thread(target=run_M_Theta, args=(swd[0], swd[2],))
        M_Rho_Thread = threading.Thread(target=run_M_Rho, args=(swd[1], swd[3],))

        #start threads
        M_Theta.running = True
        M_Rho.running = True
        M_Theta_Thread.start()
        M_Rho_Thread.start()

        #wait for threads to finish
        M_Theta_Thread.join()
        M_Rho_Thread.join()
        
def run():
    while running:
        print("running")

        #determine next file to draw
        thr_file = "test.thr"

        #clear table
        if clearTable:
            clear_table()

        #draw next file
        #draw_theta_rho_file(thr_file)

        #wait until we have to draw next file
        while running and not GPIOs.input(GPIOs.NEXTTABLE_BUTTON):
            time.sleep(0.5)

def stop_motors():
    M_Theta.running = False
    M_Rho.running = False
    M_Theta.stop()
    M_Rho.stop()
    print("\n---------- Motors Stopped! ----------")

def clear_table():
    print("Clearing table")
    coors = np.array([0, 0])
    theta = int(THETA_STEPS_FULL_TURN * 628)
    rho = int(RHO_STEPS_FULL_LENGTH * 1)

    coors = np.vstack((coors, [theta, rho]))

    steps = calc_deltasteps(coors)
    steps_with_delays = add_delays(steps)

    for swd in steps_with_delays:
        print("rotor step:", swd[0], "linear step:", swd[1], "rotor delay:", swd[2], "linear delay:", swd[3])
        #pass values to M_Theta/M_Rho and create threads
        M_Theta_Thread = threading.Thread(target=run_M_Theta, args=(swd[0], swd[2],))
        M_Rho_Thread = threading.Thread(target=run_M_Rho, args=(swd[1], swd[3],))

        #start threads
        M_Theta.running = True
        M_Rho.running = True
        M_Theta_Thread.start()
        M_Rho_Thread.start()

        #wait for threads to finish
        M_Theta_Thread.join()
        M_Rho_Thread.join()

    print("finished clearing table")


def shutdown():
    print("controller.shutdown")
    global running
    running = False
    print("stopping motors...")
    stop_motors()
    print("cleanup GPIOs")
    GPIOs.cleanup()