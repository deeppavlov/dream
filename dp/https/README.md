To use https service add it to docker compose command.
Set `DNS` variable in `.env_secret`. It should be your DNS resord. For example, `copilot3.platform.sentius.ai`.
Add `CLIENT_ID` and `CLIENT_SECRET` variables to `.env_secret` as well. 

Override AGENT_URL environment variable, if your proxied agent URL is not http://agent:4242.

To use Teams API in agent, change agent command, adding `agent.channel=ms`.
