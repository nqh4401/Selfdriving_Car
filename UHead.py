#!/usr/bin/env python3

import os
import sys
import time
import json
import pathlib
import logging
from multiprocessing import Process, Value

import RPi.GPIO as GPIO

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from Servo import Servo


class UHead(object):
    """ Ultrasonic Sensor Head control class """
    HEADER_CHANNEL = 3
    U_CHANNEL = 20
    TIMEOUT = 0.05
    MOUNT = 5
    ALARM_GATE = 20

    def __init__(self, db="config.json", bus_number=1, u_header=U_CHANNEL, header_channel=HEADER_CHANNEL):
        """ setup channels and basic stuff """
        self.logger = logging.getLogger(__name__)
        try:
            with open(os.path.join(os.getcwd(), db), 'r') as configFile:
                jsondata = configFile.read()
            self.db = json.loads(jsondata)

            # -> Header Servo
            self._header_channel = header_channel
            self.head = Servo(self._header_channel, bus_number=bus_number, offset=self.db["head_offset"])
            self.head.setup()

            self._straight_angle = 90
            self.turning_max = 90
            self._angle = {"left": self._min_angle, "straight": self._straight_angle, "right": self._max_angle}
            self.turning_offset = self.db["turning_offset"]

            # -> U Sensor GPIOs
            self._u_channel = u_header
            GPIO.setmode(GPIO.BCM)
            self.killSwitch = Value('i', 1)
            self.distance = Value('f', 0)

            self.logger.info('UHead PWM channel: %s' % self._header_channel)
            self.logger.info('UHead offset value: %s ' % self.turning_offset)
            self.logger.info('left angle: %s, straight angle: %s, right angle: %s'
                             % (self._angle["left"], self._angle["straight"], self._angle["right"]))
        except IOError as e:
            self.logger.info("CWD: %s" % os.getcwd())
            self.logger.exception("Can't open/read config pls. Please specify the path relative to your main.py file")
            raise Exception from e
        except ValueError as e:
            self.logger.exception("Json value error")
            raise Exception from e

    def u_distance(self):
        pulse_end = 0
        pulse_start = 0
        GPIO.setup(self._u_channel, GPIO.OUT)
        GPIO.output(self._u_channel, False)
        time.sleep(0.01)
        GPIO.output(self._u_channel, True)
        time.sleep(0.00001)
        GPIO.output(self._u_channel, False)
        GPIO.setup(self._u_channel, GPIO.IN)

        timeout_start = time.time()
        while GPIO.input(self._u_channel) == 0:
            pulse_start = time.time()
            if pulse_start - timeout_start > self.TIMEOUT:
                return -1
        while GPIO.input(self._u_channel) == 1:
            pulse_end = time.time()
            if pulse_start - timeout_start > self.TIMEOUT:
                return -1
        if pulse_start != 0 and pulse_end != 0:
            pulse_duration = pulse_end - pulse_start
            # Sekunden * 100 (fuer cm) * Schallgeschw in m/s /(hin plus zurueck)
            distance = pulse_duration * 100 * 343.2 / 2
            distance = int(distance)
            self.logger.debug('start: %s, end: %s' % (pulse_start, pulse_end))
            if distance >= 0:
                return distance  # in cm
            else:
                return -1
        else:
            self.logger.debug('start: %s, end: %s' % (pulse_start, pulse_end))
            return -1

    def measure(self, mount=MOUNT):
        self.logger.debug("Start Process ..")
        while self.killSwitch.value:
            sum_of_distances = 0
            for i in range(mount):
                sum_of_distances += self.u_distance()
            self.distance.value = sum_of_distances / mount
            self.logger.debug("Measured %s cm" % self.distance.value)
        self.logger.debug("Kill Process ..")

    def get_distance(self):
        return self.u_distance()

    def start_measurement_process(self):
        self.logger.info("Start measuring process..")
        self.p = Process(target=self.measure)
        self.p.start()

    def stop_measurement_process(self):
        self.logger.info("Stop measuring process..")
        self.killSwitch.value = 0
        self.p.join()

    def less_than(self, angle=None, alarm_gate=ALARM_GATE):
        dist = self.get_distance()
        state = 0
        if 0 <= dist <= alarm_gate:
            state = 1
        elif dist > alarm_gate:
            state = 0
        else:
            state = -1
        self.logger.info('distance: %s, status: %s' % dist, state)
        return state

    def turn_left(self):
        """ Turn the front heads left """
        self.logger.info('Turn left')
        self.head.write(self._angle["left"])

    def turn_straight(self):
        """ Turn the front heads back straight """
        self.logger.info('Turn straight')
        self.head.write(self._angle["straight"])

    def turn_right(self):
        """ Turn the front heads right """
        self.logger.info('Turn right')
        self.head.write(self._angle["right"])

    def turn(self, angle):
        """ Turn the front heads to the giving angle """
        self.logger.info('Turn to %s ' % angle)
        if angle < self._angle["left"]:
            angle = self._angle["left"]
        if angle > self._angle["right"]:
            angle = self._angle["right"]
        self.head.write(angle)

    @property
    def header_channel(self):
        return self._header_channel

    @header_channel.setter
    def header_channel(self, chn):
        self._header_channel = chn

    @property
    def u_channel(self):
        return self._u_channel

    @u_channel.setter
    def u_channel(self, chn):
        self._u_channel = chn

    @property
    def turning_max(self):
        return self._turning_max

    @turning_max.setter
    def turning_max(self, angle):
        self._turning_max = angle
        self._min_angle = self._straight_angle - angle
        self._max_angle = self._straight_angle + angle
        self._angle = {"left": self._min_angle, "straight": self._straight_angle, "right": self._max_angle}

    @property
    def turning_offset(self):
        return self._turning_offset

    @turning_offset.setter
    def turning_offset(self, value):
        if not isinstance(value, int):
            raise TypeError('"turning_offset" must be "int"')
        self._turning_offset = value
        self.db['turning_offset'] = value
        self.head.offset = value
        self.turn_straight()

    def ready(self):
        """ Get the front heads to the ready position. """
        self.logger.info('Turn to "Ready" position')
        self.head.offset = self.turning_offset
        self.turn_straight()

    def calibration(self):
        """ Get the front heads to the calibration position. """
        self.logger.info('Turn to "Calibration" position')
        self.turn_straight()
        self.cali_turning_offset = self.turning_offset

    def cali_left(self):
        """ Calibrate the heads to left """
        self.cali_turning_offset -= 1
        self.head.offset = self.cali_turning_offset
        self.turn_straight()

    def cali_right(self):
        """ Calibrate the heads to right """
        self.cali_turning_offset += 1
        self.head.offset = self.cali_turning_offset
        self.turn_straight()

    def cali_ok(self):
        """ Save the calibration value """
        self.turning_offset = self.cali_turning_offset
        self.db['turning_offset'] = self.turning_offset


if __name__ == '__main__':
    import time

    logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                        level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    try:
        usensor = UHead()
        logger.info('Start Process..')
        usensor.start_measurement_process()

        logger.info('turn_left')
        usensor.turn_left()
        logger.info('Measured distance: %s' % usensor.get_distance())
        time.sleep(3)
        logger.info('turn_straight')
        usensor.turn_straight()
        logger.info('Measured distance: %s' % usensor.get_distance())
        time.sleep(3)
        logger.info('turn_right')
        usensor.turn_right()
        logger.info('Measured distance: %s' % usensor.get_distance())
        time.sleep(3)
        logger.info('turn_straight')
        usensor.turn_straight()
        logger.info('Measured distance: %s' % usensor.get_distance())
        time.sleep(3)

        logger.info('Join Process..')
        usensor.stop_measurement_process()
        logger.info('Exit')
    except KeyboardInterrupt:
        usensor.turn_straight()
        logger.info('Join Process..')
        usensor.stop_measurement_process()
        logger.info('Exit')
    except Exception:
        usensor.stop_measurement_process()
        self.logger.exception("Fatal Error.! - Goodbye ^.^")


