import torch
from itertools import chain
import logging
import torch.nn.functional as F

logger = logging.getLogger(__name__)


SPECIAL_TOKENS = ["<bos>", "<eos>", "<speaker1>", "<speaker2>", "<pad>"]
MODEL_INPUTS = ["input_ids", "mc_token_ids", "lm_labels", "mc_labels", "token_type_ids"]
PADDED_INPUTS = ["input_ids", "lm_labels", "token_type_ids"]


def build_input_from_segments(persona, history, reply, tokenizer, lm_labels=False, with_eos=True):
    """Build a sequence of input from 3 segments: persona, history and last reply"""
    bos, eos, speaker1, speaker2 = tokenizer.convert_tokens_to_ids(SPECIAL_TOKENS[:-1])

    instance = {}
    sequence = [[bos] + list(chain(*persona))] + history + [reply + ([eos] if with_eos else [])]
    sequence = [sequence[0]] + [
        [speaker2 if (len(sequence) - i) % 2 else speaker1] + s for i, s in enumerate(sequence[1:])
    ]

    instance["input_ids"] = list(chain(*sequence))
    instance["token_type_ids"] = [speaker2 if i % 2 else speaker1 for i, s in enumerate(sequence) for _ in s]
    instance["mc_token_ids"] = len(instance["input_ids"]) - 1
    instance["lm_labels"] = [-1] * len(instance["input_ids"])
    if lm_labels:
        instance["lm_labels"] = ([-1] * sum(len(s) for s in sequence[:-1])) + [-1] + sequence[-1][1:]
    return instance, sequence


def create_generator(tokenizer, model, device="cpu", with_eos=False):
    def generator(personality, history, current_output=None):
        current_output = [] if current_output is None else current_output
        instance, sequence = build_input_from_segments(personality, history, current_output, tokenizer, with_eos=False)

        input_ids = torch.tensor(instance["input_ids"], device=device).unsqueeze(0)
        token_type_ids = torch.tensor(instance["token_type_ids"], device=device).unsqueeze(0)

        logits = model(input_ids, token_type_ids=token_type_ids)
        return logits

    return generator


def get_special_tokens_ids(tokenizer):
    return tokenizer.convert_tokens_to_ids(SPECIAL_TOKENS)


def top_filtering(logits, top_k=0, top_p=0.0, threshold=-float("Inf"), filter_value=-float("Inf")):
    """Filter a distribution of logits using top-k, top-p (nucleus) and/or threshold filtering
    Args:
        logits: logits distribution shape (vocabulary size)
        top_k: <=0: no filtering, >0: keep only top k tokens with highest probability.
        top_p: <=0.0: no filtering, >0.0: keep only a subset S of candidates, where S is the smallest subset
            whose total probability mass is greater than or equal to the threshold top_p.
            In practice, we select the highest probability tokens whose cumulative probability mass exceeds
            the threshold top_p.
        threshold: a minimal threshold to keep logits
    """
    assert logits.dim() == 1  # Only work for batch size 1 for now - could update but it would obfuscate a bit the code
    top_k = min(top_k, logits.size(-1))
    if top_k > 0:
        # Remove all tokens with a probability less than the last token in the top-k tokens
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value

    if top_p > 0.0:
        # Compute cumulative probabilities of sorted tokens
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probabilities = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probabilities > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        # Back to unsorted indices and set them to -infinity
        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = filter_value

    indices_to_remove = logits < threshold
    logits[indices_to_remove] = filter_value

    return logits


def sample_tokens(
    logits,
    token_position,
    special_tokens_ids,
    min_length=1,
    top_k=0,
    top_p=0.0,
    threshold=-float("Inf"),
    temperature=0.7,
    no_sample=True,
    beam_size=1,
):
    logits = logits[0, -1, :] / temperature
    logits = top_filtering(logits, top_k=top_k, top_p=top_p, threshold=threshold)
    if token_position < min_length:
        logits[special_tokens_ids] = -float("Inf")
    probs = F.softmax(logits, dim=-1)
    if no_sample:
        token_indexes = torch.topk(probs, beam_size)[1].tolist()
    else:
        available_beam_size = torch.gt(torch.topk(probs, beam_size)[0], 0.0).sum()
        token_indexes = torch.multinomial(probs, available_beam_size).tolist()
    token_probs = probs[token_indexes]
    return token_indexes, token_probs
