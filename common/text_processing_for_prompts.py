import tiktoken


def check_token_number(text, model_name="gpt-3.5-turbo", enc=None):
    if enc is None:
        enc = tiktoken.encoding_for_model(model_name)
    len_text = len(enc.encode(text))
    return len_text


def split_transcript_into_chunks(transcript, model_name="gpt-3.5-turbo", limit=3000, sep="\n"):
    transcript_list = transcript.split(sep)
    enc = tiktoken.encoding_for_model(model_name)
    n_tokens_sep = check_token_number(sep, enc=enc)
    transcript_chunks = []
    transcript_chunk = ""
    len_chunk = 0
    for curr_part in transcript_list:
        if not transcript_chunk:
            transcript_chunk = curr_part
            len_chunk = check_token_number(curr_part, enc=enc)
        else:
            n_tokens_curr_part = check_token_number(curr_part, enc=enc)
            if len_chunk + n_tokens_sep + n_tokens_curr_part <= limit:
                len_chunk += n_tokens_sep + n_tokens_curr_part
                transcript_chunk += f"{sep}{curr_part}"
            else:
                transcript_chunks.append(transcript_chunk)
                transcript_chunk = curr_part
                len_chunk = n_tokens_curr_part
    transcript_chunks.append(transcript_chunk)
    return transcript_chunks
