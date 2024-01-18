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

NbrOfCallsUntilMockValue = {
    SWITCH_IN: [0, 50, False, True],
    SWITCH_OUT: [0, 50, False, True],
    NEXTTABLE_BUTTON: [0, 2, False, True]
}


def init():
    print("initializing GPIOs...")

def input(pin):
    print("GPIOs.input pin:", pin)

    #lookup pin in Dictionary for the mock-values
    mockData = NbrOfCallsUntilMockValue[pin]
    if mockData == None:
        return 0
    
    #increment counter
    mockData[0] += 1

    #return data
    return mockData[2] if mockData[0] < mockData[1] else mockData[3]

def output(pin, value):
    print("GPIOs.output pin:", pin, "value:", value)

def cleanup():
    print("GPIOs.cleanup")
