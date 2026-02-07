"""
Generate Slack blocks
"""

import os
from schemas import DiaryEntryActivity, Film
from utils import star_to_text, html_to_mrkdwn, shorten_text


def get_url_id(film:Film):
    # Some magic cuz sometime the sortingName isnt the name in the URL
    return os.path.basename(film.links["letterboxd"].url.strip("/"))

def from_mrkdwn(mrkdwn):
    """
    Create mrkdwn blocks from plain text

    :param mrkdwn: Block content
    :return: List containing a Slack section block with mrkdwn text
    :rtype: list[dict]
    """
    return [{"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn}}]


def from_diaryentry(activity: DiaryEntryActivity):
    """
    Create blocks from Diary Entry Activity

    :param activity: Activity to use
    :type activity: DiaryEntryActivity
    :return: List of Slack blocks (section with film info and actions with Letterboxd button)
    :rtype: list[dict]
    """

    member = activity.member
    film = activity.film

    liked = ":ms-red-heart: " if activity.like else ""
    stars = star_to_text(activity.rating)

    film_name = film.full_display_name or film.name

    review = ""
    if activity.review is not None:
        if activity.review.contains_spoilers:
            review = "_This review contains spoilers_"
        else:
            review = "\n\n> " + html_to_mrkdwn(activity.review.text)
            review = shorten_text(review)

    sorting_name = get_url_id(film)

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{member.display_name} watched {film_name}*\n{liked} {stars}{review}",
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
                    "url": f"https://letterboxd.com/{member.username}/film/{sorting_name}/",
                }
            ],
        },
    ]


def modal_events(channelid, default_events):
    """
    Create a modal to choose which events are posted

    :param channelid: User's personal channel (can be None)
    :return: Slack modal object with event checkboxes
    :rtype: dict
    """
    text = "A message will be sent for each of these activities:"
    if channelid is not None:
        text = f"A message will be sent in <#{channelid}> for each of these activities:"

    events = {
        "WatchlistActivity": {
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
        "FollowActivity": {
            "text": {"type": "mrkdwn", "text": "*Follow Activity*"},
            "description": {
                "type": "mrkdwn",
                "text": "When you follow someone",
            },
            "value": "FollowActivity",
        },
        "DiaryEntryActivity": {
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
    }

    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Orpheus Le Gorilla", "emoji": True},
        "close": {"type": "plain_text", "text": "Close", "emoji": True},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "checkboxes",
                        "initial_options": [events[event] for event in default_events],
                        "options": list(events.values()),
                        "action_id": "events-change",
                    }
                ],
            },
        ],
    }


_ALL_EVENTS = ["WatchlistActivity", "DiaryEntryActivity", "FollowActivity"]


def modal_info(user):
    """
    Create a modal containing user's informations

    :param user: User tuple (slack_id, letterboxd_id, channel_id, ?, events_list)
    :return: Slack modal object with user information and event status
    :rtype: dict
    """
    infos = [
        f"Slack ID: `{user[0]}` <@{user[0]}>",
        f"Letterboxd ID: `{user[1]}`",  # <https://letterboxd.com/{}/|{}>",
        f"Channel: `{user[2]}` <#{user[2]}>" if user[2] else "Channel: None",
    ]
    infos = "\n".join(infos)

    events = [
        (
            f":ms-tick-box:  {event}"
            if event in user[4]
            else f":ms-large-white-square:  {event}"
        )
        for event in _ALL_EVENTS
    ]
    events = "\n".join(events)

    return {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Orpheus Le Gorila", "emoji": True},
        "close": {"type": "plain_text", "text": "Close", "emoji": True},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": infos + "\n\nEvents:\n" + events,
                },
            }
        ],
    }


def watchlist_pick(film:Film):
    return [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":game_die: Picked *<https://letterboxd.com/film/{get_url_id(film)}|{film.full_display_name}>*"
        }
    }]