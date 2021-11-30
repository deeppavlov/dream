import unittest
import sys

# ################ Enable code imports ##########################################
import os

SELF_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(SELF_DIR))
SRC_ROOT_DIR = f"{ROOT_DIR}/src"
sys.path.append(SRC_ROOT_DIR)
# #####################################################
from templatey.clients.aiml_embedded_bot_client import AIMLEmbeddedBotClient  # noqa

CONFIG_PATH = f"{ROOT_DIR}/config/xnix/config.yaml"


class TestAIMLEmbeddedBotClient(unittest.TestCase):
    def test_basic_initialization(self):
        path_to_programy_config = CONFIG_PATH
        seb = AIMLEmbeddedBotClient(id="koni", config_file_path=path_to_programy_config)
        resp = seb.handle_user_message(user_id="test_user", message_text="Hello I love you tell me what is your name")

        self.assertIn(resp.upper(), ["GREETINGS!", "HI THERE!", "HELLO!"])
        print("Nice!")


if __name__ == "__main__":
    unittest.main()
