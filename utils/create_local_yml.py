# ! pip install PyYAML==5.3b1
import yaml
import argparse
import pathlib

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--service_names", action="append")
parser.add_argument("-d", "--repository_root_dir", type=pathlib.Path, default=pathlib.Path("./"))
parser.add_argument("-p", "--no_drop_ports", action="store_true")
parser.add_argument("-r", "--no_one_replica", action="store_true")
args = parser.parse_args()


def run_cmd(args):
    proxy = yaml.load((args.repository_root_dir / "proxy.yml").open("rt"), yaml.FullLoader)
    dev = yaml.load((args.repository_root_dir / "dev.yml").open("rt"), yaml.FullLoader)
    dev_services = args.service_names + ["agent", "mongo"]

    for serv_name in dev_services:
        serv = dev["services"][serv_name]
        if not args.no_drop_ports:
            print(f"rm ports: {serv_name}")
            del serv["ports"]
        proxy["services"][serv_name] = serv

    if not args.no_one_replica:
        for serv_name in proxy["services"]:
            proxy["services"][serv_name]["deploy"] = {"mode": "replicated", "replicas": 1}

    yaml.dump(proxy, (args.repository_root_dir / "local.yml").open("wt"))
    print("All services: " + " ".join(proxy["services"]))


run_cmd(args)
# example:
# python venv/create_local_yml.py -s dff-friendship-skill
