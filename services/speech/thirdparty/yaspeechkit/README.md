## ASR
curl -X POST "http://0.0.0.0:6969/asr?user_id=USER_ID" -F "file=@8088-284756-0037.wav"
## TTS
curl -X POST "http://0.0.0.0:6969/asr?user_id=USER_ID" -F --output out.wav
