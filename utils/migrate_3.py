import asyncio
import argparse

from core.state_manager import StateManager
from core.state_schema import Dialog, Human, BotUtterance
from core.db import DataBase

parser = argparse.ArgumentParser()
parser.add_argument('--host', help='mongo host, default mongo', default='mongo')
parser.add_argument('--port', help='mongo port, default 27017', default=27017, type=int)
parser.add_argument('-od', '--old_db_name', help='old db name, default test', default='test')
parser.add_argument('-nd', '--new_db_name', help='new db name, default test', default='dp_agent')

args = parser.parse_args()

db_old = DataBase(args.host, args.port, args.old_db_name).get_db()
db_new = DataBase(args.host, args.port, args.new_db_name).get_db()


if args.old_db_name != args.new_db_name:
    rewrite = True
else:
    rewrite = False


async def main(db_old, db_new, rewrite):
    users = await Human.get_all(db_old)

    for u in users:
        u_dialogs = await Dialog.get_many_by_ext_id(db=db_old, human=u)
        for d in u_dialogs:
            if rewrite:
                d._id = None
                d.human._id = None
                d.bot._id = None
                d._human_id = None
                d._bot_id = None
            for u in d.utterances:
                if isinstance(u, BotUtterance):
                    bot_anno = {}
                    for k, v in u.annotations.items():
                        if k.startswith('bot_'):
                            bot_anno[k[4:]] = v
                        else:
                            bot_anno[k] = v
                    u.annotations = bot_anno
                if rewrite:
                    u._id = None
                    u._dialog_id = None
            if args.old_db_name != args.new_db_name:
                d._id = None
            await d.save(db_new, force=True)

    sm_new = StateManager(db_new)
    await sm_new.prepare_db()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(main(db_old, db_new, rewrite))
