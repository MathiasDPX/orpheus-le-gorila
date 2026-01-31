from authlib.integrations.requests_client import OAuth2Session
from schemas import *


class LetterboxdClient:
    def __init__(
        self,
        client_id,
        client_secret,
        username,
        password,
        baseurl="https://api.letterboxd.com/api/v0",
    ):
        self.baseurl = baseurl

        self.oauth = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=f"{baseurl}/auth/token",
        )

        self.token = self.oauth.fetch_token(
            url=f"{baseurl}/auth/token",
            grant_type="password",
            username=username,
            password=password,
        )

    def get_id_by_username(self, username):
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

    def get_member(self, id):
        resp = self.oauth.get(f"{self.baseurl}/member/{id}")
        resp.raise_for_status()

        return resp.json()

    def get_activity(self, id) -> list[AbstractActivity]:
        resp = self.oauth.get(
            f"{self.baseurl}/member/{id}/activity",
            params={
                "perPage": 100,
                "adult": False,
                "where": "OwnActivity"
            }
        )
        resp.raise_for_status()
        
        data = resp.json()
        
        import json
        with open("data.json", "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        activities = []
        for item in data['items']:
            if item['type'] == "WatchlistActivity":
                activities.append(WatchlistActivity(**item))
            elif item['type'] == "DiaryEntryActivity":
                activities.append(DiaryEntryActivity(**item))
        
        return activities


if __name__ == "__main__":
    from dotenv import load_dotenv
    from os import getenv

    load_dotenv()

    username = "mathias_dpx"

    client = LetterboxdClient(
        client_id=getenv("BOXD_CLIENT_ID"),
        client_secret=getenv("BOXD_CLIENT_SECRET"),
        username=getenv("BOXD_USERNAME"),
        password=getenv("BOXD_PASSWORD"),
    )

    uid = client.get_id_by_username(username)
    activities = client.get_activity(uid)
    
    for activity in activities:
        
        member = activity.member
        if type(activity) is WatchlistActivity:
            print(f"{member.displayName} added {activity.film.fullDisplayName or activity.film.name} to their watchlist")
        elif type(activity) is DiaryEntryActivity:
            print(f"{member.displayName} rate {activity.film.fullDisplayName or activity.film.name} {activity.rating} stars")