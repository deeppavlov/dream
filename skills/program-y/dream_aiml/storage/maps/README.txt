Maps Folder
===========

This folder contains you map files and associated subdirectories. You have 2 options :-

    1) Either copy the entire map files from the bot you are using and then add/modify the map files
    2) Leave the map files in the bot, and add you own into this folder

The files config section within brain -> files -> maps supports multiple directories. In Yaml this is done as follows
by starting with the '|' character and then each director listed on a seperate line

files:
        maps:
            files: |
                    ../program-y/bots/y-bot/maps
                    ./maps

Using option 2 means that any changes to the core bot in github can be picked up with out overwritting any maps
that you create yourself

Any duplicate maps are reported in the log file for you to correct
