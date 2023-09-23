#!/usr/bin/env python3

import os
import sys
import json
import pathlib
import logging

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PCA9685 import PWM
from TB6612 import Motor


class Backwheels(object):
    """ Back wheels control class """
    Motor_A = 17
    Motor_B = 27

    PWM_A = 4
    PWM_B = 5
    SPEED_DEFAULT = 30

    def __init__(self, bus_number=1, db="../config.json"):
        """ Init the direction channel and pwm channel """
        self.logger = logging.getLogger(__name__)
        try:
            with open(os.path.join(os.getcwd(), db), 'r') as configFile:
                jsondata = configFile.read()
            self.db = json.loads(jsondata)

            self.forward_A = self.db["forward_A"]
            self.forward_B = self.db["forward_B"]

            self.left_wheel = Motor(self.Motor_A, offset=self.forward_A)
            self.right_wheel = Motor(self.Motor_B, offset=self.forward_B)

            self.pwm = PWM(bus_number=bus_number)
            self.pwm.setup()

            def _set_a_pwm(value):
                pulse_wide = int(self.pwm.map(value, 0, 100, 0, 4095))
                self.pwm.write(self.PWM_A, 0, pulse_wide)

            def _set_b_pwm(value):
                pulse_wide = int(self.pwm.map(value, 0, 100, 0, 4095))
                self.pwm.write(self.PWM_B, 0, pulse_wide)

            self.left_wheel.pwm = _set_a_pwm
            self.right_wheel.pwm = _set_b_pwm

            self._speed = self.SPEED_DEFAULT

            self.logger.info('Set left wheel to #%d, PWM channel to %d' % (self.Motor_A, self.PWM_A))
            self.logger.info('Set right wheel to #%d, PWM channel to %d' % (self.Motor_B, self.PWM_B))
        except IOError as e:
            self.logger.info("CWD: %s" % os.getcwd())
            self.logger.exception("Can't open/read config pls. Please specify the path relative to your main.py file")
            raise Exception from e
        except ValueError as e:
            self.logger.exception("Json value error")
            raise Exception from e

    def forward(self, speed=None):
        """ Move both wheels forward """
        if speed is not None:
            self.speed = speed
        self.left_wheel.forward()
        self.right_wheel.forward()
        self.logger.info('Running forward')

    def forwardLeft(self, speed=None):
        """ Move left wheel forward """
        if speed is not None:
            self.speed = speed
        self.left_wheel.forward()
        self.logger.info('Left running forward')

    def forwardRight(self, speed=None):
        """ Move right wheel forward """
        if speed is not None:
            self.speed = speed
        self.right_wheel.forward()
        self.logger.info('Right running forward')

    def backward(self, speed=None):
        """ Move both wheels backward """
        if speed is not None:
            self.speed = speed
        self.left_wheel.backward()
        self.right_wheel.backward()
        self.logger.info('Running backward')

    def backwardLeft(self, speed=None):
        """ Move left wheels backward """
        if speed is not None:
            self.speed = speed
        self.left_wheel.backward()
        self.logger.info('Running backward left')

    def backwardRight(self, speed=None):
        """ Move right wheels backward """
        if speed is not None:
            self.speed = speed
        self.right_wheel.backward()
        self.logger.info('Running backward right')

    def stop(self):
        """ Stop both wheels """
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.logger.info('Stop')
    
    @property
    def speed(self, speed):
        return self._speed

    @speed.setter
    def speed(self, speed):
        self._speed = speed
        """ Set moving speeds """
        self.left_wheel.speed = self._speed
        self.right_wheel.speed = self._speed
        self.logger.info('Set speed to %s' % str(self._speed))

    def speedLeft(self, speed):
        self._speed = speed
        """ Set moving speeds """
        self.left_wheel.speed = self._speed
        self.logger.info('Set speed to %s' % str(self._speed))

    def speedRight(self, speed):
        self._speed = speed
        """ Set moving speeds """
        self.right_wheel.speed = self._speed
        self.logger.info('Set speed to %s' % str(self._speed))

    def ready(self):
        """ Get the back wheels to the ready position. (stop) """
        self.logger.info('Turn to "Ready" position')
        self.left_wheel.offset = self.forward_A
        self.right_wheel.offset = self.forward_B
        self.stop()

    def calibration(self):
        """ Get the front wheels to the calibration position. """
        self.logger.info('Turn to "Calibration" position')
        self.speed = 50
        self.forward()
        self.cali_forward_A = self.forward_A
        self.cali_forward_B = self.forward_B

    def cali_left(self):
        """ Reverse the left wheels forward direction in calibration """
        self.cali_forward_A = (1 + self.cali_forward_A) & 1
        self.left_wheel.offset = self.cali_forward_A
        self.forward()

    def cali_right(self):
        """ Reverse the right wheels forward direction in calibration """
        self.cali_forward_B = (1 + self.cali_forward_B) & 1
        self.right_wheel.offset = self.cali_forward_B
        self.forward()

    def cali_ok(self):
        """ Save the calibration value """
        self.forward_A = self.cali_forward_A
        self.forward_B = self.cali_forward_B
        self.db.set('forward_A', self.forward_A)
        self.db.set('forward_B', self.forward_B)
        self.stop()


if __name__ == '__main__':
    import time

    logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                        level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    back_wheels = Backwheels()
    DELAY = 0.01
    try:
        back_wheels.left_wheel.speed = 30
        back_wheels.right_wheel.speed = 30
        back_wheels.left_wheel.forward()
        back_wheels.right_wheel.backward()
        time.sleep(100)

        back_wheels.speed = 30
        back_wheels.forward()
        for i in range(0, 100):
            back_wheels.speed = i
            logger.info('Forward, speed = %s' % i)
            time.sleep(DELAY)
        for i in range(100, 0, -1):
            back_wheels.speed = i
            logger.info('Forward, speed = %s' % i)
            time.sleep(DELAY)

        back_wheels.backward()
        for i in range(0, 100):
            back_wheels.speed = i
            logger.info('Backward, speed = %s' % i)
            time.sleep(DELAY)
        for i in range(100, 0, -1):
            back_wheels.speed = i
            logger.info('Backward, speed = %s' % i)
            time.sleep(DELAY)

        back_wheels.backward()
        for i in range(0, 100):
            back_wheels.speed = i
            logger.info('Backward, speed = %s' % i)
            time.sleep(DELAY)
        for i in range(100, 0, -1):
            back_wheels.speed = i
            logger.info('Backward, speed = %s' % i)
            time.sleep(DELAY)
    except Exception as e:
        logger.exception("Error ...!")
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt, motor stop')
        back_wheels.stop()
    finally:
        logger.info('Finished, motor stop')
        back_wheels.stop()
