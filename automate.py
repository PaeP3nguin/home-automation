#!/usr/bin/env python3

from rpi_rf import RFDevice
from multiprocessing import Process

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO
import time

PIR_PIN = 13
PRESSURE_PIN = 18
RF_TX_PIN = 21
LIGHT_PIN = 27
RF_PULSE_LENGTH = 180
ON_CODE = 4543795
OFF_CODE = 4543804
ALL_ON_CODE = 4551939
ALL_OFF_CODE = 4551948

RF = RFDevice(RF_TX_PIN)
RF.enable_tx()

SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))


def main():
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    while True:
        reading = GPIO.input(27)
        print(reading)
        time.sleep(0.10)
        if reading:
            RF.tx_code(ON_CODE, tx_pulselength=RF_PULSE_LENGTH)
        else:
            RF.tx_code(OFF_CODE, tx_pulselength=RF_PULSE_LENGTH)
        # pressure.wait_for_pressure()
        # print("PRESSURE_PRESSURE_PRESSURE_PRESSURE_PRESSURE")
        # pressure.wait_for_no_pressure()


def monitor_pressure():
    while True:
        value = mcp.read_adc(6)
        if value >= 20:
            print("Lazy bum")
            all_lights_off(15)
        else:
            time.sleep(0.25)


def monitor_light():
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while True:
        light = GPIO.input(27)
        print(light)
        if not light:
            RF.tx_code(ON_CODE, tx_pulselength=RF_PULSE_LENGTH)
        else:
            RF.tx_code(OFF_CODE, tx_pulselength=RF_PULSE_LENGTH)


def monitor_motion():
    GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    while True:
        GPIO.wait_for_edge(PIR_PIN, GPIO.RISING)
        print("You moved")
        RF.tx_code(ON_CODE, tx_pulselength=RF_PULSE_LENGTH)
        GPIO.wait_for_edge(PIR_PIN, GPIO.FALLING)
        RF.tx_code(OFF_CODE, tx_pulselength=RF_PULSE_LENGTH)


def all_lights_on(delay=None):
    """Turn all lights on"""
    transmit_rf(ALL_ON_CODE, delay)


def all_lights_off(delay=None):
    """Turn all lights off"""
    transmit_rf(ALL_OFF_CODE, delay)


def transmit_rf(code, delay=None):
    """Transmit an RF code"""
    if delay:
        time.sleep(delay)
    RF.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)


if __name__ == '__main__':
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # pressure_process = Process(target=monitor_pressure)
    # pressure_process.start()

    # pressure_process.join()

    motion_process = Process(target=monitor_pressure)
    motion_process.start()

    motion_process.join()

    # main()
    # crain()
    # GPIO.add_event_detect(PRESSURE_PIN, GPIO.BOTH, callback=high_pressure)
    # while True:
    # time.sleep(60)
    # Also calls GPIO.cleanup()
    RF.cleanup()
