#!/usr/bin/env python3
"""
**********************************************************************
* Filename    : PCA9685.py
* Description : A driver module for PCA9685
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Version     : v2.0.0
**********************************************************************
"""
import logging
import math
import time

# import smbus
from smbus2 import SMBus


class PWM(object):
    """A PWM control class for PCA9685."""
    _MODE1 = 0x00
    _MODE2 = 0x01
    _SUBADR1 = 0x02
    _SUBADR2 = 0x03
    _SUBADR3 = 0x04
    _PRESCALE = 0xFE
    _LED0_ON_L = 0x06
    _LED0_ON_H = 0x07
    _LED0_OFF_L = 0x08
    _LED0_OFF_H = 0x09
    _ALL_LED_ON_L = 0xFA
    _ALL_LED_ON_H = 0xFB
    _ALL_LED_OFF_L = 0xFC
    _ALL_LED_OFF_H = 0xFD

    _RESTART = 0x80
    _SLEEP = 0x10
    _ALLCALL = 0x01
    _INVRT = 0x10
    _OUTDRV = 0x04

    def __init__(self, bus_number=1, address=0x40):
        self.logger = logging.getLogger(__name__)
        self._frequency = 60
        self.address = address
        self.bus_number = bus_number
        self.bus = SMBus(self.bus_number)

    def setup(self):
        """Init the class with bus_number and address"""
        self.logger.info('Resetting PCA9685 MODE1 (without SLEEP) and MODE2')
        self.write_all_value(0, 0)
        self._write_byte_data(self._MODE2, self._OUTDRV)
        self._write_byte_data(self._MODE1, self._ALLCALL)
        time.sleep(0.005)

        mode1 = self._read_byte_data(self._MODE1)
        mode1 = mode1 & ~self._SLEEP
        self._write_byte_data(self._MODE1, mode1)
        time.sleep(0.005)

    def _write_byte_data(self, reg, value):
        """Write data to I2C with self.address"""
        self.logger.info('Writing value %2X to %2X' % (value, reg))
        try:
            self.bus.write_byte_data(self.address, reg, value)
        except Exception:
            self._check_i2c()
            self.logger.exception("Write Data Byte Error.")

    def _read_byte_data(self, reg):
        """Read data from I2C with self.address"""
        self.logger.info('Reading value from %2X' % reg)
        try:
            results = self.bus.read_byte_data(self.address, reg)
            return results
        except Exception as e:
            self._check_i2c()
            self.logger.exception("Read Data Byte Error.")

    def _run_command(self, cmd):
        import subprocess
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = p.stdout.read().decode('utf-8')
        status = p.poll()
        self.logger.debug('Results:\n %sStatus: %s' % (result, status))
        return status, result

    def _check_i2c(self):
        from os import listdir
        self.logger.debug('I2C bus number is: %s' % self.bus_number)
        self.logger.debug('Checking I2C device:')
        devices = listdir("/dev/")
        if "i2c-%d" % self.bus_number in devices:
            self.logger.debug('I2C device exist.')
        else:
            self.logger.warning('Seems like I2C have not been set, run "sudo raspi-config" to enable I2C')
        cmd = "i2cdetect -y %s" % self.bus_number
        _, output = self._run_command(cmd)
        self.logger.debug('Your PCA9685 address is set to 0x%02X' % self.address)
        self.logger.debug('i2cdetect output: \n%s' % output)
        outputs = output.split('\n')[1:]
        addresses = []
        for tmp_addresses in outputs:
            tmp_addresses = tmp_addresses.split(':')
            if len(tmp_addresses) < 2:
                continue
            else:
                tmp_addresses = tmp_addresses[1]
            tmp_addresses = tmp_addresses.strip().split(' ')
            for address in tmp_addresses:
                if address != '--':
                    addresses.append(address)
        if addresses == []:
            self.logger.warning('Conneceted i2c device: None')
        else:
            self.logger.debug('Conneceted i2c device:')
            for address in addresses:
                self.logger.info('  0x%s' % address)
        if "%02X" % self.address in addresses:
            self.logger.error(
                'Wierd, I2C device is connected, Try to run the program again, If problem stills, email this information to support@sunfounder.com')
        else:
            self.logger.error('Device is missing. '
                              'Check the address or wiring of PCA9685 Server driver, or email this information to support@sunfounder.com'
                              )
            quit()

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, freq):
        """Set PWM frequency"""
        self._frequency = freq
        prescale_value = 25000000.0
        prescale_value /= 4096.0
        prescale_value /= float(freq)
        prescale_value -= 1.0
        self.logger.info('Setting PWM frequency to %d Hz' % freq)
        self.logger.info('Estimated pre-scale: %d' % prescale_value)
        prescale = math.floor(prescale_value + 0.5)
        self.logger.info('Final pre-scale: %d' % prescale)

        old_mode = self._read_byte_data(self._MODE1)
        new_mode = (old_mode & 0x7F) | 0x10
        self._write_byte_data(self._MODE1, new_mode)
        self._write_byte_data(self._PRESCALE, int(math.floor(prescale)))
        self._write_byte_data(self._MODE1, old_mode)
        time.sleep(0.005)
        self._write_byte_data(self._MODE1, old_mode | 0x80)

    def write(self, channel, on, off):
        """Set on and off value on specific channel"""
        self.logger.info('Set channel "%d" to value "%d"' % (channel, off))
        self._write_byte_data(self._LED0_ON_L + 4 * channel, on & 0xFF)
        self._write_byte_data(self._LED0_ON_H + 4 * channel, on >> 8)
        self._write_byte_data(self._LED0_OFF_L + 4 * channel, off & 0xFF)
        self._write_byte_data(self._LED0_OFF_H + 4 * channel, off >> 8)

    def write_all_value(self, on, off):
        """Set on and off value on all channel"""
        self.logger.info('Set all channel to value "%d"' % off)
        self._write_byte_data(self._ALL_LED_ON_L, on & 0xFF)
        self._write_byte_data(self._ALL_LED_ON_H, on >> 8)
        self._write_byte_data(self._ALL_LED_OFF_L, off & 0xFF)
        self._write_byte_data(self._ALL_LED_OFF_H, off >> 8)

    def map(self, x, in_min, in_max, out_min, out_max):
        """To map the value from arange to another"""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

if __name__ == '__main__':
    import time

    logging.basicConfig(format='[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d|%(levelname)s] -> %(message)s',
                        level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    try:
        pwm = PWM()
        pwm.frequency = 60
        for i in range(16):
            time.sleep(0.5)
            logger.info('\nChannel %d\n' % i)
            time.sleep(0.5)
            for j in range(4096):
                pwm.write(i, 0, j)
                logger.info('PWM value: %d' % j)
                time.sleep(0.0003)
    except KeyboardInterrupt as e:
        logger.info("Keyboard Interrupt - Goodbye")
    except Exception:
        self.logger.exception("Fatal Error.! - Goodbye ^.^")

