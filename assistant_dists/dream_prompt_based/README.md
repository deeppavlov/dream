# Dream Prompt-based Distribution

**Consider this distribution as a TEMPLATE for a prompt-based distribution**

## What is Dream Prompt-based distribution

PROMPT SELCTOR!!!

Dream Prompt-based distribution is an example of the prompt-based dialogue system. 

Each Prompt-based Skill utilizes the **same prompt during the whole dialog**!

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
  * `N_UTTERANCES_CONTEXT` contains lengths of the considered context in terms of number of dialogue utterances.

The distribution may contain several Prompt-based skills. Therefore, the **Prompt Selector** component is presented. 
The Prompt Selector is also a light-weight container utilizing **Sentence Ranker** component 
(its URL is given in `.env` file as `SENTENCE_RANKER_SERVICE_URL`) to select `N_SENTENCES_TO_RETURN` 
the most relevant prompts (precisely, it returns ordered list of prompt names) among the given ones. 
The `,`-joint list of the prompt names to be considered is given as an environmental variable `PROMPTS_TO_CONSIDER`.
Each considered prompt should be located as `dream/common/prompts/<prompt_name>.json`.

**Important!** If Prompt Selector annotations are detected in the user utterance, the Skill Selector turns on skills with names
`dff_<prompt_name>_prompt_based_skill`. Therefore, a prompt name can contain `'_'` but not `'-'`.

## How to Create a New Prompt-based Distribution

If one wants to create a new Prompt-based distribution (distribution containing prompt-based skill(s)), one should:
1. Copy the `dream/assistant_dists/dream_prompt_based` directory to `dream/assistant_dists/dream_custom_prompt_based`
(this name is an example!).
2. DFF Dream Persona Prompt-based Skill's container is described in 
`dream/assistant_dists/dream_spacex_prompt_based/dream_persona*.yml` configs. 
For each prompt-based skill, one needs to:
   1. create a `dream/common/prompts/<prompt_name>.json` files containing a prompt.
   2. copy files `dream_persona.yml` and `dream_persona_dev.yml` to `<prompt_name>.yml` and `<prompt_name>_dev.yml`;
   3. in both files replace strings `dream-persona` with `<prompt-name>` (container names are using dashes) and 
   `dream_persona` with `<prompt_name>` (component names are using underscores). 
   If your prompt name is written as a single word 
   (for example, `spacexfaq` not `spacex_faq`), replace both `dream-persona` and `dream_persona` with your prompt name.
   4. change the `SERVICE_PORT` to an unused on your distribution one.
3. Choose the generative service to be used. For that one needs to:
   1. change `dream/assistant_dists/dream_custom_prompt_based/transformers_lm*.yml` to containers 
   with your generative service of interest.
   2. in all prompt-based skills configs (from the step 2) change `GENERATIVE_SERVICE_URL` to your generative model. 
   Take into account that the service name is constructed as `http://<container-name>:<port>/<endpoint>`. 
4. For each prompt-based skill, one needs to create an input state formatter. To do that, one needs to:
   1. copy `dream/state_formatters/dream_persona.py` to `dream/state_formatters/<prompt_name>.py`.
   2. replace string  `dream_persona` with `<prompt_name>` (component names are using underscores). 
5. In `dream/assistant_dists/dream_custom_prompt_based/pipeline_conf.json` for each prompt-based skill, one needs to:
   1. replace strings `dream-persona` with `<prompt-name>` (container names are using dashes) and 
   `dream_persona` with `<prompt_name>` (component names are using underscores). It will change the container name, 
   skill name, formatter name
   2. replace port (`8134` in the example) to the assigned one in `<prompt_name>.yml`.

**Important!** Please, take into account that naming skill utilizing <prompt_name> according to the instruction above
is very important to provide Skill Selector automatically turn on the prompt-based skills which are returned as 
`N_SENTENCES_TO_RETURN` the most relevant prompts.



