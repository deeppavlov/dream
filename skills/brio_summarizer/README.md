#Wikidata dialogue skill

Skill for dialogue generation based on Wikidata triplets about entities from the dialogue.

The skill takes as input entity linking annotations from the user's utterance. Then the skill uses wiki parser to extract triplets for the entity. The triplets are ranked and the triplet with the highest score is used for generation of response utterance. The highest-score triplet and the user's utterance, separated with "SEP" token, are fed into DialoGPT for generation of the response utterance.

RAM: 5 Gb, GPU: 1.5 Gb, response time ~0.5 s.
