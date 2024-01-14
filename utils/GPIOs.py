import os
import RPi.GPIO as GPIO

SHUTDOWN_LED = 2
SHUTDOWN_BUTTON = 3

MOTOR_RHO_ENABLE = 17
MOTOR_RHO_DIR = 27
MOTOR_RHO_STEP = 22
MOTOR_RHO_RELAY = 24

MOTOR_THETA_ENABLE = 10
MOTOR_THETA_DIR = 9
MOTOR_THETA_STEP = 11
MOTOR_THETA_RELAY = 23

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

    GPIO.setup(SWITCH_OUT, GPIO.IN)
    GPIO.setup(SWITCH_IN, GPIO.IN)

    GPIO.setup(NEXTTABLE_LED, GPIO.OUT)
    GPIO.setup(NEXTTABLE_BUTTON, GPIO.IN)

    #enable Power-Button-LED
    GPIO.output(SHUTDOWN_LED, GPIO.HIGH)

    #set Motor-Relays LOW
    GPIO.output(MOTOR_RHO_RELAY, GPIO.LOW)
    GPIO.output(MOTOR_THETA_RELAY, GPIO.LOW)

    #set enable of both Motors to high (say: disable it)
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

    #set Motor-Relays LOW
    GPIO.output(MOTOR_RHO_RELAY, GPIO.LOW)
    GPIO.output(MOTOR_THETA_RELAY, GPIO.LOW)

    GPIO.cleanup()