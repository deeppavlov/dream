import time
from collections import namedtuple
from pathlib import Path
from urllib import parse

import dotenv
import requests
from deeppavlov_dreamtools.deployer.portainer import SwarmClient
from deeppavlov_dreamtools.deployer.swarm import SwarmDeployer
from deeppavlov_dreamtools.distconfigs.assistant_dists import AssistantDist
from pydantic import BaseSettings

DREAM_ROOT_PATH = Path(__file__).resolve().parents[2]

Bot = namedtuple("Bot", ("dist_name", "stack_name", "user_services", "deployment_dict", "prefix"))


class Settings(BaseSettings):
    portainer_url: str
    portainer_key: str
    registry_url: str
    proxy_host: str
    openai_api_key: str
    google_cse_id: str
    google_api_key: str
    sentry_dsn: str
    openai_api_base: str
    openai_api_type: str
    openai_api_version: str
    azure_api_key: str


settings = Settings()


def gen_mock(port, timeout=3, replicas=1):
    return {
        "command": "uvicorn server:app --port $PORT --host 0.0.0.0",
        "build": {"context": "dp/mock", "dockerfile": "Dockerfile"},
        "environment": [f"TIMEOUT={timeout}", f"PORT={port}"],
        "deploy": {
            "replicas": replicas,
            "resources": {"limits": {"memory": "100M"}, "reservations": {"memory": "50М"}},
        },
    }


def gen_proxy(port, port_forwarding=False):
    ans = {
        "command": ["nginx", "-g", "daemon off;"],
        "build": {"context": "dp/proxy", "dockerfile": "Dockerfile"},
        "environment": [f"PROXY_PASS={settings.proxy_host}:{port}", f"PORT={port}"],
        "deploy": {"resources": {"limits": {"memory": "100M"}, "reservations": {"memory": "100M"}}},
    }
    if port_forwarding is True:
        ans["ports"] = [f"{port}:{port}"]
    return ans


def gen_deployment_dict(port_number: int, kwargs: dict = None):
    if kwargs is None:
        kwargs = {}
    if "agent" in kwargs:
        raise ValueError("There is agent key in kwargs")
    return {
        "services": {
            "agent": {"ports": [f"{port_number}:4242"], "deploy": {"resources": {"reservations": {"memory": "200M"}}}},
            **kwargs,
        }
    }


def deploy(bot: Bot):
    dream_dist = AssistantDist.from_name(name=bot.dist_name, dream_root=DREAM_ROOT_PATH)
    deployer = SwarmDeployer(
        user_identifier=bot.stack_name,
        registry_addr=settings.registry_url,
        user_services=bot.user_services,
        deployment_dict=bot.deployment_dict,
        portainer_url=settings.portainer_url,
        portainer_key=settings.portainer_key,
        default_prefix=bot.prefix,
    )
    print(bot.stack_name)
    for state, _, _ in deployer.deploy(dream_dist):
        print(state)


universal_bot = Bot(
    dist_name="universal_prompted_assistant",
    stack_name="universal",
    user_services=None,
    deployment_dict=gen_deployment_dict(
        4249,
        {
            "combined-classification": gen_proxy(8087),
            "sentence-ranker": gen_proxy(8128),
            "openai-api-chatgpt": {"ports": ["8145:8145"]},
            "openai-api-davinci3": {"ports": ["8131:8131"]},
            "openai-api-gpt4": {"ports": ["8159:8159"]},
            "openai-api-gpt4-32k": {"ports": ["8160:8160"]},
            "openai-api-chatgpt-16k": {"ports": ["8167:8167"]},
            "anthropic-api-claude-v1": {"ports": ["8164:8164"]},
            "anthropic-api-claude-instant-v1": {"ports": ["8163:8163"]},
            "mongo": {
                "volumes": [{"type": "bind", "source": "/home/ubuntu/mongo", "target": "/data/db"}],
                "deploy": {"placement": {"constraints": ["node.role == manager"]}},
            },
        },
    ),
    prefix="universal_",
)

multi_bot = Bot(
    dist_name="multiskill_ai_assistant",
    stack_name="multiskill",
    user_services=[
        "prompt-selector",
        "llm-based-response-selector",
        "dff-dream-persona-chatgpt-prompted-skill",
        "dff-casual-email-prompted-skill",
        "dff-meeting-notes-prompted-skill",
        "llm-based-skill-selector",
        "dff-official-email-prompted-skill",
        "dff-plan-for-article-prompted-skill",
    ],
    deployment_dict=gen_deployment_dict(4250),
    prefix="universal_",
)


selectors_bot = Bot(
    dist_name="universal_selectors_assistant",
    stack_name="selectors",
    user_services=[
        "universal-llm-based-skill-selector",
        "universal-llm-based-response-selector",
    ],
    deployment_dict=gen_deployment_dict(4248),
    prefix="universal_",
)


def check(port):
    host = parse.urlparse(settings.portainer_url).hostname
    url = f"http://{host}:{port}/ping"
    for _ in range(100):
        try:
            resp = requests.get(url, timeout=2)
            resp.raise_for_status()
            print(f"{url} SUCCESS")
            return
        except Exception as e:
            print(f"Got {e.__class__.__name__}. Waiting response from {url}...")
            time.sleep(5)
    else:
        raise TimeoutError(f"Failed to get response from {url}")


def deploy_bot(bot_id, port):
    resp = requests.post(
        "http://0.0.0.0:6098/api/deployments/",
        headers={"accept": "application/json", "token": "test", "Content-Type": "application/json"},
        json={"virtual_assistant_id": bot_id, "assistant_port": port},
    )
    resp.raise_for_status()
    return resp.json()


def main():
    client = SwarmClient(settings.portainer_url, settings.portainer_key)
    client.drop_stacks()
    dotenv.unset_key(DREAM_ROOT_PATH / ".env", "OPENAI_API_KEY")
    dotenv.unset_key(DREAM_ROOT_PATH / ".env_secret_azure", "OPENAI_API_KEY")
    dotenv.set_key(DREAM_ROOT_PATH / ".env", "GOOGLE_CSE_ID", settings.google_cse_id)
    dotenv.set_key(DREAM_ROOT_PATH / ".env", "GOOGLE_API_KEY", settings.google_api_key)
    dotenv.set_key(DREAM_ROOT_PATH / ".env", "SENTRY_DSN", settings.sentry_dsn)

    dotenv.set_key(DREAM_ROOT_PATH / ".env_azure", "OPENAI_API_BASE", settings.openai_api_base)
    dotenv.set_key(DREAM_ROOT_PATH / ".env_azure", "OPENAI_API_TYPE", settings.openai_api_type)
    dotenv.set_key(DREAM_ROOT_PATH / ".env_azure", "OPENAI_API_VERSION", settings.openai_api_version)
    print("keys are set", flush=True)
    deploy(universal_bot)
    dotenv.set_key(DREAM_ROOT_PATH / ".env_secret", "OPENAI_API_KEY", settings.openai_api_key)
    dotenv.set_key(DREAM_ROOT_PATH / ".env_secret_azure", "OPENAI_API_KEY", settings.azure_api_key)
    deploy(multi_bot)
    deploy(selectors_bot)
    [check(port) for port in [4249, 4250, 4248]]


if __name__ == "__main__":
    main()
