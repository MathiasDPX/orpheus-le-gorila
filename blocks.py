from schemas import DiaryEntryActivity
from utils import *
import os

def from_mrkdwn(mrkdwn):
    return [{"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn}}]


def from_diaryentry(activity: DiaryEntryActivity):
    member = activity.member
    film = activity.film

    liked = ":ms-red-heart: " if activity.like else ""
    stars = star_to_text(activity.rating)

    film_name = film.fullDisplayName or film.name

    review = ""
    if activity.review != None:
        if activity.review.containsSpoilers:
            review = "_This review contains spoilers_"
        else:
            review = "\n\n> " + html_to_mrkdwn(activity.review.text)
            review = shorten_text(review)

    # Some magic cuz sometime the sortingName isnt the name in the URL
    sortingName = os.path.basename(film.links['letterboxd'].url.strip("/"))
    
    return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{member.displayName} watched {film_name}*\n{liked} {stars}{review}",
                },
                "accessory": {
                    "type": "image",
                    "image_url": film.poster.sizes[
                        len(film.poster.sizes) // 2
                    ].url,  # Take the average quality
                    "alt_text": f"{film.name}'s poster",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "open_letterboxd",
                        "text": {
                            "type": "plain_text",
                            "text": ":boxd: See on Letterboxd",
                            "emoji": True,
                        },
                        "url": f"https://letterboxd.com/{member.username}/film/{sortingName}/",
                    }
                ],
            },
        ]
