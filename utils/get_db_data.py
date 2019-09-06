import argparse
from warnings import warn

from core.state_schema import Dialog, Utterance, HumanUtterance, BotUtterance, Human, Bot, User
from core.transform_config import DB_HOST, DB_PORT, DB_NAME

from mongoengine import connect

state_storage = connect(host=DB_HOST, port=DB_PORT, db=DB_NAME)
collections = {'Dialog': Dialog,
               'Utterance': Utterance,
               'HumanUtterance': HumanUtterance,
               'BotUtterance': BotUtterance,
               'Human': Human,
               'Bot': Bot,
               'User': User}

parser = argparse.ArgumentParser()
parser.add_argument('collections', metavar='collections', type=str, nargs='+',
                    help='a list of db collections to retrieve')


def main():
    args = parser.parse_args()
    cols = args.collections
    for col in cols:
        if col in collections.keys():
            for o in collections[col].objects():
                print(o.to_dict())
        else:
            warn(f'There is no {col} collection in the DB.', stacklevel=2)


if __name__ == '__main__':
    main()
