## Description

Intent Catcher. Each utterance is decomposed into sentences using sentseg, each sentence is embedded using an Universal sentence encoder (USE, https://arxiv.org/pdf/1803.11175.pdf).
You can find a number of various detectors in the `src/detector.py`.

## IMPORTANT:

As you **add new phrases to the intents**, please be very careful. Intents should not cross, as that would make a negative impact over the detector. For example, you should add phrases like "let's talk about something else" to topic\_switching not to lets\_talk\_about. Don't add unclear/meaningless phrases where intent isn't clear, or where speech wasn't correctly transcribed - this would only make detector's quality deteriorate. Intents are detected through the segments, so please take the segment of the phrase for the intent, not the whole phrase.

## Detectors Descriptions:

- **USESimpleDetector**:  each utterance is compared using the metric (*cosine similarity*) with the intent phrases, max score is obtained over all of these phrases and is cut through the threshold calculated before.
- **USERegCombinedDetector**: each phrase is sent through the regexp, and if none of the intents were matched, sentence is sent to **USESimpleDetector**.
- **ClassifierDetector**: (linear) classifier, trained over USE embeddings.
- **ClassRegCombinedDetector** (TBD): same as **USERegCombinedDetector**, but with **ClassifierDetector**.

## TODO:

- Code refactoring

## Метрики

**USERegCombinedDetector**:

| metrics/intents | exit        | repeat      | what\_is\_your\_name | where\_are\_you\_from | what\_can\_you\_do | who\_made\_you | what\_is\_your\_job |
|-----------------|-------------|-------------|----------------------|-----------------------|--------------------|----------------|---------------------|
| precision       | 0.933369776 | 0.819418869 | 0.996363636          | 0.958124098           | 0.851321586        | 0.876727199    | 0.92990404          |
| recall          | 0.617079005 | 0.731826007 | 0.818103175          | 0.87984127            | 0.72               | 0.877472177    | 0.905040404         |
| f1              | 0.735439153 | 0.767964591 | 0.893786162          | 0.909311858           | 0.670418219        | 0.874162102    | 0.912530126         |

**Linear classifier**

| metrics/intent | cant\_do            | doing\_well         | dont\_understand    | exit                | lets\_chat\_about   | no                  | opinion\_request    | repeat              | stupid              | tell\_me\_a\_story  | tell\_me\_more      | topic\_switching    | weather\_forecast\_intent | what\_can\_you\_do  | what\_is\_your\_job | what\_is\_your\_name | what\_time           | where\_are\_you\_from | who\_made\_you      | yes                 |
|----------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------------|---------------------|---------------------|----------------------|----------------------|-----------------------|---------------------|---------------------|
| precision      | 0\.996370827930234  | 1\.0                | 0\.9963139895369914 | 0\.976848369399141  | 0\.9980131016611729 | 0\.98259640923863   | 0\.9967476604124078 | 1\.0                | 0\.9915204483975734 | 1\.0                | 1\.0                | 0\.9938837358914336 | 0\.9981449057007502       | 0\.9457619876521479 | 0\.9834451345755694 | 0\.9954545454545455  | 0\.4                 | 0\.9979233801034255   | 0\.9842851620862507 | 0\.9989473684210527 |
| recall         | 0\.9789907024298004 | 0\.8418686609758457 | 0\.9612128273947134 | 0\.8852047711902987 | 0\.7815816203758551 | 0\.7292528054953611 | 0\.9930852795250376 | 0\.9606103041529309 | 0\.9339179376498782 | 0\.9954179988769324 | 0\.7009442054333695 | 0\.975010632291602  | 0\.9809229005599981       | 0\.680864462197054  | 0\.7706581286360698 | 0\.7832070707070706  | 0\.10833333333333332 | 0\.9268384477169841   | 0\.9664957811945529 | 0\.5560519627197736 |
| f1             | 0\.9875945058294399 | 0\.9118411709630541 | 0\.9783849317626867 | 0\.9287165438688353 | 0\.8761461561467232 | 0\.8350542929671784 | 0\.9949123130751806 | 0\.9797954964671032 | 0\.9617408474913504 | 0\.9976824122078183 | 0\.819892689538017  | 0\.9843307745941875 | 0\.9894513879675697       | 0\.7842091598255596 | 0\.8606044927745723 | 0\.8700951447994909  | 0\.16369047619047622 | 0\.960758547879826    | 0\.9746511535963178 | 0\.711350597533756  |

**MLP**


| metrics/intent | cant\_do | doing\_well         | dont\_understand    | exit                | lets\_chat\_about   | no                  | opinion\_request    | repeat              | stupid              | tell\_me\_a\_story  | tell\_me\_more      | topic\_switching    | weather\_forecast\_intent | what\_can\_you\_do  | what\_is\_your\_job | what\_is\_your\_name | what\_time          | where\_are\_you\_from | who\_made\_you      | yes                 |
|----------------|----------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------|---------------------------|---------------------|---------------------|----------------------|---------------------|-----------------------|---------------------|---------------------|
| precision      | 1\.0     | 0\.966337657643772  | 0\.9941786949997526 | 0\.9959737009098506 | 0\.9976744186046511 | 0\.9998061970482512 | 0\.9959529792950844 | 0\.9966334389061504 | 0\.9955994529512531 | 0\.9778503174816345 | 0\.9957693734493146 | 0\.9995826812380196 | 0\.9945025990630013       | 0\.9497847985347985 | 0\.9293557422969189 | 0\.9996125591687537  | 0\.9745467013971766 | 0\.950023450544103    | 0\.9590464245899029 | 0\.9774537676284331 |
| recall         | 1\.0     | 0\.9614285714285714 | 0\.9873376623376625 | 0\.9825153374233129 | 0\.9976190476190474 | 0\.9997367531955627 | 0\.9837837837837838 | 0\.9952876984126986 | 0\.9938321536905965 | 0\.9677383592017736 | 0\.9911184210526315 | 0\.9994601274879666 | 0\.9914965986394557       | 0\.9461538461538461 | 0\.89               | 0\.9985533453887884  | 0\.9290540540540541 | 0\.8921052631578947   | 0\.8975             | 0\.9395348837209303 |
| f1             | 1\.0     | 0\.9634078726101022 | 0\.9907162874862274 | 0\.989157787642809  | 0\.9976187101346564 | 0\.9997714674908474 | 0\.9897389913767114 | 0\.995958372527378  | 0\.9947100660089335 | 0\.9726567253338555 | 0\.9933878181968314 | 0\.999521355803318  | 0\.9929910060745823       | 0\.9437942539441788 | 0\.9028755224660395 | 0\.9990826096033283  | 0\.9508483602105748 | 0\.9169075719953568   | 0\.9198216883789179 | 0\.9576263101054515 |


## Getting started

To add new intent, you should
 1. Add a name of your intent to the `<intent_data_path>/intent_phrases.json` file; add phrases/regexps for those phrases, acceptable punctuation symbols, as well as the min_precision - minimally acceptable precision for the threshold. \\
 If you want a phrase to be manually checked through regexp (see `RegMD`), but not through the trained model (e.g., `let's play .*`), then add it to a separate subelement `reg_phrases` of the intent.
 2. Call this script `python3 create_data_and_train_model.py` to train the model. Thresholds will be automatically saved to `intent_data.json`

Example for running this command within the Docker Container:
 ```
  python3 /data/create_data_and_train_model.py
 ```
