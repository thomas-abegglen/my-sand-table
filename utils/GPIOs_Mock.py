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

def input(pin):
    print("GPIOs.input pin:", pin)
    return 0

def output(pin, value):
    print("GPIOs.output pin:", pin, "value:", value)

def cleanup():
    print("GPIOs.cleanup")
