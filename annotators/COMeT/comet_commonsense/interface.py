import re
from typing import Dict, Sequence, Optional

import src.interactive.functions as interactive

import schemas
from config import settings

POSTPROCESSING_REGEXP = re.compile(r"[^a-zA-Z0-9\- ]|\bnone\b", re.IGNORECASE)


class COMeTBaseEngine:
    def __init__(self, graph, model_path, decoding_algorithm):
        self.graph = graph
        self.model_path = model_path
        self.decoding_algorithm = decoding_algorithm

        self._opt, self._state_dict = interactive.load_model_file(self.model_path)
        self._data_loader, self._text_encoder = interactive.load_data(self.graph, self._opt)
        self._sampler = interactive.set_sampler(self._opt, self.decoding_algorithm, self._data_loader)
        self._n_ctx = self._calc_n_ctx()
        self._n_vocab = len(self._text_encoder.encoder) + self._n_ctx

        self._model = interactive.make_model(self._opt, self._n_vocab, self._n_ctx, self._state_dict)
        self._model.to(device=settings.device)

        self._input_event_model = None
        self._response_model = None
        self._annotator_input_model = None
        self._annotator_response_model = None

    @property
    def input_event_model(self) -> Optional[schemas.BaseModel]:
        return self._input_event_model

    @property
    def response_model(self) -> Optional[schemas.BaseModel]:
        return self._response_model

    @property
    def annotator_input_model(self) -> Optional[schemas.BaseModel]:
        return self._annotator_input_model

    @property
    def annotator_response_model(self) -> Optional[schemas.BaseModel]:
        return self._annotator_response_model

    @staticmethod
    def beams_cleanup(preprocessed_beams):
        postprocessed_beams = []
        for beam in preprocessed_beams:
            postprocessed_beam = re.sub(POSTPROCESSING_REGEXP, "", beam).strip()
            if len(postprocessed_beam):
                postprocessed_beams.append(postprocessed_beam)
        return postprocessed_beams

    def all_beams_cleanup(self, raw_result, include_beams_key=True):
        for relation_or_category in raw_result:
            preprocessed_beams = raw_result[relation_or_category].get("beams", [])
            if include_beams_key:
                raw_result[relation_or_category]["beams"] = self.beams_cleanup(preprocessed_beams)
            else:
                raw_result[relation_or_category] = self.beams_cleanup(preprocessed_beams)
        return raw_result

    def _calc_n_ctx(self) -> int:
        pass

    def process_request(self, *args, **kwargs):
        pass

    def _get_result(self, *args, **kwargs):
        pass

    def annotator(self, *args, **kwargs):
        pass


class COMeTAtomic(COMeTBaseEngine):
    def __init__(self, model_path, decoding_algorithm):
        super().__init__(graph="atomic", model_path=model_path, decoding_algorithm=decoding_algorithm)
        self._input_event_model = schemas.AtomicInputEventModel
        self._response_model = schemas.AtomicResponseModel

    def _calc_n_ctx(self):
        return self._data_loader.max_event + self._data_loader.max_effect

    def process_request(self, input_event: schemas.AtomicInputEventModel) -> Dict:
        return self._get_result(input_event["input"], input_event["category"])

    def _get_result(self, event: str, category: Sequence[str]) -> Dict:
        raw_result = interactive.get_atomic_sequence(
            event,
            self._model,
            self._sampler,
            self._data_loader,
            self._text_encoder,
            category
        )
        return self.all_beams_cleanup(raw_result)

    def annotator(self, *args, **kwargs):
        raise NotImplementedError("No annotator for atomic graph is available!")


class COMeTConceptNet(COMeTBaseEngine):
    def __init__(self, model_path, decoding_algorithm):
        super().__init__(graph="conceptnet",
                         model_path=model_path,
                         decoding_algorithm=decoding_algorithm
                         )
        self._input_event_model = schemas.ConceptNetInputEventModel
        self._response_model = schemas.ConceptNetResponseModel
        self._annotator_input_model = schemas.ConceptNetAnnotatorEventModel
        self._annotator_response_model = schemas.ConceptNetAnnotatorResponseModel

    def _calc_n_ctx(self):
        return self._data_loader.max_e1 + self._data_loader.max_e2 + self._data_loader.max_r

    def process_request(self, input_event: schemas.ConceptNetInputEventModel) -> Dict:
        return self._get_result(input_event["input"], input_event["category"])

    def _get_result(self, event, category):
        raw_result = interactive.get_conceptnet_sequence(
            event,
            self._model,
            self._sampler,
            self._data_loader,
            self._text_encoder,
            category
        )
        return self.all_beams_cleanup(raw_result)

    def annotator(self, input_event: schemas.ConceptNetAnnotatorEventModel):
        batch = []
        for nounphrases in input_event["nounphrases"]:
            result = {}
            for nounphrase in nounphrases:
                conceptnet_result = self._get_result(nounphrase, input_event["category"])
                result[nounphrase] = self.all_beams_cleanup(conceptnet_result, include_beams_key=False)
            batch += [result]
        return batch


class COMeTFactory:
    def __init__(self, graph):
        self.graph = graph

    def __call__(self, model_path, decoding_algorithm):
        if self.graph == "atomic":
            return COMeTAtomic(
                model_path=model_path,
                decoding_algorithm=decoding_algorithm
            )
        elif self.graph == "conceptnet":
            return COMeTConceptNet(
                model_path=model_path,
                decoding_algorithm=decoding_algorithm
            )
        else:
            raise ValueError(f"Graph {self.graph} does not exist!")
