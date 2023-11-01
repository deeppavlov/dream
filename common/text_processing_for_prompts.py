import tiktoken


def check_token_number(text, model_name="gpt-3.5-turbo", enc=None):
    if enc is None:
        enc = tiktoken.encoding_for_model(model_name)
    len_text = len(enc.encode(text))
    return len_text


def decide_where_to_break(transcript, model_name="gpt-3.5-turbo", limit=3000, sep="\n"):
    # the list of models with available encoders, see to define what model_name you need:
    # https://github.com/openai/tiktoken/blob/39f29cecdb6fc38d9a3434e5dd15e4de58cf3c80/tiktoken/model.py#L19
    transcript_list = transcript.split(sep)
    enc = tiktoken.encoding_for_model(model_name)
    len_tokens = 0
    break_points = []
    for n, utt in enumerate(transcript_list):
        len_tokens += check_token_number(utt, enc=enc)
        if len_tokens > limit:
            len_tokens = check_token_number(utt, enc=enc)
            break_points.append(n - 1)
    return break_points


def split_transcript_into_chunks(transcript, break_points):
    transcript_list = transcript.split("\n")
    transcript_chunks = []
    start_point = 0
    for break_point in break_points:
        chunk = "\n".join(transcript_list[start_point:break_point])
        transcript_chunks.append(chunk)
        start_point = break_point
    last_chunk = "\n".join(transcript_list[start_point:])
    transcript_chunks.append(last_chunk)
    return transcript_chunks
