from typing import List, TypedDict
from dataclasses import dataclass
from itertools import chain

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


@dataclass
class H2PersonaChatHyperparametersV1:
    """
    chat_history_pair_length: int - number of dialogue pairs from the end
    """

    chat_history_pair_length: int = 7

    persona_max_length: int = 14
    chat_max_length: int = 25

    debug_status: int = 0


class PersonaChatDatasetSampleV1(TypedDict):
    """
    persona: List[str] - person fact sentence set
    history: List[str] - dialogue history
    """

    persona: List[str]
    history: List[str]
    sample_id: str


class H2Seq2SeqInferenceSampleDictV1(TypedDict):
    input_ids: List[int]
    attention_mask: List[int]


class H2Seq2SeqInferenceSampleDictV2(TypedDict):
    input_ids: torch.Tensor
    attention_mask: torch.Tensor


def flat_list(list_of_lists: List[List]) -> List:
    return list(chain.from_iterable(list_of_lists))


class H2Seq2SeqInferencePersonaSampleV1:
    def __init__(
        self,
        dataset_sample: PersonaChatDatasetSampleV1,
        tokenizer: AutoTokenizer,
        hyperparameters: H2PersonaChatHyperparametersV1,
    ) -> None:
        self.dataset_sample = dataset_sample
        self.tokenizer = tokenizer
        self.hyperparameters = hyperparameters

    def add_spaces_after(
        self,
        items: List[str],
    ) -> List[str]:
        items = [item + " " for item in items]
        return items

    @property
    def bos_token_id(self):
        if self.tokenizer.bos_token_id is None:
            return []

        return [self.tokenizer.bos_token_id]

    @property
    def eos_token_id(self):
        if self.tokenizer.eos_token_id is None:
            return []

        return [self.tokenizer.eos_token_id]

    def add_sep_beetween(self, items: List[str], sep=" EOS ") -> List[str]:
        for i in range(1, len(items)):
            items[i] = sep + items[i]

        return items

    def add_spaces_between(self, items: List[str]) -> List[str]:
        items = self.add_spaces_after(items)
        items[-1] = items[-1].strip()
        return items

    def get_sample(self) -> H2Seq2SeqInferenceSampleDictV1:

        dialog_history = self.dataset_sample["history"]
        dialog_history = dialog_history[-self.hyperparameters.chat_history_pair_length * 2 - 1 :]
        dialog_history = self.add_sep_beetween(dialog_history)

        persona = self.dataset_sample["persona"]
        persona = self.add_sep_beetween(
            persona,
            sep=" ",
        )

        KNOWLEDGE_IDS = self.tokenizer.encode(
            " [KNOWLEDGE] ",
            add_special_tokens=False,
        )
        CONTEXT_IDS = self.tokenizer.encode(
            " [CONTEXT] ",
            add_special_tokens=False,
        )

        encoded_history = self.tokenizer.batch_encode_plus(
            dialog_history,
            add_special_tokens=False,
            truncation=True,
            max_length=self.hyperparameters.chat_max_length,
        )
        encoded_history = flat_list(encoded_history["input_ids"])

        encoded_persona = self.tokenizer.batch_encode_plus(
            persona,
            add_special_tokens=False,
            truncation=True,
            max_length=self.hyperparameters.persona_max_length,
        )

        encoded_persona = flat_list(encoded_persona["input_ids"])

        input_ids = [
            *self.bos_token_id,
            *CONTEXT_IDS,
            *encoded_history,
            *KNOWLEDGE_IDS,
            *encoded_persona,
            *self.eos_token_id,
        ]

        attention_mask = [1] * len(input_ids)

        return H2Seq2SeqInferenceSampleDictV1(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )


class DialogBotV1:
    def __init__(
        self,
        model: AutoModelForSeq2SeqLM,
        tokenizer: AutoTokenizer,
        hyperparameters: H2PersonaChatHyperparametersV1,
        history: List[str] = None,
        persona: List[str] = None,
        device: str = "cuda",
        shuffle_persona: bool = True,
    ):
        self.model = model

        self.tokenizer = tokenizer
        self.hyperparameters = hyperparameters
        self.device = device
        self.shuffle_persona = shuffle_persona

        self.debug_status = hyperparameters.debug_status

        if history is None:
            self.history = []
        self.history = history

        if persona is None:
            self.persona = []
        self.persona = persona

    def _get_sample(
        self,
        persona: List[str],
        history: List[str],
    ) -> H2Seq2SeqInferenceSampleDictV1:
        dataset_sample = PersonaChatDatasetSampleV1(
            persona=persona,
            history=history,
        )

        sample = H2Seq2SeqInferencePersonaSampleV1(
            tokenizer=self.tokenizer,
            hyperparameters=self.hyperparameters,
            dataset_sample=dataset_sample,
        )
        sample = sample.get_sample()

        for key in sample.keys():
            sample[key] = torch.tensor(sample[key]).unsqueeze(0).to(self.device)

        return sample

    def next_response(
        self,
        **generation_params,
    ) -> str:
        """
        делает предсказание на основе текущей истории
        и персоны
        """

        sample = self._get_sample(
            persona=self.persona,
            history=self.history,
        )
        answer = self.generate_response(
            sample,
            **generation_params,
        )
        answer = self.tokenizer.batch_decode(
            answer,
            skip_special_tokens=True,
        )
        self.history.append(answer[0])
        return answer[0]

    def generate_response(
        self,
        sample: H2Seq2SeqInferenceSampleDictV1,
        **generation_params,
    ):
        """
        generation_params - https://huggingface.co/docs/transformers/v4.24.0/en/main_classes/text_generation
        """
        with torch.no_grad():
            return self.model.generate(
                **sample,
                **generation_params,
            )
