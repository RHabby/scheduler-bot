import os
import pprint
from datetime import datetime

import praw
import requests
from extruct.opengraph import OpenGraphExtractor

import config
import constants as cs

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    username=config.REDDIT_USERNAME,
    password=config.REDDIT_PASSWORD,
    user_agent=config.REDDIT_USER_AGENT
)


def get_full_info(
        subreddit_name: str,
        submission_sort: str = "new",
        limit: int = 3) -> list:

    if submission_sort == "new":
        subreddit = reddit.subreddit(subreddit_name).new(limit=limit+2)
    elif submission_sort == "hot":
        subreddit = reddit.subreddit(subreddit_name).hot(limit=limit+2)
    elif submission_sort == "top":
        subreddit = reddit.subreddit(subreddit_name).top(
            time_filter="day",
            limit=limit+2
        )
    elif submission_sort == "rising":
        subreddit = reddit.subreddit(subreddit_name).rising(limit=limit+2)

    submissions = []
    for submission in subreddit:
        if submission.distinguished is not None:
            continue

        domain = vars(submission)["domain"]
        urls = get_url(submission, domain)

        if domain == cs.GFY_DOMAIN:
            if not urls.get("video_link"):
                print("video link is None")
                continue

        result = {
            "reddit_id": submission.id,
            "title": submission.title,
            "author": submission.author,
            "over_18": submission.over_18,
            "subreddit": submission.subreddit.display_name,
            "permalink": f"{cs.REDDIT_BASE}{submission.permalink}",
            "domain": domain,
            "created_reddit_utc": submission.created_utc,
            "added_utc": get_current_utctime(),
            "was_posted": False,
            "content_type": urls.get("content_type"),
            "url": urls.get("url"),
            "video_link": urls.get("video_link"),
            "gif_link": urls.get("gif_link")
        }
        submissions.append(result)
    pprint.pprint(submissions)
    print("-"*40)
    return submissions[:limit]


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


def get_url(submission, domain: str) -> dict:
    url = submission.url
    content_type = what_inside(url)

    if domain == cs.GFY_DOMAIN:
        urls = get_gfycat_links(url)
        if urls[2] is not None:
            what_type = urls[2].split(".")[-1]
            if what_type in cs.GIF_TYPES:
                content_type = cs.GIF_TYPE
        return {
            "url": urls[0],
            "gif_link": urls[1],
            "video_link": urls[2],
            "content_type": content_type
        }
    elif domain in cs.IMGUR_DOMAIN or domain in cs.OTHER:
        og = extract_open_graph(url)
        if domain == cs.IMGUR_DOMAIN[2] or domain in cs.OTHER:
            try:
                url = og["og:video"]
                content_type = cs.GIF_TYPE
            except KeyError:
                url = og.get("og:image")
                url = url.split("?")[0]
                content_type = cs.IMG_TYPE

        # in cases when url is direct .gifv
        elif content_type == cs.GIFV:
            try:
                url = og["og:video"].split("?")[0]
            except KeyError:
                url = og.get("og:url").split("?")[0]
            content_type = cs.GIF_TYPE
        return {"url": url, "content_type": content_type}
    elif domain in cs.RED_DOMAIN:
        if domain == cs.RED_DOMAIN[1]:
            content_type = cs.TEXT_TYPE
            url = f"{cs.REDDIT_BASE}{submission.permalink}"
        return {"url": url, "content_type": content_type}
    elif "self" in domain or submission.is_self:
        return {"url": url, "content_type": cs.TEXT_TYPE}
    else:
        return {"url": url, "content_type": cs.OTHER_TYPE}


def download_file(url, source, subreddit_name):
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


def get_html(url):
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


def extract_open_graph(url):
    url_page = get_html(url)
    og = OpenGraphExtractor()
    try:
        # data: List(tuple)
        data = og.extract(url_page.text)[0]["properties"]
        new_data = {}
        for key, value in data:
            if key not in new_data:
                new_data[key] = value
        # pprint.pprint(new_data)
        return new_data
    except IndexError:
        data = og.extract(url_page.text)
        return data


if __name__ == "__main__":
    get_full_info("pikabu", limit=2)
