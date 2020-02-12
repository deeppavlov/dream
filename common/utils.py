def get_skill_outputs_from_dialog(utterances, skill_name, activated=False):
    """
    Extract list of dictionaries with already formatted outputs of `skill_name` from full dialog.
    If `activated=True`, skill also should be chosen as `active_skill`;
    otherwise, empty list.

    Args:
        utterances: utterances, the first one is user's reply
        skill_name: name of target skill
        activated: if target skill should be chosen by response selector on previous step or not

    Returns:
        list of dictionaries with formatted outputs of skill
    """
    result = []

    # do not consider last user's utterance because it doesn't have hypotheses
    for i in range(0, len(utterances) - 1, 2):
        is_active = utterances[i + 1]["active_skill"] == skill_name
        skills_outputs = utterances[i]["hypotheses"]
        skill_output = {}
        for skop in skills_outputs:
            if skop["skill_name"] == skill_name:
                skill_output = skop
                break

        if not activated or is_active:
            result.append(skill_output)

    return result


def transform_vbg(s):
    """
    Transform infinitive form of verb to Ving form.

    Args:
        s: verb infinitive

    Returns:
        string with required verb form
    """
    import re

    # by Anastasia Kravtsova
    s += '+VBG'
    # irregular cases
    s1 = re.compile(r'(?<![a-z])be\+VBG')
    s2 = re.compile(r'(?<![aouiey])([^aouiey][aouiey]([^aouieywr]))\+VBG')
    s3 = re.compile(r'ie\+VBG')
    s4 = re.compile(r'(ee)\+VBG')
    s5 = re.compile(r'e\+VBG')
    # regular case
    s6 = re.compile(r"\+VBG")

    # irregular cases
    s = re.sub(s1, 'being', s)
    s = re.sub(s2, r'\1\2ing', s)
    s = re.sub(s3, r'ying', s)
    s = re.sub(s4, r'\1ing', s)
    s = re.sub(s5, r'ing', s)
    # regular case
    s = re.sub(s6, "ing", s)
    return s


def get_list_of_active_skills(utterances):
    """
    Extract list of active skills names

    Args:
        utterances: utterances, the first one is user's reply

    Returns:
        list of string skill names
    """
    result = []

    for uttr in utterances:
        if "active_skill" in uttr:
            result.append(uttr["active_skill"])

    return result
