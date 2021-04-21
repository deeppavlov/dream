import heapq
import operator

from infer.utils import sample_tokens

import logging


logger = logging.getLogger(__name__)


class BeamSearchNode(object):
    def __init__(self, infered_token_ids, previous_node, token_id, prob):
        """
        :param hiddenstate:
        :param previous_node:
        :param token_id:
        :param prob:
        :param length:
        """
        self.infered_token_ids = infered_token_ids
        self.previous_node = previous_node
        self.token_id = token_id
        self.prob = prob
        self.length = len(infered_token_ids)

    def eval(self, personality=None, history=None, alpha=1.0):
        personality = [] if personality is None else personality
        history = [] if history is None else history
        reward = 0
        # Add here a function for shaping a reward

        return float(self.prob / float(self.length + 1e-6) + alpha * reward)


def beam_sampler(
    personality,
    history,
    generator,
    special_tokens_ids,
    beam_size=3,
    nbest=3,  # how many sentence do you want to generate
    min_length=1,
    max_length=20,
    top_k=0,
    top_p=0.0,
    threshold=-float("Inf"),
    temperature=0.7,
    no_sample=True,
    infered_token_ids=None,
):
    """

    Args:
        target_tensor: target indexes tensor of shape [B, T] where B is the
            batch size and T is the maximum length of the output sentence
        decoder_hidden: input tensor of shape [1, B, H] for start of the decoding
        encoder_outputs: if you are using attention mechanism you can pass encoder outputs,
            [T, B, H] where T is the maximum length of input sentence
    Returns:
        decoded_batch
    """

    # Start with the start of the sentence token
    if infered_token_ids is None:
        infered_token_ids = []

    # Number of sentence to generate
    ended_nodes = []
    number_required = min((nbest + 1), nbest - len(ended_nodes))

    # starting node -  hidden vector, previous node, token id, prob, length
    node = BeamSearchNode(infered_token_ids, None, 0, 1)
    queue = []
    # start the queue
    heapq.heappush(queue, (-node.eval(), node))

    # start beam search
    for step_n in range(10000):
        # give up when decoding takes too long
        if len(queue) > 90:
            # logger.info(f"step_n = {step_n}")
            break

        # fetch the best node
        score, cur_node = heapq.heappop(queue)
        token_id = cur_node.token_id
        infered_token_ids = cur_node.infered_token_ids

        if token_id in special_tokens_ids and cur_node.length >= min_length:
            ended_nodes.append((score, cur_node))
            # if we reached maximum # of sentences required
            if len(ended_nodes) >= number_required:
                break
            else:
                continue

        # decode for one step using decoder
        logits = generator(personality, history, infered_token_ids)
        token_indexes, token_probs = sample_tokens(
            logits=logits,
            token_position=cur_node.length,
            special_tokens_ids=special_tokens_ids,
            min_length=min_length,
            top_k=top_k,
            top_p=top_p,
            threshold=threshold,
            temperature=temperature,
            no_sample=no_sample,
            beam_size=beam_size,
        )
        for token_index, token_prob in zip(token_indexes, token_probs):
            node = BeamSearchNode(infered_token_ids + [token_index], cur_node, token_index, cur_node.prob + token_prob)
            heapq.heappush(queue, (-node.eval(), node))

    # logger.info(f"queue = {len(queue)}")
    # choose nbest paths, back trace them

    if len(ended_nodes) == 0:
        ended_nodes = [heapq.heappop(queue) for _ in range(nbest)]

    infered_token_ids, probs_output = list(
        zip(*[(node.infered_token_ids, -score) for score, node in sorted(ended_nodes, key=operator.itemgetter(0))])
    )

    return infered_token_ids, probs_output
