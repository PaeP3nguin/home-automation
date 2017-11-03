/*
  RFSniffer

  Usage: ./RFSniffer [<pulseLength>]
  [] = optional

  Hacked from http://code.google.com/p/rc-switch/
  by @justy to provide a handy RF code sniffer
*/

#include "rc-switch/RCSwitch.h"
#include <cstdio>
#include <cstdlib>
#include <ctime>

int main(int argc, char *argv[]) {
	if (wiringPiSetupGpio() == -1) {
		printf("setup-fail");
		return 0;
	} else {
		printf("setup");
	}

	// Using BCM numbering
	int PIN = 20;
	if (argv[1] != NULL) {
		PIN = atoi(argv[1]);
	}

	RCSwitch rfReceiver = RCSwitch();
	rfReceiver.enableReceive(PIN);

	int milliseconds = 100;
	struct timespec ts;
	ts.tv_sec = 0;
	ts.tv_nsec = milliseconds * 1000000L;

	while (true) {
		if (rfReceiver.available()) {
			int value = rfReceiver.getReceivedValue();

			if (value != 0) {
				// code:pulse length, ex. 4551939:180
				printf("%i:%i\n", value, rfReceiver.getReceivedDelay());
			}

			rfReceiver.resetAvailable();
		}

		// Sleep 100ms so we just check 10x a second instead of as fast as possible
		nanosleep(&ts, NULL);
	}

	exit(0);
}
