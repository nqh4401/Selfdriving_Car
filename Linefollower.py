#!/usr/bin/env python3

import logging
import math
import time

# import smbus
from smbus2 import SMBus


class Linefollower(object):
    def __init__(self, address=0x11, references=[170,170,170,170,170]):
        self.logger = logging.getLogger(__name__)
        self.bus = SMBus(1)
        self.address = address
        self._references = references

    def read_raw(self):
        for i in range(0, 5):
            try:
                raw_result = self.bus.read_i2c_block_data(self.address, 0, 10)
                Connection_OK = True
                break
            except:
                Connection_OK = False

        if Connection_OK:
            return raw_result
        else:
            self.logger.error('Error accessing %2X' % self.address)
            return False

    def read_analog(self, trys=5):
        for _ in range(trys):
            raw_result = self.read_raw()
            if raw_result:
                analog_result = [0, 0, 0, 0, 0]
                for i in range(0, 5):
                    high_byte = raw_result[i * 2] << 8
                    low_byte = raw_result[i * 2 + 1]
                    analog_result[i] = high_byte + low_byte
                    if analog_result[i] > 1024:
                        continue
                return analog_result
        else:
            raise IOError("Line follower read error. Please check the wiring.")

    def read_digital(self, references=None):
        lt = self.read_analog()
        digital_list = []
        if not references:
            references = self.references
        for i in range(0, 5):
            if lt[i] > references[i]:
                digital_list.append(0)
            elif lt[i] < references[i]:
                digital_list.append(1)
            else:
                digital_list.append(-1)
        return digital_list

    def get_average(self, mount):
        if not isinstance(mount, int):
            raise ValueError("Mount must be integer")
        average = [0, 0, 0, 0, 0]
        lt_list = [[], [], [], [], []]
        for times in range(0, mount):
            lt = self.read_analog()
            for lt_id in range(0, 5):
                lt_list[lt_id].append(lt[lt_id])
        for lt_id in range(0, 5):
            average[lt_id] = int(math.fsum(lt_list[lt_id]) / mount)
        return average

    def found_line_in(self, timeout):
        if isinstance(timeout, int) or isinstance(timeout, float):
            pass
        else:
            raise ValueError("timeout must be integer or float")
        time_start = time.time()
        time_during = 0
        while time_during < timeout:
            lt_status = self.read_digital()
            result = 0
            if 1 in lt_status:
                return lt_status
            time_now = time.time()
            time_during = time_now - time_start
        return False

    def wait_tile_status(self, status):
        while True:
            lt_status = self.read_digital()
            if lt_status in status:
                break

    def wait_tile_center(self):
        while True:
            lt_status = self.read_digital()
            if lt_status[2] == 1:
                break
        print("%d", lt_status[2])

    def cali(self, fw):
        references = [0, 0, 0, 0, 0]
        print("cali for module:\n  first put all sensors on white, then put all sensors on black")
        mount = 100
        #fw.turn(70)
        print("\n cali white")
        time.sleep(4)
        #fw.turn(90)
        white_references = self.get_average(mount)
        #fw.turn(95)
        time.sleep(0.5)
        #fw.turn(85)
        time.sleep(0.5)
        #fw.turn(90)
        time.sleep(1)

        #fw.turn(110)
        print("\n cali black")
        time.sleep(4)
        #fw.turn(90)
        black_references = self.get_average(mount)
        #fw.turn(95)
        time.sleep(0.5)
        #fw.turn(85)
        time.sleep(0.5)
        #fw.turn(90)
        time.sleep(1)

        for i in range(0, 5):
            references[i] = (white_references[i] + black_references[i]) / 2
        print("Middle references =", references)
        time.sleep(1)
        return references


    @property
    def references(self):
        return self._references

    @references.setter
    def references(self, value):
        self._references = value


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    try:
        lf = Linefollower()
        while True:
            logger.info(lf.read_analog())
            logger.info(lf.read_digital())
            time.sleep(0.5)
    except Exception as e:
        logger.exception("Error ...!")
    except KeyboardInterrupt as e:
        logger.info("Keyboard Interrupt - Goodbye")

