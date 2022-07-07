from transformers import T5Tokenizer


class QGTokenizer:
    def __init__(self, tokenizer, max_src_len=200, max_tgt_len=25):
        self.tokenizer = T5Tokenizer.from_pretrained(tokenizer)
        self.max_src_len = max_src_len
        self.max_tgt_len = max_tgt_len

    def _truncate(self, ids, truncate_len, from_start=True):
        if from_start:
            return ids[-truncate_len:]
        return ids[:truncate_len]

    def __call__(self, sample):
        src = sample["text"] + " answer: " + sample["answer"]
        src_tokenized = self.tokenizer(src, add_special_tokens=True)
        if "q" in sample:
            tgt = "question: " + sample["q"]
            tgt_tokenized = self.tokenizer(tgt, add_special_tokens=True)
        else:
            tgt_tokenized = {"input_ids": []}
        return {
            "input_ids": self._truncate(src_tokenized["input_ids"], self.max_src_len),
            "attention_mask": self._truncate(src_tokenized["attention_mask"], self.max_src_len),
            "labels": self._truncate(tgt_tokenized["input_ids"], self.max_tgt_len, from_start=False),
        }
