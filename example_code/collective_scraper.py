import requests
import time
import cv2
import os

BEARER_TOKEN = "you need to fill this in before using the script"
request_timeout = 3600

def fetch_collective_feed_images(limit=30):
    url = "https://api.ifnapp.com/v4/feeds/collective"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Accept": "video/mp4, image/jpeg, application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en_US",
        "ApplicationState": "1",
        "Ifunny-Project-Id": "iFunny",
        "User-Agent": "iFunny/10.7.11(24487) iPhone/15.6.1 (Apple; iPhone13,2)",
        "Events-Info": '{"context":{"session":{"start":1732129706036}}}',  # Session info
    }

    # Prepare the data to be sent in the POST request
    data = {"limit": limit}  # Adjust the limit as needed

    # Send the POST request
    response = requests.post(url, headers=headers, data=data,timeout=request_timeout)

    # Handle the response
    if response.status_code == 200:
        response_json = response.json()
        if "data" in response_json:
            for key, image_object_list in response_json["data"]["content"].items():
                if key == "items":
                    return image_object_list
    else:
        print(f"Failed to retrieve images. Status code: {response.status_code}")
        print(response.text)


def download_given_url(url, export_folder):
    def save():
        file_extension = url.split(".")[-1]
        uid = str(time.time()).replace(".", "")
        fn = f"{uid}.{file_extension}"
        fp = f"{export_folder}/{fn}"
        # save the url as a jpg
        with open(fp, "wb") as handle:
            response = requests.get(url, stream=True,timeout=request_timeout)

            if not response.ok:
                print(response)

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)

        return fp

    def crop(image_path):
        # remove the bottom 100 pixels to remove IF watermark
        # TODO this crop isnt perfect. some math needs to be done to make it more accurate
        image = cv2.imread(image_path)
        height, width, _ = image.shape
        image = image[0 : height - 25, 0:width]
        cv2.imwrite(image_path, image)

    os.makedirs("images", exist_ok=True)
    fp=save()

    if '.jpg' in url:
        crop(fp)


if __name__ == "__main__":
    media_objects = fetch_collective_feed_images(limit=3)
    for media_object in media_objects:
        url = media_object["url"]
        print(url)
        download_given_url(url, "images")

    print(f'Found {len(media_objects)} images')
    print('This is the first url:',media_objects[0]['url'])
    print('This is the last url:',media_objects[-1]['url'])


