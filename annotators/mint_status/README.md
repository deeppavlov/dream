# mint_status annotator service

This annotator does the following:
1. checks whether there is a command currently being performed on the side of *connector* (e.g. minecraft-interface);
2. if command is performed, then it is added to the list of performed commands and removes the "performing" flag from attrs.

This annotator is needed so we don't start executing the command unless there are no other commands being executed at that time. It prevents undefined and weird behaviour on both connector-side and dream-side.