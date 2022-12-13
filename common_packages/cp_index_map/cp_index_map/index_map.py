def make_map_from_spans(span_maps, L):
    """
    Input: [((i_1, j_1), n_1), ..., ((i_k, j_k), n_k)]
    """
    pos, answer = 0, []
    for (i, j), n in span_maps:
        while pos < i:
            answer.append(pos)
            pos += 1
        answer.extend([i] * n)
        pos = j
    answer.extend(range(pos, L + 1))
    return answer


def compose_map(first, second):
    # answer[i] = first[second[i]]
    try:
        answer = [first[index] for index in second]
        return answer
    except:
        print(first)
        print(second)
        raise ValueError
