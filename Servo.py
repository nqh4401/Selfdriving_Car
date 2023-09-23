#!/usr/bin/env python3
"""
**********************************************************************
* Filename    : Servo.py
* Description : Driver module for servo, with PCA9685
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-13    New release
*               Cavon    2016-09-21    Change channel from 1 to all
**********************************************************************
"""
import sys
import pathlib
import logging

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PCA9685 import PWM


class Servo(object):
    """Servo driver class"""
    _MIN_PULSE_WIDTH = 600
    _MAX_PULSE_WIDTH = 2400
    _DEFAULT_PULSE_WIDTH = 1500
    _FREQUENCY = 60

    def __init__(self, channel, offset=0, lock=True, bus_number=1, address=0x40):
        """ Init a servo on specific channel, this offset """
        self.logger = logging.getLogger(__name__)
        if channel < 0 or channel > 16:
            raise ValueError("Servo channel \"{0}\" is not in (0, 15).".format(channel))
        self.channel = channel
        self.offset = offset
        self.lock = lock
        self.pwm = PWM(bus_number=bus_number, address=address)
        self.frequency = self._FREQUENCY
        self.write(90)

    def setup(self):
        self.pwm.setup()

    def _angle_to_analog(self, angle):
        """ Calculate 12-bit analog value from giving angle """
        pulse_wide = self.pwm.map(angle, 0, 180, self._MIN_PULSE_WIDTH, self._MAX_PULSE_WIDTH)
        analog_value = int(float(pulse_wide) / 1000000 * self.frequency * 4096)
        self.logger.debug('Angle %d equals Analog_value %d' % (angle, analog_value))
        return analog_value

    @property
    def frequency(self):
        return self._frequency
    @frequency.setter
    def frequency(self, value):
        self._frequency = value
        self.pwm.frequency = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        """ Set offset for much user-friendly """
        self._offset = value
        self.logger.debug('Set offset to %d' % self.offset)

    def write(self, angle):
        """ Turn the servo with giving angle. """
        if self.lock:
            if angle > 180:
                angle = 180
            if angle < 0:
                angle = 0
        else:
            if angle < 0 or angle > 180:
                raise ValueError("Servo \"{0}\" turn angle \"{1}\" is not in (0, 180).".format(self.channel, angle))
        val = self._angle_to_analog(angle)
        val += self.offset
        self.pwm.write(self.channel, 0, val)
        self.logger.info('Turn angle = %d' % angle)


if __name__ == '__main__':
    import sys
    import time

    logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                        level=logging.DEBUG)

    try:
        logger = logging.getLogger(__name__)
        a = Servo(1)
        b = Servo(2)
        c = Servo(3)
        a.setup()
        for i in range(0, 180, 5):
            logger.info(i)
            a.write(i)
            b.write(i)
            c.write(i)
            time.sleep(0.1)
        for i in range(180, 0, -5):
            logger.info(i)
            a.write(i)
            b.write(i)
            c.write(i)
            time.sleep(0.1)
    except KeyboardInterrupt as e:
        logger.info("Keyboard Interrupt - Goodbye")
    except Exception:
        self.logger.exception("Fatal Error.! - Goodbye ^.^")

