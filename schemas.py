"""
Schemas from Letterboxd API Docs
"""

from enum import Enum
from utils import format_boxd_date


class AccountStatus(Enum):
    """
    The member’s account status
    """
    ACTIVE = "Active"
    MEMORIALIZED = "memorialized"


class LinkType(Enum):
    """
    Denotes which site the link is for
    """
    LETTERBOXD = "letterboxd"
    BOXD = "boxd"
    TMDB = "tmdb"
    IMDB = "imdb"
    JUSTWATCH = "justwatch"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    TICKETS = "tickets"
    TIKTOK = "tiktok"
    BLUESKY = "bluesky"
    THREADS = "threads"


class MemberStatus(Enum):
    """
    The member’s account type.
    """
    CREW = "Crew"
    ALUM = "Alum"
    HQ = "Hq"
    PATRON = "Patron"
    PRO = "Pro"
    MEMBER = "Member"


class Pronoun:
    """
    The member’s preferred pronoun
    """
    def __init__(self, data):
        self.id = data["id"]
        self.label = data["label"]
        self.subject_pronoun = data["subjectPronoun"]
        self.object_pronoun = data["objectPronoun"]
        self.possessive_adjective = data["possessiveAdjective"]
        self.possessive_pronoun = data["possessivePronoun"]
        self.reflexive = data["reflexive"]


class Genre:
    """
    A film genres
    """
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]


class ImageSize:
    """
    The available sizes for the image.
    """
    def __init__(self, data):
        self.width = data["width"]
        self.height = data["height"]
        self.url = data["url"]


class Image:
    """
    Represent an Image
    """
    def __init__(self, data):
        self.sizes = [ImageSize(size) for size in data["sizes"]]


class Review:
    """
    Review details for the log entry
    """
    def __init__(self, data):
        self.lbml = data["lbml"]
        self.text = data["text"]
        self.when_reviewed = format_boxd_date(data["whenReviewed"])
        self.contains_spoilers = data["containsSpoilers"]


class Link:
    """
    Relevent URLs for an entity
    """
    def __init__(self, data):
        self.type = LinkType(data["type"])
        self.id = data["id"]
        self.url = data["url"]
        self.label = data.get("label")
        self.check_url = data.get("checkUrl")


class MemberSummary:
    """
    The member's data
    """
    def __init__(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.given_name = data.get("givenName")
        self.family_name = data.get("familyName")
        self.display_name = data["displayName"]
        self.short_name = data["shortName"]
        self.pronoun = Pronoun(data["pronoun"])
        self.avatar = Image(data["avatar"])
        self.member_status = MemberStatus(data["memberStatus"])
        self.account_status = AccountStatus(data["accountStatus"])


class Film:
    """
    The file's data
    """
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.sorting_name = data["sortingName"]
        self.full_display_name = data.get("fullDisplayName")
        self.release_year = data.get("releaseYear")
        self.runtime = data.get("runTime")
        self.rating = data.get("rating")
        self.poster = Image(data.get("poster")) if "poster" in data else None
        self.adult = data["adult"]
        self.links = {link["type"]: Link(link) for link in data["links"]}
        self.genres = [Genre(genre) for genre in data["genres"]]
        self.description = data.get("description")
        self.tagline = data.get("tagline")


class AbstractActivity:
    """
    Common parent for all activities
    """
    def __init__(self, whenCreated, member, type, **kwargs):
        self.when_created = format_boxd_date(whenCreated)
        self.member = MemberSummary(member)
        self.type = type


class DiaryEntryActivity(AbstractActivity):
    """
    New entry in diary activity
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        diary_entry = kwargs["diaryEntry"]
        self.id: str = diary_entry["id"]
        self.name: str = diary_entry["name"]
        self.rating: int = diary_entry["rating"]
        self.like: bool = diary_entry["like"]
        self.film = Film(diary_entry["film"])
        self.review = Review(diary_entry["review"]) if "review" in diary_entry else None


class WatchlistActivity(AbstractActivity):
    """
    New film in watchlist activity
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.film = Film(kwargs["film"])


class FollowActivity(AbstractActivity):
    """
    Followed someone activity
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.followed: MemberSummary = MemberSummary(kwargs["followed"])
