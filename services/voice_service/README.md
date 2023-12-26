# Voice Service

## Description

A audio captioning service.
It receives a file in one of the following extensions:
- `oga`
- `mp3`
- `ogg`
- `flac`
- `mp4`

The service then extracts audio from the file by converting it to `wav` using ffmpeg.

After the conversion, the service passes the audio as an input to the audio captioning model.
The model then infers captions for the audio.

The service returns adds the following attributes to the response:
- `sound_type`
- `sound_duration`
- `sound_path`
- `caption`

Sound type is either an audio attachment, a voice message, or a videonote.
Sound duration is the duration of the audiofile in seconds.
Sound path is the path to the audiofile on the local server.
Caption is the text that captioning model outputs.