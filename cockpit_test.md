Copyright (C) 2021 Martin Hailstone

# Cockpit - getting started with simulated experiments 25.02.2021

This is my experience of writing an Experiment in cockpit. It contains instructions, with examples, for setting up cockpit, and then for creating an experiment to run on a simulated microscope[1].

It's probably most useful to those with an existing microscope that is set up with cockpit and are looking to write custom experiments for it, although it might also be a useful starting point for those with more hardware oriented goals.

I'm sort assuming you -like me- are somewhat proficient at python programming, but are not so familiar with microscope control software.

[1][Just in case it was ambiguous, this is does not simulate the optics of a microscope, just the control of it, although if you wanted to add that feature, it should be possible.]

## Part 1: Setting up a simulated microscope

Cockpit can be installed directly from pip,

```
pip install microscope-cockpit    
```

I think if you just want the core cockpit functionality, this is probably fine, but it is advisable to install the dependencies via a package manager, especially if using additional packages e.g. microscope-aotools like me. I used conda to install scipy, scikit-image and numba, which are required by microscope-aotools. NB/ The aotools functionality is not currently on the main branch, so you'll want to install iandobbie's dm-sim branch if you want a dm.

Once installed cockpit can be run directly with
```
cockpit
```
And this will load up the GUI and generate a number of dummy devices: primarily lasers and cameras for your convenience and viewing pleasure (assuming you're a big fan of uniform noise). 

All done, now you can skip to the actual Experiment writing bit...

Well, sort of. This might be sufficient if all that is needed for your experiment a way of capturing images from a dummy camera, but most likely you want to do some form of configuration: this allows you to name devices and specify ones that aren't part of the default. For instance, I want a DM device that's not part of the existing config.

-----
### Side note: A brief cockpit-centric view of cockpit and microscope
If you've read the documentation on [cockpit](https://github.com/MicronOxford/cockpit/blob/master/doc/),
you'll know it's based on [microscope](https://www.micron.ox.ac.uk/software/microscope/),
which handles the hardware level device communication, and then offers the device over Pyro4, which assigns it to port for cockpit (or whatever else) to deal with. I'm going to call it python-microscope here, because a) that's what it's called on pip and b) it gets confusing otherwise.
Cockpit doesn't care if the python-microscope devices are real or not, as long as they communicate in the correct manner.

-----
### A custom simulated microscope
This means setting up our simulated microscope requires first setting up some python-microscope devices:
This requires a config file. What does a config file look like?

~~https://github.com/MicronOxford/cockpit/blob/master/doc/config.rst~~

*No not that kind of config file*, those are for cockpit, we'll come back to that later! A python-microscope config file:
https://www.micron.ox.ac.uk/software/microscope/doc/architecture/device-server.html

These are regular python files with imports and everything, but are run (with python-microscope installed) with 
```deviceserver PATHTOCONFIGFILE.py ```
At this point we need to make sure there is a suitably defined simulated device (`microscope/simulators/__init__.py`)
The options currently are
```
SimulatedCamera
SimulatedController
SimulatedFilterWheel
SimulatedLightSource
SimulatedDeformableMirror
SimulatedStageAxis
SimulatedStage
```
But there are also test_devices which largely inherit from the simulated devices (`microscope/testsuite/devices`)
```
TestCamera
TestLaser
DummySLM
DummyDSP
TestFloatingDevice
```
And mock devices (`microscope/testsuite/mock_devices`)
```
CoherentSapphireLaserMock
CoboltLaserMock
OmicronDeepstarLaserMock
```
Or of course you can write your own device!

NB/ *I believe this is currently in the process of being reworked, so this is probably going to change.*

For what I want, the python-microscope config file is below:
```python
# """Config file for deviceserver.
Import device classes, then define entries in DEVICES as:
    devices(CLASS, HOST, PORT, other_args)
"""
import sys
sys.path.append("~\\Documents\\GitHub\\microscope-aotools\\") # I specifically want to import from aotools, and deviceserver doesn't seem to see the current path

# Function to create record for each device.
from microscope.devices import device

# Where we find our test devices
import microscope.testsuite.devices as testdevices
from microscope import simulators
from microAO.aoDev import AdaptiveOpticsDevice

# So the AdaptiveOpticsDevice is not a single device, it is a composite device that has its own camera for the purposes of calibration, so we first define the component devices
mirror_args = [simulators.SimulatedDeformableMirror, "127.0.0.1", 8007]
wavefront_args = [testdevices.TestCamera, "127.0.0.1", 8008]

#And now we make all the devices, specifying unique ports
DEVICES = [
    device(testdevices.DummyDSP, "127.0.0.1", 8010),
    device(testdevices.TestCamera, "127.0.0.1", 8001,),
    device(testdevices.TestLaser, "127.0.0.1", 8003),
    device(testdevices.TestFilterWheel, "127.0.0.1", 8005, conf={"positions": 5}),
    device(*mirror_args, conf={"n_actuators": 10}),
    device(*wavefront_args),
    device(
        AdaptiveOpticsDevice,
        "127.0.0.1",
        8009,
        conf={
            "ao_element_uri": mirror_args,
            "wavefront_uri": wavefront_args,
            #          'slm_uri': slm_arg
        },
    ),
]
```
Hopefully this runs just fine (this can be run from anywhere), and now we have a successful test devices running.

#### Cockpit Configuration

Now we need to connect them up to cockpit. [This requires a 'depot' file in a specific location.](https://github.com/MicronOxford/cockpit/blob/master/doc/config.rst) The depot file is a `.conf` file, and specifically deals with the link to python-microscope devices, and is not present by default. It is also separate from the GUI configuration file `config.py` (which is created when you run the cockpit GUI), and the `INI` file (which is also not present by default).

So for me (Windows) there is a `config.py` file (and some log files) at 
```%LocalAppData%\cockpit\ ```
so I'm just going to add the `depot.conf` file here too. 

NB1/ This `config.py` file is for the cockpit GUI options that is not really detailed in the docs as far as I can see, but it has some useful settings: I explicitly enabled PyShell here because it was convenient for (later) testing parts of my experiment.

NB2/ If you've already got a microscope running on cockpit, then it would probably be useful to 'borrow' the `depot.conf` file, and then make a python-microscope config file to match. Alternatively, some example configuration files can be found [here](https://github.com/MicronOxford/cockpit/tree/master/sample-configs)

This needs to match the corresponding microscope config file:
```
[server]
ipAddress: 127.0.0.1
port: 7700

[dsp]
type: cockpit.devices.executorDevices.ExecutorDevice
uri: PYRO:DummyDSP@127.0.0.1:8010
dlines: 16
alines: 2

[camera]
type: cockpit.devices.microscopeCamera.MicroscopeCamera
uri: PYRO:TestCamera@127.0.0.1:8001

[wavefront]
type: cockpit.devices.microscopeCamera.MicroscopeCamera
uri: PYRO:TestCamera@127.0.0.1:8008

[488nm]
type: cockpit.devices.microscopeDevice.MicroscopeLaser
uri: PYRO:TestLaser@127.0.0.1:8003
wavelength: 488

[dm]
type: cockpit.devices.microscopeDeformableMirror.MicroscopeDeformableMirror
uri: PYRO:AdaptiveOpticsDevice@127.0.0.1:8009
triggerSource: dsp
triggerLine: 1
```

#### Testing the cockpit configuration
We can then test this with 
```python -m cockpit.status```

We should then see something like this:
```
Ping statistics for 127.0.0.1:
    Packets: Sent = 1, Received = 1, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 0ms, Maximum = 0ms, Average = 0ms
DEVICE                        HOSTNAME  STATUS    PORT  
======                        ========  ======    ======
488nm                        127.0.0.1  up        open  
camera                       127.0.0.1  up        open  
dm                           127.0.0.1  up        open  
dsp                          127.0.0.1  up        open  
server                       127.0.0.1  up        closed
wavefront                    127.0.0.1  up        open  
```

Ignoring the server being closed (which is normal), we want all the devices connected to be open. If one of them is not, there are at least a couple of possible problems:
* The `depot.conf` file has the wrong port/host name
* Theres something else on the port which is screwing it up. Try changing the port (in both the depot and python-microscope config files).


Now we can run ```cockpit```. Hopefully this just works!

#### Troubleshooting the cockpit configuration
1. Say we have accidentally switched our dm and our camera ports. This won't show up earlier with cockpit.status, but when cockpit proper tries to run, it's likely to realise that the device doesn't work like it should: and then cockpit gives a communication error:
```
Pyro4.errors.CommunicationError: connection to ('127.0.0.1', 8001) rejected: unknown object
```
2. Or if we specify an object that doesn't match the PYRO uri e.g. Laser and Camera.
We get Cockpit "Failed to Initialise window" with some traceback.
```
File "c:\users\martin\anaconda2\envs\cockpit\lib\site-packages\cockpit\gui\mainWindow.py", line 143, in __init__
    lightPowerThings.sort(key = lambda l: l.wavelength)
TypeError: '<' not supported between instances of 'str' and 'NoneType'
```
This is not the most helpful traceback for this problem , so it's worth noting Cockpit redirects `stdout` and `stderr` to *"Logging panels"* so it is worth checking them for information as well (they can sometimes be partially hidden by other panels). In this case, the `stderr` is quite informative:
```
AttributeError: remote object "PYRO:TestCamera" has no exposed Attribute "power".
```
I suppose a camera could have a power attribute, but probably it's because we're trying to get the laser "power" on a camera. This is easily solved with ~~more lasers.~~ correctly setting the uri in the depot file.

3. Sometimes, you try and run cockpit and you get... nothing.

For instance if I put a """multiline comment""" in a depot file, ```cockpit``` at the command line gives no feedback at all. If this kind of thing happens, fallback to
```python -m cockpit.status```
 
Here we get:
```
configparser.ParsingError: Source contains parsing errors: 'C:\\Users\\Martin\\AppData\\Local\\cockpit\\depot.conf'
        [line  4]: '"""\n'
        [line  5]: 'Multiline Comment\n'
        [line  6]: 'Line"""\n'
```
Yeah like don't put random stuff in your depot files (# comments are fine though!)

Now assuming this is working, there you are, your very own fake microscope.

## Part 2: The Experiment

So Cockpit has at least a couple of options for writing experiments:
* PyShell: we could directly import a module/function to tell cockpit what to do
* The `Experiment` class which allows for speed optimised experiments featuring hardware actiontables that I don't currently understand enough about
    *   It has a little GUI that allows you to do things like set a file names (we'll come back to this), automatically save files, set a number of repetitions, easy timelapse functionality
* The `ImmediateModeExperiment` class which is just a subclass of `Experiment`, but doesn't deal with the hardware actiontables and so is nominally easier to write

I'm going to start with an `ImmediateModeExperiment`, because dealing with a full `Experiment` seems like a complicated starting point, and having things like automatic file saving, and easy setting of the repetition number are useful to me. Plus it is probably more easily reused by someone else.

### Experiment dialogue
If you run cockpit and click on "Single Site Experiment", a dialog box with various options will pop up, including a choice of experiment (that we will be making in a minute). There are relatively few other options here, but they are sufficient for simple experiments, and you could of course making your own if you're so inclined.

### Experiment set up
New experiments need to be registered in `cockpit\experiment\ExperimentRegistry`. Conveniently, there are also a number of experiments already there, so if for instance you want to make an experiment around creating a ZStack, it might be worth checking those out.

The actual registration is straightforward, you just need to import your module, and then add it to `registeredModules`. Note this list is the same ordering as found in the "Single Site Experiment", so if you want your experiment to be the default, put it at the top!


