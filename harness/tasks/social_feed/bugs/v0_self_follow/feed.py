"""Social feed: users, short posts, one-way follows and timelines.

Planted bug (initial version): following yourself is allowed. The public
checks never try it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from feed import SocialFeed
    feed = SocialFeed()
    feed.add_user("ana")
    post_id = feed.post("ana", "hello")
    feed.get_timeline("ana")  # -> [post_id]
"""

MAX_LENGTH = 280


class FeedError(Exception):
    pass


class SocialFeed:
    def __init__(self):
        self._following = {}  # user -> list of followed names, in follow order
        self._posts = {}  # post id -> (author, text), in posting order

    def add_user(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("user name must be a non-empty str")
        if name in self._following:
            raise FeedError(f"user {name!r} was already added")
        self._following[name] = []

    def post(self, author, text):
        self._require(author)
        if not isinstance(text, str) or not 1 <= len(text) <= MAX_LENGTH:
            raise ValueError(f"text must be a str of 1 to {MAX_LENGTH} characters")
        post_id = len(self._posts) + 1
        self._posts[post_id] = (author, text)
        return post_id

    def get_text(self, post_id):
        if post_id not in self._posts:
            raise KeyError(post_id)
        return self._posts[post_id][1]

    def follow(self, follower, followee):
        self._require(follower)
        self._require(followee)
        if followee in self._following[follower]:
            raise FeedError(f"{follower!r} already follows {followee!r}")
        self._following[follower].append(followee)

    def unfollow(self, follower, followee):
        self._require(follower)
        self._require(followee)
        if followee not in self._following[follower]:
            raise FeedError(f"{follower!r} does not follow {followee!r}")
        self._following[follower].remove(followee)

    def get_following(self, user):
        self._require(user)
        return list(self._following[user])

    def get_timeline(self, user):
        self._require(user)
        authors = {user, *self._following[user]}
        return [pid for pid, (author, _) in self._posts.items() if author in authors]

    def _require(self, user):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(user, str) or user not in self._following:
            raise KeyError(user)
