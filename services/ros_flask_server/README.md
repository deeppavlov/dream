# ros_flask_server service

This is an intermediate node in the chain of dream_embodied:

### Architecture

[Architecture](../../assistant_dists/dream_embodied/architecture.png)

### Description

This service is basically a ROS-Flask server. 

The Flask part of this service consists of endpoints like `/set_commands`, `/is_command_valid`, `/perform_command` et cetera. Some of these endpoints are meant to be accessed from client-side (e.g. `/set_commands`), and some of them are only meant to be accessed from Dream-side (e.g. `/perform_command`).
These endpoints create a two-way API for Dream and connector so that they can interact with each other in a standardized and controlled easily-modifiable manner.

The ROS part of this server is for example:
If Dream wants the connector to perform a command by sending a request to `/perform_command` endpoint of this service, the command is first being published to a ROS-node where it can be processed in a ROS-compliant way to make interacting with real ROS-controlled and compliant robots and apps possible.

### Endpoints

##### `/set_commands`

This endpoint should only be accessed from client-side. It is used to set a valid command list for the server. Only the commands set using this endpoint are to be executed.

##### `/is_command_valid`

This endpoint is used to check whether a command is valid. It checks if the supplied string is in a list of valid commands.

##### `/perform_command`

This endpoint should only be accessed from Dream-side. When a request is sent to this endpoint, the supplied command name is appended to command queue if the command name is valid.

##### `/receive_command`

This endpoint should only be accessed from client-side. Every few seconds client sends a request to this endpoint to receive a command if there is one in queue to be executed.

##### `/is_command_performed`

This endpoint should only be accessed from Dream-side. When a request is sent to this endpoint, it simply checks whether there is a command currently being executed. If there is none, we infer that the last command is already performed.

##### `/command_is_performed`

This endpoint should only be accessed from client-side. When the client finishes performing a command, they send a request to this endpoint to let Dream know that the client may now receive new commands.
