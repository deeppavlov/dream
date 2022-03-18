# Russian DialogRPT model

Code from https://github.com/golsun/DialogRPT

Trained on 827k samples (plus 95k validation samples) from Russian Pikabu web-site. 

Data parsed from Pikabu by `zhirzemli` (OpenDataScience Slack nickname), code is available [on GitHub](https://github.com/alexeykarnachev/dialogs_data_parsers) 
and the data is available [here](https://drive.google.com/file/d/1XYCprTqn_MlzDD9qgj7ANJkwFigK66mv/view?usp=sharing).

Final acc=0.64 (on valid).

Trained on 8 GPUs.
```
python src/main.py train --data=data/out/updown  --min_score_gap=20 --min_rank_gap=0.5 --max_seq_len 256 --batch 16 1>out.txt 2>&1
```