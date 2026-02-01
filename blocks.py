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
    sortingName = os.path.basename(film.links["letterboxd"].url.strip("/"))

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

def modal_events(channelid):
    text = "A message will be sent for each of these activities:"
    if channelid is not None:
        text = f"A message will be sent in <#{channelid}> for each of these activities:"
        
    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Orpheus Le Gorilla", "emoji": True},
        "close": {"type": "plain_text", "text": "Close", "emoji": True},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "checkboxes",
                        "options": [
                            {
                                "text": {"type": "mrkdwn", "text": "*Follow Activity*"},
                                "description": {
                                    "type": "mrkdwn",
                                    "text": "When you follow someone",
                                },
                                "value": "FollowActivity",
                            },
                            {
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Watchlist Activity*",
                                },
                                "description": {
                                    "type": "mrkdwn",
                                    "text": "When you add a film to your watchlist",
                                },
                                "value": "WatchlistActivity",
                            },
                            {
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Diary Entry Activity*",
                                },
                                "description": {
                                    "type": "mrkdwn",
                                    "text": "When you log a film",
                                },
                                "value": "DiaryEntryActivity",
                            },
                        ],
                        "action_id": "events-change",
                    }
                ],
            },
        ],
    }
