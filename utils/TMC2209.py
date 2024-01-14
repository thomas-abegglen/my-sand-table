#import utils.GPIOs as GPIO
import utils.GPIOs_Mock as GPIOs
import time


MotorDir = [
    'forward',
    'backward',
]

class TMC2209():

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
        while GPIOs.input(limit_switch) == 1 and self.running:
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
            if GPIOs.input(limit_switch) == 0:
                return False
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            steps -= 1

        return True