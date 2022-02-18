AIML Folder
===========

This folder contains you aiml files and associated subdirectories. You have 2 options :-

    1) Either copy the entire aiml files from the bot you are using and then add/modify the aiml files
    2) Leave the aiml files in the bot, and add you own into this folder

The files config section within brain -> files -> aiml supports multiple directories. In Yaml this is done as follows
by starting with the '|' character and then each director listed on a seperate line

    files:
        aiml:
            files: |
                    ../program-y/bots/y-bot/aiml
                    ./aiml

Using option 2 means that any changes to the core bot in github can be picked up with out overwritting any grammar
that you create yourself