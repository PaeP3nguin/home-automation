#!/usr/bin/env python3

from rpi_rf import RFDevice
from multiprocessing import Process

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO
import signal
import time
import sys

LIGHT_CODES = {
    1: {
        "on": 4543795,
        "off": 4543804,
    },
    2: {
        "on": 4543939,
        "off": 4543948,
    },
    3: {
        "on": 4544259,
        "off": 4544268,
    },
    "all": {
        "on": 4551939,
        "off": 4551948,
    },
}

PIR_PIN = 13
PRESSURE_PIN = 18
RF_TX_PIN = 21
RF_RX_PIN = 20
LIGHT_PIN = 27
RF_PULSE_LENGTH = 180

RF_TX = RFDevice(RF_TX_PIN)
RF_TX.enable_tx()

RF_RX = RFDevice(RF_RX_PIN)
# RF_RX.enable_rx()

SPI_PORT = 0
SPI_DEVICE = 0


def main():
    # listen_rf_proc = Process(target=listen_rf)
    motion_process = Process(target=monitor_pressure)
    # pressure_process = Process(target=monitor_pressure)

    # listen_rf_proc.start()
    motion_process.start()
    # pressure_process.start()

    # listen_rf_proc.join()
    motion_process.join()
    # pressure_process.join()


def monitor_pressure():
    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    while True:
        value = mcp.read_adc(6)
        if value >= 20:
            print("Lazy bum")
            all_lights_off(15)
        else:
            time.sleep(0.25)


def monitor_light():
    GPIO.setup(LIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while True:
        light = GPIO.input(LIGHT_PIN)
        print(light)
        if not light:
            RF_TX.tx_code(LIGHT_CODES[1]["on"],
                          tx_pulselength=RF_PULSE_LENGTH)
        else:
            RF_TX.tx_code(LIGHT_CODES[1]["off"],
                          tx_pulselength=RF_PULSE_LENGTH)


def monitor_motion():
    GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    while True:
        GPIO.wait_for_edge(PIR_PIN, GPIO.RISING)
        print("You moved")
        RF_TX.tx_code(LIGHT_CODES[1]["on"], tx_pulselength=RF_PULSE_LENGTH)
        GPIO.wait_for_edge(PIR_PIN, GPIO.FALLING)
        RF_TX.tx_code(LIGHT_CODES[1]["off"], tx_pulselength=RF_PULSE_LENGTH)


def listen_rf():
    last_rf = None

    while True:
        if RF_RX.rx_code_timestamp != last_rf:
            last_rf = RF_RX.rx_code_timestamp
            print("code: {}, pulselength: {}, protocol: {}".format(
                str(RF_RX.rx_code), str(RF_RX.rx_pulselength), str(RF_RX.rx_proto)))
        time.sleep(0.25)


def all_lights_on(delay=None):
    """Turn all lights on"""
    transmit_rf(LIGHT_CODES["all"]["on"], delay)


def all_lights_off(delay=None):
    """Turn all lights off"""
    transmit_rf(LIGHT_CODES["all"]["off"], delay)


def transmit_rf(code, delay=None):
    """Transmit an RF code"""
    if delay:
        time.sleep(delay)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)


def exithandler(signal, frame):
    # These also call GPIO.cleanup()
    RF_TX.cleanup()
    RF_RX.cleanup()
    sys.exit(0)


if __name__ == '__main__':
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    signal.signal(signal.SIGINT, exithandler)

    main()
