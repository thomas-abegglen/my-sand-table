import glob, os, math, random
import numpy as np

THETA_STEPS_FULL_TURN = 2000
RHO_STEPS_FULL_LENGTH = 200

DEFAULT_SPEED = 800
MAX_SPEED = 2000

def init():
    print("initializing...")
    #ToDo:
    #Calibration-file exists?
    #No: 
    #   Calibrate
    #Yes: 
    #   Read calibration-file
 
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
            Rotor_delay = round(1 / DEFAULT_SPEED, 5) #delay für Rotor mit DEFAULT_SPEED berechnen
            Linear_delay = round(elapsed_time / abs(s[1]), 5) if s[1] != 0 else None #delay für Linear berechnen (sollte zwischen DEFAULT_SPEED und>
            print("Rotor_delay:", Rotor_delay, "Linear_delay:", Linear_delay)
        else:
            #entweder ist die theta-Verschiebung 0 oder es müsste für Linear schneller gehen als mit MAX_SPEED
            print("Linear mit MAX_SPEED")
            min_time = abs(s[1]) / MAX_SPEED #wie lange dauert rho-Verschiebung mit MAX_SPEED?
            Rotor_delay = round(min_time / abs(s[0]), 5) if s[0] != 0 else None #delay für Rotor berechnen (sollte etwas unterhalb DEFAULT_SPEED li>
            Linear_delay = round(1 / MAX_SPEED, 5) #delay für Linear mit MAX_SPEED berechnen
            print("Rotor_delay:", Rotor_delay, "Linear_delay:", Linear_delay)
 
        delays = np.vstack((delays, [Rotor_delay, Linear_delay]))

    print("delays:", delays)
    delays = delays[1:]
    steps_with_delays = np.concatenate((steps, delays), axis=1)

    return steps_with_delays

def draw_theta_rho_file(thr_file):
    coors = get_coors(thr_file)
    steps = calc_deltasteps(coors)
    steps_with_delays = add_delays(steps)

    #ToDo: set Button-LED: Playing
    for s in steps_with_delays:
        print("rotor step:", s[0], "linear step:", s[1], "rotor delay:", s[2], "linear delay:", s[3])
        #pass values to M_Rot/M_Lin
        #start threads
        
    #ToDo: set Button-LED: Stopped
 
