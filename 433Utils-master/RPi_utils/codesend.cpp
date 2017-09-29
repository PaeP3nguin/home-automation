/*
Usage: ./codesend decimalcode [protocol] [pulselength]
decimalcode - As decoded by RFSniffer
protocol    - According to rc-switch definitions
pulselength - pulselength in microseconds

 'codesend' hacked from 'send' by @justy

 - The provided rc_switch 'send' command uses the form systemCode, unitCode, command
   which is not suitable for our purposes.  Instead, we call
   send(code, length); // where length is always 24 and code is simply the code
   we find using the RF_sniffer.ino Arduino sketch.

(Use RF_Sniffer.ino to check that RF signals are being produced by the RPi's transmitter
or your remote control)
*/
#include "../rc-switch/RCSwitch.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
	// This pin is not the first pin on the RPi GPIO header!
	// Consult https://projects.drogon.net/raspberry-pi/wiringpi/pins/
	// for more information.
	int PIN = 0;

	// Parse the first parameter to this command as an integer
	int protocol = 0; // A value of 0 will use rc-switch's default value
	int pulseLength = 0;

	// If no command line argument is given, print the help text
	if (argc == 1) {
		printf("Usage: %s decimalcode [protocol] [pulselength]\n", argv[0]);
		printf("decimalcode\t- As decoded by RFSniffer\n");
		printf("protocol\t- According to rc-switch definitions\n");
		printf("pulselength\t- pulselength in microseconds\n");
		return -1;
	}

	// Change protocol and pulse length accroding to parameters
	int code = atoi(argv[1]);
	if (argc >= 3)
		protocol = atoi(argv[2]);
	if (argc >= 4)
		pulseLength = atoi(argv[3]);

	printf("sending code[%i]\n", code);
	return sendCode(code, PIN, pulseLength);
}

int sendCode(int code, int pin, int pulseLength) {
	if (wiringPiSetup() == -1) {
		return 1;
    }

	RCSwitch mySwitch = RCSwitch();
	mySwitch.enableTransmit(pin);
    mySwitch.setPulseLength(pulseLength);

    mySwitch.send(code, 24);

    return 0;
}
