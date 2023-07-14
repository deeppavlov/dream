# ros_flask_server service

This is an intermediate node in the chain of dream_mint:

[Architecture](../../assistant_dists/dream_mint/architecture.png)

This service is basically a ROS-Flask server. 

The Flask part of it consists of endpoints like `/set_commands`, `/is_command_valid`, `/perform_command` et cetera. Some of these endpoints are meant to be accessed from connector-side (e.g. `/set_commands`), and some of them are only meant to be accessed from dream-side (e.g. `/perform_command`).
These endpoints create a two-way API for dream and connector so that they can interact with each other in a standardized and controlled easily-modifiable manner.

The ROS part of this server is for examle:
If dream wants the connector to perform a command by sending a request to `/perform_command` endpoint of this service, the command is first being published to a ROS-node where it can be processed in a ROS-compliant way to make interacting with real ROS-controlled and compliant robots and apps possible.