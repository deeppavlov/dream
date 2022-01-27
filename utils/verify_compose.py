"""Making sure that all services from docker-compose.yml are present in dev.yml and proxy.yml"""

from argparse import ArgumentParser
import yaml
from pathlib import Path


repo_root = Path(__file__).resolve().parents[1]
parser = ArgumentParser()
parser.add_argument(
    "-d",
    "--directory",
    required=True,
    type=Path,
    help=(
        "Relative or full path to Dream distribution containing "
        "docker-compose.override.yml, dev.yml and proxy.yml, "
        "e.g. ./assistant_dists/dream"
    ),
)
options = parser.parse_args()


def load_yaml(path: Path) -> dict:
    with open(path) as fin:
        return yaml.load(fin, Loader=yaml.FullLoader)


def get_services(compose_file: Path) -> set:
    data = load_yaml(compose_file)
    return set(data["services"])


def verify_compose():
    assistant_dist_dir = options.directory.resolve()
    compose = get_services(assistant_dist_dir / "docker-compose.override.yml")
    for el in ["agent", "mongo"]:
        try:
            compose.remove(el)
        except KeyError:
            pass
    dev = get_services(assistant_dist_dir / "dev.yml")
    dev.remove("mongo")
    proxy = get_services(assistant_dist_dir / "proxy.yml")
    assert not (
        compose - dev
    ), f"Following services from docker-compose.override.yml are missing in dev.yml: {compose - dev}"
    assert not (compose - proxy), (
        f"Following services from docker-compose.override.yml are missing in proxy.yml: " f"{compose - proxy}"
    )
    print(f"{assistant_dist_dir} is OK")


if __name__ == "__main__":
    verify_compose()
