#!/usr/bin/env python3

from rpi_rf import RFDevice
from datetime import datetime, timedelta
from multiprocessing import Process, Value

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import logging.handlers
import RPi.GPIO as GPIO
import subprocess
import argparse
import logging
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

PIR_PIN = 26
RF_TX_PIN = 21
RF_RX_PIN = 20
LIGHT_PIN = 19
RF_PULSE_LENGTH = 180

RF_TX = RFDevice(RF_TX_PIN)
RF_TX.enable_tx()

SPI_PORT = 0
SPI_DEVICE = 0

IS_DARK = Value('i', 0)
ARE_LIGHTS_ON = Value('i', 0)

RF_RX_PROC = subprocess.Popen(['./433Utils/RFSniffer'],
                              stdout=subprocess.PIPE,
                              universal_newlines=True)

LOGGER = logging.getLogger(__name__)


def main():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    signal.signal(signal.SIGINT, exithandler)

    parser = argparse.ArgumentParser(description='Automate lights.')
    parser.add_argument('--log_to_file', help="log output to a file",
                        action="store_true")
    parser.add_argument('-t', '--testing', help="testing mode on",
                        action="store_true")
    try:
        args = parser.parse_args()
    except SystemExit:
        cleanup()
        sys.exit()

    setup_logger(args.log_to_file)
    start_processes(args.testing)


def start_processes(testing=False):
    listen_rf_proc = Process(target=listen_rf, args=(ARE_LIGHTS_ON,))
    listen_rf_proc.daemon = True
    listen_rf_proc.start()

    motion_process = Process(target=monitor_motion, args=(IS_DARK,))
    motion_process.daemon = True
    motion_process.start()

    pressure_process = Process(target=monitor_pressure, args=(IS_DARK,))
    pressure_process.daemon = True
    pressure_process.start()

    # light_process = Process(target=monitor_light, args=(IS_DARK,))
    # light_process.daemon = True
    # light_process.start()

    # Stop running at 6AM next day
    # Script is expected to be started by cron
    tomorrow = datetime.now().replace(hour=6) + timedelta(days=1)
    kill_at(tomorrow, testing)


def kill_at(end_time, testing=False):
    LOGGER.debug("Kill timer started")
    while True:
        if datetime.now() > end_time and not testing:
            LOGGER.debug("Killing")
            cleanup()
            sys.exit()
        time.sleep(60)


def listen_rf(lights_on):
    LOGGER.info("Started listening")
    LOGGER.debug("RFSniffer " + RF_RX_PROC.stdout.readline().strip())
    for line in iter(RF_RX_PROC.stdout.readline, ''):
        code, length = [int(n) for n in line.split(':')]
        LOGGER.debug("Code: %d, len: %d", code, length)
        if code == LIGHT_CODES["all"]["on"]:
            LOGGER.info("Detected lights on")
            lights_on.value = 1
        elif code == LIGHT_CODES["all"]["off"]:
            LOGGER.info("Detected lights off")
            lights_on.value = 0


def monitor_pressure(is_dark):
    def median(in_list):
        l = len(in_list)
        if l == 0:
            return 0
        return sorted(in_list)[l // 2]

    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    last_values = []
    last_median = 0
    while True:
        value = mcp.read_adc(6)
        curr_median = median(last_values)
        if curr_median >= 30 and last_median < 30 and not is_dark.value:
            LOGGER.info("Lazy bum")
            all_lights_off(15)
        last_values.append(value)
        if len(last_values) > 5:
            last_values.pop(0)
        last_median = curr_median
        time.sleep(0.25)


def monitor_light(is_dark):
    GPIO.setup(LIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    is_dark.value = GPIO.input(LIGHT_PIN)
    while True:
        GPIO.wait_for_edge(LIGHT_PIN, GPIO.BOTH)
        is_dark.value = GPIO.input(LIGHT_PIN)
        print(is_dark.value)


def monitor_motion(is_dark):
    GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    bedtime = datetime.now().replace(hour=23)

    while True:
        GPIO.wait_for_edge(PIR_PIN, GPIO.RISING)
        LOGGER.debug("You moved, dark: " + str(is_dark.value))
        # if is_dark.value:
        if datetime.now() > bedtime:
            # It's late! Just turn on one light
            LOGGER.debug("Only turning on light 2 because it's late")
            turn_lights_on(2)
        else:
            all_lights_on()
        # Don't re-trigger for 30 seconds
        time.sleep(30)


def all_lights_on(delay=None):
    """Turn all lights on"""
    turn_lights_on("all")


def turn_lights_on(light, delay=None):
    """Turn a light on, with light being the key for LIGHT_CODES"""
    LOGGER.info("Turning lights on")
    if ARE_LIGHTS_ON.value:
        LOGGER.warning("Cancelled as lights already on")
        return
    transmit_rf(LIGHT_CODES[light]["on"], delay)


def all_lights_off(delay=None):
    """Turn all lights off"""
    LOGGER.info("Turning lights off")
    if not ARE_LIGHTS_ON.value:
        LOGGER.warning("Cancelled as lights already off")
        return
    transmit_rf(LIGHT_CODES["all"]["off"], delay)


def transmit_rf(code, delay=None):
    """Transmit an RF code. Tries 3 times for reliability"""
    if delay:
        time.sleep(delay)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)
    time.sleep(0.10)
    RF_TX.tx_code(code, tx_pulselength=RF_PULSE_LENGTH)


def setup_logger(log_to_file=False):
    formatter = logging.Formatter(
        '%(asctime)s : %(name)-10s : %(levelname)-7s : %(message)s')

    LOGGER.setLevel(logging.DEBUG)
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            'automate.log', maxBytes=10000, backupCount=1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        LOGGER.addHandler(file_handler)
    else:
        print_handler = logging.StreamHandler(sys.stdout)
        print_handler.setLevel(logging.DEBUG)
        print_handler.setFormatter(formatter)
        LOGGER.addHandler(print_handler)

    LOGGER.debug("Starting main")


def exithandler(signal, frame):
    cleanup()


def cleanup():
    LOGGER.info("Cleaning up")
    # This also calls GPIO.cleanup()
    RF_TX.cleanup()
    RF_RX_PROC.kill()
    sys.exit()


if __name__ == '__main__':
    main()
