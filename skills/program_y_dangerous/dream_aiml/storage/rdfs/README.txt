RDF Folder
===========

This folder contains you rdf files and associated subdirectories. You have 2 options :-

    1) Either copy the entire rdf files from the bot you are using and then add/modify the rdf files
    2) Leave the rdf files in the bot, and add you own into this folder

The files config section within brain -> files -> rdf supports multiple directories. In Yaml this is done as follows
by starting with the '|' character and then each director listed on a seperate line

  brain:
    files:
        rdf:
            files:  |
                    ../program-y/bots/y-bot/rdf
                    ./rdf
            extension: .txt
            directories: false

Using option 2 means that any changes to the core bot in github can be picked up with out overwritting any grammar
that you create yourself

