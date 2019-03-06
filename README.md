# max31865 addition
- it's not a phidget, so maybe should rename the module.

- if RPI.GPIO isn't available, because not running on Raspberry PI, the import will fail.  However that isn't a hard failure, just raises an exception if caller does try to use the max31865.  This allows this module to gracefully disable itself on non-Raspberry PI devices.

- regarding GPIO pins, the module uses BCM addressing (see https://pinout.xyz/)
- So csPin = 8, for example, corresponds to BCM 8 in the pinout diagram.

See also these schematics and fritzing diagram
