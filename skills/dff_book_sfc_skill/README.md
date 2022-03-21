# Book SFC skill (DFF)
This is an SFC-customized Book Skill service that handles typical book questions. Unlike the original Book Skill, this Skill has been augmented with the Speech Function classifier and predictor.
It can recommend books according to user's preferences.

# Example of using SFCs in DFF DSL in this Skill
To see how SFCs are used in this Skill, check out this file:

```/skills/dff_book_sfc_skill/scenario/main.py```, [line #244](https://github.com/deepmipt/dream/blob/feat/speech-function-dist-book-skill/skills/dff_book_sfc_skill/scenario/main.py#L244)

In this version, you can see that ...

# Metrics

OS: Windows 10
CPU: AMD Ryzen 5 3500U @ 2.10GHz

| Metric       | Average value |
| ------------ | ------------- |
| RAM          | ~ 385 MB      |
| Startup time | ~  3.985s     |
| Execute time | ~  2.687s     |
