from datetime import datetime
from enum import Enum


class AccountStatus(Enum):
    active = "Active"
    memorialized = "memorialized"


class LinkType(Enum):
    letterboxd = "letterboxd"
    boxd = "boxd"
    tmdb = "tmdb"
    imdb = "imdb"
    justwatch = "justwatch"
    facebook = "facebook"
    instagram = "instagram"
    twitter = "twitter"
    youtube = "youtube"
    tickets = "tickets"
    tiktok = "tiktok"
    bluesky = "bluesky"
    threads = "threads"


class MemberStatus(Enum):
    crew = "Crew"
    alum = "Alum"
    hq = "Hq"
    patron = "Patron"
    pro = "Pro"
    member = "Member"


class Pronoun:
    def __init__(self, data):
        self.id = data["id"]
        self.label = data["label"]
        self.subjectPronoun = data["subjectPronoun"]
        self.objectPronoun = data["objectPronoun"]
        self.possessiveAdjective = data["possessiveAdjective"]
        self.possessivePronoun = data["possessivePronoun"]
        self.reflexive = data["reflexive"]


class Genre:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]


class ImageSize:
    def __init__(self, data):
        self.width = data["width"]
        self.height = data["height"]
        self.url = data["url"]


class Image:
    def __init__(self, data):
        self.sizes = [ImageSize(size) for size in data["sizes"]]


class Link:
    def __init__(self, data):
        self.type = LinkType(data["type"])
        self.id = data["id"]
        self.url = data["url"]
        self.label = data.get("label")
        self.checkUrl = data.get("checkUrl")


class MemberSummary:
    def __init__(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.givenName = data.get("givenName")
        self.familyName = data.get("familyName")
        self.displayName = data["displayName"]
        self.shortName = data["shortName"]
        self.pronoun = Pronoun(data["pronoun"])
        self.avatar = Image(data["avatar"])
        self.memberStatus = MemberStatus(data["memberStatus"])
        self.accountStatus = AccountStatus(data["accountStatus"])


class Film:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.sortingName = data["sortingName"]
        self.fullDisplayName = data.get("fullDisplayName")
        self.releaseYear = data.get("releaseYear")
        self.runTime = data.get("runTime")
        self.rating = data.get("rating")
        self.poster = Image(data.get("poster")) if "poster" in data else None
        self.adult = data["adult"]
        self.links = [Link(link) for link in data["links"]]
        self.genres = [Genre(genre) for genre in data["genres"]]
        self.description = data.get("description")
        self.tagline = data.get("tagline")


class AbstractActivity:
    def __init__(self, whenCreated, member, **kwargs):
        self.whenCreated = datetime.fromisoformat(whenCreated.replace("Z", "+00:00"))
        self.member = MemberSummary(member)


class DiaryEntryActivity(AbstractActivity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        diaryEntry = kwargs["diaryEntry"]
        self.id: str = diaryEntry["id"]
        self.name: str = diaryEntry["name"]
        self.rating: int = diaryEntry["rating"]
        self.like: bool = diaryEntry["like"]
        self.film = Film(diaryEntry["film"])


class WatchlistActivity(AbstractActivity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.film = Film(kwargs["film"])


class FollowActivity(AbstractActivity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.followed: MemberSummary = kwargs["followed"]
