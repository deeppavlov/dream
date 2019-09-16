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