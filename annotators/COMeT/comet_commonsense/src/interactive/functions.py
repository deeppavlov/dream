import torch

from src.data.utils import TextEncoder
import src.data.data as data
import src.models.models as models

from src.evaluate.sampler import BeamSampler, GreedySampler, TopKSampler
from config import settings

import utils.utils as utils


def load_model_file(model_file):
    model_stuff = data.load_checkpoint(model_file)
    opt = model_stuff["opt"]
    state_dict = model_stuff["state_dict"]

    return opt, state_dict


def load_data(dataset, opt):
    if dataset == "atomic":
        data_loader = load_atomic_data(opt)
    elif dataset == "conceptnet":
        data_loader = load_conceptnet_data(opt)

    # Initialize TextEncoder
    encoder_path = "comet_commonsense/model/encoder_bpe_40000.json"
    bpe_path = "comet_commonsense/model/vocab_40000.bpe"
    text_encoder = TextEncoder(encoder_path, bpe_path)
    text_encoder.encoder = data_loader.vocab_encoder
    text_encoder.decoder = data_loader.vocab_decoder

    return data_loader, text_encoder


def load_atomic_data(opt):
    # Hacky workaround, you may have to change this
    # if your models use different pad lengths for e1, e2, r
    if opt.data.get("maxe1", None) is None:
        opt.data.maxe1 = 17
        opt.data.maxe2 = 35
        opt.data.maxr = 1
    path = "comet_commonsense/data/atomic/processed/generation/{}.pickle".format(
        utils.make_name_string(opt.data))
    data_loader = data.make_data_loader(opt, opt.data.categories)
    data_loader.load_data(path)

    return data_loader


def load_conceptnet_data(opt):
    # Hacky workaround, you may have to change this
    # if your models use different pad lengths for r
    if opt.data.get("maxr", None) is None:
        if opt.data.rel == "language":
            opt.data.maxr = 5
        else:
            opt.data.maxr = 1
    path = "comet_commonsense/data/conceptnet/processed/generation/{}.pickle".format(
        utils.make_name_string(opt.data))
    data_loader = data.make_data_loader(opt)
    data_loader.load_data(path)
    return data_loader


def make_model(opt, n_vocab, n_ctx, state_dict):
    model = models.make_model(
        opt, n_vocab, n_ctx,
        return_acts=True, return_probs=False)

    models.load_state_dict(model, state_dict)

    model.eval()
    return model


def set_sampler(opt, sampling_algorithm, data_loader):
    if "beam" in sampling_algorithm:
        opt.eval.bs = int(sampling_algorithm.split("-")[1])
        sampler = BeamSampler(opt, data_loader)
    elif "topk" in sampling_algorithm:
        opt.eval.k = int(sampling_algorithm.split("-")[1])
        sampler = TopKSampler(opt, data_loader)
    else:
        sampler = GreedySampler(opt, data_loader)

    return sampler


def get_atomic_sequence(input_event, model, sampler, data_loader, text_encoder, category):
    if isinstance(category, (list, tuple)):
        outputs = {}
        for cat in category:
            new_outputs = get_atomic_sequence(
                input_event, model, sampler, data_loader, text_encoder, cat)
            outputs.update(new_outputs)
        return outputs
    elif category == "all":
        outputs = {}

        for category in data_loader.categories:
            new_outputs = get_atomic_sequence(
                input_event, model, sampler, data_loader, text_encoder, category)
            outputs.update(new_outputs)
        return outputs
    else:

        sequence_all = {}

        sequence_all["event"] = input_event
        sequence_all["effect_type"] = category

        with torch.no_grad():

            batch = set_atomic_inputs(
                input_event, category, data_loader, text_encoder)
            max_event = data_loader.max_event + data.atomic_data.num_delimiter_tokens["category"]
            max_effect = data_loader.max_effect - data.atomic_data.num_delimiter_tokens["category"]
            sampling_result = sampler.generate_sequence(
                batch, model, data_loader, max_event, max_effect)

        sequence_all['beams'] = sampling_result["beams"]
        return {category: sequence_all}


def set_atomic_inputs(input_event, category, data_loader, text_encoder):
    XMB = torch.zeros(1, data_loader.max_event + 1).long().to(settings.device)
    prefix, suffix = data.atomic_data.do_example(text_encoder, input_event, None, True, None)
    max_len = min(len(prefix), data_loader.max_event + 1)

    XMB[:, :max_len] = torch.LongTensor(prefix[:max_len])
    XMB[:, -1] = torch.LongTensor([text_encoder.encoder["<{}>".format(category)]])

    batch = {}
    batch["sequences"] = XMB
    batch["attention_mask"] = data.atomic_data.make_attention_mask(XMB)

    return batch


def get_conceptnet_sequence(e1, model, sampler, data_loader, text_encoder, relation, force=False):
    if isinstance(relation, (list, tuple)):
        outputs = {}

        for rel in relation:
            new_outputs = get_conceptnet_sequence(
                e1, model, sampler, data_loader, text_encoder, rel)
            outputs.update(new_outputs)
        return outputs
    elif relation == "all":
        outputs = {}

        for relation in data.conceptnet_data.conceptnet_relations:
            new_outputs = get_conceptnet_sequence(
                e1, model, sampler, data_loader, text_encoder, relation)
            outputs.update(new_outputs)
        return outputs
    else:

        sequence_all = {}

        sequence_all["e1"] = e1
        sequence_all["relation"] = relation

        with torch.no_grad():
            if data_loader.max_r != 1:
                relation_sequence = data.conceptnet_data.split_into_words[relation]
            else:
                relation_sequence = "<{}>".format(relation)

            batch, abort = set_conceptnet_inputs(
                e1, relation_sequence, text_encoder,
                data_loader.max_e1, data_loader.max_r, force)

            if abort:
                return {relation: sequence_all}

            sampling_result = sampler.generate_sequence(
                batch, model, data_loader,
                data_loader.max_e1 + data_loader.max_r,
                data_loader.max_e2)

        sequence_all['beams'] = sampling_result["beams"]
        return {relation: sequence_all}


def set_conceptnet_inputs(input_event, relation, text_encoder, max_e1, max_r, force):
    abort = False

    e1_tokens, rel_tokens, _ = data.conceptnet_data.do_example(text_encoder, input_event, relation, None)

    if len(e1_tokens) > max_e1:
        if force:
            XMB = torch.zeros(1, len(e1_tokens) + max_r).long().to(settings.device)
        else:
            XMB = torch.zeros(1, max_e1 + max_r).long().to(settings.device)
            return {}, True
    else:
        XMB = torch.zeros(1, max_e1 + max_r).long().to(settings.device)

    XMB[:, :len(e1_tokens)] = torch.LongTensor(e1_tokens)
    XMB[:, max_e1:max_e1 + len(rel_tokens)] = torch.LongTensor(rel_tokens)

    batch = {}
    batch["sequences"] = XMB
    batch["attention_mask"] = data.conceptnet_data.make_attention_mask(XMB)

    return batch, abort
