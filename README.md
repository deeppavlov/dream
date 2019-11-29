# ConvAI Router Bot Poller (CRBP)

Integration tool which makes DeepPavlov agents accessible via ConvAI Router Bot

## Installation
1. Clone CRBP and `cd` to repository folder:
    ```
    git clone https://github.com/deepmipt/convai_router_bot_poller.git
    cd convai_router_bot_poller
    ```
2. Create and activate Python 3.6 virtual environment:
    ```
    virtualenv env -p python3.6
    source env/bin/activate
    ```
3.  Install dependencies:
    ```
    pip install -r requirements.txt
    ```
4. To start CRBP run:
    ```
    python poller.py [--model_url <model_infer_url>] \
                     [--host <router_bot_host>] \
                     [--port <router_bot_port>] \
                     [--token <bot_token>] \
                     [--state] \
                     [--convai] \
                     [--agent]
    ```
 * `--model_url <model_infer_url>`: where to send POST-requests from the
    [ConvAI Router Bot](https://github.com/deepmipt/convai_router_bot) for processing. Overrides default settings from `config.json`.
 * `--host <router_bot_host>`: `ConvAI Router Bot` host address. Overrides default settings from `config.json`.
 * `--port <router_bot_port>`: `ConvAI Router Bot` port. Overrides default settings from `config.json`.
 * `--token <bot_token>`: `ConvAI Router Bot` token. Overrides default settings from `config.json`.
 * `--state`: add this argument to send dialogue state besides utterance to model. Overrides default settings from `config.json`.
 * `--convai`: add this argument to send full payload to model instead of plain text. Overrides default settings from `config.json`.
 * `--agent`: add this argument to send utterances from router bot to web interface of `dp-agent`. Overrides default settings from `config.json`.
 

## ConvAI Router Bot Poller modes

One can use 4 combinations of `convai` and `state` states while `agent` is set to `False`. `agent` mode could be
set to `True` only when `convai` and `state` are set to `False`.

In `state` mode `CRBP` sends two argument batches: utterances batch and state batch. State could be `None` or any JSON structure.
Argument names are stored at `config.json`.

In `convai` mode `CRBP` sends as utterance data received from [ConvAI Router Bot](https://github.com/deepmipt/convai_router_bot) as is.
Payload structure could be seen in `_get_message_dict` function from
[conversation_getaways](https://github.com/deepmipt/convai_router_bot/blob/master/convai/conversation_gateways.py) module.
In not `convai` mode `CRBP` sends only `text` field.

| CRBP mode | request payload |
|:---:|:---:|
| `convai=False`, `state=False`, `agent=False` | `{'x': ['a', 'b']}` |
| `convai=True`, `state=False`, `agent=False` | `{'x': [<payload_0>, <payload_1>]}` |
| `convai=False`, `state=True`, `agent=False` | `{'x': ['a', 'b'], 'state': [<state_0>, <state_1>]}` |
| `convai=True`, `state=True`, `agent=False` | `{'x': [<payload_0>, <payload_1>], 'state': [<state_0>, <state_1>]}` |
| `convai=False`, `state=False`, `agent=True` | `{'user_id': 74455, 'payload': 'Hello, Agent!'}` |