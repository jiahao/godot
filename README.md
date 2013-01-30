godot
=====

MBTA/Nextbus real time data scraper

This collection of python scripts downloads bus arrival data from NextBus.com to collect arrival time statistics for buses in the Massachusetts Bay Transportation Authority (MBTA) network.

The main scripts are:

- mbta_daemon.py: Designed to run in the background to download available bus tracking data in raw XML format, and periodically save all the data into an HDF5 database file.
- analyze_all_named_stops.py: This script analyzes MBTA timetables and generates statistics of when buses arrive.

This data analysis project was inspired by work in random matrix theory studying the universality of bus arrival statistics, such as this paper by Krábalek and Šeba [doi:10.1088/0305-4470/33/26/102][ks00]

[ks00]: http://iopscience.iop.org/0305-4470/33/26/102/ "The statistical properties of the city transport in Cuernavaca (Mexico) and random matrix ensembles"

*Caveat: these scripts are under active development.*

These scripts are licensed under the MIT License, as described in LICENSE.md.
