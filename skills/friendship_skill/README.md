### Построение DialogFlow

DialogFlow строится по вершинам, которые могут быть 2-х видов `SYSTEM` и `USER`. Переход `SYSTEM` -> `USER` - сопровождается ответом системы. Переход `USER` -> `SYSTEM` - сопровождается проверкой условий перехода. Таким образом переход из `SYSTEM` -> `USER` может быть один и не будет меняться. К примеру,  из вершины `SYS_WHAT_DO_YOU_WANT` можно перейти только в `USR_WHAT_DO_YOU_WANT`. А переход из `USR_WHAT_DO_YOU_WANT` можно выполнить в разные `SYS_*`

Сам граф диалога выстраивается с помощью функций `add_system_transition` - переход `SYSTEM` -> `USER` и   `add_user_transition` - переход `USER` -> `SYSTEM` . При вызове `add_system_transition` необходимо передать вершины графа и request функцию. При вызове `add_user_transition` необходимо передать вершины графа и response функцию. 

Если необходимо обработать вариант, когда ни одна из функций перехода `SYSTEM` -> `USER` не отработала с ответом `True` используется функция `set_error_successor`

Для DialogFlow необходимы 2 типа функций:
- 1 тип - request функции, они должны возвращать булевое значении, которое будет определять переход по ребру графа, к которому они "привязаны"
- 2 тип - response функции, они должны возвращать cтроку, которая будет отправленна из скилла, с помощью специальной функции `set_confidence`, можно задавать конфиденс отличный от дефолтного

Оба типа функций, получают переменную `vars["agent"]` - она содержит все необходимые переменные/данные, включая стейт диалога, дерево entities, историю всех пройденных системных вершин графа `history`, предыдущий индекс ответа пользователя `last_human_utter_index`, текущий индекс ответа пользователя `human_utter_index` и т.д. 

Так же в `vars["agent"]` выделен специальный ключ `dialog_flow` - который можно использовать для сохранения переменных. Все переменные из `dialog_flow` - сохраняются в общий диалог стейт и могут быть использованы для обмена информации между нодами в графе.


 
 ### Shared Memory of DialogFlow
 request/response functions use a variable `vars`. `vars` - it's shared dictionary of a dialogflow. It consists from diferent fields, one of them is `agent`. For dialog design you can use only field `agent`.

 ```yaml
 vars:
    # some systems fileds for dialogflow
    # ...
    agent:
        dialog: # dialog state, that we get from agent, to get closed look at formatter of the service.
            human_utterances: [...] # len == 2
            bot_utterances: [...] # len == 1
        last_human_utter_index: 9998 # previos human utterence index
        human_utter_index: 9999 # current human utterence index
        entities: # it projects relations of `entity_name`(str)->`entity`(Entity), where each of entities are objects of class `Entity` from `common/entity_utils.py`. 
            enity_name_1: "object of class Entity"
            enity_name_2: "object of class Entity"
            # ...
        history: # human_utter_index -> state_name
            "0": State.SYS_STATE_0
            "1": State.SYS_STATE_1
            # ...
        shared_memory: # it's a dictionary for other purposes, you can store to this yours variables/objects for sharing between nodes of dialogflow
            CUSTOM_VAR_NAME_0: CUSTOM_VAR_0
            CUSTOM_VAR_NAME_1: CUSTOM_VAR_1
            # ...
 ```
