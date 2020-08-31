# Citymapper ETA Clock

An Arduino project for building a WiFi-powered ETA clock, that displays the number of minutes until you're expected to arrive, when a Citymapper ETA is shared with it.

In order to share with the system, either use [HTTP Request Shortcuts](https://play.google.com/store/apps/details?id=ch.rmy.android.http_shortcuts) for Android with the supplied `settings.json` (alter the URL to match your own), or use workflow.is for iOS.

The system consists of two components:

First, an AWS setup (which could easily be ported to a Raspberry Pi if you're willing to put it on the internet). It consists of an API Gateway that triggers a lambda that then enables a cloudwatch rule to trigger itself every minute until the ETA expires or you arrive. Each minute it updates the eta into an S3 bucket that's set to serve static HTTP, from which the Arduino gets its information.

Second, an Arduino Nano Nano 33 IOT project that fetches this information and reports the current eta using a stepper motor, updating every minute.

The dial points to zero when idle, and counts down from 60 minutes otherwise.

The Arduino WiFi connection can be re/configured via BLE to save having to reprogram. The stepper motor position can also be manually reset if required.

To set up the 'server-side' component on AWS (you could of course host it yourself elsewhere if suitable, but this setup costs <$1/mo, or free during first year):

* Create a Lambda function with a python 3 runtime
* Create a Bucket to store the data, and enable static website hosting
* Create a Cloudwatch event rule to trigger the lambda every minute (disabled to begin with!)
* Make sure the lambda has permissions to write to the bucket
* Create an API Gateway endpoint that backs onto the lambda
* Update the Arduino project with the S3 URL to get its angle
* Use [HTTP Request Shortcuts](https://play.google.com/store/apps/details?id=ch.rmy.android.http_shortcuts) on Android (or workflow.is on iOS - untested) to set up a Share menu option that calls the API Gateway webhook

The Arduino project requires the following:

* An Arduino Nano 333 IOT
* A 28BYJ-48 Stepper moter and ULN2003 driver board
* A push to break switch (to reset the stepper) + pulldown resisitor
* An LED

The Arduino operates as follows:

* At boot, it tries to connect to Wifi with stored credentials. If this fails, it enables BLE and the LED starts blinking
* When successfully connected, the LED goes solid, and the SSID and password can be set via the two available characteristics, using a BLE debug app (e.g. nRF Connect for Android)
* Once disconnected, the LED goes out, and the WiFi connection is attempted again
* Once successfully connected, the credentials are stored in Flash memory
* Every minute, the board connects to the given URL to fetch the number of steps to turn, and updates accordingly
* In order to reset the stepper position (since it has no 'memory', and the Flash memory on the board is unsuitable for many writes), hold the button down until the dial points to zero, then release, the clock will then adjust to the correct offset.
