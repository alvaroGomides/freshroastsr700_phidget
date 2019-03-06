# max31865 addition
- it's not a phidget, so maybe should rename the module.
- if RPI.GPIO isn't available, because not running on Raspberry PI, the import will fail.  However that isn't a hard failure, just raises an exception if caller does try to use the max31865.  This allows this module to be used on non-Raspberry PI devices if desired.

