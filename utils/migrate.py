import argparse
import asyncio
from collections import defaultdict

import motor.motor_asyncio
from bson.objectid import ObjectId

from core.state_schema import Bot, BotUtterance, Dialog, Human, HumanUtterance

parser = argparse.ArgumentParser()
parser.add_argument('--host', help='mongo host, default mongo', default='mongo')
parser.add_argument('--port', help='mongo port, default 27017', default=27017, type=int)
parser.add_argument('-od', '--old_db_name', help='old db name, default test', default='test')
parser.add_argument('-nd', '--new_db_name', help='new db name, default test', default='dp_agent')

args = parser.parse_args()


async def get_users(coll):
    result = {}
    async for i in coll.find():
        result[i['_id']] = i
    return result


async def get_dialogs(coll):
    result = []
    async for i in coll.find():
        result.append(i)
    return result


async def get_utterances(coll):
    result = {}
    async for i in coll.find():
        result[i['_id']] = i
    return result


async def prepare_db(db):
    await BotUtterance.prepare_collection(db)
    await HumanUtterance.prepare_collection(db)
    await Human.prepare_collection(db)
    await Dialog.prepare_collection(db)


async def create_and_save_dialogs(dialogs, utterances, users, db_new):
    users_and_dialogs = defaultdict(dict)
    users_and_utterances = defaultdict(list)
    users_dict = {}
    print('dialogs preparation')
    for d in dialogs:
        user = users[d.get('user') or d.get('human')]
        if user['user_telegram_id'] in users_dict:
            user_obj = users_dict[user['user_telegram_id']]
        else:
            user_obj = Human(telegram_id=user['user_telegram_id'], profile=user['profile'])
            await user_obj.save(db_new)
            users_dict[user['user_telegram_id']] = user_obj

        bot = users.get(d['bot'])
        bot_obj = Bot(persona=bot['persona'])
        await bot_obj.save(db_new)

        d_obj = Dialog(human=user_obj, channel_type=d['channel_type'], _active=False)
        d_obj.bot = bot_obj
        for j in d['utterances']:
            users_and_utterances[user_obj].append(utterances[j])

        users_and_dialogs[user_obj][d['utterances'][0]] = d_obj
    print('adding utterances and saving dialogs')
    for k, v in users_and_utterances.items():
        d_utt_dict = users_and_dialogs[k]
        utterances = sorted(v, key=lambda x: x['date_time'])
        dialogs = []
        for utt in utterances:
            if utt['_id'] in d_utt_dict:
                dialogs.append(d_utt_dict.pop(utt['_id']))
            if not dialogs:
                raise ValueError('something happened with dialog')
            if utt['_cls'] == 'Utterance.HumanUtterance':
                dialogs[-1].add_human_utterance()
                dialogs[-1].utterances[-1].text = utt['text']
                dialogs[-1].utterances[-1].annotations = utt['annotations']
                dialogs[-1].utterances[-1].date_time = utt['date_time']
                dialogs[-1].utterances[-1].attributes = utt.get('attributes', {})
                dialogs[-1].utterances[-1].hypotheses = []
                if 'hypotheses' in utt:
                    dialogs[-1].utterances[-1].hypotheses = utt['hypotheses']
                elif 'selected_skills' in utt and utt['selected_skills']:
                    for k, v in utt['selected_skills'].items():
                        v['skill_name'] = k
                        dialogs[-1].utterances[-1].hypotheses.append(v)
                if isinstance(utt['user'], dict):
                    dialogs[-1].utterances[-1].user = utt['user']
                elif isinstance(utt['user'], ObjectId):
                    dialogs[-1].utterances[-1].user = dialogs[-1].human.to_dict()
            elif utt['_cls'] == 'Utterance.BotUtterance':
                dialogs[-1].add_bot_utterance()
                dialogs[-1].utterances[-1].text = utt['text']
                dialogs[-1].utterances[-1].annotations = utt['annotations']
                dialogs[-1].utterances[-1].date_time = utt['date_time']
                dialogs[-1].utterances[-1].orig_text = utt.get('orig_text') or utt['text']
                dialogs[-1].utterances[-1].active_skill = utt['active_skill']
                dialogs[-1].utterances[-1].confidence = utt['confidence']
            if isinstance(utt['user'], dict):
                dialogs[-1].utterances[-1].user = utt['user']
            elif isinstance(utt['user'], ObjectId):
                dialogs[-1].utterances[-1].user = dialogs[-1].bot.to_dict()
        dialogs[-1]._active = True
        for i in dialogs:
            await i.save(db_new)


async def main(db_old, db_new):
    users_old = db_old.user
    dialog_old = db_old.dialog
    utterances_old = db_old.utterance
    print('Collecting old database...')
    users_dict = await get_users(users_old)
    utterances_dict = await get_utterances(utterances_old)
    dialogs_list = await get_dialogs(dialog_old)
    print('collection done, new database preparation')
    await prepare_db(db_new)

    await create_and_save_dialogs(dialogs_list, utterances_dict, users_dict, db_new)


def check_keys(iterable):
    result = defaultdict(int)
    for i in iterable:
        for k, v in i.items():
            if v:
                result[k] += 1

    return result


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    client = motor.motor_asyncio.AsyncIOMotorClient(args.host, int(args.port))

    db_old = client[args.old_db_name]
    db_new = client[args.new_db_name]

    loop.run_until_complete(main(db_old, db_new))
    loop.close()
