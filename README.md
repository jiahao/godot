godot
=====

MBTA/Nextbus real time data scraper

This collection of python scripts downloads bus arrival data from NextBus.com to collect arrival time statistics for buses in the Massachusetts Bay Transportation Authority (MBTA) network.

The main scripts are:

- mbta_daemon.py: Designed to run in the background to download available bus tracking data in raw XML format, and periodically save all the data into an HDF5 database file.
- analyze_all_named_stops.py: This script analyzes MBTA timetables and generates statist

*Caveat: these scripts are under active development*

These scripts are licensed under the MIT License, as described in LICENSE.md.
