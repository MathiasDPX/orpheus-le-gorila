"""
Letterboxd API client for interacting with the Letterboxd API.

Provides OAuth2-authenticated access to Letterboxd member data, including
activity feeds, member search, and profile information.
"""

from authlib.integrations.requests_client import OAuth2Session
from schemas import (
    AbstractActivity,
    WatchlistActivity,
    FollowActivity,
    DiaryEntryActivity,
    Film,
)


class LetterboxdClient:
    """
    Client for interacting with the Letterboxd API using OAuth2 authentication.
    """

    DEFAULT_BASEURL = "https://api.letterboxd.com/api/v0"

    def __init__(
        self,
        client_id,
        client_secret,
        username,
        password,
    ):
        """
        Initialize the Letterboxd API client with OAuth2 credentials.

        :param client_id: OAuth2 client ID from Letterboxd API application
        :param client_secret: OAuth2 client secret from Letterboxd API application
        :param username: Letterboxd account username for authentication
        :param password: Letterboxd account password for authentication
        """
        self.baseurl = self.DEFAULT_BASEURL

        self.oauth = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=f"{self.baseurl}/auth/token",
        )

        self.token = self.oauth.fetch_token(
            url=f"{self.baseurl}/auth/token",
            grant_type="password",
            username=username,
            password=password,
        )

    def get_id_by_username(self, username):
        """
        Search for a Letterboxd member by username and return their ID.

        :param username: The exact username to search for
        :return: Member ID if found, None otherwise
        :rtype: str or None
        """
        resp = self.oauth.get(
            f"{self.baseurl}/search",
            params={
                "input": username,
                "include": "MemberSearchItem",
                "adult": False,
            },
        )
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])

        if len(items) == 0:
            return None

        for item in items:
            if item["member"]["username"] == username:
                return item["member"]["id"]

        return None

    def get_member(self, boxd_id):
        """
        Retrieve detailed member information by member ID.

        :param boxd_id: The Letterboxd member ID
        :return: Member data including profile information
        :rtype: dict
        """
        resp = self.oauth.get(f"{self.baseurl}/member/{boxd_id}")
        resp.raise_for_status()

        return resp.json()

    def get_activity(self, boxd_id) -> list[AbstractActivity]:
        """
        Fetch the activity feed for a member.

        :param boxd_id: The Letterboxd member ID
        :return: List of activity objects
        :rtype: list[AbstractActivity]
        """
        resp = self.oauth.get(
            f"{self.baseurl}/member/{boxd_id}/activity",
            params={"perPage": 100, "adult": False, "where": "OwnActivity"},
        )
        resp.raise_for_status()

        data = resp.json()

        _activities = []
        for item in data["items"]:
            if item["type"] == "WatchlistActivity":
                _activities.append(WatchlistActivity(**item))
            elif item["type"] == "DiaryEntryActivity":
                _activities.append(DiaryEntryActivity(**item))
            elif item["type"] == "FollowActivity":
                _activities.append(FollowActivity(**item))

        return _activities

    def get_watchlist(self, boxd_id):
        resp = self.oauth.get(
            f"{self.baseurl}/member/{boxd_id}/watchlist", params={"perPage": 100}
        )

        return [film['id'] for film in resp.json()["items"]]


    def get_film(self, film_id):
        resp = self.oauth.get(
            f"{self.baseurl}/film/{film_id}"
        )
        
        return Film(resp.json())


if __name__ == "__main__":
    from dotenv import load_dotenv
    from os import getenv

    load_dotenv()

    USERNAME = "mathias_dpx"

    client = LetterboxdClient(
        client_id=getenv("BOXD_CLIENT_ID"),
        client_secret=getenv("BOXD_CLIENT_SECRET"),
        username=getenv("BOXD_USERNAME"),
        password=getenv("BOXD_PASSWORD"),
    )

    uid = client.get_id_by_username(USERNAME)
    activities = client.get_activity(uid)

    for activity in activities:
        member = activity.member
        if isinstance(activity, WatchlistActivity):
            print(
                f"Added {activity.film.full_display_name or activity.film.name} to their watchlist"
            )
        elif isinstance(activity, DiaryEntryActivity):
            print(
                f"Rated {activity.film.full_display_name or activity.film.name} {activity.rating}⭐"
            )
