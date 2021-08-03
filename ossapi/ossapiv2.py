from typing import (get_type_hints, get_origin, get_args, Union, TypeVar,
    Optional, List, _GenericAlias)
import logging
import webbrowser
import socket
import pickle
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime
from enum import Enum
from urllib.parse import unquote
import inspect
import json
from keyword import iskeyword

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from ossapi.models import (Beatmap, BeatmapUserScore, ForumTopicAndPosts,
    Search, CommentBundle, Cursor, Score, BeatmapSearchResult,
    ModdingHistoryEventsBundle, User, Rankings, BeatmapScores, KudosuHistory,
    Beatmapset, BeatmapPlaycount, Spotlight, Spotlights, WikiPage, _Event,
    Event, BeatmapsetDiscussionPostResult, Build, ChangelogListing)
from ossapi.mod import Mod
from ossapi.enums import (GameMode, ScoreType, RankingFilter, RankingType,
    UserBeatmapType, BeatmapDiscussionPostSort, UserLookupKey,
    BeatmapsetEventType)
from ossapi.utils import (is_compatible_type, is_primitive_type, is_optional,
    is_base_model_type, is_model_type, is_high_model_type)

# our ``request`` function below relies on the ordering of these types. The
# base type must come first, with any auxiliary types that the base type accepts
# cooming after.
# These types are intended to provide better type hinting for consumers. We
# want to support the ability to pass ``"osu"`` instead of ``GameMode.STD``,
# for instance. We automatically convert any value to its base class if the
# relevant parameter has a type hint of the form below (see ``request`` for
# details).
GameModeT = Union[GameMode, str]
ScoreTypeT = Union[ScoreType, str]
ModT = Union[Mod, str, int, list]
RankingFilterT = Union[RankingFilter, str]
RankingTypeT = Union[RankingType, str]
UserBeatmapTypeT = Union[UserBeatmapType, str]
BeatmapDiscussionPostSortT = Union[BeatmapDiscussionPostSort, str]
UserLookupKeyT = Union[UserLookupKey, str]
BeatmapsetEventTypeT = Union[BeatmapsetEventType, str]


def request(function):
    """
    Automatically instantiates parameters with their type hint if the type hint
    is a union of a base class. This means, for instance, that a function which
    accepts a ``ModT`` will have the value of that parameter automatically
    converted to a ``Mod``, even if the user passes a `str`.
    """
    instantiate = {}
    for name, type_ in function.__annotations__.items():
        origin = get_origin(type_)
        args = get_args(type_)
        if origin is Union and is_base_model_type(args[0]):
            instantiate[name] = args[0]

    arg_names = list(inspect.signature(function).parameters)

    def wrapper(*args, **kwargs):
        # we may need to edit this later so convert from tuple
        args = list(args)

        # args and kwargs are handled separately, but in a similar fashion.
        # The difference is that for ``args`` we need to know the name of the
        # argument so we can look up its type hint and see if it's a parameter
        # we need to convert.
        for i, (arg, arg_name) in enumerate(zip(args, arg_names)):
            if arg_name in instantiate:
                type_ = instantiate[arg_name]
                args[i] = type_(arg)

        for arg in kwargs:
            if arg in instantiate:
                type_ = instantiate[arg]
                kwargs[arg] = type_(kwargs[arg])

        return function(*args, **kwargs)
    return wrapper


class OssapiV2:
    TOKEN_URL = "https://osu.ppy.sh/oauth/token"
    AUTH_CODE_URL = "https://osu.ppy.sh/oauth/authorize"
    BASE_URL = "https://osu.ppy.sh/api/v2"

    AUTHORIZATION_TOKEN_FILE = (Path(__file__).parent /
        "authorization_code.pickle")
    CLIENT_TOKEN_FILE = Path(__file__).parent / "client_credentials.pickle"

    def __init__(self, client_id, client_secret, redirect_uri=None,
        scopes=["public"], strict=False):
        self.strict = strict
        self.log = logging.getLogger(__name__)

        self.session = self.authenticate(client_id, client_secret, redirect_uri,
            scopes)

    def authenticate(self, client_id, client_secret, redirect_uri, scopes):
        # Prefer saved sessions to re-authenticating. Furthermore, prefer the
        # authorization code grant over the client credentials grant if both
        # exist.
        if self.AUTHORIZATION_TOKEN_FILE.is_file():
            with open(self.AUTHORIZATION_TOKEN_FILE, "rb") as f:
                token = pickle.load(f)
            return self._auth_oauth_session(client_id, client_secret, scopes,
                token=token)

        # TODO I think this breaks if the token is expired?
        if self.CLIENT_TOKEN_FILE.is_file():
            with open(self.CLIENT_TOKEN_FILE, "rb") as f:
                token = pickle.load(f)
            return OAuth2Session(client_id, token=token)

        # if redirect_uri is not passed, assume the user wanted to use the
        # client credentials grant.
        if not redirect_uri:
            if scopes != ["public"]:
                raise ValueError(f"`scopes` must be ['public'] if the "
                    f"client credentials grant is used. Got {scopes}")
            return self._client_credentials_grant(client_id, client_secret)
        return self._authorization_code_grant(client_id, client_secret,
            redirect_uri, scopes)

    @staticmethod
    def clear_authentication():
        if OssapiV2.AUTHORIZATION_TOKEN_FILE.is_file():
            OssapiV2.AUTHORIZATION_TOKEN_FILE.unlink()
        if OssapiV2.CLIENT_TOKEN_FILE.is_file():
            OssapiV2.CLIENT_TOKEN_FILE.unlink()

    def _client_credentials_grant(self, client_id, client_secret):
        client = BackendApplicationClient(client_id=client_id, scope=["public"])
        oauth = OAuth2Session(client=client)

        token = oauth.fetch_token(token_url=self.TOKEN_URL,
            client_id=client_id, client_secret=client_secret)
        self._save_token(token, "client")

        return oauth

    def _authorization_code_grant(self, client_id, client_secret, redirect_uri,
        scopes):
        oauth = self._auth_oauth_session(client_id, client_secret, scopes,
            redirect_uri=redirect_uri)
        authorization_url, _state = oauth.authorization_url(self.AUTH_CODE_URL)
        webbrowser.open(authorization_url)

        # open up a temporary socket so we can receive the GET request to the
        # callback url
        port = int(redirect_uri.rsplit(":", 1)[1].split("/")[0])
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(("localhost", port))
        serversocket.listen(1)
        connection, _ = serversocket.accept()
        # arbitrary "large enough" byte receive size
        data = str(connection.recv(8192))
        connection.send(b"HTTP/1.0 200 OK\n")
        connection.send(b"Content-Type: text/html\n")
        connection.send(b"\n")
        connection.send(b"""<html><body>
            <h2>Ossapi has received your authentication.</h2> You
            may now close this tab safely.
            </body></html>
        """)
        connection.close()
        serversocket.close()

        code = data.split("code=")[1].split("&state=")[0]
        token = oauth.fetch_token(self.TOKEN_URL, client_id=client_id,
            client_secret=client_secret, code=code)
        self._save_token(token, "auth")

        return oauth

    def _auth_oauth_session(self, client_id, client_secret, scopes, *,
        token=None, redirect_uri=None):
        auto_refresh_kwargs = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        return OAuth2Session(client_id, token=token, redirect_uri=redirect_uri,
            auto_refresh_url=self.TOKEN_URL,
            auto_refresh_kwargs=auto_refresh_kwargs,
            token_updater=lambda token: self._save_token(token, "auth"),
            scope=scopes)

    def _save_token(self, token, flow):
        self.log.info(f"saving token to pickle file for flow {flow}")
        filename = ("authorization_code.pickle" if flow == "auth" else
            "client_credentials.pickle")
        path = Path(__file__).parent / filename
        with open(path, "wb+") as f:
            pickle.dump(token, f)

    def _get(self, type_, url, params={}):
        params = self._format_params(params)
        r = self.session.get(f"{self.BASE_URL}{url}", params=params)
        self.log.info(f"made request to {r.request.url}")
        json_ = r.json()
        self.log.debug(f"received json: \n{json.dumps(json_, indent=4)}")
        # TODO this should just be ``if "error" in json``, but for some reason
        # ``self.search_beatmaps`` always returns an error in the response...
        # open an issue on osu-web?
        if len(json_) == 1 and "error" in json_:
            raise ValueError(f"api returned an error of `{json_['error']}` for "
                f"a request to {unquote(r.request.url)}")
        return self._instantiate_type(type_, json_)

    def _format_params(self, params):
        for key, value in params.copy().items():
            if isinstance(value, list):
                # we need to pass multiple values for this key, so make its
                # value a list https://stackoverflow.com/a/62042144
                params[f"{key}[]"] = []
                for v in value:
                    params[f"{key}[]"].append(self._format_value(v))
                del params[key]
            elif isinstance(value, Cursor):
                new_params = self._format_params(value.__dict__)
                for k, v in new_params.items():
                    params[f"cursor[{k}]"] = v
                del params[key]
            elif isinstance(value, Mod):
                params[f"{key}[]"] = value.decompose()
                del params[key]
            else:
                params[key] = self._format_value(value)
        return params

    def _format_value(self, value):
        if isinstance(value, datetime):
            return 1000 * int(value.timestamp())
        if isinstance(value, Enum):
            return value.value
        return value

    def _resolve_annotations(self, obj):
        """
        This is where the magic happens. Since python lacks a good
        deserialization library, I've opted to use type annotations and type
        annotations only to convert json to objects. A breakdown follows.

        Every endpoint defines a base object, let's say it's a ``Score``. We
        first instantiate this object with the json we received. This is easy to
        do because (almost) all of our objects are dataclasses, which means we
        can pass the json as ``Score(**json)`` and since the names of our fields
        coincide with the names of the api json keys, everything works.

        This populates all of the surface level members, but nested attributes
        which are annotated as another dataclass object will still be dicts. So
        we traverse down the tree of our base object's attributes (depth-first,
        though I'm pretty sure BFS would work just as well), looking for any
        attribute with a type annotation that we need to deal with. For
        instance, ``Score`` has a ``beatmap`` attribute, which is annotated as
        ``Optional[Beatmap]``. We ignore the optional annotation (since we're
        looking at this attribute, we must have received data for it, so it's
        nonnull) and then instantiate the ``beatmap`` attribute the same way
        we instantiated the ``Score`` - with ``Beatmap(**json)``. Of course, the
        variables will look different in the method (``type_(**value)``).

        Finally, when traversing the attribute tree, we also look for attributes
        which aren't dataclasses, but we still need to convert. For instance,
        any attribute with an annotation of ``datetime`` or ``Mod`` we convert
        to a ``datetime`` and ``Mod`` object respectively.

        This code is arguably trying to be too smart for its own good, but I
        think it's very elegant from the perspective of "just add a dataclass
        that mirrors the api's objects and everything works". Will hopefully
        make changing our dataclasses to account for breaking api changes in
        the future trivial as well.

        And if I'm being honest, it was an excuse to learn the internals of
        python's typing system.
        """
        # we want to get the annotations of inherited members as well, which is
        # why we pass ``type(obj)`` instead of just ``obj``, which would only
        # return annotations for attributes defined in ``obj`` and not its
        # inherited attributes.
        annotations = get_type_hints(type(obj))
        override_annotations = obj.override_types()
        annotations = {**annotations, **override_annotations}
        self.log.debug(f"resolving annotations for type {type(obj)}")
        for attr, value in obj.__dict__.items():
            # we use this attribute later if we encounter an attribute which
            # has been instantiated generically, but we don't need to do
            # anything with it now.
            if attr == "__orig_class__":
                continue
            type_ = annotations[attr]
            # when we instantiate types, we explicitly fill in optional
            # attributes with ``None``. We want to skip these, but only if the
            # attribute is actually annotated as optional, otherwise we would be
            # skipping fields that are null which aren't supposed to be, and
            # prevent that error from being caught.
            if value is None and is_optional(type_):
                continue
            self.log.debug(f"resolving attribute {attr}")

            value = self._instantiate_type(type_, value, obj, attr_name=attr)
            if not value:
                continue
            setattr(obj, attr, value)
        self.log.debug(f"resolved annotations for type {type(obj)}")
        return obj

    def _instantiate_type(self, type_, value, obj=None, attr_name=None):
        # ``attr_name`` is purely for debugging, it's the name of the attribute
        # being instantiated
        origin = get_origin(type_)
        args = get_args(type_)

        # if this type is an optional, "unwrap" it to get the true type.
        # We don't care about the optional annotation in this context
        # because if we got here that means we were passed a value for this
        # attribute, so we know it's defined and not optional.
        if is_optional(type_):
            # leaving these assertions in to help me catch errors in my
            # reasoning until I better understand python's typing.
            assert len(args) == 2
            type_ = args[0]
            origin = get_origin(type_)
            args = get_args(type_)

        # validate that the values we're receiving are the types we expect them
        # to be
        if is_primitive_type(type_):
            if not is_compatible_type(value, type_):
                raise TypeError(f"expected type {type_} for value {value}, got "
                    f"type {type(value)}"
                    f" (for attribute: {attr_name})" if attr_name else "")

        if is_base_model_type(type_):
            self.log.debug(f"instantiating base type {type_}")
            return type_(value)

        if origin is list and (is_model_type(args[0]) or
            isinstance(args[0], TypeVar)):
            assert len(args) == 1
            # check if the list has been instantiated generically; if so,
            # use the concrete type backing the generic type.
            if isinstance(args[0], TypeVar):
                # ``__orig_class__`` is how we can get the concrete type of
                # a generic. See https://stackoverflow.com/a/60984681 and
                # https://www.python.org/dev/peps/pep-0560/#mro-entries.
                type_ = get_args(obj.__orig_class__)[0]
            # otherwise, it's been instantiated with a concrete model type,
            # so use that type.
            else:
                type_ = args[0]
            new_value = []
            for entry in value:
                if is_base_model_type(type_):
                    entry = type_(entry)
                else:
                    entry = self._instantiate(type_, entry)
                # if the list entry is a high (non-base) model type, we need to
                # resolve it instead of just sticking it into the list, since
                # its children might still be dicts and not model instances.
                # We don't do this for base types because that type is the one
                # responsible for resolving its own annotations or doing
                # whatever else it needs to do, not us.
                if is_high_model_type(type_):
                    entry = self._resolve_annotations(entry)
                new_value.append(entry)
            return new_value

        # either we ourself are a model type (eg ``Search``), or we are
        # a special indexed type (eg ``type_ == SearchResult[UserCompact]``,
        # ``origin == UserCompact``). In either case we want to instantiate
        # ``type_``.
        if not is_model_type(type_) and not is_model_type(origin):
            return None
        value = self._instantiate(type_, value)
        # we need to resolve the annotations of any nested model types before we
        # set the attribute. This recursion is well-defined because the base
        # case is when ``value`` has no model types, which will always happen
        # eventually.
        return self._resolve_annotations(value)

    def _instantiate(self, type_, kwargs):
        self.log.debug(f"instantiating type {type_}")
        # we need a special case to handle when ``type_`` is a
        # ``_GenericAlias``. I don't fully understand why this exception is
        # necessary, and it's likely the result of some error on my part in our
        # type handling code. Nevertheless, until I dig more deeply into it,
        # we need to extract the type to use for the init signature and the type
        # hints from a ``_GenericAlias`` if we see one, as standard methods
        # won't work.
        override_type = type_.override_class(kwargs)
        type_ = override_type or type_
        signature_type = type_
        try:
            type_hints = get_type_hints(type_)
        except TypeError:
            assert type(type_) is _GenericAlias # pylint: disable=unidiomatic-typecheck

            signature_type = get_origin(type_)
            type_hints = get_type_hints(signature_type)

        # make a copy so we can modify while iterating
        for key in list(kwargs):
            value = kwargs.pop(key)
            # replace any key names that are invalid python syntax with a valid
            # one. Note: this is relying on our models replacing an at sign with
            # an underscore when declaring attributes.
            key = key.replace("@", "_")
            # python classes can't have keywords as attribute names, so if the
            # api has given us a keyword attribute, append an underscore. As
            # above, this is relying on our models to match this by appending
            # an underscore to keyword attribute names.
            if iskeyword(key):
                key += "_"
            kwargs[key] = value

        # if we've annotated a class with ``Optional[X]``, and the api response
        # didn't return a value for that attribute, pass ``None`` for that
        # attribute.
        # This is so that we don't have to define a default value of ``None``
        # for each optional attribute of our models, since the default will
        # always be ``None``.
        for attribute, annotation in type_hints.items():
            if is_optional(annotation):
                if attribute not in kwargs:
                    kwargs[attribute] = None

        # The osu api often adds new fields to various models, and these are not
        # considered breaking changes. To make this a non-breaking change on our
        # end as well, we ignore any unexpected parameters, unless
        # ``self.strict`` is ``True``. This means that consumers using old
        # ossapi versions (which aren't up to date with the latest parameters
        # list) will have new fields silently ignored instead of erroring.
        # This also means that consumers won't be able to benefit from new
        # fields unless they upgrade, but this is a conscious decision on our
        # part to keep things entirely statically typed. Otherwise we would be
        # going the route of PRAW, which returns dynamic results for all api
        # queries. I think a statically typed solution is better for the osu!
        # api, which promises at least some level of stability in its api.
        parameters = list(inspect.signature(signature_type.__init__).parameters)
        kwargs_ = {}

        # Some special classes take arbitrary parameters, so we can't evaluate
        # whether a parameter is unexpected or not until we instantiate it.
        if isinstance(type_, type) and issubclass(type_, Cursor):
            kwargs_ = kwargs
        else:
            for k, v in kwargs.items():
                if k in parameters:
                    kwargs_[k] = v
                else:
                    if self.strict:
                        raise TypeError(f"unexpected parameter `{k}` for type "
                            f"{type_}")
                    self.log.info(f"ignoring unexpected parameter `{k}` from "
                        f"api response for type {type_}")
        try:
            val = type_(**kwargs_)
        except TypeError as e:
            raise TypeError(f"type error while instantiating class {type_}: "
                f"{str(e)}") from e

        return val


    # =========
    # Endpoints
    # =========


    # /beatmaps
    # ---------

    @request
    def beatmap_lookup(self,
        checksum: Optional[str] = None,
        filename: Optional[str] = None,
        beatmap_id: Optional[int] = None
    ) -> Beatmap:
        """
        https://osu.ppy.sh/docs/index.html#lookup-beatmap
        """
        params = {"checksum": checksum, "filename": filename, "id": beatmap_id}
        return self._get(Beatmap, "/beatmaps/lookup", params)

    @request
    def beatmap_user_score(self,
        beatmap_id: int,
        user_id: int,
        mode: Optional[GameModeT] = None,
        mods: Optional[ModT] = None
    ) -> BeatmapUserScore:
        """
        https://osu.ppy.sh/docs/index.html#get-a-user-beatmap-score
        """
        params = {"mode": mode, "mods": mods}
        return self._get(BeatmapUserScore,
            f"/beatmaps/{beatmap_id}/scores/users/{user_id}", params)

    @request
    def beatmap_scores(self,
        beatmap_id: int,
        mode: Optional[GameModeT] = None,
        mods: Optional[ModT] = None,
        type_: Optional[RankingTypeT] = None
    ) -> BeatmapScores:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmap-scores
        """
        params = {"mode": mode, "mods": mods, "type": type_}
        return self._get(BeatmapScores, f"/beatmaps/{beatmap_id}/scores",
            params)

    @request
    def beatmap(self,
        beatmap_id: int
    ) -> Beatmap:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmap
        """
        return self._get(Beatmap, f"/beatmaps/{beatmap_id}")


    # /beatmapsets
    # ------------

    @request
    def beatmapset_discussion_posts(self,
        beatmapset_session_id: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[BeatmapDiscussionPostSortT] = None,
        user_id: Optional[int] = None,
        with_deleted: Optional[bool] = None
    ) -> BeatmapsetDiscussionPostResult:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-posts
        """
        params = {"beatmapset_session_id": beatmapset_session_id,
            "limit": limit, "page": page, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussionPostResult,
            "/beatmapsets/discussions/posts", params)


    # /changelog
    # ----------

    @request
    def changelog_build(self,
        stream: str,
        build: str
    ) -> Build:
        """
        https://osu.ppy.sh/docs/index.html#get-changelog-build
        """
        return self._get(Build, f"/changelog/{stream}/{build}")

    @request
    def changelog_listing(self,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        max_id: Optional[int] = None,
        stream: Optional[str] = None
    ) -> ChangelogListing:
        """
        https://osu.ppy.sh/docs/index.html#get-changelog-listing
        """
        params = {"from": from_, "to": to, "max_id": max_id, "stream": stream}
        return self._get(ChangelogListing, "/changelog", params)

    @request
    def changelog_lookup(self,
        changelog: str,
        key: Optional[str] = None
    ) -> Build:
        """
        https://osu.ppy.sh/docs/index.html#lookup-changelog-build
        """
        params = {"key": key}
        return self._get(Build, f"/changelog/{changelog}", params)

    # /comments
    # ---------

    @request
    def comments(self,
        commentable_type=None,
        commentable_id=None,
        cursor=None,
        parent_id=None,
        sort=None
    ) -> CommentBundle:
        """
        A list of comments and their replies, up to 2 levels deep.

        https://osu.ppy.sh/docs/index.html#get-comments

        Notes
        -----
        ``pinned_comments`` is only included when ``commentable_type`` and
        ``commentable_id`` are specified.
        """
        params = {"commentable_type": commentable_type,
            "commentable_id": commentable_id, "cursor": cursor,
            "parent_id": parent_id, "sort": sort}
        return self._get(CommentBundle, "/comments", params)

    @request
    def comment(self,
        comment_id: int
    ) -> CommentBundle:
        """
        https://osu.ppy.sh/docs/index.html#get-a-comment
        """
        return self._get(CommentBundle, f"/comments/{comment_id}")


    # /forums
    # -------

    @request
    def topic(self,
        topic,
        cursor: Optional[Cursor] = None,
        sort=None,
        limit=None,
        start=None,
        end=None
    ) -> ForumTopicAndPosts:
        """
        A topic and its posts.

        https://osu.ppy.sh/docs/index.html#get-topic-and-posts
        """
        params = {"cursor": cursor, "sort": sort, "limit": limit,
            "start": start, "end": end}
        return self._get(ForumTopicAndPosts, f"/forums/topics/{topic}", params)


    # / ("home")
    # ----------

    @request
    def search(self,
        mode="all",
        query=None,
        page=None
    ) -> Search:
        """
        https://osu.ppy.sh/docs/index.html#search
        """
        params = {"mode": mode, "query": query, "page": page}
        return self._get(Search, "/search", params)

    # /me
    # ---

    @request
    def get_me(self,
        mode: Optional[GameModeT] = None
    ):
        """
        https://osu.ppy.sh/docs/index.html#get-own-data
        """
        return self._get(User, f"/me/{mode.value if mode else ''}")

    # /rankings
    # ---------

    @request
    def ranking(self,
        mode: GameModeT,
        type_: RankingTypeT,
        country: Optional[str] = None,
        cursor: Optional[Cursor] = None,
        filter_: RankingFilterT = RankingFilter.ALL,
        spotlight: Optional[int] = None,
        variant: Optional[str] = None
    ) -> Rankings:
        """
        https://osu.ppy.sh/docs/index.html#get-ranking
        """
        params = {"country": country, "cursor": cursor, "filter": filter_,
            "spotlight": spotlight, "variant": variant}
        return self._get(Rankings, f"/rankings/{mode.value}/{type_.value}",
            params=params)

    @request
    def spotlights(self) -> List[Spotlight]:
        """
        https://osu.ppy.sh/docs/index.html#get-spotlights
        """
        spotlights = self._get(Spotlights, "/spotlights")
        return spotlights.spotlights

    # /users
    # ------

    @request
    def user_kudosu(self,
        user_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[KudosuHistory]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-kudosu
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[KudosuHistory], f"/users/{user_id}/kudosu",
            params)

    @request
    def user_scores(self,
        user_id: int,
        type_: ScoreTypeT,
        include_fails: Optional[bool] = None,
        mode: Optional[GameModeT] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Score]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-scores
        """
        params = {"include_fails": include_fails, "mode": mode, "limit": limit,
            "offset": offset}
        return self._get(List[Score], f"/users/{user_id}/scores/{type_.value}",
            params)

    @request
    def user_beatmaps(self,
        user_id: int,
        type_: UserBeatmapTypeT,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Union[List[Beatmapset], List[BeatmapPlaycount]]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-beatmaps
        """
        params = {"limit": limit, "offset": offset}

        return_type = List[Beatmapset]
        if type_ is UserBeatmapType.MOST_PLAYED:
            return_type = List[BeatmapPlaycount]

        return self._get(return_type, f"/users/{user_id}/beatmapsets/"
            f"{type_.value}", params)

    @request
    def user_recent_activity(self,
        user_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Event]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-recent-activity
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[_Event], f"/users/{user_id}/recent_activity/",
            params)

    @request
    def user(self,
        user: Union[int, str],
        mode: Optional[GameModeT] = None,
        key: Optional[UserLookupKeyT] = None
    ) -> User:
        """
        https://osu.ppy.sh/docs/index.html#get-user
        """
        params = {"key": key}
        return self._get(User, f"/users/{user}/{mode.value or ''}", params)

    # /wiki
    # -----

    @request
    def wiki_page(self,
        locale: str,
        path: str
    ) -> WikiPage:
        """
        https://osu.ppy.sh/docs/index.html#get-wiki-page
        """
        return self._get(WikiPage, f"/wiki/{locale}/{path}")


    # undocumented
    # ------------

    @request
    def score(self,
        mode: GameModeT,
        score_id: int
    ) -> Score:
        return self._get(Score, f"/scores/{mode.value}/{score_id}")

    @request
    def download_score(self,
        mode: GameModeT,
        score_id: int
    ) -> str:
        r = self.session.get(f"{self.BASE_URL}/scores/{mode.value}/"
            f"{score_id}/download")

        tempfile = NamedTemporaryFile(mode="wb", delete=False)
        with tempfile as f:
            f.write(r.content)

        return tempfile.name

    @request
    def search_beatmaps(self,
        query: Optional[str] = None,
        cursor: Optional[Cursor] = None
    ) -> BeatmapSearchResult:
        # Param key names are the same as https://osu.ppy.sh/beatmapsets,
        # so from eg https://osu.ppy.sh/beatmapsets?q=black&s=any we get that
        # the query uses ``q`` and the category uses ``s``.
        # TODO implement all possible queries, or wait for them to be
        # documented. Currently we only implement the most basic "query" option.
        params = {"cursor": cursor, "q": query}
        return self._get(BeatmapSearchResult, "/beatmapsets/search/", params)

    @request
    def beatmapsets_events(self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        user_id: Optional[int] = None,
        types: Optional[List[BeatmapsetEventTypeT]] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None
    ) -> ModdingHistoryEventsBundle:
        """
        Beatmap history

        https://osu.ppy.sh/beatmapsets/events
        """
        # limit is 5-50
        params = {"limit": limit, "page": page, "user": user_id,
            "min_date": min_date, "max_date": max_date, "types": types}
        return self._get(ModdingHistoryEventsBundle, "/beatmapsets/events",
            params)
