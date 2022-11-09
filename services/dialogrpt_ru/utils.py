import os
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


EOS_token = "<|endoftext|>"
TOKENIZER_NAME_OR_PATH = os.getenv("TOKENIZER_NAME_OR_PATH", "DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2")


class Option:
    def __init__(self, args):
        if isinstance(args, dict):
            if args["cpu"] or not torch.cuda.is_available():
                self.cuda = False
            else:
                self.cuda = True
            self.task = args["task"]
            self.path_load = args["path_load"]
            self.batch = args["batch"]
            self.vali_size = max(self.batch, args["vali_size"])
            self.vali_print = args["vali_print"]
            self.lr = args["lr"]
            self.max_seq_len = args["max_seq_len"]
            self.min_score_gap = args["min_score_gap"]
            self.min_rank_gap = args["min_rank_gap"]
            self.max_hr_gap = args["max_hr_gap"]
            self.mismatch = args["mismatch"]
            self.fld_data = args["data"]
            if args["task"] == "train" or self.path_load is None:
                self.fld_out = "out/%i" % time.time()
            else:
                self.fld_out = "out/temp"
        else:
            if args.cpu or not torch.cuda.is_available():
                self.cuda = False
            else:
                self.cuda = True
            self.task = args.task
            self.path_load = args.path_load
            self.batch = args.batch
            self.vali_size = max(self.batch, args.vali_size)
            self.vali_print = args.vali_print
            self.lr = args.lr
            self.max_seq_len = args.max_seq_len
            self.min_score_gap = args.min_score_gap
            self.min_rank_gap = args.min_rank_gap
            self.max_hr_gap = args.max_hr_gap
            self.mismatch = args.mismatch
            self.fld_data = args.data
            if args.task == "train" or self.path_load is None:
                self.fld_out = "out/%i" % time.time()
            else:
                self.fld_out = "out/temp"

        os.makedirs(self.fld_out, exist_ok=True)

        self.clip = 1
        self.step_max = 1e6
        self.step_print = 10
        self.step_vali = 100
        self.step_save = 500
        self.len_acc = self.step_vali

    def save(self):
        d = self.__dict__
        lines = []
        for k in d:
            lines.append("%s\t%s" % (k, d[k]))
        with open(self.fld_out + "/opt.tsv", "w") as f:
            f.write("\n".join(lines))


class ScorerBase(torch.nn.Module):
    def __init__(self, opt):
        super().__init__()
        self.ix_EOS = 50257
        self.ix_OMT = 655
        self.opt = opt
        self.tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME_OR_PATH)

    def core(self, ids, l_ids, return_logits=False):
        # to be implemented in child class
        return 0

    def predict(self, cxt, hyps, max_cxt_turn=None):
        # cxt = str
        # hyps = list of str

        self.eval()
        cxt_turns = cxt.split(EOS_token)
        if max_cxt_turn is not None:
            cxt_turns = cxt_turns[-min(max_cxt_turn, len(cxt_turns)) :]
        ids_cxt = []
        for turn in cxt_turns:
            ids_cxt += self.tokenizer.encode(turn.strip()) + [self.ix_EOS]
        seqs = []
        lens = []
        for hyp in hyps:
            seq = ids_cxt + self.tokenizer.encode(hyp.strip())
            lens.append(len(seq))
            seqs.append(seq)
        max_len = max(lens)
        ids = []
        for seq in seqs:
            ids.append(seq + [self.ix_EOS] * (max_len - len(seq)))
        with torch.no_grad():
            ids = torch.LongTensor(ids)
            if self.opt.cuda:
                ids = ids.cuda()
            scores = self.core(ids, lens)
        if not isinstance(scores, dict):
            if self.opt.cuda:
                scores = scores.cpu()
            return scores.detach().numpy()

        for k in scores:
            if self.opt.cuda:
                scores[k] = scores[k].cpu()
            scores[k] = scores[k].detach().numpy()
        return scores

    def predict_on_batch(self, cxts, hyps, max_cxt_turn=None):
        # cxt = list of str
        # hyps = list of str

        self.eval()

        seqs = []
        lens = []
        for cxt, hyp in zip(cxts, hyps):
            cxt_turns = cxt.split(EOS_token)
            if max_cxt_turn is not None:
                cxt_turns = cxt_turns[-min(max_cxt_turn, len(cxt_turns)) :]
            ids_cxt = []
            for turn in cxt_turns:
                ids_cxt += self.tokenizer.encode(turn.strip()) + [self.ix_EOS]

            seq = ids_cxt + self.tokenizer.encode(hyp.strip())
            lens.append(len(seq))
            seqs.append(seq)
        max_len = max(lens)

        ids = []
        for seq in seqs:
            ids.append(seq + [self.ix_EOS] * (max_len - len(seq)))

        with torch.no_grad():
            ids = torch.LongTensor(ids)
            if self.opt.cuda:
                ids = ids.cuda()
            scores = self.core(ids, lens)
        if not isinstance(scores, dict):
            if self.opt.cuda:
                scores = scores.cpu()
            return scores.detach().numpy()

        for k in scores:
            if self.opt.cuda:
                scores[k] = scores[k].cpu()
            scores[k] = scores[k].detach().numpy()
        return scores

    def forward(self, batch):
        logits_pos = self.core(batch["ids_pos"], batch["len_pos"], return_logits=True)
        logits_neg = self.core(batch["ids_neg"], batch["len_neg"], return_logits=True)
        # softmax to get the `probability` to rank pos/neg correctly
        return torch.exp(logits_pos) / (torch.exp(logits_pos) + torch.exp(logits_neg))


class Scorer(ScorerBase):
    def __init__(self, opt):
        super().__init__(opt)
        n_embd = 1024
        self.transformer = AutoModelForCausalLM.from_pretrained(TOKENIZER_NAME_OR_PATH)
        self.transformer.resize_token_embeddings(len(self.tokenizer))

        self.score = torch.nn.Linear(n_embd, 1, bias=False)

    def core(self, ids, l_ids, return_logits=False):
        n = ids.shape[0]
        attention_mask = torch.ones_like(ids)
        for i in range(n):
            attention_mask[i, l_ids[i] :] *= 0
        transformer_output = self.transformer(ids, attention_mask=attention_mask, output_hidden_states=True)
        logits = self.score(transformer_output.hidden_states[0]).squeeze(-1)
        logits = torch.stack([logits[i, l_ids[i] - 1] for i in range(n)])
        if return_logits:
            return logits
        else:
            return torch.sigmoid(logits)

    def load(self, path):

        print("loading from " + path)
        weights = torch.load(path, map_location=torch.device("cpu"))
        if path.endswith(".pkl"):
            # russian DialoGPT checkpoint
            pass
        else:
            self.load_state_dict(weights)
        if self.opt.cuda:
            self.cuda()
