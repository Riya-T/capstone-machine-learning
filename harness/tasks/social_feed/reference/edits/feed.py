"""Social feed where posts can be edited, with a version check per post.

Correct solution for social_feed after c_edits. A post's version is the
number of texts it has had, so it is derived from its revisions.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from feed import SocialFeed
    feed = SocialFeed()
    feed.add_user("ana")
    post_id = feed.post("ana", "helo")
    feed.edit(post_id, "hello", expected_version=1)
"""

MAX_LENGTH = 280


class FeedError(Exception):
    pass


class VersionConflict(FeedError):
    pass


def check_text(text):
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_LENGTH:
        raise ValueError(f"text must be a str of 1 to {MAX_LENGTH} characters")


class SocialFeed:
    def __init__(self):
        self._following = {}  # user -> list of followed names, in follow order
        self._posts = {}  # post id -> (author, list of texts, oldest first)

    def add_user(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("user name must be a non-empty str")
        if name in self._following:
            raise FeedError(f"user {name!r} was already added")
        self._following[name] = []

    def post(self, author, text):
        self._require(author)
        check_text(text)
        post_id = len(self._posts) + 1
        self._posts[post_id] = (author, [text])
        return post_id

    def edit(self, post_id, text, expected_version=None):
        revisions = self._revisions(post_id)
        check_text(text)
        if expected_version is not None and expected_version != len(revisions):
            raise VersionConflict(
                f"post {post_id} is at version {len(revisions)}, not {expected_version}"
            )
        revisions.append(text)

    def get_text(self, post_id):
        return self._revisions(post_id)[-1]

    def get_version(self, post_id):
        return len(self._revisions(post_id))

    def get_revisions(self, post_id):
        return list(self._revisions(post_id))

    def follow(self, follower, followee):
        self._require(follower)
        self._require(followee)
        if follower == followee:
            raise ValueError("users cannot follow themselves")
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

    def _revisions(self, post_id):
        if post_id not in self._posts:
            raise KeyError(post_id)
        return self._posts[post_id][1]

    def _require(self, user):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(user, str) or user not in self._following:
            raise KeyError(user)
