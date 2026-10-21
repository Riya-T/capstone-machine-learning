"""Social feed with an adjustable post length limit and blocking.

Planted bug (after c_post_limit and c_block): blocking works, but
set_max_length no longer validates the new limit.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from feed import SocialFeed
    feed = SocialFeed()
    feed.add_user("ana")
    feed.add_user("ben")
    feed.block("ana", "ben")
"""

DEFAULT_MAX_LENGTH = 280


class FeedError(Exception):
    pass


class Blocked(FeedError):
    pass


def check_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"max_length must be an int >= 1, got {limit!r}")


class SocialFeed:
    def __init__(self, max_length=DEFAULT_MAX_LENGTH):
        check_limit(max_length)
        self._max_length = max_length
        self._following = {}  # user -> list of followed names, in follow order
        self._own_limits = {}  # user -> their own limit, or None for the feed's
        self._blocked = {}  # user -> list of names they blocked, in block order
        self._posts = {}  # post id -> (author, text), in posting order

    def add_user(self, name, max_length=None):
        if not isinstance(name, str) or not name:
            raise ValueError("user name must be a non-empty str")
        if max_length is not None:
            check_limit(max_length)
        if name in self._following:
            raise FeedError(f"user {name!r} was already added")
        self._following[name] = []
        self._own_limits[name] = max_length
        self._blocked[name] = []

    def post(self, author, text):
        self._require(author)
        self._check_text(author, text)
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
        if follower == followee:
            raise ValueError("users cannot follow themselves")
        if self._between_blocked(follower, followee):
            raise Blocked(f"{follower!r} and {followee!r} have a block between them")
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

    def get_max_length(self, user):
        self._require(user)
        own = self._own_limits[user]
        return self._max_length if own is None else own

    def set_max_length(self, user, max_length):
        self._require(user)
        self._own_limits[user] = max_length

    def block(self, user, other):
        self._require(user)
        self._require(other)
        if user == other:
            raise ValueError("users cannot block themselves")
        if other not in self._blocked[user]:
            self._blocked[user].append(other)
        for a, b in ((user, other), (other, user)):
            if b in self._following[a]:
                self._following[a].remove(b)

    def unblock(self, user, other):
        self._require(user)
        self._require(other)
        if other in self._blocked[user]:
            self._blocked[user].remove(other)

    def is_blocked(self, user, other):
        self._require(user)
        self._require(other)
        return other in self._blocked[user]

    def get_blocked(self, user):
        self._require(user)
        return list(self._blocked[user])

    def _between_blocked(self, a, b):
        return b in self._blocked[a] or a in self._blocked[b]

    def _check_text(self, author, text):
        limit = self.get_max_length(author)
        if not isinstance(text, str) or not 1 <= len(text) <= limit:
            raise ValueError(f"text must be a str of 1 to {limit} characters")

    def _require(self, user):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(user, str) or user not in self._following:
            raise KeyError(user)
