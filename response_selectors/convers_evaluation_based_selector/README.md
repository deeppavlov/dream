# Labeled Data

Labeled data is located in `response_selectors/convers_evaluation_based_selector/labeled_data/`.

To label more data you can use data_labelling.py script.
It takes `dialog_id` from http://ec2-3-90-214-142.compute-1.amazonaws.com/admin/conversation/
and `save_dir` (should be labeled_data/ folder) as an input.
It provides console interface to label the data for quality measuring for response selector.

Example: `python response_selectors/convers_evaluation_based_selector/data_labelling.py --dialog_id 5e4822a81506f4f91a8aaf5e --save_dir response_selectors/convers_evaluation_based_selector/labeled_data/`

Example output:

```
human: turn off how do you talk about british
bot: Hi, this is an Alexa Prize Socialbot!
human: hi there
0 hypot: Could you, please, help and explain to me. Yesterday I was browsing photos on the Internet. And seen a lot of people in very, very strange poses. It was called yoga. Have you ever tried to tie yourself in a knot?; skill: meta_script_skill; conf: 0.99
1 hypot: Good Evening, this is an Alexa Prize Socialbot! How are you?; skill: program_y; conf: 0.98
2 hypot: Hi there!; skill: alice; conf: 0.65
3 hypot: how are you doing today?; skill: dummy_skill; conf: 0.6
4 hypot: Let's talk about something else.; skill: dummy_skill; conf: 0.5
Type best hypot num(s), separated by comma:
```

It shows context with latest user sentence (`human: hi there`) and list of hypotheses for this user response.
In `Type best hypot num(s), separated by comma:` hypots nums expected.
If no hypot num provided this sample will be skipped.

For this context you may type 0,3 hypots:
```
Type best hypot num(s), separated by comma: 0,3
```

When dialog ends it saves it into labeled_data folder.


# Measuring quality

It takes `--data_dir` as an input (the same as save_dir from data labelling script).
Outputs overall accuracy.

Example of usage:

```
python response_selectors/convers_evaluation_based_selector/measure_quality.py \
                   --data_dir response_selectors/convers_evaluation_based_selector/labeled_data/

Overall accuracy: 0.5185185185185185
```

## How to run conversation evaluator locally

`docker-compose -f docker-compose.yml -f dev.yml -f cpu.yml -f one_worker.yml up toxic_classification blacklisted_words convers_evaluation_selector`

Then use `--url`.

Example of usage with url:

```
python response_selectors/convers_evaluation_based_selector/measure_quality.py \
                   --data_dir response_selectors/convers_evaluation_based_selector/labeled_data/  \
                   --url http://0.0.0.0:8009/respond
```
