import stanza
stanza.download('en')
nlp = stanza.Pipeline('en')


pos_type_expl = {'i - someone': 1,
                 'you - someone': 2,
                 'i - you': 3,
                 'you - you': 3,
                 'i - i': 4,
                 'you - i': 5,
                 'we - someone': 6,
                 'someone - someone': 6,
                 'we - we': 7}

neg_type_expl = {'i - you': 1,
                 'i - someone': 2,
                 'we - someone': 3,
                 'you - someone': 3,
                 'you - i': 4,
                 'i - i': 5,
                 'we - we': 5}

first_prons = ['i', 'me', 'myself']
second_prons = ['you']
inclusive_prons = ['we']


def find_root(sent):
    for token in sent:
        if token['deprel'] == 'root':
            return token


def find_clause_head(root, sent):
    clauses = ['ccomp', 'xcomp', 'acl', 'acl:relcl', 'advcl']
    all_clause_heads = []
    head_id = root['id']
    for token in sent:
        if token['head'] == head_id and token['deprel'] in clauses:
            all_clause_heads.append(token)
    return all_clause_heads


def find_arguments(head, sent):
    objects = ['obl', 'obj', 'iobj']
    head_id = head['id']
    subj = ''
    obj = ''
    for token in sent:
        if token['head'] == head_id and 'subj' in token['deprel']:
            subj = token
        elif token['head'] == head_id and token['deprel'] in objects:
            obj = token
    return subj, obj


def reverse_if_not_verb(root, subj, obj, has_clauses):
    not_verbs = ['NOUN', 'ADJ', 'ADV']
    if has_clauses:
        return subj, obj
    if root['upos'] in not_verbs:
        obj = subj
        subj = 'I'
    return subj, obj


def find_final_arguments(sent):
    root = find_root(sent)
    subj, obj = find_arguments(root, sent)
    next_clause_heads = find_clause_head(root, sent)
    has_clauses = False
    if next_clause_heads:
        has_clauses = True
    queue = next_clause_heads

    if subj and not obj:
        dep_subj, dep_obj = '', ''
        while not dep_subj and not dep_obj and queue:
            root = queue[0]
            queue = queue[1:]
            dep_subj, dep_obj = find_arguments(root, sent)
            next_clause_heads = find_clause_head(root, sent)
            queue.extend(next_clause_heads)
        if dep_subj:
            obj = dep_subj
        else:
            obj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)

    while not subj and not obj and queue:
        root = queue[0]
        queue = queue[1:]
        subj, obj = find_arguments(root, sent)
        next_clause_heads = find_clause_head(root, sent)
        queue.extend(next_clause_heads)

    if obj and not subj:
        if 'Mood=Imp' in root['feats']:
            subj = {'text': 'you'}
        else:
            subj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)
    elif not subj and not obj:
        subj = {'text': 'someone'}
        obj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)
    elif subj and obj:
        return subj['text'], obj['text']
    else:
        obj = {'text': 'someone'}
        return subj['text'], obj['text']


def get_dsript_type(orig_sent, type_expl):
    doc = nlp(orig_sent)
    sent = doc.sentences[0].to_dict()
    subj, obj = find_final_arguments(sent)
    subj = subj.lower()
    obj = obj.lower()
    if subj not in first_prons and subj not in second_prons and subj not in inclusive_prons:
        subj = 'someone'
    if obj not in first_prons and obj not in second_prons and obj not in inclusive_prons:
        obj = 'someone'
    if subj in first_prons:
        subj = 'i'
    if obj in first_prons:
        obj = 'i'
    line = subj + ' - ' + obj
    if line not in type_expl:
        type_num = 3
    else:
        type_num = type_expl[line]
    return type_num