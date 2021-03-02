## Part 2: The Experiment

So Cockpit has at least a couple of options for writing experiments:
* PyShell
   * We could directly import a module/function to tell cockpit what to do
* The `Experiment` class 
   * Allows for speed optimised experiments featuring hardware actiontables that I don't currently understand enough about
   * It has a little GUI that allows you to do things like set a filenames (we'll come back to this), automatically save files, set a number of repetitions, easy timelapse functionality
* The `ImmediateModeExperiment` class 
   * A subclass of `Experiment`, but doesn't deal with the hardware actiontables and so is nominally easier to write
   * The intended use of the `ImmediateModeExperiment` is actually via import into PyShell (as I found out on re-reading the docs), so really this should be the starting point for working with PyShell

I'm going to start with an `ImmediateModeExperiment`, because dealing with a full `Experiment` seems like a complicated starting point, and having things like automatic file saving, and easy setting of the repetition number are useful to me. Plus it is probably more easily reused by someone else.

***
As a brief aside, for the experiment I am building here, I want to:
* Set the AO device to one of 11 different settings
* Take an image
* Save the 11 images as a single file with a specified name

Much of the code below will be specific to this design, but I think the general idea (Get Devices, Do something with Device, Capture Images, Save Images) is probably pretty general.
***

### ImmediateModeExperiment

Starting points for the `ImmediateModeExperiment` can be found [here](https://github.com/MicronOxford/cockpit/tree/master/doc/experiment-examples)

#### A working example

`immediateModeExample2.py` doesn't work out of the box: I've included a tweaked version here(todo:add link) that addresses the problems, and is setup up to work with a laser called '488nm' (so make sure you have this your depot file).

Key changes to note are:
* Need to define is_running to return False (otherwise cockpit won't let you use takeImage). This is definitely a hacky workaround, so might break something.
* The way you access the available Imagers has changed since this was written: use `depot.getHandlerWithName(f"{camera.name} imager").takeImage`

From here it isn't difficult to make this into the kind of experiment I want to run, but first we need to be able to set the AO device:

#### Setting/Getting devices:
Obviously we need to get a reference to the device before we can tell it what to do. In cockpit, all the devices we defined in our `depot` file are accessible through `cockpit.depot`, and we can list them all with `depot.getAllDevices()`.

Probably the easiest way to get a specific device is using `getDeviceWithName`, that is assuming you know the device name. Then we can run functions that tell the device what to do e.g.
```python
aodev = depot.getDeviceWithName("dm")  # IS THIS THE CORRECT DEVICE NAME?
try:
   aodev.proxy.get_controlMatrix()

except:
   print("Failed to Get Control Matrix: Please Calibrate DM")
   aodev.proxy.set_controlMatrix(np.zeros((aodev.no_actuators, 61)))
   print("Set fake control matrix")
```
Note the use of proxy here to access functions available over Pyro4 for this device.

#### Image capture:
Once we've set our AO device, we can then capture an image:
```python
activeCams = depot.getActiveCameras()
camera = activeCams[0]
takeimage = depot.getHandlerWithName(f"{camera.name} imager").takeImage
result = events.executeAndWaitForOrTimeout(
    events.NEW_IMAGE % camera.name,
    takeimage,
    camera.getExposureTime() / 1000 + CAMERA_TIMEOUT,
)
``` 
Note here that we are specifying a 'handler', in this case an imager, that is reponsible for telling the camera to collect an image, not directly the camera.

#### Saving images:
The MRC datasaver class works fine for saving multiple images to a file and should definitely be the default pick because it saves images with metadata, but if we want a bit more control over the saving process, this is difficult to do. I opted for just using imageio to save as tiff files, because they are super widely supported.
```python
filename = f"{self.saveBasePath}{fprefix}.tif"
imageio.mimwrite(filename, imlist, format="tif")
```

### Experiment dialog
If you run cockpit and click on "Single Site Experiment", a dialog box with various options will pop up, including a choice of experiment (that we will be making in a minute). There are relatively few other options here, but they are sufficient for simple experiments, and you could of course make your own if you're so inclined.

### Experiment set up
New experiments need to be registered in `cockpit\experiment\ExperimentRegistry`. Conveniently, there are also a number of experiments already there, so if for instance you want to make an experiment around creating a ZStack, it might be worth checking those out. Even more conveniently, if you've already made the ImmediateModeExperiment above, you can register it here, and not have to faff around with PyShell (although that is a useful fallback if it doesn't work!)

The actual registration is straightforward, you just need to import your module, and then add it to `registeredModules`. Note this list is the same ordering as found in the "Single Site Experiment", so if you want your experiment to be the default, put it at the top!

Split into GUI Experiment
vs. PyShell?
