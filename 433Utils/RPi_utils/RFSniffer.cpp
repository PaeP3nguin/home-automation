/*
  RFSniffer

  Usage: ./RFSniffer [<pulseLength>]
  [] = optional

  Hacked from http://code.google.com/p/rc-switch/
  by @justy to provide a handy RF code sniffer
*/

#include "../rc-switch/RCSwitch.h"
#include <stdio.h>
#include <stdlib.h>

RCSwitch mySwitch;

int main(int argc, char *argv[]) {
	// This pin is not the first pin on the RPi GPIO header!
	// Consult https://projects.drogon.net/raspberry-pi/wiringpi/pins/
	// for more information.
	int PIN = 20;

	if (wiringPiSetupGpio() == -1) {
		printf("wiringPiSetup failed, exiting...");
		return 0;
	}

	int pulseLength = 0;
	if (argv[1] != NULL) {
		pulseLength = atoi(argv[1]);
	}

	mySwitch = RCSwitch();
	if (pulseLength != 0) {
		mySwitch.setPulseLength(pulseLength);
	}
	mySwitch.enableReceive(PIN);

	while (1) {
		if (mySwitch.available()) {
			int value = mySwitch.getReceivedValue();

			if (value == 0) {
				printf("Unknown encoding\n");
			} else {
				printf("Received %i\n", mySwitch.getReceivedValue());
				printf("Received pulse %i\n", mySwitch.getReceivedDelay());
			}

			mySwitch.resetAvailable();
		}
	}

	exit(0);
}
