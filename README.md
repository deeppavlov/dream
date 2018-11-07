# ConvAI Router Bot Poller (CRBC)

Integration tool which makes DeepPavlov agents accessible via ConvAI Router Bot

## Installation
1. Clone CRBC repository and `cd` to CRBC folder:
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
4. Clone and install DeepPavlov (checkout to required branch if needed):    
    ```
    git clone https://github.com/deepmipt/DeepPavlov.git
    cd DeepPavlov
    python setup.py develop
    cd ..
    ```
