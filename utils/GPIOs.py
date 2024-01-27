import os
import RPi.GPIO as GPIO

SHUTDOWN_LED = 2
SHUTDOWN_BUTTON = 3

MOTOR_THETA_ENABLE = 17
MOTOR_THETA_DIR = 27
MOTOR_THETA_STEP = 22
MOTOR_THETA_RELAY = 23

MOTOR_RHO_ENABLE = 10
MOTOR_RHO_DIR = 9
MOTOR_RHO_STEP = 11
MOTOR_RHO_RELAY = 24

SWITCH_OUT = 5
SWITCH_IN = 6

NEXTTABLE_LED = 19
NEXTTABLE_BUTTON = 26

def init():
    print("initializing GPIOs...")

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(SHUTDOWN_LED, GPIO.OUT)
    GPIO.setup(SHUTDOWN_BUTTON, GPIO.IN)

    GPIO.setup(MOTOR_RHO_ENABLE, GPIO.OUT)
    GPIO.setup(MOTOR_RHO_DIR, GPIO.OUT)
    GPIO.setup(MOTOR_RHO_STEP, GPIO.OUT)
    GPIO.setup(MOTOR_RHO_RELAY, GPIO.OUT)

    GPIO.setup(MOTOR_THETA_ENABLE, GPIO.OUT)
    GPIO.setup(MOTOR_THETA_DIR, GPIO.OUT)
    GPIO.setup(MOTOR_THETA_STEP, GPIO.OUT)
    GPIO.setup(MOTOR_THETA_RELAY, GPIO.OUT)

    GPIO.setup(SWITCH_OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SWITCH_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(NEXTTABLE_LED, GPIO.OUT)
    GPIO.setup(NEXTTABLE_BUTTON, GPIO.IN)

    #enable Power-Button-LED
    GPIO.output(SHUTDOWN_LED, GPIO.HIGH)

    #enable Motor-Relays (set them to LOW)
    GPIO.output(MOTOR_RHO_RELAY, GPIO.LOW)
    GPIO.output(MOTOR_THETA_RELAY, GPIO.LOW)

    #set enable of both Motors to high (say: disable it). The TMC2209 software driver will enable them if needed
    GPIO.output(MOTOR_RHO_ENABLE, GPIO.HIGH)
    GPIO.output(MOTOR_THETA_ENABLE, GPIO.HIGH)


def input(pin):
    return GPIO.input(pin)

def output(pin, value):
    GPIO.output(pin, value)

def cleanup():
    #disable Motors
    GPIO.output(MOTOR_RHO_ENABLE, GPIO.HIGH)
    GPIO.output(MOTOR_THETA_ENABLE, GPIO.HIGH)

    #disable Motor-Relays 
    GPIO.output(MOTOR_RHO_RELAY, GPIO.HIGH)
    GPIO.output(MOTOR_THETA_RELAY, GPIO.HIGH)

    #disable Power-Button-LED
    GPIO.output(SHUTDOWN_LED, GPIO.LOW)

    GPIO.cleanup()