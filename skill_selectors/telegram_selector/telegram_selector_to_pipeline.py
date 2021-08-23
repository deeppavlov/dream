"""
This script replaces skill selector in `pipeline_conf.json` to telegram selector.
"""

import json
from pathlib import Path


def main():
    pipeline_path = Path(__file__).resolve().parents[2] / 'pipeline_conf.json'
    with open(pipeline_path) as file:
        pipeline_conf = json.loads(file.read())

    def replace_selector(config: dict) -> None:
        tags = config.get('tags', [])
        if len(tags) == 1 and tags[0] == 'selector':
            config['connector']['class_name'] = 'skill_selectors.telegram_selector.connector:TelegramSelector'
            config['dialog_formatter'] = 'telegram_selector_formatter_in'
        else:
            for value in config.values():
                if isinstance(value, dict):
                    replace_selector(value)

    replace_selector(pipeline_conf['services']['skill_selectors'])

    with open(pipeline_path, 'w') as file:
        json.dump(pipeline_conf, file, indent=4)


if __name__ == '__main__':
    main()
