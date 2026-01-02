# project
hawaiian roaming rooster simulator

## goal
create an organic model of rooster movements and their calls which will be played through a 5.1 or 7.1 surround sound system

## rooster behavior
the program will take a config file that will include:
 - the number of roosters in the simulation
 - a time unit to reevaluate the state of the roosters
 - a second time parameter to randomize the first time parameter to make it less predictable
 - the frequency of their movements
 - the chance that they move at all
 - the distance of their movements
 - the frequency of their calls
 - their responsiveness to other roosters calling in their proximity
    - likelihood that they "reply" to the other rooster
    - distance where this effect is triggered
    - randomizing parameter

## area of operations
the area that the roosters are operating in is radial. the center point is the human listening to their calls.
the radial area will be divided into four quadrants, which will be associated with the four speakers in the surround sound stereo. as the roosters move volume and location of their calls should be changed to reflect appropriate volume and spacial location.
the following should be parameterized:
 - the distance to the furthest point from the origin in meters
 - the number of points to calculate from the origin to the outermost point

## calls
the sound files for the roosters calls will be located in a subdirectory, `calls`
the following should be parameterized:
 - the default call
 - the percentage probability that a different call is used
 - the "stickiness" of a specific call to a specific rooster
    - the percentage of roosters that have a "stickiness" attribute
    - the chance of them picking something other than the default call
    - the chance of them returning to the default call
    - a randomizing factor for the former three parameters

### frequency based on time
the roosters crow 24x7, however, the likelihood of them crowing is also based on time, eg, there is a 100% chance that they will crow at dawn and are less likely to crow at 0200 -- but still do sometimes!
parameters:
 - the time of dawn
    - 100% probability
 - daylight hours
     - parametrized probability
 - nighttime hours
     - parametrized probability
