"""
Utility functions used across the project
"""

from bs4 import BeautifulSoup


def star_to_text(rating: int):
    """
    Convert the rating into text

    :param rating: Description
    """
    full_stars = int(rating // 1) * ":ms-star:"
    half_star = ":ms-half-star:" if rating % 1 == 0.5 else ""
    empty_stars = int((5 - rating) // 1) * ":ms-empty-star:"

    return full_stars + half_star + empty_stars


def shorten_text(text):
    """Cut the text to 200 chars, remove the last word and replace by '...' (if needed)"""
    if len(text) < 200:
        return text

    text = text[:200]
    text = " ".join(text.split(" ")[:-1])
    text = text + "..."

    return text


def html_to_mrkdwn(html: str) -> str:
    """
    Convert HTML from Letterboxd review to Mrkdwn

    :param html: html from review
    :type html: str
    :return: mrkdwn to use in slack
    :rtype: str
    """

    soup = BeautifulSoup(html, "html.parser")

    # Line breaks
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Bold
    for tag in soup.find_all(["strong", "b"]):
        tag.replace_with(f"*{tag.get_text()}*")

    # Italic
    for tag in soup.find_all(["em", "i"]):
        tag.replace_with(f"_{tag.get_text()}_")

    # Links
    for tag in soup.find_all("a", href=True):
        text = tag.get_text()
        href = tag["href"]
        tag.replace_with(f"<{href}|{text}>")

    # Blockquotes
    for bq in soup.find_all("blockquote"):
        lines = bq.get_text().splitlines()
        quoted = "\n".join(f"> {line}" for line in lines if line.strip())
        bq.replace_with(quoted)

    return soup.get_text()
