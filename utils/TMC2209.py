#import utils.GPIOs as GPIO
import utils.GPIOs_Mock as GPIOs
import time

MOTOR_DIR_FORWARD = 'forward'
MOTOR_DIR_BACKWARD = 'backward'

MotorDir = [
    MOTOR_DIR_FORWARD,
    MOTOR_DIR_BACKWARD,
]

class TMC2209():
    MOTOR_DIR_FORWARD = 'forward'
    MOTOR_DIR_BACKWARD = 'backward'

    def __init__(self, dir_pin, step_pin, enable_pin):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.running = True


    def digital_write(self, pin, value):
        GPIOs.output(pin, value)


    def stop(self):
        self.digital_write(self.enable_pin, 1)


    def turn_steps(self, Dir, steps, stepdelay):
        if (Dir == MotorDir[0]):
            # print("forward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 0)
        elif (Dir == MotorDir[1]):
            # print("backward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 1)
        else:
            # print("the dir must be : 'forward' or 'backward'")
            self.digital_write(self.enable_pin, 1)
            return

        if (steps == 0):
            return

        # print("turn step: ",steps)
        while steps > 0 and self.running:
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            steps -= 1
        
        print("turn_steps finished")


    def turn_until_switch(self, Dir, limit_switch, stepdelay):
        if (Dir == MotorDir[0]):
            # print("forward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 0)
        elif (Dir == MotorDir[1]):
            # print("backward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 1)
        else:
            # print("the dir must be : 'forward' or 'backward'")
            self.digital_write(self.enable_pin, 1)
            return

        # print("turn step: ",steps)
        pos = 0
        while not GPIOs.input(limit_switch) and self.running:
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            pos += 1

        if Dir == MotorDir[0]:
            return pos
        else:
            return -1*pos

    def turn_check_cali(self, Dir, steps, limit_switch, stepdelay):
        if (Dir == MotorDir[0]):
            # print("forward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 0)
        elif (Dir == MotorDir[1]):
            # print("backward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 1)
        else:
            # print("the dir must be : 'forward' or 'backward'")
            self.digital_write(self.enable_pin, 1)
            return

        if (steps == 0):
            return

        # print("turn step: ",steps)
        while steps > 0 and self.running:
            if not GPIOs.input(limit_switch):
                return False
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            steps -= 1

        return True