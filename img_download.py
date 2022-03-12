import requests
from uuid import uuid4
import os


def download_img(pic_url, path):
    if not os.path.isdir(path):
        os.mkdir(path)
    # for twitter
    pic_url = pic_url.split('&name=')[0]
    img_name = str(uuid4()) + '.jpg'
    img_path = os.path.join(path, img_name)
    with open(img_path, 'wb') as handle:
        response = requests.get(pic_url, stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)


def download_list(urls, path='downloaded_images'):
    for url in urls:
        download_img(url, path)


if __name__ == '__main__':
    imgs_list = [
        'https://pbs.twimg.com/media/FLLcI75XsAMVJc4?format=jpg&name=360x360',
    ]
    download_list(imgs_list)
