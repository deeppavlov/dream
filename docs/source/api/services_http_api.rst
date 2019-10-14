There are 5 types of dialog services that can be connected to the `Agent's dialog pipeline <dialog-pipeline_>`__:

    *  **Annotators**
    *  **Skill Selector**
    *  **Skills**
    *  **Response Selector**
    *  **Postprocessor**


Input Format
============

All services get a standardized Agent State as input. The input format is described `here <state_>`__.

To reformat Agent State format into your service's input format, you need to write a **formatter** function and
specify it's name into the Agent's `config file <config file>`__. You can use our DeepPavlov `formatters <formatters>`__
as example.

Output Format
=============

All services have it's own specified output format. If you need to reformat your service's response, you should use the same
formatter function that you used for the input format, just use the ``mode=='out'`` flag.

Annotator
=========

Annotator should return a free-form response.

For example, the NER annotator may return a dictionary with ``tokens`` and ``tags`` keys:

    .. code:: json

        {"tokens": ["Paris"], "tags": ["I-LOC"]}

For example, a Sentiment annotator can return a list of labels:

    .. code:: json

        ["neutral", "speech"]

Also a Sentiment annotator can return just a string:

    .. code:: json

        "neutral"

Skill Selector
==============

Skill Selector should return a list of selected skill names.

For example:

    .. code:: json

        ["chitchat", "hello_skill"]


Skill
=====

Skill should return a **list of dicts** where each dict ia a single hypothesis. Each dict requires
``text`` and ``confidence`` keys. If a skill wants to update either **Human** or **Bot** profile,
it should pack these attributes into ``human_attributes`` and ``bot_attributes`` keys.

All attributes in ``human_attributes`` and ``bot_attributes`` will overwrite current **Human** and **Bot**
attribute values accordingly. And if there are no such attributes, they will be stored under ``attributes``
key inside **Human** or **Bot**.

The minimum required response of a skill is a 2-key dictionary:


    .. code:: json

        [{"text": "hello", "confidence": 0.33}]

But it's possible to extend it with  ``human_attributes`` and ``bot_attributes`` keys:

    .. code:: json

        [{"text": "hello", "confidence": 0.33, "human_attributes": {"name": "Vasily"},
        "bot_attributes": {"persona": ["I like swimming.", "I have a nice swimming suit."]}}]

Everything sent to ``human_attributes`` and ``bot_attributes`` keys will update `user` field in the same
utterance for the human and in the next utterance for the bot. Please refer to user_state_api_ to find more
information about the **User** object updates.

Also it's possible for a skill to send any additional key to the state:

    .. code:: json

        [{"text": "hello", "confidence": 0.33, "any_key": "any_value"}]


Response Selector
=================

Unlike Skill Selector, Response Selector should select a *single* skill responsible for generation of the
final response shown to the user. The expected result is a name of the selected skill, text (may be
overwritten from the original skill response) and confidence (also may be overwritten):

 .. code:: json

        {"skill_name": "chitchat", "text": "Hello, Joe!", "confidence": 0.3}

Also it's possible for a Response Selector to overwrite any ``human`` or ``bot`` attributes:

 .. code:: json

        {"skill_name": "chitchat", "text": "Hello, Joe!", "confidence": 0.3, "human_attributes": {"name": "Ivan"}}

Postprocessor
=============

Postprocessor has a power to rewrite a final bot answer selected by the Response Selector. For example, it can
take a user's name from the state and add it to the final answer.

It simply should return a rewritten answer. The rewritten answer will go the ``text`` field of the final
utterance shown to the user, and the original skill answer will go to the ``orig_text`` field.

 .. code:: json

        "Goodbye, Joe!"


.. _dialog-pipeline: https://deeppavlov-agent.readthedocs.io/en/latest/intro/overview.html#architecture-overview
.. _state: https://deeppavlov-agent.readthedocs.io/en/latest/_static/api.html
.. _config file: https://github.com/deepmipt/dp-agent/blob/master/config.py
.. _formatters: https://github.com/deepmipt/dp-agent/blob/master/state_formatters/dp_formatters.py
.. _user_state_api: https://deeppavlov-agent.readthedocs.io/en/latest/api/user_state_api.html

