apt update
apt install git -y
pip install git+https://github.com/openai/CLIP.git
pip install gdown
# create dirs for data and models
mkdir -p /opt/conda/lib/python3.7/site-packages/data/models
gdown 1IdaBtMSvtyzF0ByVaBHtvM0JYSXRExRX -O /opt/conda/lib/python3.7/site-packages/data/models/coco_weights.pt

apt install wget -y
apt install unzip -y
wget --no-verbose --show-progress --progress=bar:force:noscroll http://images.cocodataset.org/zips/val2017.zip -O tmp.zip > /dev/null
unzip tmp.zip -d /opt/conda/lib/python3.7/site-packages/data/val2017 > /dev/null
rm tmp.zip

#wget http://images.cocodataset.org/annotations/annotations_trainval2017.zip -O tmp.zip
#unzip tmp.zip -d /opt/conda/lib/python3.7/site-packages/data/annotations
#rm tmp.zip
