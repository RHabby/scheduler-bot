import os
from datetime import datetime

import requests
from extruct.opengraph import OpenGraphExtractor

import constants as cs
import pprint


def get_gfycat_links(url: str) -> tuple:
    gfy_id = url.split("/")[-1]
    if "-" in gfy_id:
        gfy_id = gfy_id.split("-")[0]

    api_url = f"https://api.gfycat.com/v1/gfycats/{gfy_id}"
    r = get_html(api_url)
    if r:
        r = r.json()
        size = r["gfyItem"]["mp4Size"]
        if size > cs.TELEGRAM_VIDEO_LIMIT:
            return url, None, None
        else:
            gfy_gif_link = r["gfyItem"]["gifUrl"]
            gfy_vid_link = r["gfyItem"]["mp4Url"]
            # all request objects contains "mp4Url" and
            # "gifUrl" links directly from "gfyItem" key
            # gfy_gif_link = \
            #     r.json()["gfyItem"]["content_urls"]["largeGif"]["url"]
            # gfy_vid_link = r.json()["gfyItem"]["content_urls"]["mp4"]["url"]
            return url, gfy_gif_link, gfy_vid_link
    else:
        return url, None, None


def what_inside(url: str) -> str:
    what_type = url.split(".")[-1]
    if what_type in cs.IMG_TYPES:
        content_type = cs.IMG_TYPE
    elif what_type in cs.GIF_TYPES:
        content_type = cs.GIF_TYPE
    elif what_type == cs.GIFV:
        content_type = what_type
    else:
        content_type = cs.TEXT_TYPE
    return content_type


def download_file(url: str, source: str, subreddit_name: str) -> str:
    file_dir = f"./attachments/{source}/{subreddit_name}"
    local_filename = url.split('/')[-1]
    path_to_file = os.path.join(file_dir, local_filename)

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    if os.path.exists(path_to_file):
        print(f"{path_to_file} — exists")
        return path_to_file
    else:
        print(f"{path_to_file} — downloading")
        # NOTE the stream=True parameter below
        chunk_size = 1024
        chunk_counter = 0
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path_to_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        # f.flush()
                        chunk_counter += 1
                        if chunk_counter > cs.TELEGRAM_VIDEO_LIMIT / chunk_size:
                            break
        return path_to_file


def get_current_utctime() -> float:
    return datetime.timestamp(datetime.utcnow())


def get_html(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0)\
             Gecko/20100101 Firefox/70.0"
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r
    except (requests.RequestException, ValueError):
        return False


def extract_open_graph(url: str):
    url_page = get_html(url)
    og = OpenGraphExtractor()
    try:
        # data: List(tuple)
        data = og.extract(url_page.text)[0]["properties"]
        new_data = {}
        for key, value in data:
            if key not in new_data:
                new_data[key] = value
        # print(new_data)
        return new_data
    except IndexError:
        data = og.extract(url_page.text)
        return data


def is_direct_link(url: str) -> bool:
    frmt = url.split(".")[-1]
    print(frmt)
    if frmt == "mp4" or frmt in cs.IMG_TYPES:
        return True
    else:
        return False


if __name__ == "__main__":
    pass
