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
        items = data.get('items', [])
        
        if len(items) == 0:
            return None
        
        for item in items:
            if item['member']['username'] == username:
                return item['member']['id']
            
        return None
    
    def get_member(self, id):
        resp = self.oauth.get(f"{self.baseurl}/member/{id}")
        resp.raise_for_status()
        
        return resp.json()

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

    print("id:", client.get_id_by_username(username))