from bs4 import BeautifulSoup

from utils import get_html


def process_scripts(html):
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script", {"type": "text/javascript"})
    return scripts


def process_shared_data(data):
    shared_data = [s.string for s in data if "window._sharedData = " in str(s)]
    post_links = str(shared_data).split(
        "edge_sidecar_to_children")[-1].replace(r"\\u0026", "&")
    post_links = post_links.split(",")
    links = [str(link.split('":"')[-1].rstrip('"'))
             for link in post_links if 'display_url' in link or 'video_url' in link]

    return links


if __name__ == "__main__":
    html = get_html("https://www.instagram.com/p/CCnsE2PJktq/").text
    data = process_scripts(html)
    print(process_shared_data(data))
