# max31865 addition
- it's not a phidget, so maybe should rename the module.

- if RPi.GPIO isn't available, because not running on Raspberry PI, the import of max31865 will fail.  However that isn't a hard failure.  It just raises an exception later if caller does try to use the max31865.  This allows this module to gracefully disable the max31865 part of itself on non-Raspberry PI devices.

- Regarding GPIO pins, the module uses BCM addressing (see https://pinout.xyz/), so csPin = 8, for example, corresponds to BCM 8 in the pinout diagram.

See also these schematics and fritzing diagram
![](docs/freshroastsr700_max31865_bb.png)

![](docs/freshroastsr700_max31865_schem.png)
