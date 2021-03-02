## Part 2: The Experiment

So Cockpit has at least a couple of options for writing experiments:
* PyShell: we could directly import a module/function to tell cockpit what to do
* The `Experiment` class which allows for speed optimised experiments featuring hardware actiontables that I don't currently understand enough about
    *   It has a little GUI that allows you to do things like set a filenames (we'll come back to this), automatically save files, set a number of repetitions, easy timelapse functionality
* The `ImmediateModeExperiment` class which is just a subclass of `Experiment`, but doesn't deal with the hardware actiontables and so is nominally easier to write
    *   On re-reading the docs, it appears that the intended use of the `ImmediateModeExperiment` is actually via import into PyShell, so really this is a repeat

I'm going to start with an `ImmediateModeExperiment`, because dealing with a full `Experiment` seems like a complicated starting point, and having things like automatic file saving, and easy setting of the repetition number are useful to me. Plus it is probably more easily reused by someone else.

### Experiment dialog
If you run cockpit and click on "Single Site Experiment", a dialog box with various options will pop up, including a choice of experiment (that we will be making in a minute). There are relatively few other options here, but they are sufficient for simple experiments, and you could of course make your own if you're so inclined.

### Experiment set up
New experiments need to be registered in `cockpit\experiment\ExperimentRegistry`. Conveniently, there are also a number of experiments already there, so if for instance you want to make an experiment around creating a ZStack, it might be worth checking those out.

The actual registration is straightforward, you just need to import your module, and then add it to `registeredModules`. Note this list is the same ordering as found in the "Single Site Experiment", so if you want your experiment to be the default, put it at the top!

Split into GUI Experiment
vs. PyShell?
