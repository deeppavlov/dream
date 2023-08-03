# mint_status annotator service

This annotator does the following:
1. Checks whether there is a command currently being performed on the side of *connector* (e.g. minecraft-interface);
2. After a command is executed, it is appended the list of performed commands, and the "performing" flag is removed from attributes.

This annotator is needed so we don't start executing the command unless there are no other commands being executed at that time. It prevents undefined and weird behaviour on both connector-side and Dream-side.