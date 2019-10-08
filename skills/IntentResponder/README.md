## Description

Скилл для выхода из диалога.

Здесь только ответы, детект фраз выхода из диалога проиходит в **IntentCatcher** аннотаторе.

Сделано:
- **SimpleExiter**: бейзлайн, детектит фразы выхода на окончании строки. На respond выдаем одну из рандомных фраз.
- Использование **cobot_offensive/cobot_sentiment** на последней фразе пользователя

## TODO:

- Добавить анализ **cobot_sentiment/cobot_offensive** по всему диалогу (Нужно ли это?)
- Refactor code

## Getting started

Базовые ответы находятся в `data/farewells/bot_farewells.txt`. К ним добавляются фразы, определяющиеся по *sentiment* или *offensiveness* последней фразы пользователя.
