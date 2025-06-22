import signal
import utils.GPIOs as GPIOs
import time
import os
import csv
import json
import math
import sys

# This script controls a stepper motor system to move to specified positions based on a playlist of coordinates.
# It handles calibration, position saving, and synchronized movement of two motors (Theta and Rho).
# It also waits for a button press to continue between movements.

# Constants
THETA_STEPS_PER_REV = 8 * 200 * 320 / 12 #8: microsteps, 200: nbrOfSteps for the motor for one turn, 320: nbrOfTeeth of pully at axis, 12: nbrOfTeeth of pully at motor
CALIBRATION_FILE = "calibration.dat"
POSITION_FILE = "current_position.json"
PLAYLIST_FILE = "playlist.txt"

DIR_IN = 0
DIR_OUT = 1

# Position wird nur in Variablen gehalten, und nur im SIGTERM-Handler gespeichert
current_position = {
    "theta": 0.0,
    "rho": 0.0,
    "current_file": "",
    "line_index": 0
}

# GPIO setup
print(f"Initialisiere GPIOs..")
GPIOs.init()
print(f"GPIOs initialisiert.")

def step_motor(step_pin):
    GPIOs.output(step_pin, GPIOs.HIGH)
    time.sleep(0.0001)
    GPIOs.output(step_pin, GPIOs.LOW)

def dynamic_rho_delay(rho_norm):
    min_delay = 0.0005
    max_delay = 0.003
    return min_delay + (max_delay - min_delay) * rho_norm

def set_motor_direction(motor_dir_pin, direction):
    if direction == DIR_OUT:
        GPIOs.output(motor_dir_pin, GPIOs.LOW)
    elif direction == DIR_IN:
        GPIOs.output(motor_dir_pin, GPIOs.HIGH)
    else:
        raise ValueError("Ungültige Richtung. Verwenden Sie 'Direction.IN' oder 'Direction.OUT'.")

def calibrate_rho():
    print("Starte Kalibrierung von Rho...")
    # Fahre rückwärts bis zum Endschalter
    print("Starte Rückwärtsfahrt bis zum Endschalter...")
    set_motor_direction(GPIOs.MOTOR_RHO_DIR, DIR_IN)
    while GPIOs.input(GPIOs.SWITCH_IN):
        step_motor(GPIOs.MOTOR_RHO_STEP)
        time.sleep(0.001)

    print("Rückwärtsfahrt abgeschlossen. Warte 0.5 Sekunden...")
    time.sleep(0.5)

    steps = 0
    # Fahre vorwärts bis zum Endschalter
    print("Starte Vorwärtsfahrt bis zum Endschalter...")
    set_motor_direction(GPIOs.MOTOR_RHO_DIR, DIR_OUT)
    while GPIOs.input(GPIOs.SWITCH_OUT):
        step_motor(GPIOs.MOTOR_RHO_STEP)
        time.sleep(0.001)
        steps += 1

    print("Vorwärtsfahrt abgeschlossen. Schritte gezählt:", steps)
    # Sicherheitsmarge: 40 Schritte
    #steps -= 40
    #ToDo: 40 Schritte rückwärts fahren, um den Endschalter nicht zu beschädigen

    with open(CALIBRATION_FILE, 'w') as f:
        f.write(str(steps))
    print(f"Kalibrierung abgeschlossen. Schritte für Rho: {steps}")
    return steps

def load_calibration():
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, 'r') as f:
            return int(f.read().strip())
    else:
        return calibrate_rho()

def load_last_position():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, 'r') as f:
            data = json.load(f)
            return data.get("theta", 0.0), data.get("rho", 0.0), data.get("current_file", ""), data.get("line_index", 0)
    return 0.0, 0.0, "", 0

def save_current_position(theta, rho, current_file, line_index):
    # Nur Variablen aktualisieren, nicht direkt in Datei schreiben
    current_position["theta"] = theta
    current_position["rho"] = rho
    current_position["current_file"] = current_file
    current_position["line_index"] = line_index

def persist_current_position():
    with open(POSITION_FILE, 'w') as f:
        json.dump(current_position, f)

def read_thr_file(filename):
    coordinates = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) == 2:
                try:
                    theta, rho = map(float, parts)
                    coordinates.append((theta, rho))
                except ValueError:
                    continue
    return coordinates

def synchronized_move(delta_theta_steps, delta_rho_steps, theta_dir, rho_dir, base_delay):
    max_steps = max(abs(delta_theta_steps), abs(delta_rho_steps))
    theta_interval = max_steps / abs(delta_theta_steps) if delta_theta_steps != 0 else float('inf')
    rho_interval = max_steps / abs(delta_rho_steps) if delta_rho_steps != 0 else float('inf')

    theta_counter = 0
    rho_counter = 0

    set_motor_direction(GPIOs.MOTOR_THETA_DIR, theta_dir)
    set_motor_direction(GPIOs.MOTOR_RHO_DIR, rho_dir)

    for i in range(max_steps):
        if i / theta_interval >= theta_counter and theta_counter < abs(delta_theta_steps):
            step_motor(GPIOs.MOTOR_THETA_STEP)
            theta_counter += 1
        if i / rho_interval >= rho_counter and rho_counter < abs(delta_rho_steps):
            step_motor(GPIOs.MOTOR_RHO_STEP)
            rho_counter += 1
        time.sleep(base_delay)

def move_to_position(current_theta, current_rho, target_theta, target_rho, rho_max_steps):
    current_theta_steps = int(current_theta / (2 * math.pi) * THETA_STEPS_PER_REV)
    target_theta_steps = int(target_theta / (2 * math.pi) * THETA_STEPS_PER_REV)
    
    delta_theta_steps = target_theta_steps - current_theta_steps
    theta_dir = DIR_OUT if delta_theta_steps >= 0 else DIR_IN

    current_rho_steps = int(current_rho * rho_max_steps)
    target_rho_steps = int(target_rho * rho_max_steps)
    delta_rho_steps = target_rho_steps - current_rho_steps
    rho_dir = DIR_OUT if delta_rho_steps >= 0 else DIR_IN

    base_delay = dynamic_rho_delay(target_rho)

    print(f"Bewege von Theta {current_theta} rad zu {target_theta} rad, Rho {current_rho} zu {target_rho}")
    
    synchronized_move(abs(delta_theta_steps), abs(delta_rho_steps), theta_dir, rho_dir, base_delay)

    return target_theta, target_rho

def wait_for_button_press():
    print("Warte auf Knopfdruck, um fortzufahren...")
    # Wenn der Button bereits gedrückt ist, sofort weitermachen
    if GPIOs.input(GPIOs.NEXTTABLE_BUTTON) == GPIOs.HIGH:
        print("Button ist bereits gedrückt. Weiter geht's.")
        return
    # Andernfalls warten, bis er gedrückt wird (entprellt)
    while True:
        if GPIOs.input(GPIOs.NEXTTABLE_BUTTON) == GPIOs.HIGH:
            time.sleep(0.05)  # Entprellzeit
            if GPIOs.input(GPIOs.NEXTTABLE_BUTTON) == GPIOs.HIGH:
                print("Button wurde gedrückt. Weiter geht's.")
                break

def clean_table(current_theta, current_rho, coordinates, rho_max_steps):
    print("Reinige Tisch...")
    new_rho = 0.0 if current_rho <= 0.5 else 1.0
    current_theta, current_rho = move_to_position(current_theta, current_rho, 0.0, new_rho, rho_max_steps)
    save_current_position(current_theta, current_rho, "", 0)
    time.sleep(0.5)
    
    if coordinates:
        first_theta, first_rho = coordinates[0]
    else:
        first_theta = 0.0
        first_rho = 0.0 if current_rho > 0.5 else current_rho

    if current_rho == 0.0 and first_rho > 0.5:
        current_theta, current_rho = move_to_position(current_theta, current_rho, 314, 1.0, rho_max_steps)
    elif current_rho == 1.0 and first_rho <= 0.5:
        current_theta, current_rho = move_to_position(current_theta, current_rho, 314, 0.0, rho_max_steps)
    else:
        new_rho = 1.0 if current_rho == 0.0 else 0.0
        current_theta, current_rho = move_to_position(current_theta, current_rho, 157, new_rho, rho_max_steps)
        new_rho = 1.0 if current_rho == 0.0 else 0.0
        current_theta, current_rho = move_to_position(current_theta, current_rho, 314, new_rho, rho_max_steps)

    current_theta = first_theta
    print(f"Tisch gereinigt. current_theta: {current_theta} rad current_rho: {current_rho} rad")
    return current_theta, current_rho

# Signal handler to save current position on termination
def signal_handler(sig, frame):
    print("SIGTERM empfangen, speichere aktuelle Position...")
    # Speichere die aktuelle Position vor dem Beenden
    persist_current_position()
    GPIOs.cleanup()
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        rho_max_steps = load_calibration()
        current_theta, current_rho, last_file, last_index = load_last_position()

        if not os.path.exists(PLAYLIST_FILE):
            print("Keine playlist.txt gefunden.")
            return

        with open(PLAYLIST_FILE, 'r') as f:
            playlist = [line.strip() for line in f if line.strip()]

        resume = False if not last_file else True

        for file in playlist:
            if resume and file != last_file:
                continue
            coordinates = read_thr_file(file)
            start_index = last_index if resume else 0

            if not resume:
                current_theta, current_rho = clean_table(current_theta, current_rho, coordinates, rho_max_steps)
            
            resume = False  # Nur beim ersten Treffer fortsetzen

            for i in range(start_index, len(coordinates)):
                theta, rho = coordinates[i]
                current_theta, current_rho = move_to_position(current_theta, current_rho, theta, rho, rho_max_steps)
                save_current_position(current_theta, current_rho, file, i + 1)
                time.sleep(0.5)

            wait_for_button_press()

    finally:
        GPIOs.cleanup()

if __name__ == "__main__":
    main()