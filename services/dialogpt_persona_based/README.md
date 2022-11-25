RAM = 3 Gb
GPU RAM = 2.1 Gb
cpu time = 70 sec 
gpu time = 1-1.2 sec 

### Finetune details
- epochs=1
- freeze 3 last fransformer blocks
- optimizer Adam
- lr=5e-4
- batch_size=4
- perplexity train ~ 3.4
- perplexity valid ~ 4.059
- [metrics details](https://wandb.ai/dimweb/gpt_persona_bot/runs/8ryub57u?workspace=user-dimweb)
- train/test split 0.1