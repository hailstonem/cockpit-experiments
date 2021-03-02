# Cockpit - getting started with simulated experiments 25.02.2021

This is my experience of writing an Experiment in cockpit. It contains instructions, with examples, for setting up cockpit, and then for creating an experiment to run on a simulated microscope*.

It's probably most useful to those with an existing microscope that is set up with cockpit and are looking to write custom experiments for it, although it might also be a useful starting point for those with more hardware oriented goals.

I've made an effort not to assume familiarity with reading the cockpit code, but I am sort assuming you -like me- are somewhat proficient at python programming, but are not so familiar with microscope control software.

This is split into two sections:

* [Part I](part1.md) is concerned with setting up cockpit/ a simulated microscope in cockpit. 

* [Part II](part2.md)  is about how to write an automated experiment for cockpit, with specific reference to adaptive optics


\* Just in case it was ambiguous, this is does not simulate the optics of a microscope, just the control of it, although if you wanted to add that feature, it should be possible.

<!-- (C) Martin Hailstone -->
