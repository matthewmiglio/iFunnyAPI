import requests
import os
import random
import time
from auth.community import get_random_community_bearer_token


request_timeout = 3600

bearer_token = "you need to fill this in before using the script"


def post_image_to_ifunny(image_path: str, title: str = "", tags: list[str] = []):
    def format_tag_string(tags):
        if len(tags) == 0:
            return "[]"

        string = "["
        for tag in tags:
            string += f'"{tag}",'

        string = string[:-1] + "]"
        return string

    print(f"posting this file: {image_path}")

    # if title is empty, give a warning (optional)
    if title == "":
        print(f"Warning: Title is empty!")

    url = "https://api.ifnapp.com/v4/contenthub"
    headers = {
        "Content-Type": "multipart/form-data; boundary=Boundary+0E6BF3B8-DC9C-45DB-8172-831110BBBDB3",
        "Accept": "video/mp4, image/jpeg, application/json",
        "Authorization": f"Bearer {bearer_token}",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en_US",
        "ApplicationState": "1",
        "Ifunny-Project-Id": "iFunny",
        "User-Agent": "iFunny/10.7.11(24487) iPhone/15.6.1 (Apple; iPhone13,2)",
        "Events-Info": '{"context":{"session":{"start":1732127011362}}}',
    }

    # Manually construct the multipart body with proper boundaries
    boundary = "Boundary+0E6BF3B8-DC9C-45DB-8172-831110BBBDB3"

    # Read the image file
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="publish"\r\n\r\n'
        f'{{"visibility":"public"}}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="tags"\r\n\r\n'
        f"{format_tag_string(tags)}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="content"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    )

    # Combine the body and the image data
    full_body = body.encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

    # Send the request with the image data
    response = requests.post(
        url, headers=headers, data=full_body, timeout=request_timeout
    )

    # Print the response from the server
    if 429 == response.status_code:
        print("Error: Rate limited")
        time.sleep(3600)
        return post_image_to_ifunny(image_path, title, tags)

    print(response.json())


def post_random_image():
    images_dir = r"images"
    images = os.listdir(images_dir)
    if len(images) == 0:
        print("No images in images directory. Try scraping first.")
        return

    random_image = random.choice(images)
    image_path = os.path.join(images_dir, random_image)
    post_image_to_ifunny(image_path, f"Yup it's a post {time.time()}")


if __name__ == "__main__":
    post_random_image()
    print(f"Posted image to iFunny at {time.time()}")
