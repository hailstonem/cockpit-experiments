#!/usr/bin/env python
# -*- coding: utf-8 -*-

## Copyright (C) 2018 Mick Phillips <mick.phillips@gmail.com>
##
## This file is part of Cockpit.
##
## Cockpit is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Cockpit is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Cockpit.  If not, see <http://www.gnu.org/licenses/>.

## Copyright 2013, The Regents of University of California
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions
## are met:
##
## 1. Redistributions of source code must retain the above copyright
##   notice, this list of conditions and the following disclaimer.
##
## 2. Redistributions in binary form must reproduce the above copyright
##   notice, this list of conditions and the following disclaimer in
##   the documentation and/or other materials provided with the
##   distribution.
##
## 3. Neither the name of the copyright holder nor the names of its
##   contributors may be used to endorse or promote products derived
##   from this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
## FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
## COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
## INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
## BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
## LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
## CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
## LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
## POSSIBILITY OF SUCH DAMAGE.


from cockpit import depot
from cockpit import events
from . import immediateMode
import cockpit.interfaces.imager
import cockpit.interfaces.stageMover
import cockpit.util
import wx
import numpy
import os
import time


## This class serves as an example of how to run an immediate-mode
# experiment. Make a copy of this file, and modify it to have the logic
# you want. To run it (supposing that your copy is in
# experiment/myExperiment.py), do this in the Python shell in the Cockpit:
# >>> import experiment.myExperiment
# >>> runner = experiment.myExperiment.MyExperiment()
# >>> runner.run()
# If you make changes to the experiment while the cockpit is running, you will
# need to reload the experiment module for those changes to take effect:
# >>> reload(experiment.myExperiment)
class MyExperiment(immediateMode.ImmediateModeExperiment):
    def __init__(self):
        # We need to tell our parent class (the ImmediateModeExperiment)
        # how many reps we'll be doing, how long each rep lasts, how
        # many images we'll be collecting, and the filepath to save the
        # data to. The experiment assumes we're
        # using the currently-active cameras and light sources for setting
        # up the output data file.
        # Here we do 5 reps, with a 4s duration, and 1 image per rep. The
        # file will get saved as "out.mrc" in the current user's data
        # directory.
        datadir = cockpit.util.userConfig.getValue("data-dir")

        if not datadir:  # we do this over using default because we explicitly want to avoid having None here
            datadir = "~/data/"

        savePath = os.path.join(datadir, "out.mrc")
        print("Saving files to", savePath)

        self.table = None
        super().__init__(numReps=5, repDuration=4, imagesPerRep=1, savePath=savePath)

    def is_running(self):
        # HACK: Imager won't collect images if an experiment is running... Catch 22 here... So just breaking this for now
        return False

    ## This function is where you will implement the logic to be performed
    # in each rep of the experiment.
    def executeRep(self, repNum):
        # Get all light sources that the microscope has.
        allLights = depot.getHandlersOfType(depot.LIGHT_TOGGLE)
        # getHandlersOfType returns an unordered set datatype. If we want to
        # index into allLights, we need to convert it to a list first.
        allLights = list(allLights)
        # Print the names of all light sources.
        for light in allLights:
            print(light.name)
        # Get all power controls for light sources.
        allLightPowers = depot.getHandlersOfType(depot.LIGHT_POWER)
        # Get all light source filters.
        allLightFilters = depot.getHandlersOfType(depot.LIGHT_FILTER)

        # Get all camera handlers that the microscope has, and filter it
        # down to the ones that are currently active.
        activeCams = depot.getActiveCameras()

        if not activeCams:
            raise RuntimeWarning("No Active Cameras Detected")
        # self.cameraToImageCount = [1 for _ in activeCams]
        # Get a specific light.
        laser488 = depot.getHandlerWithName("488nm")

        # Set this light source to be enabled when we take images.
        laser488.setEnabled(True)

        # Take images, using all current active camera views and light
        # sources; wait for the image (and time of acquisition) from the named
        # camera to be available.
        # Note: that if you try to wait for an image
        # that will never arrive (e.g. for the wrong camera name) then your
        # script will get stuck at this point.
        CAMERA_TIMEOUT = 2

        for camera in activeCams:
            takeimage = depot.getHandlerWithName(f"{camera.name} imager").takeImage
            image = events.executeAndWaitForOrTimeout(
                events.NEW_IMAGE % camera.name, takeimage, camera.getExposureTime() / 1000 + CAMERA_TIMEOUT,
            )

            if image is not None:
                image = image[0]
            # Get the min, max, median, and standard deviation of the image
            imageMin = image.min()
            imageMax = image.max()
            imageMedian = numpy.median(image)
            imageStd = numpy.std(image)

            print("Image stats:", imageMin, imageMax, imageMedian, imageStd)

        # Some miscellaneous functions below.

        # Get the current stage position; positions are in microns.
        curX, curY, curZ = cockpit.interfaces.stageMover.getPosition()
        # Move to a new Z position, and wait until we arrive.
        cockpit.interfaces.stageMover.goToZ(curZ + 5, shouldBlock=True)
        # Move to a new XY position.
        # Note: the goToXY function expects a "tuple" for the position,
        # hence the extra parentheses (i.e. "goToXY(x, y)" is invalid;
        # "goToXY((x, y))" is correct).
        cockpit.interfaces.stageMover.goToXY((curX + 50, curY - 50), shouldBlock=True)

