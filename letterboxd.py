from authlib.integrations.requests_client import OAuth2Session


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

    def get_activity(self, id):
        resp = self.oauth.get(
            f"{self.baseurl}/member/{id}/activity",
            params={
                "perPage": 100,
                "adult": False,
                "where": "OwnActivity"
            }
        )
        print(resp.headers)
        resp.raise_for_status()
        
        data = resp.json()
        activities = []
        for item in data['items']:
            if item['type'] == "WatchlistActivity":
                activities.append(WatchlistActivity(**item))
            elif item['type'] == "DiaryEntryActivity":
                activities.append(DiaryEntryActivity(**item))
        
        return activities

class Film:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.sortingName = data['sortingName']
        self.fullDisplayName = data.get('fullDisplayName')
        self.releaseYear = data.get('releaseYear')
        self.runTime = data.get('runTime')
        self.rating = data.get('rating')
        # TODO: posters
        self.adult = data['adult']
        self.links = data['links']
        self.genres = data['genres']
        self.description = data.get('description')
        self.tagline = data.get("tagline")

class AbstractActivity:
    def __init__(self, whenCreated):
        self.whenCreated = whenCreated
        
class DiaryEntryActivity(AbstractActivity):
    def __init__(self, whenCreated, diaryEntry, **kwargs):
        super().__init__(whenCreated)
        
        self.id = diaryEntry['id']
        self.name = diaryEntry['name']
        self.rating = diaryEntry['rating']
        self.like = diaryEntry['like']
        self.film = Film(diaryEntry['film'])
        
class WatchlistActivity(AbstractActivity):
    def __init__(self, whenCreated, film, **kwargs):
        super().__init__(whenCreated)
        self.film = Film(film)

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
    print("id:", uid)
    activities = client.get_activity(uid)
    
    for activity in activities:
        if type(activity) is WatchlistActivity:
            print(f"{username} added {activity.film.fullDisplayName or activity.film.name} to their watchlist")
        elif type(activity) is DiaryEntryActivity:
            print(f"{username} rate {activity.film.fullDisplayName or activity.film.name} {activity.rating} stars")