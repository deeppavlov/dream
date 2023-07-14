# mint_sender service

The logic behind this service boils down to:
if there is a `command_to_perform`, but no command being performed on connector-side at the moment, send the command to the ROS server where it shall be further processed if needed (for more details, check README in annotators/mint_status).