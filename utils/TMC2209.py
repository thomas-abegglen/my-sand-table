#import utils.GPIOs as GPIOs
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

    def __init__(self, dir_pin, step_pin, enable_pin, limit_switches):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.limit_switches = limit_switches
        self.running = True


    def digital_write(self, pin, value):
        GPIOs.output(pin, value)


    def stop(self):
        self.digital_write(self.enable_pin, 1)


    def turn_steps(self, Dir, steps, stepdelay):
        limit_switch = 0
        if (Dir == MotorDir[0]):
            # print("forward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 0)
            limit_switch = self.limit_switches[0] if self.limit_switches != None else None
        elif (Dir == MotorDir[1]):
            # print("backward")
            self.digital_write(self.enable_pin, 0)
            self.digital_write(self.dir_pin, 1)
            limit_switch = self.limit_switches[1] if self.limit_switches != None else None
        else:
            # print("the dir must be : 'forward' or 'backward'")
            self.digital_write(self.enable_pin, 1)
            return

        if (steps == 0):
            return

        # print("turn step: ",steps)
        while steps > 0 and self.running and (GPIOs.input(limit_switch) if limit_switch != None else True):
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            steps -= 1
        
        if limit_switch != None and not GPIOs.input(limit_switch):
            #limit_switch is pressed, return 5 steps
            self.turn_steps(MotorDir[1] if Dir == MotorDir[0] else MotorDir[0], 5, 0.0005)


        current_time = time.localtime()
        print("%H:%M:%S - turn_steps finished", current_time)


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
        while self.running and GPIOs.input(limit_switch):
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
            pos += 1

        if limit_switch != None and not GPIOs.input(limit_switch):
            #limit_switch is pressed, return 5 steps
            self.turn_steps(MotorDir[1] if Dir == MotorDir[0] else MotorDir[0], 5, 0.0005)
            pos -= 5

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