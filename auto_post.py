import keyboard
import threading
import cv2
import requests
import time
import random
import os
import sys
import datetime


class IFunnyAPI:
    def __init__(self):
        # api stuff
        self.bearer_token_path = r"bearer_token.txt"
        self.get_bearer_token()

        # stats
        self.featured_scrapes = 0
        self.collective_scrapes = 0
        self.posts = 0
        self.scrape_rate_limits = 0
        self.post_rate_limits = 0

        # file stuff
        os.makedirs("images", exist_ok=True)

    def get_bearer_token(self):
        if not os.path.exists(self.bearer_token_path):
            with open(self.bearer_token_path, "w") as file:
                self.bearer_token = file.write("your_bearer_token_here")
                raise Exception("Please add your bearer token to bearer_token.txt")
        else:
            try:
                with open(self.bearer_token_path, "r") as file:
                    self.bearer_token = file.read().strip()
                    if self.bearer_token == "your_bearer_token_here":
                        raise Exception(
                            "Please add your bearer token to bearer_token.txt"
                        )
            except Exception as e:
                print(f"An error occured reading your bearer token file: {e}")
                raise Exception(e)

    def get_images(self, source="featured", limit=10, save=True) -> list[str] | bool:
        def parse_urls(image_object_list):
            urls = [image["share_url"] for image in image_object_list]
            urls = list(set(urls))
            urls = [url for url in urls if ".jpg" in url]
            return urls

        if source == "collective":
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                # "Accept": "video/mp4, image/jpeg, application/json",
                "Accept": "image/jpeg, application/json",
                "Authorization": f"Bearer {self.bearer_token}",  # Your Bearer token
                "Accept-Encoding": "gzip, deflate, br",
                # "Accept-Language": "en_US",
                "ApplicationState": "1",
                "Ifunny-Project-Id": "iFunny",
                # "User-Agent": "iFunny/10.7.11(24487) iPhone/15.6.1 (Apple; iPhone13,2)",
                "Events-Info": '{"context":{"session":{"start":1732129706036}}}',  # Session info
            }
            url = "https://api.ifnapp.com/v4/feeds/collective"
            response = requests.post(
                url, headers=headers, data={"limit": limit}, timeout=60
            )

        elif source == "featured":
            headers = {
                # "Accept": "video/mp4, image/jpeg, application/json",
                "Accept": "image/jpeg, application/json",
                "Authorization": f"Bearer {self.bearer_token}",  # Use your Bearer token
                "Accept-Encoding": "gzip, deflate, br",
                # "Accept-Language": "en_US",
                "ApplicationState": "1",
                "Ifunny-Project-Id": "iFunny",
                # "User-Agent": "iFunny/10.7.11(24487) iPhone/15.6.1 (Apple; iPhone13,2)",
                "Events-Info": '{"context":{"session":{"start":1732132752448}}}',  # Session info
            }
            url = "https://api.ifnapp.com/v4/feeds/featured"
            response = requests.get(
                url, headers=headers, params={"limit": limit}, timeout=60
            )

        else:
            return False

        if response.status_code == 200:
            try:
                response_json = response.json()
                if "data" in response_json:
                    for key, image_object_list in response_json["data"][
                        "content"
                    ].items():
                        if key == "items":
                            urls = parse_urls(image_object_list)
                            if source != "featured":
                                self.collective_scrapes += len(urls)
                            else:
                                self.featured_scrapes += len(urls)
                            if save is True:
                                for url in urls:
                                    self.download_image(url, "images")
                            return urls
            except Exception as e:
                print(e)
                print(response.text)
                return False

        elif response.status_code == 429:
            print("Rate limited for get_images().")
            self.scrape_rate_limits += 1
            return False

        elif response.status_code == 401:
            print("Unauthorized. Please check your bearer token")
            raise Exception("Unauthorized. Please check your bearer token")

        print(f"An unknown error occured in get_images: {response.status_code}")
        print(response.text)
        return False

    def post_image(
        self, image_path: str, title: str = "", tags: list[str] = []
    ) -> bool:
        def format_tag_string(tags):
            if len(tags) == 0:
                return "[]"

            string = "["
            for tag in tags:
                string += f'"{tag}",'

            string = string[:-1] + "]"
            return string

        url = "https://api.ifnapp.com/v4/contenthub"
        headers = {
            "Content-Type": "multipart/form-data; boundary=Boundary+0E6BF3B8-DC9C-45DB-8172-831110BBBDB3",
            "Accept": "video/mp4, image/jpeg, application/json",
            "Authorization": f"Bearer {self.bearer_token}",  # Use your Bearer token
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
        response = requests.post(url, headers=headers, data=full_body, timeout=60)

        if response.status_code == 429:
            print("Rate limited for post_image().")
            self.post_rate_limits += 1
            return False

        # if its a good reponse code, delete the image
        elif response.status_code == 200:
            os.remove(image_path)
            self.posts += 1
            return True

        elif response.status_code == 401:
            print("Unauthorized. Please check your bearer token")
            raise Exception("Unauthorized. Please check your bearer token")

        print(f"Got an unknown response code in get_images: {response.status_code}")
        print(response.text)
        return False

    def download_image(self, url, export_folder):
        def save():
            file_extension = url.split(".")[-1]
            uid = str(time.time()).replace(".", "")
            fn = f"{uid}.{file_extension}"
            fp = f"{export_folder}/{fn}"
            # save the url as a jpg
            with open(fp, "wb") as handle:
                response = requests.get(url, stream=True)

                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handle.write(block)

            return fp

        def crop(image_path):
            # remove the bottom 100 pixels
            image = cv2.imread(image_path)
            height, width, _ = image.shape
            image = image[0 : height - 25, 0:width]
            cv2.imwrite(image_path, image)

        os.makedirs("images", exist_ok=True)
        crop(save())

    def post_random_image(self) -> bool:
        images_dir = r"images"
        images = os.listdir(images_dir)
        if len(images) == 0:
            print("No images in images directory")
            return False

        random_image = random.choice(images)
        image_path = os.path.join(images_dir, random_image)
        return self.post_image(image_path, f"yup its a post {time.time()}") is True

    def post_text_post(self, title, body, tags):
        def format_tag_string(tags):
            if len(tags) == 0:
                return "[]"

            string = "["
            for tag in tags:
                string += f'"{tag}",'

            string = string[:-1] + "]"
            return string

        # if both title and body are empty, return
        if title == "" and body == "":
            print(f"Error: Title and body are BOTH empty!")
            return

        url = "https://api.ifnapp.com/v4/contenthub"
        headers = {
            "Content-Type": "multipart/form-data; boundary=Boundary+B3429CD3-F483-4F41-B3DE-318ACFE7AAC5",
            "Accept": "video/mp4, image/jpeg, application/json",
            "Authorization": f"Bearer {self.bearer_token}",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en_US",
            "ApplicationState": "1",
            "Ifunny-Project-Id": "iFunny",
            "User-Agent": "iFunny/10.7.11(24487) iPhone/15.6.1 (Apple; iPhone13,2)",
            "Events-Info": '{"context":{"session":{"start":1732127011362}}}',
        }

        # Manually construct the multipart body with proper boundaries
        boundary = "Boundary+B3429CD3-F483-4F41-B3DE-318ACFE7AAC5"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="publish"\r\n\r\n'
            f'{{"visibility":"public"}}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="tags"\r\n\r\n'
            # f'["htggyooohii","tag2"]\r\n'
            f"{format_tag_string(tags)}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="text_post"\r\n\r\n'
            f'{{"title":"{title}","description":"{body}"}}\r\n'
            f"--{boundary}--\r\n"
        )

        # Send the request with manually crafted data
        response = requests.post(url, headers=headers, data=body, timeout=60)

        # Print the response from the server
        print(response.status_code)
        print(response.json())


class PostBot:
    def __init__(self):
        # runtime stuff
        self.TAKE_IT_EASY = True
        self.start_time = time.time()
        self.running_event = threading.Event()
        self.running_event.set()
        self.threads = []
        self.kill_key = "insert"

        # api stuff
        self.ifunny = IFunnyAPI()

        # logger stuff
        self.logger = Logger()

        # bot stuff
        self.image_count_lower_bound = 3
        self.image_scrape_limit = 1
        self.time_of_last_post = None
        self.time_of_last_collective_scrape = None
        self.time_of_last_featured_scrape = None

        # thread status stuff
        self.image_scrape_thread_status = ""
        self.post_thread_status = ""

        # wait times
        self.good_post_wait_time = 2 * 60 * 60  # 2 hours
        self.fail_post_wait_time = 5 * 60 * 60  # 5 hours
        self.good_get_images_wait_time = 0
        self.fail_get_images_wait_time = 120 * 60



    def stop(self):
        print(f"Stopping PostBot")
        self.running_event.clear()  # stop the event
        for thread in self.threads:
            try:
                thread.join()  # wait for all threads to complete
            except:
                pass
        sys.exit()

    def close_via_keyboard_thread(self):
        def _to_wrap():
            print("Running keyboard-shutoff thread")
            while self.running_event.is_set():
                if keyboard.is_pressed(self.kill_key):
                    print("Shutoff key pressed!")
                    self.stop()
                    break
                time.sleep(1)
            print("Done running keyboard-shutoff thread")

        t = threading.Thread(target=_to_wrap)
        self.threads.append(t)
        t.start()

    def post_thread(self):
        def _to_wrap():
            print("Running post thread")
            is_waiting = False
            time_of_next_post_attempt = None
            while self.running_event.is_set():
                if is_waiting is True:
                    time_till_next_post = (
                        time_of_next_post_attempt - time.time()
                    ) // 60  # in minutes
                    self.post_thread_status = (
                        f"Waiting {time_till_next_post} minutes..."
                    )
                    if time_till_next_post < 0:
                        is_waiting = False
                    else:
                        time.sleep(5 if self.TAKE_IT_EASY else 1)
                        continue

                if self.ifunny.post_random_image() is not True:
                    self.post_thread_status = "Rate limited..."
                    self.logger.log("post_rate_limit")
                    is_waiting = True
                    time_of_next_post_attempt = time.time() + self.fail_post_wait_time
                else:
                    self.post_thread_status = "Waiting after good post..."
                    self.logger.log("post_successful")
                    is_waiting = True
                    time_of_next_post_attempt = time.time() + self.good_post_wait_time

            print("Done Running post thread")
            self.post_thread_status = "Idle"

        t = threading.Thread(target=_to_wrap)
        self.threads.append(t)
        t.start()

    def print_thread(self):
        def print_stats():
            def format_runtime(runtime):
                def format_digit(d):
                    d = str(d)
                    while len(d) < 2:
                        d = "0" + str(d)
                    return d

                r = runtime
                hours = r // (60 * 60)
                r = r % (60 * 60)
                minutes = r // 60
                r = r % 60
                seconds = r
                hours, minutes, seconds = (
                    format_digit(int(hours)),
                    format_digit(int(minutes)),
                    format_digit(int(seconds)),
                )
                return f"{hours}h {minutes}m {seconds}s"

            stat2value = {
                "Posts": self.ifunny.posts,
                "Scrapes (coll)": self.ifunny.collective_scrapes,
                "Scrapes (feat)": self.ifunny.featured_scrapes,
                "Scrapes (total)": self.ifunny.collective_scrapes
                + self.ifunny.featured_scrapes,
                "Post timeouts": self.ifunny.post_rate_limits,
                "Scrape timeouts": self.ifunny.scrape_rate_limits,
                "Post thread:": self.post_thread_status,
                "Scrape thread:": self.image_scrape_thread_status,
                "runtime": format_runtime(time.time() - self.start_time),
            }
            string = "-" * 50
            for stat, value in stat2value.items():
                string += "\n{:^25}: {:^25}".format(stat, value)
            string += f"\nKill key: {self.kill_key}"
            string += "\n" + "-" * 50
            print(string, end="\r")

        def _to_wrap():
            print("Running print thread")
            while self.running_event.is_set():
                print_stats()
                time.sleep(4.99 if self.TAKE_IT_EASY else 0.95)
            print("Done Running print thread")

        t = threading.Thread(target=_to_wrap)
        self.threads.append(t)
        t.start()

    def get_images_thread(self):
        def _to_wrap():
            print("Running get_images thread")
            is_waiting = False
            time_of_next_scrape_attempt = None

            while self.running_event.is_set():
                if is_waiting is True:
                    time_left = (
                        time_of_next_scrape_attempt - time.time()
                    ) // 1  # in seconds
                    self.image_scrape_thread_status = f"Waiting {time_left} seconds..."
                    if time_left < 0:
                        is_waiting = False
                    else:
                        time.sleep(5 if self.TAKE_IT_EASY else 0)
                        continue

                image_count = len(os.listdir("images"))
                self.logger.log(f"image_count {image_count}")
                if image_count > self.image_count_lower_bound:
                    is_waiting = True
                    time_of_next_scrape_attempt = time.time() + 60
                    continue

                self.logger.log("Featured_scrape_attempt")
                self.image_scrape_thread_status = "Scraping featured..."
                if (
                    self.ifunny.get_images(
                        "featured", self.image_scrape_limit, save=True
                    )
                    is not False
                ):
                    self.logger.log("featured_scrape_successful")
                    continue

                self.logger.log("featured_scrape_rate_limit")
                self.image_scrape_thread_status = "Failed to scrape featured..."
                print("Featured scrape is limited. Moving to collective...")
                self.image_scrape_thread_status = "Scraping collective..."
                self.logger.log("collective_scrape_attempt")
                if (
                    self.ifunny.get_images(
                        "collective", self.image_scrape_limit, save=True
                    )
                    is not False
                ):
                    self.logger.log("collective_scrape_successful")
                    continue

                print("Failed to scrape collective!")
                self.logger.log("collective_scrape_rate_limit")
                self.image_scrape_thread_status = "Failed to scrape collective!"
                print(
                    f"Waiting {self.fail_get_images_wait_time}s after fail scrapes..."
                )
                is_waiting = True
                time_of_next_scrape_attempt = (
                    time.time() + self.fail_get_images_wait_time
                )

            print("Done Running get_images thread")
            self.image_scrape_thread_status = "Idle"

        t = threading.Thread(target=_to_wrap)
        self.threads.append(t)
        t.start()

    def run(self):
        print("Starting PostBot...")
        self.get_images_thread()
        self.close_via_keyboard_thread()
        self.post_thread()
        self.print_thread()
        while self.running_event.is_set():
            time.sleep(1)
        self.stop()


class Logger:
    def __init__(self):
        self.log_folder = r"logs"
        self.current_log_file = None
        os.makedirs(self.log_folder, exist_ok=True)

    def new_log_folder(self):
        uid = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        this_log_file_path = os.path.join(self.log_folder, f"{uid}.txt")
        with open(this_log_file_path, "w") as file:
            file.write("\n\n\n")
        self.current_log_file = this_log_file_path

    def log(self, line):
        if self.current_log_file is None:
            self.new_log_folder()

        with open(self.current_log_file, "a") as file:
            this_line = f"\n{time.time()} {line}"
            file.write(this_line)


if __name__ == "__main__":
    pb = PostBot()
    pb.run()
