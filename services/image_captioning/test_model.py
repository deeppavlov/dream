import requests
from pycocotools.coco import COCO
from ignite.metrics.nlp import Bleu
import random

def test_simple():
    url = "http://0.0.0.0:8123/respond"

    path = ["example.jpg"]
    request_data = {"text": path}
    result = requests.post(url, json=request_data).json()['captions'][0].split()
    result = [word.lower() for word in result]

    assert "frog" in result
    assert "drink" in result
    print("Simple test passed")

def test_quality():
    url = "http://0.0.0.0:8123/respond"

    annFile = 'services/image_captioning/annotations/captions_val2017.json'
    coco_caps=COCO(annFile)
    imgIds = random.choices(coco_caps.getImgIds(), k=10)
    imgIdsStr = [str(imgId) for imgId in imgIds]
    imgIdsStr = ['0' * (12 - len(imgIdStr)) + imgIdStr for imgIdStr in imgIdsStr]

    coco_path = '/opt/conda/lib/python3.7/site-packages/data/val2017/val2017/'
    paths = [coco_path + imgIdStr + '.jpg' for imgIdStr in imgIdsStr]
    request_data = {"text": paths}
    result = requests.post(url, json=request_data).json()['captions']

    m = Bleu(ngram=4, smooth="smooth1")
    for i, imgId in enumerate(imgIds):
        annId = coco_caps.getAnnIds(imgIds=imgId)
        anns = [ann['caption'] for ann in coco_caps.loadAnns(annId)]      
        m.update(([result[i].split()], [[ann.split() for ann in anns]]))
    assert m.compute() > 0.2
    print("Quality test passed")


if __name__ == "__main__":
    test_simple()
    #test_quality()
