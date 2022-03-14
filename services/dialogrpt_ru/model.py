# author: Xiang Gao at Microsoft Research AI NLP Group


import torch
from shared import EOS_token
from transformers import AutoModelForCausalLM, AutoTokenizer


class OptionInfer:
    def __init__(self, cuda=True):
        self.cuda = cuda


tokenizer = AutoTokenizer.from_pretrained("Grossmend/rudialogpt3_medium_based_on_gpt2")



class ScorerBase(torch.nn.Module):
    def __init__(self, opt):
        super().__init__()
        self.ix_EOS = 50257
        self.ix_OMT = 655
        self.opt = opt
        self.tokenizer = tokenizer


    def core(self, ids, l_ids, return_logits=False):
        # to be implemented in child class
        return 0

    
    def predict(self, cxt, hyps, max_cxt_turn=None):
        # cxt = str
        # hyps = list of str

        self.eval()
        cxt_turns = cxt.split(EOS_token)
        if max_cxt_turn is not None:
            cxt_turns = cxt_turns[-min(max_cxt_turn, len(cxt_turns)):]
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


    def forward(self, batch):
        logits_pos = self.core(batch['ids_pos'], batch['len_pos'], return_logits=True)
        logits_neg = self.core(batch['ids_neg'], batch['len_neg'], return_logits=True)
        # softmax to get the `probability` to rank pos/neg correctly
        return torch.exp(logits_pos) / (torch.exp(logits_pos) + torch.exp(logits_neg))


class Scorer(ScorerBase):
    def __init__(self, opt):
        super().__init__(opt)
        n_embd = 1024
        self.transformer = AutoModelForCausalLM.from_pretrained("Grossmend/rudialogpt3_medium_based_on_gpt2")
        self.transformer.resize_token_embeddings(len(self.tokenizer))

        self.score = torch.nn.Linear(n_embd, 1, bias=False)

    def core(self, ids, l_ids, return_logits=False):
        n = ids.shape[0]
        attention_mask = torch.ones_like(ids)
        for i in range(n):
            attention_mask[i, l_ids[i]:] *= 0
        transformer_output = self.transformer(ids, attention_mask=attention_mask, output_hidden_states=True)
        logits = self.score(transformer_output.hidden_states[0]).squeeze(-1)
        logits = torch.stack([logits[i, l_ids[i] - 1] for i in range(n)])
        if return_logits:
            return logits
        else:
            return torch.sigmoid(logits)

    
    def load(self, path):

        print('loading from '+path)
        weights = torch.load(path, map_location=torch.device('cpu'))
        if path.endswith('.pkl'):
            # russian DialoGPT checkpoint
            pass
        else:
            self.load_state_dict(weights)
        if self.opt.cuda:
            self.cuda()


class JointScorer(ScorerBase):
    
    def core(self, ids, l_ids, return_logits=False):
        assert(not return_logits)
        scores = dict()
        for k in self.kk['prior'] + self.kk['cond']:
            scorer = getattr(self, 'scorer_%s'%k)
            scores[k] = scorer.core(ids, l_ids)
        
        def avg_score(kk):
            if not kk:
                return 1
            sum_score_wt = 0
            sum_wt = 0
            for k in kk:
                sum_score_wt = sum_score_wt + scores[k] * self.wt[k]
                sum_wt += self.wt[k]
            return sum_score_wt / sum_wt

        prior = avg_score(self.kk['prior'])
        cond = avg_score(self.kk['cond'])
        scores['final'] = prior * cond
        return scores

    
    def load(self, path_config):
        import yaml
        with open(path_config, 'r') as stream:
            config = yaml.safe_load(stream)
        print(config)

        paths = dict()
        self.wt = dict()
        self.kk = dict()
        for prefix in ['prior', 'cond']:
            self.kk[prefix] = []
            for d in config[prefix]:
                k = d['name']
                self.kk[prefix].append(k)
                self.wt[k] = d['wt']
                paths[k] = d['path']
        
        for k in paths:
            path = paths[k]
            print('setting up model `%s`'%k)
            scorer = Scorer(OptionInfer(cuda=self.opt.cuda))
            scorer.load(path)
            if self.opt.cuda:
                scorer.cuda()
            setattr(self, 'scorer_%s'%k, scorer)



