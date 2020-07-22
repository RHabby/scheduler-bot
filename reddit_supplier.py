import pprint

import praw

import config
import constants as cs
import utils

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
            "added_utc": utils.get_current_utctime(),
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


def get_url(submission, domain: str) -> dict:
    url = submission.url.split("?")[0]
    content_type = utils.what_inside(url)

    if domain == cs.GFY_DOMAIN:
        urls = utils.get_gfycat_links(url)
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
        og = utils.extract_open_graph(url)
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


if __name__ == "__main__":
    get_full_info("pikabu", limit=2)
