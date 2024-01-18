import numpy as np

MICROSTEPS = 8
THETA_STEPS_FULL_TURN = 200 * 10 * MICROSTEPS
RHO_STEPS_FULL_LENGTH = 1000 * MICROSTEPS


def get_steps(thr_file):
    with open(thr_file, 'r') as f:
        content = f.readlines()
        
    lines = [line.rstrip('\n') for line in content]
    #print("lines 1:", lines[:29])

    steps = np.array([0, 0])
    #print("steps 1:", steps)
    for c in lines:
        theta = float(c[:c.find(" ")])
        rho = float(c[c.find(" ")+1:])

        print("theta:", theta, "rho:", rho)

        #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
        theta = int(THETA_STEPS_FULL_TURN * theta)
        rho = int(RHO_STEPS_FULL_LENGTH * rho)

        steps = np.vstack((steps, [theta, rho]))

    #print("steps 2:", steps)
    min_value = steps[1:, 0].min() #suche den kleinsten Wert aus den theta-Werten
    #print("min_value:", min_value)

    steps[1:, 0] -= min_value
    #print("steps 3:", steps)
    return steps

def calc_deltasteps(deltasteps):
    #print("steps[1:]", steps[1:]) #alles aus steps ohne die erste Zeile
    #print("steps[:-1]", steps[:-1]) #alles aus steps ohne die letzte Zeile
    print ("calc_deltasteps(", deltasteps, ")")
    return deltasteps[1:] - deltasteps[:-1]

def coors_to_steps(coors):
    print("coors_to_steps(", coors, ")")

    for coor in coors:
        #konvertieren auf Steps (theta mit Anzahl Zähnen pro Umdrehung, rho mit Anzahl Zähnen 0->1 multiplizieren)
        coor[0] = int(THETA_STEPS_FULL_TURN * coor[0])
        coor[1] = int(RHO_STEPS_FULL_LENGTH * coor[1])


