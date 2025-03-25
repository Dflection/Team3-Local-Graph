The Local Graph
Group 3's campus navigation solution
Project by Ashton Pankey, Chase Varvayanis, Dylan Henley, Marcel Ortiz, and Melanie Foley
Readme by Chase Varvayanis

TO RUN:
    - Run by opening RUN_LOCAL_GRAPH.py, all dependencies should automatically be installed

USE INSTRUCTIONS:
    - To navigate, Search for a start and end point by typing into the boxes below the map, and then selecting 'Find Route' at the bottom of the page to plot your route.
    - If you would like to add intermediate waypoints, say you want to got from Fir to Manzanita to Oak Pavilion, Select Fir as a start waypoint and Oak Pavilion as an end waypoint. Below these fields, under the 'Optional Waypoints' Heading, search or use the dropdown box to use intermediate waypoints. When all start, finish, and intermediate waypoints are added select Find Route Once again at the bottom of the page
    - To clear the path and start a new search query, select the clear paths button at the bottom of the page.
    - To see all path data in the system, select the 'All Path Data' checkbox at the bottom of the page to toggle its visibility

PLANNED/POTENTIAL FUTURE FEATURES:
    - More comprehensive campus trail and building data
    - AI Text to Speech and voice navigation
    - Compilation into a standalone executable (streamlit made this more of a challenge than i thought...)
    - Hosting  of application on webserver

KNOWN ISSUES:
    - Certain paths have display errors (notably, the path between ~Pinyon and Ponderosa has a graphical display error)
    - Path data is not comprehensive, there are a number of auxiliary and primary paths that were missed by our dataset, notably the path from dorm parking to campus, lower student parking by Oak Pavilion, and path between Redbud and Tamarack Hall.