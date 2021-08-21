from infer.utils import sample_tokens


def top_sampler(
    personality,
    history,
    generator,
    special_tokens_ids,
    min_length=1,
    max_length=20,
    top_k=0,
    top_p=0.0,
    threshold=-float("Inf"),
    temperature=0.7,
    no_sample=True,
    infered_token_ids=None,
):
    if infered_token_ids is None:
        infered_token_ids = []

    probs_output = []
    for token_position in range(max_length):
        logits = generator(personality, history, infered_token_ids)
        token_indexes, token_probs = sample_tokens(
            logits=logits,
            token_position=token_position,
            special_tokens_ids=special_tokens_ids,
            min_length=min_length,
            top_k=top_k,
            top_p=top_p,
            threshold=threshold,
            temperature=temperature,
            no_sample=no_sample,
            beam_size=1,
        )
        token_index, token_prob = token_indexes[0], token_probs[0]
        if token_index in special_tokens_ids:
            break
        infered_token_ids.append(token_index)
        probs_output.append(token_prob)

    return infered_token_ids, probs_output
