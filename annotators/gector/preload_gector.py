print("Begin to preload model")
from gector.gec_model import GecBERTModel

model = GecBERTModel(
    vocab_path="vocab/output_vocabulary",
    model_paths=["/model_data/xlnet_0_gector.th", "/model_data/roberta_1_gector.th"],
    min_probability=0.0,
    model_name="roberta",
    special_tokens_fix=0,
    is_ensemble=True,
)
