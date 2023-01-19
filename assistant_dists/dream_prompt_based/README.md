# Dream Prompt-based Distribution

**Consider this distribution as a TEMPLATE for a prompt-based distribution**

## What is Dream Prompt-based distribution

Dream Prompt-based distribution is an example of the prompt-based dialogue system. 

It contains the following skills:
* Dummy Skill (`dummy_skill`) is a fallback skill (also it is a part of agent container, so no separate container required)
* DFF Dream Persona Prompt-based Skill (`dff_dream_persona_prompt_based_skill`) is a skill created via DFF (Dialog Flow Framework)
which generates a response to the current dialogue context taking into account the given prompt 
(the **prompt is the same for all the dialogue steps**).

The **DFF Dream Persona Prompt-based Skill** is a light-weight container sending requests to the generative service 
which utilizes a neural network for prompt-based generation.
DFF Dream Persona Prompt-based Skill accepts two main environmental variables:
  * `PROMPT_FILE`  contains a path to a JSON file containing dictionary with prompt, 
  * `GENERATIVE_SERVICE_URL` contains a URL of the generative service to be used. 
  The service must utilize the same input-output format as Transformers-LM (`transformers_lm`). 

The distribution may contain several Prompt-based skills. Therefore, the **Prompt Selector** component is presented. 
The Prompt Selector is also a light-weight container utilizing **Sentence Ranker** component 
(its URL is given in `.env` file as `SENTENCE_RANKER_SERVICE_URL`) to select `N_SENTENCES_TO_RETURN` 
the most relevant prompts (precisely, it returns ordered list of prompt names) among the given ones. 
The `,`-joint list of the prompt names to be considered is given as an environmental variable `PROMPTS_TO_CONSIDER`.
Each considered prompt should be located as `dream/common/prompts/<prompt_name>.json`.

**Important!** If Prompt Selector annotations are detected in the user utterance, the Skill Selector turns on skills with names
`dff_<prompt_name>_prompt_based_skill`. Therefore, a prompt name can contain `'_'` but not `'-'`.

## How to Create a New Prompt-based Distribution

