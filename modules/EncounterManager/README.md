# Encounter Manager
This module provides a simple initiative tracker and turn-timer in a simple GUI. 

## Setup
The manager_config.csv dictates the size of the window in pixels (will be square) and the length of the turn timer. The turn timer is useful for keeping combat encounters moving. 

Individual encounters are configured by csv files with names that start with "@" and contain player/npc/monster names, iniative, and DEX data. The manager will load whichever encounter configuration file has the most recent modification date. If player/npc/monster names in the encounter configuration match image names in ./SourceImages, the manager window will display the corresponding images on the respective turns.

## To-do
When more than one of a particular npc/monster is used, add a label to their image in the image viewer to distinguish between them.
