# Post-Annotator Skill Selector


## Description
The Skill Selector service provides a list of selected skills to generate a response for a dialogue. It is a part of the main Dream distribution, built on the DeepPavlov Agent framework.

The Skill Selector forms a list of the most relevant skills based on the dialogue context. 
It considers fallback and open-domain skills by default. Closed-domain skills are selected if specific triggers _(topics, entities, intents, or regular expressions)_ are detected. 

To avoid resource overload, the number of selected skills is controlled.


## Input/Output

**Input**
Annotated user input and dialogue context

**Output**
A list of selected skills

## Dependencies
none 