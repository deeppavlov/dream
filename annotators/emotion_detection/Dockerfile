FROM python:3.9

WORKDIR /src

RUN apt update

RUN pip install gdown

RUN git clone https://github.com/anna-a-m/MultimodalERC repo

RUN mv -f repo/* .
RUN rm -rf repo

RUN gdown 'https://drive.google.com/file/d/12C36rGUe7tuWGAh_FByw80c3wAtdUHx8/view?usp=drive_link' -O '1d_cnn_with_opensmile.pt'
RUN gdown 'https://drive.google.com/file/d/1ZHw2MEbjLwU5A7EaNysgVHZlaWq4FJZG/view?usp=drive_link' -O 'bert-large-uncased_none_seed-42.pt'
RUN gdown 'https://drive.google.com/file/d/1tDf-jWihZ6M0oX-niOfVmLUimJqYrG_M/view?usp=drive_link' -O 'final_model.pt'
RUN gdown 'https://drive.google.com/file/d/1DMUHqbwqn-j9XIhoqnfSwqyqrlPMkVJe/view?usp=drive_link' -O 'XCLIP_Augmented.pt'

COPY . /src

RUN pip install -r requirements.txt
