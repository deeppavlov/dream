# ASR : Automatic Speech Recognition

## Description
component_type: annotator
is_customizable: true

ASR component allows users to provide speech input via its `http://_service_name_:4343/asr?user_id=` endpoint.  To do so, attach the recorded voice as a `.wav` file, 16KHz. 

## I/O
...

## Dependencies

Configuration settings specified in the [environment.yml](service_configs/asr/environment.yml) and [service.yml](service_configs/asr/service.yml)files

Required Python packages specified in [requirements.txt](requirements.txt)