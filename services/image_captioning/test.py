

import requests


def test_respond():
    url = "http://0.0.0.0:8123/respond"

   # image_url = 'https://www.gcvs.com/wp-content/uploads/2019/06/why_dog_eats_grass.jpg'
   # img_data = requests.get(image_url).content
   # with open('/src/test_img.jpg', 'wb') as handler:
   #     handler.write(img_data)

    img_path = ["/src/dog.jpg"]

    request_data = {"text": img_path}

    result = requests.post(url, json=request_data).json()

    print(result['caption'])


if __name__ == "__main__":
    test_respond()