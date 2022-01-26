Sets Folder
===========

This folder contains you set files and associated subdirectories. You have 2 options :-

    1) Either copy the entire set files from the bot you are using and then add/modify the set files
    2) Leave the set files in the bot, and add you own into this folder
    
The files config section within brain -> files -> sets supports multiple directories. In Yaml this is done as follows
by starting with the '|' character and then each director listed on a seperate line

    files:
        sets:
            files: |
                    ../program-y/bots/y-bot/sets
                    ./sets
            extension: .txt
            directories: false

Using option 2 means that any changes to the core bot in github can be picked up with out overwritting any sets
that you create yourself

Any duplicate sets are reported in the log file for you to correct
    
