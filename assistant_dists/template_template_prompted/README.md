# Template Prompted Distribution

**_One may consider this distribution as a TEMPLATE for a prompt-based distribution which may contain any number of 
prompt-based skills each of which is conditioned on a single prompt during the whole conversation_**

**Note!** Each Prompt-based Skill utilizes the **same prompt during the whole dialog**!

# What is Dream Prompted Distribution

Template Prompted distribution is an example of the prompt-based dialogue system which contains one prompt-based skill, 
in particular, prompt is a persona description. 

Template Prompted distribution contains the following skills:
* Dummy Skill (`dummy_skill`) is a fallback skill (also it is a part of agent container, so no separate container required)
* DFF Template Prompted Skill (`dff_template_template_prompted_skill`) is a skill created via DFF (Dialog Flow Framework)
which generates a response to the current dialogue context taking into account the given prompt, i.g., bot's persona description.

### DFF Template Prompted Skill

The **DFF Template Prompted Skill** is a light-weight container sending requests to the generative service 
which utilizes a neural network for prompt-based generation.
DFF Template Prompted Skill accepts two main environmental variables:
  * `PROMPT_FILE`  contains a path to a JSON file containing dictionary with prompt, 
  * `GENERATIVE_SERVICE_URL` contains a URL of the generative service to be used.
  The service must utilize the same input-output format as Transformers-LM (`transformers_lm`). 
  * `GENERATIVE_SERVICE_CONFIG` contains a name of config file containing the generative service's parameters to be used.
  * `GENERATIVE_TIMEOUT` contains a timeout in seconds for the generative service.
  * `N_UTTERANCES_CONTEXT` contains lengths of the considered context in terms of number of dialogue utterances.
  * `ENVVARS_TO_SEND` \[optional\] contains names of environmental variables to be sent to generative service (for example, API keys for OpenAI).
  These environmental variables can be specified only in case of development mode (not in production).
  In production mode, the API keys are a part of the request.


**Note!** DFF Template Prompted Skill utilizes a special universal template `skills/dff_template_prompted_skill`
which do not require creation of the new skill's directory. For your convenience, creating a new skill, 
you should utilize the same template folder but specify another prompt file, service port, and specify another container name.

### Prompt Selector

The distribution may contain **several Prompt-based skills.** Therefore, the **Prompt Selector** component is presented. 
The Prompt Selector is also a light-weight container utilizing **Sentence Ranker** component 
(its URL is given in `.env` file as `SENTENCE_RANKER_SERVICE_URL`) to select `N_SENTENCES_TO_RETURN` 
the most relevant prompts (precisely, it returns ordered list of prompt names) among the given ones. 
The `,`-joint list of the prompt names to be considered is given as an environmental variable `PROMPTS_TO_CONSIDER`.
Each considered prompt should be located as `dream/common/prompts/<prompt_name>.json`.

**Note!** In the Template Prompted Distribution we give a single prompt to the Prompt Selector: `template_template`.
You may specify several prompts separated with semicolon just for the demonstration of the `PROMPTS_TO_CONSIDER`'s input format. 
Template Prompted Distribution contains only one prompted skill which utilizes Template prompt.

### Skill Selector

You should not do any changes in the Skill Selector, it would call all the skills with the most relevant prompts
automatically according to the Prompt Selector.  If Prompt Selector annotations are detected in the user utterance, 
the Skill Selector turns on skills with names `dff_<prompt_name>_prompted_skill` for each prompt_name from
`N_SENTENCES_TO_RETURN` the most relevant prompts detected by Prompt Selector. 
Therefore, a prompt name can contain `'_'` but not `'-'`. 

**Note!** Pay attention that you may specify to the Prompt Selector prompt names 
even if the corresponding skills are not presented in the distribution, so if you, for example, specify 5 prompt names
while your distribution contains only 2 prompted skill, and you assign the number of returned most relevant prompts
(`N_SENTENCES_TO_RETURN`) to 3, you may face a situation when the Prompt Selector will choose all prompts for which
you do not have skills, so the response on that step will be provided by other skills presented in the distribution 
(in particular, by Dummy Skill for the current version of Dream Prompted distribution).

# How to Create a New Prompted Distribution

If one wants to create a new prompted distribution (distribution containing prompt-based skill(s)), one should:

1. Copy the `dream/assistant_dists/template_template_prompted` directory to `dream/assistant_dists/dream_custom_prompted`
(the name is an example!).
2. **For each prompt-based skill, one needs to**:
   1. create a `dream/common/prompts/<prompt_name>.json` files containing a prompt. 
   **Important!** `<prompt_name>` should only contain letters, numbers and underscores (`_`) but no dashes (`-`)!
   2. in `dream/assistant_dists/dream_custom_prompted/` folder in files `docker-compose.override.yml`, `dev.yml` 
   copy description of container `template-template` and replace strings `template-template` with `<prompt-name>` 
   (container names are using dashes) and 
   `template_template` with `<prompt_name>` (component names are using underscores). 
   If your prompt name is written as a single word 
   (for example, `spacexfaq` not `spacex_faq`), replace both `template-template` and `template_template` with your prompt name.
   3. for each new container (a new container for each new DFF skill) change the `SERVICE_PORT` 
   to an unused one.
3. Choose the generative service to be used. For that one needs to:
   1. in `dream/assistant_dists/dream_custom_prompted/` folder in files `docker-compose.override.yml`, `dev.yml` 
   replace `transformers-lm-gptj` container description to a new one. 
   In particular, one may replace in `PRETRAINED_MODEL_NAME_OR_PATH` parameter 
   a utilized Language Model (LM) `GPT-J` with another one from `Transformers` library. 
   Please change a port (`8130` for `transformers-lm-gptj`) to unused ones. 
   2. in all prompted skills' containers descriptions change `GENERATIVE_SERVICE_URL` to your generative model. 
   Take into account that the service name is constructed as `http://<container-name>:<port>/<endpoint>`. 
4. For each prompted skill, one needs to create an input state formatter. To do that, one needs to:
   1. in `dream/dp_formatters/state_formatters.py` duplicate function:
   ```python
   def dff_template_template_prompted_skill_formatter(dialog):
       return utils.dff_formatter(
           dialog, "dff_template_template_prompted_skill",
           types_utterances=["human_utterances", "bot_utterances", "utterances"]
       )
   ```
   2. replace string  `template_template` with `<prompt_name>` (component names are using underscores) in each duplicated function. 
5. In `dream/assistant_dists/dream_custom_prompted/pipeline_conf.json` for each prompt-based skill, one needs to:
   1. copy description of DFF Dream Persona Prompted Skill:
   ```json
            "dff_template_template_prompted_skill": {
                "connector": {
                    "protocol": "http",
                    "timeout": 4.5,
                    "url": "http://dff-template-template-prompted-skill:template_port/respond"
                },
                "dialog_formatter": "state_formatters.dp_formatters:dff_template_template_prompted_skill_formatter",
                "response_formatter": "state_formatters.dp_formatters:skill_with_attributes_formatter_service",
                "previous_services": [
                    "skill_selectors"
                ],
                "state_manager_method": "add_hypothesis"
            },
   ```
   2. replace strings `template-template` with `<prompt-name>` (container names are using dashes) and 
   `template_template` with `<prompt_name>` (component names are using underscores). It will change the container name, 
   skill name, formatter name
   3. replace port (`template_port` in the example) to the assigned one in 
   `dream/assistant_dists/dream_custom_prompted/docker-compose.override.yml`.
6. If one does not want to keep DFF Dream Persona Prompted Skill in their distribution, one should remove all mentions
of DFF Dream Persona Prompted Skill container from `yml`-configs and `pipeline_conf.json` files.

**Note!** Please, take into account that naming skill utilizing <prompt_name> according to the instruction above
is very important to provide Skill Selector automatically turn on the prompt-based skills which are returned as 
`N_SENTENCES_TO_RETURN` the most relevant prompts.



