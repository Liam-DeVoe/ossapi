from typing import Union, TypeVar, Optional, List, _GenericAlias
import logging
import webbrowser
import socket
import pickle
from pathlib import Path
from datetime import datetime
from enum import Enum
from urllib.parse import unquote
import inspect
import json
import hashlib
import functools
import sys

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import (BackendApplicationClient, TokenExpiredError,
    AccessDeniedError)
from oauthlib.oauth2.rfc6749.errors import InsufficientScopeError
from oauthlib.oauth2.rfc6749.tokens import OAuth2Token
import osrparse
from typing_utils import issubtype, get_type_hints, get_origin, get_args

from ossapi.models import (Beatmap, BeatmapCompact, BeatmapUserScore,
    ForumTopicAndPosts, Search, CommentBundle, Cursor, Score,
    BeatmapsetSearchResult, ModdingHistoryEventsBundle, User, Rankings,
    BeatmapScores, KudosuHistory, Beatmapset, BeatmapPlaycount, Spotlight,
    Spotlights, WikiPage, _Event, Event, BeatmapsetDiscussionPosts, Build,
    ChangelogListing, MultiplayerScores,
    BeatmapsetDiscussionVotes, CreatePMResponse, BeatmapsetDiscussions,
    UserCompact, NewsListing, NewsPost, SeasonalBackgrounds, BeatmapsetCompact,
    BeatmapUserScores, DifficultyAttributes, Users, Beatmaps,
    CreateForumTopicResponse, ForumPoll, ForumPost, ForumTopic, Room,
    RoomLeaderboard, Matches, Match, MatchResponse, ChatChannel)
from ossapi.enums import (GameMode, ScoreType, RankingFilter, RankingType,
    UserBeatmapType, BeatmapDiscussionPostSort, UserLookupKey,
    BeatmapsetEventType, CommentableType, CommentSort, ForumTopicSort,
    SearchMode, MultiplayerScoresSort, BeatmapsetDiscussionVote,
    BeatmapsetDiscussionVoteSort, BeatmapsetStatus, MessageType,
    BeatmapsetSearchCategory, BeatmapsetSearchMode,
    BeatmapsetSearchExplicitContent, BeatmapsetSearchGenre,
    BeatmapsetSearchLanguage, NewsPostKey, BeatmapsetSearchSort, RoomSearchType,
    ChangelogMessageFormat)
from ossapi.utils import (is_compatible_type, is_primitive_type, is_optional,
    is_base_model_type, is_model_type, is_high_model_type, Field)
from ossapi.mod import Mod
from ossapi.replay import Replay

# our `request` function below relies on the ordering of these types. The
# base type must come first, with any auxiliary types that the base type accepts
# coming after.
# These types are intended to provide better type hinting for consumers. We
# want to support the ability to pass `"osu"` instead of `GameMode.STD`,
# for instance. We automatically convert any value to its base class if the
# relevant parameter has a type hint of the form below (see `request` for
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
CommentableTypeT = Union[CommentableType, str]
CommentSortT = Union[CommentSort, str]
ForumTopicSortT = Union[ForumTopicSort, str]
SearchModeT = Union[SearchMode, str]
MultiplayerScoresSortT = Union[MultiplayerScoresSort, str]
BeatmapsetDiscussionVoteT = Union[BeatmapsetDiscussionVote, int]
BeatmapsetDiscussionVoteSortT = Union[BeatmapsetDiscussionVoteSort, str]
MessageTypeT = Union[MessageType, str]
BeatmapsetStatusT = Union[BeatmapsetStatus, str]
BeatmapsetSearchCategoryT = Union[BeatmapsetSearchCategory, str]
BeatmapsetSearchModeT = Union[BeatmapsetSearchMode, int]
BeatmapsetSearchExplicitContentT = Union[BeatmapsetSearchExplicitContent, str]
BeatmapsetSearchGenreT = Union[BeatmapsetSearchGenre, int]
BeatmapsetSearchLanguageT = Union[BeatmapsetSearchLanguage, str]
NewsPostKeyT = Union[NewsPostKey, str]
BeatmapsetSearchSortT = Union[BeatmapsetSearchSort, str]
RoomSearchTypeT = Union[RoomSearchType, str]

BeatmapIdT = Union[int, BeatmapCompact]
UserIdT = Union[int, UserCompact]
BeatmapsetIdT = Union[int, BeatmapCompact, BeatmapsetCompact]
RoomIdT = Union[int, Room]
MatchIdT = Union[int, Match]

def request(scope, *, requires_user=False, category):
    """
    Handles various validation and preparation tasks for any endpoint request
    method.

    This method does the following things:
    * makes sure the client has the requuired scope to access the endpoint in
      question
    * makes sure the client has the right grant to access the endpoint in
      question (the client credentials grant cannot access endpoints which
      require the user to be "logged in", such as downloading a replay)
    * converts parameters to an instance of a base model if the parameter is
      annotated as being a base model. This means, for instance, that a function
      with an argument annotated as ``ModT`` (``Union[Mod, str, int, list]``)
      will have the value of that parameter automatically converted to a
      ``Mod``, even if the user passes a `str`.
    * converts arguments of type ``BeatmapIdT`` or ``UserIdT`` into a beatmap or
      user id, if the passed argument was a ``BeatmapCompact`` or
      ``UserCompact`` respectively.

    Parameters
    ----------
    scope: Scope
        The scope required for this endpoint. If ``None``, no scope is required
        and any authenticated cliient can access it.
    requires_user: bool
        Whether this endpoint requires a user to be associated with the grant.
        Currently, only authtorization code grants can access these endpoints.
    category: str
        What category of endpoints this endpoint belongs to. Used for grouping
        in the docs.
    """
    def decorator(function):
        instantiate = {}
        for name, type_ in function.__annotations__.items():
            origin = get_origin(type_)
            args = get_args(type_)
            if origin is Union and is_base_model_type(args[0]):
                instantiate[name] = type_

        arg_names = list(inspect.signature(function).parameters)

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            self = args[0]
            if scope is not None and scope not in self.scopes:
                raise InsufficientScopeError(f"A scope of {scope} is required "
                    "for this endpoint. Your client's current scopes are "
                    f"{self.scopes}")

            if requires_user and self.grant is Grant.CLIENT_CREDENTIALS:
                raise AccessDeniedError("To access this endpoint you must be "
                    "authorized using the authorization code grant. You are "
                    "currently authorized with the client credentials grant")

            # we may need to edit this later so convert from tuple
            args = list(args)

            def id_from_id_type(arg_name, arg):
                annotations = function.__annotations__
                if arg_name not in annotations:
                    return None
                arg_type = annotations[arg_name]

                if issubtype(BeatmapsetIdT, arg_type):
                    if isinstance(arg, BeatmapCompact):
                        return arg.beatmapset_id
                    if isinstance(arg, BeatmapsetCompact):
                        return arg.id
                elif issubtype(BeatmapIdT, arg_type):
                    if isinstance(arg, BeatmapCompact):
                        return arg.id
                elif issubtype(UserIdT, arg_type):
                    if isinstance(arg, UserCompact):
                        return arg.id
                elif issubtype(RoomIdT, arg_type):
                    if isinstance(arg, Room):
                        return arg.id
                elif issubtype(MatchIdT, arg_type):
                    if isinstance(arg, Match):
                        return arg.id

            # args and kwargs are handled separately, but in a similar fashion.
            # The difference is that for `args` we need to know the name of
            # the argument so we can look up its type hint and see if it's a
            # parameter we need to convert.

            for i, (arg_name, arg) in enumerate(zip(arg_names, args)):
                if arg_name in instantiate:
                    type_ = instantiate[arg_name]
                    # allow users to pass None for optional args. Without this
                    # we would try to instantiate types like `GameMode(None)`
                    # which would error.
                    if is_optional(type_) and arg is None:
                        continue
                    type_ = get_args(type_)[0]
                    args[i] = type_(arg)
                id_ = id_from_id_type(arg_name, arg)
                if id_:
                    args[i] = id_

            for arg_name, arg in kwargs.items():
                if arg_name in instantiate:
                    type_ = instantiate[arg_name]
                    if is_optional(type_) and arg is None:
                        continue
                    type_ = get_args(type_)[0]
                    kwargs[arg_name] = type_(arg)
                id_ = id_from_id_type(arg_name, arg)
                if id_:
                    kwargs[arg_name] = id_

            return function(*args, **kwargs)

        # for docs generation
        wrapper.__ossapi_category__ = category
        wrapper.__ossapi_scope__ = scope

        return wrapper
    return decorator


class Grant(Enum):
    """
    The grant types used by the api.
    """
    CLIENT_CREDENTIALS = "client"
    AUTHORIZATION_CODE = "authorization"

class Scope(Enum):
    """
    The OAuth scopes used by the api.
    """
    CHAT_WRITE = "chat.write"
    DELEGATE = "delegate"
    FORUM_WRITE = "forum.write"
    FRIENDS_READ = "friends.read"
    IDENTIFY = "identify"
    PUBLIC = "public"


class Ossapi:
    """
    A wrapper around osu! api v2. The main entry point for ossapi.

    Parameters
    ----------
    client_id: int
        The id of the client to authenticate with.
    client_secret: str
        The secret of the client to authenticate with.
    redirect_uri: str
        The redirect uri for the client. Must be passed if using the
        authorization code grant. This must exactly match the redirect uri on
        the client's settings page. Additionally, in order for ossapi to receive
        authentication from this redirect uri, it must be a port on localhost.
        So "http://localhost:3914/", "http://localhost:727/", etc are all valid
        redirect uris. You can change your client's redirect uri from its
        settings page.
    scopes: List[str]
        What scopes to request when authenticating.
    grant: Grant or str
        Which oauth grant (aka flow) to use when authenticating with the api.
        The osu api offers the client credentials (pass "client" for this
        parameter) and authorization code (pass "authorization" for this
        parameter) grants.
        |br|
        The authorization code grant requires user interaction to authenticate
        the first time, but grants full access to the api. In contrast, the
        client credentials grant does not require user interaction to
        authenticate, but only grants guest user access to the api. This means
        you will not be able to do things like download replays on the client
        credentials grant.
        |br|
        If not passed, the grant will be automatically inferred as follows: if
        ``redirect_uri`` is passed, use the authorization code grant. If
        ``redirect_uri`` is not passed, use the client credentials grant.
    strict: bool
        Whether to run in "strict" mode. In strict mode, ossapi will raise an
        exception if the api returns an attribute in a response which we didn't
        expect to be there. This is useful for developers which want to catch
        new attributes as they get added. More checks may be added in the future
        for things which developers may want to be aware of, but normal users do
        not want to have an exception raised for.
        |br|
        If you are not a developer, you are very unlikely to want to use this
        parameter.
    token_directory: str
        If passed, the given directory will be used to store and retrieve token
        files instead of locally wherever ossapi is installed. Useful if you
        want more control over token files.
    token_key: str
        If passed, the given key will be used to name the token file instead of
        an automatically generated one. Note that if you pass this, you are
        taking responsibility for making sure it is unique / unused, and also
        for remembering the key you passed if you wish to eg remove the token in
        the future, which requires the key.
    """
    TOKEN_URL = "https://osu.ppy.sh/oauth/token"
    AUTH_CODE_URL = "https://osu.ppy.sh/oauth/authorize"
    BASE_URL = "https://osu.ppy.sh/api/v2"

    def __init__(self,
        client_id: int,
        client_secret: str,
        redirect_uri: Optional[str] = None,
        scopes: List[Union[str, Scope]] = [Scope.PUBLIC],
        *,
        grant: Optional[Union[Grant, str]] = None,
        strict: bool = False,
        token_directory: Optional[str] = None,
        token_key: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        if not grant:
            grant = (Grant.AUTHORIZATION_CODE if redirect_uri else
                Grant.CLIENT_CREDENTIALS)
        grant = Grant(grant)

        self.grant = grant
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = [Scope(scope) for scope in scopes]
        self.strict = strict

        self.log = logging.getLogger(__name__)
        self.token_key = token_key or self.gen_token_key(self.grant,
            self.client_id, self.client_secret, self.scopes)

        # support saving tokens when being run from pyinstaller
        if hasattr(sys, '_MEIPASS') and not token_directory:
            token_directory = sys._MEIPASS # pylint: disable=no-member

        self.token_directory = (
            Path(token_directory) if token_directory else Path(__file__).parent
        )
        self.token_file = self.token_directory / f"{self.token_key}.pickle"

        if self.grant is Grant.CLIENT_CREDENTIALS:
            if self.scopes != [Scope.PUBLIC]:
                raise ValueError(f"`scopes` must be ['public'] if the "
                    f"client credentials grant is used. Got {self.scopes}")

        if self.grant is Grant.AUTHORIZATION_CODE and not self.redirect_uri:
            raise ValueError("`redirect_uri` must be passed if the "
                "authorization code grant is used.")

        token = None
        if access_token is not None:
            # allow refresh_token to be null for the case of client credentials
            # grant from access token, which does not have an associated refresh
            # token.
            params = {
                "token_type": "Bearer",
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            token = OAuth2Token(params)

        self.session = self.authenticate(token=token)

    @staticmethod
    def gen_token_key(grant, client_id, client_secret, scopes):
        """
        The unique key / hash for the given set of parameters. This is intended
        to provide a way to allow multiple OssapiV2's to live at the same time,
        by eg saving their tokens to different files based on their key.

        This function is also deterministic, to eg allow tokens to be reused if
        OssapiV2 is instantiated twice with the same parameters. This avoids the
        need to reauthenticate unless absolutely necessary.
        """
        grant = Grant(grant)
        scopes = [Scope(scope) for scope in scopes]
        m = hashlib.sha256()
        m.update(grant.value.encode("utf-8"))
        m.update(str(client_id).encode("utf-8"))
        m.update(client_secret.encode("utf-8"))
        for scope in scopes:
            m.update(scope.value.encode("utf-8"))
        return m.hexdigest()

    @staticmethod
    def remove_token(key, token_directory=None):
        """
        Removes the token file associated with the given key. If
        ``token_directory`` is passed, looks there for the token file instead of
        locally in ossapi's install site.

        To determine the key associated with a given grant, client_id,
        client_secret, and set of scopes, use ``gen_token_key``.
        """
        token_directory = (
            Path(token_directory) if token_directory else Path(__file__).parent
        )
        token_file = token_directory / f"{key}.pickle"
        token_file.unlink()

    def authenticate(self, token=None):
        """
        Returns a valid OAuth2Session, either from a saved token file associated
        with this OssapiV2's parameters, or from a fresh authentication if no
        such file exists.
        """
        if self.token_file.exists() or token is not None:
            if token is None:
                with open(self.token_file, "rb") as f:
                    token = pickle.load(f)

            if self.grant is Grant.CLIENT_CREDENTIALS:
                return OAuth2Session(self.client_id, token=token)

            if self.grant is Grant.AUTHORIZATION_CODE:
                auto_refresh_kwargs = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
                return OAuth2Session(self.client_id, token=token,
                    redirect_uri=self.redirect_uri,
                    auto_refresh_url=self.TOKEN_URL,
                    auto_refresh_kwargs=auto_refresh_kwargs,
                    token_updater=self._save_token,
                    scope=[scope.value for scope in self.scopes])

        if self.grant is Grant.CLIENT_CREDENTIALS:
            return self._new_client_grant(self.client_id, self.client_secret)

        return self._new_authorization_grant(self.client_id, self.client_secret,
            self.redirect_uri, self.scopes)

    def _new_client_grant(self, client_id, client_secret):
        """
        Authenticates with the api from scratch on the client grant.
        """
        self.log.info("initializing client credentials grant")
        client = BackendApplicationClient(client_id=client_id, scope=["public"])
        session = OAuth2Session(client=client)
        token = session.fetch_token(token_url=self.TOKEN_URL,
            client_id=client_id, client_secret=client_secret)

        self._save_token(token)
        return session

    def _new_authorization_grant(self, client_id, client_secret, redirect_uri,
        scopes):
        """
        Authenticates with the api from scratch on the authorization code grant.
        """
        self.log.info("initializing authorization code")

        auto_refresh_kwargs = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        session = OAuth2Session(client_id, redirect_uri=redirect_uri,
            auto_refresh_url=self.TOKEN_URL,
            auto_refresh_kwargs=auto_refresh_kwargs,
            token_updater=self._save_token,
            scope=[scope.value for scope in scopes])

        authorization_url, _state = (
            session.authorization_url(self.AUTH_CODE_URL)
        )
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
        token = session.fetch_token(self.TOKEN_URL, client_id=client_id,
            client_secret=client_secret, code=code)
        self._save_token(token)

        return session

    def _save_token(self, token):
        """
        Saves the token to this OssapiV2's associated token file.
        """
        self.log.info(f"saving token to {self.token_file}")
        with open(self.token_file, "wb+") as f:
            pickle.dump(token, f)

    def _request(self, type_, method, url, params={}, data={}):
        params = self._format_params(params)
        # also format data for post requests
        data = self._format_params(data)
        try:
            r = self.session.request(method, f"{self.BASE_URL}{url}",
                params=params, data=data)
        except TokenExpiredError:
            # provide "auto refreshing" for client credentials grant. The client
            # grant doesn't actually provide a refresh token, so we can't hook
            # onto OAuth2Session's auto_refresh functionality like we do for the
            # authorization code grant. But we can do something effectively
            # equivalent: whenever we make a request with an expired client
            # grant token, just request a new one.
            if self.grant is not Grant.CLIENT_CREDENTIALS:
                raise
            self.session = self._new_client_grant(self.client_id,
                self.client_secret)
            # redo the request now that we have a valid token
            r = self.session.request(method, f"{self.BASE_URL}{url}",
                params=params, data=data)

        self.log.info(f"made {method} request to {r.request.url}, data {data}")
        json_ = r.json()
        self.log.debug(f"received json: \n{json.dumps(json_, indent=4)}")
        self._check_response(json_, r.url)

        return self._instantiate_type(type_, json_)

    def _check_response(self, json_, url):
        # TODO this should just be `if "error" in json`, but for some reason
        # `self.search_beatmaps` always returns an error in the response...
        # open an issue on osu-web?
        if len(json_) == 1 and "error" in json_:
            raise ValueError(f"api returned an error of `{json_['error']}` for "
                f"a request to {unquote(url)}")

    def _get(self, type_, url, params={}):
        return self._request(type_, "GET", url, params=params)

    def _post(self, type_, url, data={}):
        return self._request(type_, "POST", url, data=data)

    def _put(self, type_, url, data={}):
        return self._request(type_, "PUT", url, data=data)

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
        if isinstance(value, bool):
            return "true" if bool is True else "false"
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
        # why we pass `type(obj)` instead of just `obj`, which would only
        # return annotations for attributes defined in `obj` and not its
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
            # attributes with `None`. We want to skip these, but only if the
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
        # `attr_name` is purely for debugging, it's the name of the attribute
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
        def _check_primitive_type():
            # The osu api occasionally makes attributes optional, so allow null
            # values even for non-optional fields if we're not in
            # strict mode.
            if not self.strict and value is None:
                return
            if not is_compatible_type(value, type_):
                raise TypeError(f"expected type {type_} for value {value}, got "
                    f"type {type(value)}"
                    f" (for attribute: {attr_name})" if attr_name else "")

        if is_primitive_type(type_):
            _check_primitive_type()

        if is_base_model_type(type_):
            self.log.debug(f"instantiating base type {type_}")
            return type_(value)

        if origin is list and (is_model_type(args[0]) or
            isinstance(args[0], TypeVar)):
            assert len(args) == 1
            # check if the list has been instantiated generically; if so,
            # use the concrete type backing the generic type.
            if isinstance(args[0], TypeVar):
                # `__orig_class__` is how we can get the concrete type of
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

        # either we ourself are a model type (eg `Search`), or we are
        # a special indexed type (eg `type_ == SearchResult[UserCompact]`,
        # `origin == UserCompact`). In either case we want to instantiate
        # `type_`.
        if not is_model_type(type_) and not is_model_type(origin):
            return None
        value = self._instantiate(type_, value)
        # we need to resolve the annotations of any nested model types before we
        # set the attribute. This recursion is well-defined because the base
        # case is when `value` has no model types, which will always happen
        # eventually.
        return self._resolve_annotations(value)

    def _instantiate(self, type_, kwargs):
        self.log.debug(f"instantiating type {type_}")

        kwargs = type_.preprocess_data(kwargs)
        override_type = type_.override_class(kwargs)

        type_ = override_type or type_
        signature_type = type_

        # we need a special case to handle when `type_` is a
        # `_GenericAlias`. I don't fully understand why this exception is
        # necessary, and it's likely the result of some error on my part in our
        # type handling code. Nevertheless, until I dig more deeply into it,
        # we need to extract the type to use for the init signature and the type
        # hints from a `_GenericAlias` if we see one, as standard methods
        # won't work.
        try:
            type_hints = get_type_hints(type_)
        except TypeError:
            assert type(type_) is _GenericAlias # pylint: disable=unidiomatic-typecheck

            signature_type = get_origin(type_)
            type_hints = get_type_hints(signature_type)

        field_names = {}
        for name in type_hints:
            # any inherited attributes will be present in the annotations
            # (type_hints) but not actually an attribute of the type. Just skip
            # them for now. TODO I'm pretty sure this is going to cause issues
            # if we ever have a field on a model and then another model
            # inheriting from it; the inheriting model won't have the field
            # picked up here and the override name won't come into play.
            # probably just traverse the mro?
            if not hasattr(type_, name):
                continue
            value = getattr(type_, name)
            if not isinstance(value, Field):
                continue
            if value.name:
                field_names[value.name] = name

        # make a copy so we can modify while iterating
        for key in list(kwargs):
            value = kwargs.pop(key)
            if key in field_names:
                key = field_names[key]
            kwargs[key] = value

        # if we've annotated a class with `Optional[X]`, and the api response
        # didn't return a value for that attribute, pass `None` for that
        # attribute.
        # This is so that we don't have to define a default value of `None`
        # for each optional attribute of our models, since the default will
        # always be `None`.
        for attribute, annotation in type_hints.items():
            if is_optional(annotation):
                if attribute not in kwargs:
                    kwargs[attribute] = None

        # The osu api often adds new fields to various models, and these are not
        # considered breaking changes. To make this a non-breaking change on our
        # end as well, we ignore any unexpected parameters, unless
        # `self.strict` is `True`. This means that consumers using old
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

        for k, v in kwargs.items():
            if k in parameters:
                kwargs_[k] = v
            else:
                if self.strict:
                    raise TypeError(f"unexpected parameter `{k}` for type "
                        f"{type_}")
                self.log.info(f"ignoring unexpected parameter `{k}` from "
                    f"api response for type {type_}")

        # every model gets a special `_api` parameter, which is the
        # `OssapiV2` instance which loaded it (aka us).
        kwargs_["_api"] = self

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

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmap_user_score(self,
        beatmap_id: BeatmapIdT,
        user_id: UserIdT,
        *,
        mode: Optional[GameModeT] = None,
        mods: Optional[ModT] = None
    ) -> BeatmapUserScore:
        """
        Get a user's best score on a beatmap. If you want to retrieve all
        scores, see :meth:`beatmap_user_scores`.

        Parameters
        ----------
        beatmap_id
            The beatmap the score was set on.
        user_id
            The user who set the score.
        mode
            The mode the scores were set on.
        mods
            The mods the score was set with.

        Notes
        -----
        Implements the `User Beatmap Score
        <https://osu.ppy.sh/docs/index.html#get-a-user-beatmap-score>`__
        endpoint.
        """
        params = {"mode": mode, "mods": mods}
        return self._get(BeatmapUserScore,
            f"/beatmaps/{beatmap_id}/scores/users/{user_id}", params)

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmap_user_scores(self,
        beatmap_id: BeatmapIdT,
        user_id: UserIdT,
        *,
        mode: Optional[GameModeT] = None
    ) -> List[BeatmapUserScore]:
        """
        Get all of a user's scores on a beatmap. If you only want the top user
        score, see :meth:`beatmap_user_score`.

        Parameters
        ----------
        beatmap_id
            The beatmap the scores were set on.
        user_id
            The user who set the scores.
        mode
            The mode the scores were set on.

        Notes
        -----
        Implements to `User Beatmap Scores
        <https://osu.ppy.sh/docs/index.html#get-a-user-beatmap-scores>`__
        endpoint.
        """
        params = {"mode": mode}
        scores = self._get(BeatmapUserScores,
            f"/beatmaps/{beatmap_id}/scores/users/{user_id}/all", params)
        return scores.scores

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmap_scores(self,
        beatmap_id: BeatmapIdT,
        *,
        mode: Optional[GameModeT] = None,
        mods: Optional[ModT] = None,
        type: Optional[RankingTypeT] = None
    ) -> BeatmapScores:
        """
        Get the top scores of a beatmap.

        Parameters
        ----------
        beatmap_id
            The beatmap to get scores of.
        mode
            The mode to get scores of.
        mods
            Get the top scores set with exactly these mods, if passed.
        type
            How to order the scores. Defaults to ordering by score.

        Notes
        -----
        Implements the `Get Beatmap Scores
        <https://osu.ppy.sh/docs/index.html#get-beatmap-scores>`__ endpoint.
        """
        params = {"mode": mode, "mods": mods, "type": type}
        return self._get(BeatmapScores, f"/beatmaps/{beatmap_id}/scores",
            params)

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmap(self,
        beatmap_id: Optional[BeatmapIdT] = None,
        *,
        checksum: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Beatmap:
        """
        Get a beatmap from an id, checksum, or filename.

        Parameters
        ----------
        beatmap_id
            The id of the beatmap.
        checksum
            The md5 hash of the beatmap.
        filename
            The filename of the beatmap.

        Notes
        -----
        Combines the
        `Get Beatmap <https://osu.ppy.sh/docs/index.html#get-beatmapL>`_ and
        `Lookup Beatmap <https://osu.ppy.sh/docs/index.html#lookup-beatmap>`_
        endpoints.
        """
        if not (beatmap_id or checksum or filename):
            raise ValueError("at least one of beatmap_id, checksum, or "
                "filename must be passed")
        params = {"checksum": checksum, "filename": filename, "id": beatmap_id}
        return self._get(Beatmap, "/beatmaps/lookup", params)

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmaps(self,
        beatmap_ids: List[BeatmapIdT]
    ) -> List[Beatmap]:
        """
        Batch get beatmaps by id. If you only want to retrieve a single beatmap,
        or want to retrieve beatmaps by something other than id (eg checksum),
        see :meth:`beatmap`.

        Parameters
        ----------
        beatmap_ids
            The beatmaps to get.

        Notes
        -----
        Implements the `Get Beatmaps
        <https://osu.ppy.sh/docs/index.html#get-beatmaps>`__ endpoint.
        """
        params = {"ids": beatmap_ids}
        return self._get(Beatmaps, "/beatmaps", params).beatmaps

    @request(Scope.PUBLIC, category="beatmaps")
    def beatmap_attributes(self,
        beatmap_id: int,
        *,
        mods: Optional[ModT] = None,
        ruleset: Optional[GameModeT] = None,
        ruleset_id: Optional[int] = None
    ) -> DifficultyAttributes:
        """
        Get the difficult attributes of a beatmap. Used for pp calculation.

        Parameters
        ----------
        beatmap_id
            The beatmap to get the difficulty attributes of.
        mods
            The mods to calculate difficulty attributes with.
        ruleset
            The ruleset (gamemode) to calculate difficulty attributes of.
        ruleset_id
            Alternative parameter to ruleset which takes an integer (ruleset id)
            instead of a string (ruleset name).

        Notes
        -----
        Implements the `Get Beatmap Attributes
        <https://osu.ppy.sh/docs/index.html#get-beatmap-attributes>`__ endpoint.
        """
        data = {"mods": mods, "ruleset": ruleset, "ruleset_id": ruleset_id}
        return self._post(DifficultyAttributes,
            f"/beatmaps/{beatmap_id}/attributes", data=data)


    # /beatmapsets
    # ------------

    @request(Scope.PUBLIC, category="beatmapsets")
    def beatmapset_discussion_posts(self,
        beatmapset_discussion_id: Optional[int] = None,
        *,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[BeatmapDiscussionPostSortT] = None,
        user_id: Optional[UserIdT] = None,
        with_deleted: Optional[bool] = None
    ) -> BeatmapsetDiscussionPosts:
        """
        Get the posts of a beatmapset discussion.

        Parameters
        ----------
        beatmapset_discussion_id
            The beatmapset discussion to get the posts of.
        limit
            Maximum number of posts to return.
        page
            Pagination for results.
        sort
            How to sort the posts.
        user_id

        with_deleted
            Whether to include deleted posts. Currently has no effect even if
            you are a gmt/admin.

        Notes
        -----
        Implements the `Get Beatmapset Discussion Posts
        <https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-posts>`__
        endpoint.
        """
        params = {"beatmapset_discussion_id": beatmapset_discussion_id,
            "limit": limit, "page": page, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussionPosts,
            "/beatmapsets/discussions/posts", params)

    @request(Scope.PUBLIC, category="beatmapsets")
    def beatmapset_discussion_votes(self,
        *,
        beatmapset_discussion_id: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        receiver_id: Optional[int] = None,
        vote: Optional[BeatmapsetDiscussionVoteT] = None,
        sort: Optional[BeatmapsetDiscussionVoteSortT] = None,
        user_id: Optional[UserIdT] = None,
        with_deleted: Optional[bool] = None
    ) -> BeatmapsetDiscussionVotes:
        """
        Get beatmapset discussion votes.

        Parameters
        ----------
        beatmapset_discussion_id
            Filter by a beatmapset discussion.
        limit
            Maximum number of votes to return.
        page
            Pagination for results.
        receiver_id
            Filter by the user receiving the votes.
        vote
            Specify to return either only upvotes or only downvotes.
        sort
            How to sort the votes.
        user_id
            Filter by the user giving the votes.
        with_deleted
            Whether to include deleted posts. Currently has no effect even if
            you are a gmt/admin.

        Notes
        -----
        Implements the `Get Beatmapset Discussion Posts
        <https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-posts>`__
        endpoint.
        """
        params = {"beatmapset_discussion_id": beatmapset_discussion_id,
            "limit": limit, "page": page, "receiver": receiver_id,
            "score": vote, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussionVotes,
            "/beatmapsets/discussions/votes", params)

    @request(Scope.PUBLIC, category="beatmapsets")
    def beatmapset_discussions(self,
        *,
        beatmapset_id: Optional[BeatmapsetIdT] = None,
        beatmap_id: Optional[BeatmapIdT] = None,
        beatmapset_status: Optional[BeatmapsetStatusT] = None,
        limit: Optional[int] = None,
        message_types: Optional[List[MessageTypeT]] = None,
        only_unresolved: Optional[bool] = None,
        page: Optional[int] = None,
        sort: Optional[BeatmapDiscussionPostSortT] = None,
        user_id: Optional[UserIdT] = None,
        with_deleted: Optional[bool] = None,
    ) -> BeatmapsetDiscussions:
        """
        Get beatmapset discussions.

        Parameters
        ----------
        beatmapset_id
            Filter by a beatmapset.
        beatmap_id
            Filter by a beatmap.
        beatmapset_status
            Filter by a category of beatmapsets.
        limit
            Maximum number of discussions to return.
        message_types
            Filter by a discussion message type.
        only_unresolved
            ``True`` to only show unresolved issues. Defaults to ``False``.
        page
            Pagination for results.
        sort
            How to sort the discussions.
        user
            Filter by poster id.
        with_deleted
            Whether to include deleted posts. Currently has no effect even if
            you are a gmt/admin.

        Notes
        -----
        Implements the `Get Beatmapset Discussion Posts
        <https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-posts>`__
        endpoint.
        """
        params = {"beatmapset_id": beatmapset_id, "beatmap_id": beatmap_id,
            "beatmapset_status": beatmapset_status, "limit": limit,
            "message_types": message_types, "only_unresolved": only_unresolved,
            "page": page, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussions,
            "/beatmapsets/discussions", params)

    @request(Scope.PUBLIC, category="beatmapsets")
    def search_beatmapsets(self,
        query: Optional[str] = None,
        *,
        mode: BeatmapsetSearchModeT = BeatmapsetSearchMode.ANY,
        category: BeatmapsetSearchCategoryT =
            BeatmapsetSearchCategory.HAS_LEADERBOARD,
        explicit_content: BeatmapsetSearchExplicitContentT =
            BeatmapsetSearchExplicitContent.HIDE,
        genre: BeatmapsetSearchGenreT = BeatmapsetSearchGenre.ANY,
        language: BeatmapsetSearchLanguageT = BeatmapsetSearchLanguage.ANY,
        # "Extra"
        force_video: bool = False,
        force_storyboard: bool = False,
        # "General"
        force_recommended_difficulty: bool = False,
        include_converts: bool = False,
        force_followed_mappers: bool = False,
        force_spotlights: bool = False,
        force_featured_artists: bool = False,
        cursor: Optional[Cursor] = None,
        sort: Optional[BeatmapsetSearchSortT] = None
    ) -> BeatmapsetSearchResult:
        """
        Search beatmapsets. Equivalent to the beatmapset search page on the
        website (https://osu.ppy.sh/beatmapsets).

        Parameters
        ----------
        query
            The search query. Can include filters like ``ranked<2019``.
        mode
            Filter by mode.
        category
            Filter by category.
        explicit_content
            Whether to include beatmaps with explicit content.
        genre
            Filter by genre.
        language
            Filter by language.
        force_video
            ``True`` to only return beatmapsets with videos.
        force_storyboard
            ``True`` to only return beatmapsets with storyboards.
        force_recommended_difficulty
            ``True`` to filter by recommended difficulty.
        include_converts
            ``True`` to include converted beatmapsets.
        force_followed_mappers
            ``True`` to only return beatmapsets by mappers you follow.
        force_spotlights
            ``True`` to only return beatmapsets which have been in a spotlight.
        force_featured_artists
            ``True`` to only return beatmapsets by a featured artist.
        cursor
            Cursor for pagination.
        sort
            How to sort the beatmapsets.

        Notes
        -----
        Implements the `Search Beatmapsets
        <https://osu.ppy.sh/docs/index.html#beatmapsetssearchfilters>`__
        endpoint.
        """
        # Param key names are the same as https://osu.ppy.sh/beatmapsets,
        # so from eg https://osu.ppy.sh/beatmapsets?q=black&s=any we get that
        # the query uses `q` and the category uses `s`.

        explicit_content = {
            BeatmapsetSearchExplicitContent.SHOW: "true",
            BeatmapsetSearchExplicitContent.HIDE: "false",
        }[explicit_content]

        extras = []
        if force_video:
            extras.append("video")
        if force_storyboard:
            extras.append("storyboard")
        extra = ".".join(extras)

        generals = []
        if force_recommended_difficulty:
            generals.append("recommended")
        if include_converts:
            generals.append("converts")
        if force_followed_mappers:
            generals.append("follows")
        if force_spotlights:
            generals.append("spotlights")
        if force_featured_artists:
            generals.append("featured_artists")
        general = ".".join(generals)

        params = {"cursor": cursor, "q": query, "s": category, "m": mode,
            "g": genre, "l": language, "nsfw": explicit_content, "e": extra,
            "c": general, "sort": sort}

        # BeatmapsetSearchGenre.ANY is the default and doesn't have a correct
        # corresponding value
        if genre is BeatmapsetSearchGenre.ANY:
            del params["g"]

        # same for BeatmapsetSearchLanguage.ANY
        if language is BeatmapsetSearchLanguage.ANY:
            del params["l"]

        return self._get(BeatmapsetSearchResult, "/beatmapsets/search/", params)

    @request(Scope.PUBLIC, category="beatmapsets")
    def beatmapset(self,
        beatmapset_id: Optional[BeatmapsetIdT] = None,
        *,
        beatmap_id: Optional[BeatmapIdT] = None
    ) -> Beatmapset:
        """
        Get a beatmapset from a beatmapset id or a beatmap id.

        Parameters
        ----------
        beatmapset_id
            The beatmapset to get.
        beatmap_id
            Get the beatmapset associated with this beatmap.

        Notes
        -----
        Combines the `Get Beatmapset
        <https://osu.ppy.sh/docs/index.html#beatmapsetsbeatmapset>`__ and
        `Beatmapset Lookup
        <https://osu.ppy.sh/docs/index.html#beatmapsetslookup>`__ endpoints.
        """
        if not bool(beatmap_id) ^ bool(beatmapset_id):
            raise ValueError("exactly one of beatmap_id and beatmapset_id must "
                "be passed.")
        if beatmap_id:
            params = {"beatmap_id": beatmap_id}
            return self._get(Beatmapset, "/beatmapsets/lookup", params)
        return self._get(Beatmapset, f"/beatmapsets/{beatmapset_id}")

    @request(Scope.PUBLIC, category="beatmapsets")
    def beatmapset_events(self,
        *,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        user_id: Optional[UserIdT] = None,
        types: Optional[List[BeatmapsetEventTypeT]] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None
    ) -> ModdingHistoryEventsBundle:
        """
        Get beatmapset events. Equivalent to the events search page on the
        website (https://osu.ppy.sh/beatmapsets/events).

        Parameters
        ----------
        limit
            Maximum number of events to return.
        page
            Pagination for events.
        user_id
            Filter by event author.
        types
            Filter by event type.
        min_date
            Filter by event date.
        max_date
            Filter by event date.

        Notes
        -----
        Implements the `Beatmapset Events
        <https://osu.ppy.sh/docs/index.html#beatmapsetsevents>`__ endpoint.
        """
        # limit is 5-50
        params = {"limit": limit, "page": page, "user": user_id,
            "min_date": min_date, "max_date": max_date, "types": types}
        return self._get(ModdingHistoryEventsBundle, "/beatmapsets/events",
            params)


    # /changelog
    # ----------

    @request(scope=None, category="changelog")
    def changelog_build(self,
        stream: str,
        build: str
    ) -> Build:
        """
        Get changelog build details.

        Parameters
        ----------
        stream
            The changelog stream name (eg ``stable40``).
        build
            The changelog build name (eg ``20230121.1``)

        Notes
        -----
        Implements the `Get Changelog Build
        <https://osu.ppy.sh/docs/index.html#get-changelog-build>`__ endpoint.
        """
        return self._get(Build, f"/changelog/{stream}/{build}")

    @request(scope=None, category="changelog")
    def changelog_listing(self,
        *,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        max_id: Optional[int] = None,
        stream: Optional[str] = None,
        message_formats: List[ChangelogMessageFormat] =
            [ChangelogMessageFormat.HTML, ChangelogMessageFormat.MARKDOWN]
    ) -> ChangelogListing:
        """
        Get list of changelogs.

        Parameters
        ----------
        from_
            Minimum build version.
        to
            Maximum build version.
        max_id
            Maximum build id.
        stream
            Filter changelogs by stream.
        message_formats
            Format to return text of changelog entries in.

        Notes
        -----
        Implements the `Get Changelog Listing
        <https://osu.ppy.sh/docs/index.html#get-changelog-listing>`__ endpoint.
        """
        params = {"from": from_, "to": to, "max_id": max_id, "stream": stream,
            "message_formats": message_formats}
        return self._get(ChangelogListing, "/changelog", params)

    # TODO can almost certainly be combined with changelog_build endpoint, in
    # line with other get/lookup endpoint combinations (beatmap, beatmapset)
    @request(scope=None, category="changelog")
    def changelog_build_lookup(self,
        changelog: str,
        *,
        key: Optional[str] = None,
        message_formats: List[ChangelogMessageFormat] =
            [ChangelogMessageFormat.HTML, ChangelogMessageFormat.MARKDOWN]
    ) -> Build:
        """
        Look up a changelog build by version, update stream name, or id.

        Parameters
        ----------
        changelog
            Build version, update stream name, or build id.
        key
            Unset to query by build version or stream name, or ``id`` to query
            by build id.
        message_formats
            Format to return text of changelog entries in.

        Notes
        -----
        Implements the `Lookup Changelog Build
        <https://osu.ppy.sh/docs/index.html#lookup-changelog-build>`__ endpoint.

        """
        params = {"key": key, "message_formats": message_formats}
        return self._get(Build, f"/changelog/{changelog}", params)


    # /chat
    # -----

    @request(Scope.CHAT_WRITE, category="chat")
    def send_pm(self,
        user_id: UserIdT,
        message: str,
        *,
        is_action: Optional[bool] = False
    ) -> CreatePMResponse:
        """
        Send a pm to a user.

        Parameters
        ----------
        user_id
            The user to send a message to.
        message
            The message to send.
        is_action

        Notes
        -----
        Implements the `Create New PM
        <https://osu.ppy.sh/docs/index.html#create-new-pm>`__ endpoint.
        """
        data = {"target_id": user_id, "message": message,
            "is_action": is_action}
        return self._post(CreatePMResponse, "/chat/new", data=data)

    # this method requires a user in the announce group, so I've never tested
    # it.
    @request(Scope.CHAT_WRITE, category="chat")
    def send_announcement(self,
        channel_name: str,
        channel_description: str,
        message: str,
        # TODO need to add support to automatic conversion for lists of id types
        # instead of just bare types (: UserIdT)
        target_ids: List[UserIdT],
    ) -> ChatChannel:
        """
        Send an announcement message. You must be in the announce usergroup to
        use this endpoint (and if you don't know what that is, then you aren't
        in it).

        If you want to send a normal pm, see :meth:`send_pm`.

        Parameters
        ----------
        channel_name
            The name of the announce channel that will be created.
        channel_description
            The description of the announce channel that will be created.
        message
            The message to send.
        target_ids
            The users to send the message to.

        Notes
        -----
        Implements the `Create Channel
        <https://osu.ppy.sh/docs/index.html#create-channel>`__ endpoint.

        Warnings
        --------
        I don't have an account in the announce usergroup, so I've never tested
        this endpoint. If it breaks for you, please open an issue on github or
        dm me on discord (tybug#8490)!
        """
        data = {
            "channel.name": channel_name,
            "channel.description": channel_description,
            "message": message,
            "target_ids": target_ids,
            "type": "ANNOUNCE"
        }
        return self._post(ChatChannel, "/chat/channels", data=data)


    # /comments
    # ---------

    @request(Scope.PUBLIC, category="comments")
    def comments(self,
        *,
        commentable_type: Optional[CommentableTypeT] = None,
        commentable_id: Optional[int] = None,
        cursor: Optional[Cursor] = None,
        parent_id: Optional[int] = None,
        sort: Optional[CommentSortT] = None
    ) -> CommentBundle:
        """
        Get comments and their replies (up to 2 levels deep). If you only want
        to retrieve a single comment, see :meth:`comment`.

        Parameters
        ----------
        commentable_type
            The type of resource to get comments for.
        commentable_id
            The id of the resource to get comments for.
        cursor
            Cursor for pagination.
        parent_id
            Filter by id of the parent comment.
        sort
            How to sort the comments. Defaults to ``new`` for guest account and
            the user-specified default when authenticated.

        Notes
        -----
        Implements the `Get Comments
        <https://osu.ppy.sh/docs/index.html#get-comments>`__ endpoint.
        """
        params = {"commentable_type": commentable_type,
            "commentable_id": commentable_id, "cursor": cursor,
            "parent_id": parent_id, "sort": sort}
        return self._get(CommentBundle, "/comments", params)

    @request(scope=None, category="comments")
    def comment(self,
        comment_id: int
    ) -> CommentBundle:
        """
        Get a comment and its replies (up to 2 levels deep).

        Parameters
        ----------
        comment_id
            The comment to get.

        Notes
        -----
        Implements the `Get a Comment
        <https://osu.ppy.sh/docs/index.html#get-a-comment>`__ endpoint.
        """
        return self._get(CommentBundle, f"/comments/{comment_id}")


    # /forums
    # -------

    @request(Scope.FORUM_WRITE, category="forums")
    def forum_create_topic(self,
       forum_id: int,
       title: str,
       body: str,
       *,
       poll: Optional[ForumPoll] = None,
   ) -> CreateForumTopicResponse:
        """
        https://osu.ppy.sh/docs/index.html#create-topic
        """
        data = {
            "body": body,
            "forum_id": forum_id,
            "title": title,
        }
        if poll:
            data["with_poll"] = True
            data["forum_topic_poll[hide_results]"] = poll.hide_results
            data["forum_topic_poll[length_days]"] = poll.length_days
            data["forum_topic_poll[max_options]"] = poll.max_options
            data["forum_topic_poll[options]"] = "\r\n".join(poll.options)
            data["forum_topic_poll[title]"] = poll.title
            data["forum_topic_poll[vote_change]"] = poll.vote_change

        return self._post(CreateForumTopicResponse, "/forums/topics", data=data)

    @request(Scope.FORUM_WRITE, category="forums")
    def forum_reply(self, topic_id: int, body: str) -> ForumPost:
        """
        Reply to a forum topic.

        Parameters
        ----------
        topic_id
            The topic to reply to.
        body
            Content of the reply.

        Notes
        -----
        Implements the `Reply Topic
        <https://osu.ppy.sh/docs/index.html#reply-topic>`__ endpoint.
        """
        data = {"body": body}
        return self._post(ForumPost, f"/forums/topics/{topic_id}/reply", data)

    @request(Scope.FORUM_WRITE, category="forums")
    def forum_edit_topic(self, topic_id: int, title: str) -> ForumTopic:
        """
        Edit a forum topic.

        Parameters
        ---------
        topic_id
            The topic to edit.
        title
            The new title of the topic.

        Notes
        -----
        Implements the `Edit Topic
        <https://osu.ppy.sh/docs/index.html#edit-topic>`__ endpoint.
        """
        data = {"forum_topic[topic_title]": title}
        return self._put(ForumTopic, f"/forums/topics/{topic_id}", data)

    @request(Scope.FORUM_WRITE, category="forums")
    def forum_edit_post(self, post_id: int, body: str) -> ForumPost:
        """
        Edit a forum post.

        Parameters
        ----------
        post_id
            The post to edit.
        body
            The new content of the post.

        Notes
        -----
        Implements the `Edit Post
        <https://osu.ppy.sh/docs/index.html#edit-post>`__ endpoint.
        """
        data = {"body": body}
        return self._put(ForumPost, f"/forums/posts/{post_id}", data)

    @request(Scope.PUBLIC, category="forums")
    def forum_topic(self,
        topic_id: int,
        *,
        cursor_string: Optional[str] = None,
        sort: Optional[ForumTopicSortT] = None,
        limit: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> ForumTopicAndPosts:
        """
        Get a forum topic and its posts.

        Parameters
        ----------
        topic_id
            The topic to get.
        cursor_string
            Cursor for pagination.
        sort
            How to sort the posts.
        limit
            Maximum number of posts to return.
        start
            First post id to be returned when ``sort`` is
            :data:`ForumTopicSort.NEW <ossapi.enums.ForumTopicSort.NEW>`.
            Ignored otherwise.
        end
            First post id to be returned when ``sort`` is
            :data:`ForumTopicSort.OLD <ossapi.enums.ForumTopicSort.OLD>`.
            Ignored otherwise.

        Notes
        -----
        Implements the `Get Topic and Posts
        <https://osu.ppy.sh/docs/index.html#get-topic-and-posts>`__ endpoint.
        """
        params = {"cursor_string": cursor_string, "sort": sort, "limit": limit,
            "start": start, "end": end}
        return self._get(ForumTopicAndPosts, f"/forums/topics/{topic_id}",
            params)


    # /friends
    # --------

    @request(Scope.FRIENDS_READ, category="friends")
    def friends(self) -> List[UserCompact]:
        """
        Get the friends of the authenticated user.

        Notes
        -----
        Implements the `Get Friends
        <https://osu.ppy.sh/docs/index.html#friends>`__ endpoint.
        """
        return self._get(List[UserCompact], "/friends")


    # / ("home")
    # ----------

    @request(Scope.PUBLIC, category="home")
    def search(self,
        query: str,
        *,
        mode: Optional[SearchModeT] = None,
        page: Optional[int] = None
    ) -> Search:
        """
        Search users and wiki pages. If you want to search beatmapsets, see
        :meth:`search_beatmapsets`.

        Parameters
        ----------
        query
            Search query.
        mode
            Filter results by type (forum, wiki, player, etc.).
        page
            Pagination for results.

        Notes
        -----
        Implements the `Search
        <https://osu.ppy.sh/docs/index.html#search>`__ endpoint.
        """
        params = {"mode": mode, "query": query, "page": page}
        return self._get(Search, "/search", params)


    # /matches
    # --------

    @request(Scope.PUBLIC, category="matches")
    def matches(self) -> Matches:
        """
        Get current matches. If you want to get a specific match, see
        :meth:`match`.

        Notes
        -----
        Implements the `Get Matches
        <https://osu.ppy.sh/docs/index.html#matches>`__ endpoint.
        """
        return self._get(Matches, "/matches")

    @request(Scope.PUBLIC, category="matches")
    def match(self, match_id: MatchIdT) -> MatchResponse:
        """
        Get a match (eg https://osu.ppy.sh/community/matches/97947404).

        Parameters
        ----------
        match_id
            The match to get.

        Notes
        -----
        Implements the `Get Match
        <https://osu.ppy.sh/docs/index.html#matchesmatch>`__ endpoint.
        """
        return self._get(MatchResponse, f"/matches/{match_id}")


    # /me
    # ---

    @request(Scope.IDENTIFY, category="me")
    def get_me(self,
        mode: Optional[GameModeT] = None
    ):
        """
        Get data about the authenticated user.

        Parameters
        ----------
        mode
            Get data about the specified mode. Defaults to the user's default
            mode.

        Notes
        -----
        Implements the `Get Own Data
        <https://osu.ppy.sh/docs/index.html#get-own-data>`__ endpoint.
        """
        return self._get(User, f"/me/{mode.value if mode else ''}")


    # /news
    # -----

    @request(scope=None, category="news")
    def news_listing(self,
        *,
        limit: Optional[int] = None,
        year: Optional[int] = None,
        cursor_string: Optional[str] = None
    ) -> NewsListing:
        """
        Get news posts.

        Parameters
        ----------
        limit
            Maximum number of news posts to return.
        year
            Filter by year the news post was created.
        cursor_string
            Cursor for pagination.

        Notes
        -----
        Implements the `Get News Listing
        <https://osu.ppy.sh/docs/index.html#get-news-listing>`__ endpoint.
        """
        params = {"limit": limit, "year": year, "cursor_string": cursor_string}
        return self._get(NewsListing, "/news", params=params)

    @request(scope=None, category="news")
    def news_post(self,
        news: str,
        *,
        key: Optional[NewsPostKeyT] = NewsPostKey.SLUG
    ) -> NewsPost:
        """
        Get a news post by id or slug.

        Parameters
        ----------
        news
            The id or slug of the news post.
        key
            Whether to query by id or slug.

        Notes
        -----
        Implements the `Get News Post
        <https://osu.ppy.sh/docs/index.html#get-news-post>`__ endpoint.
        """
        # docs state key should be "unset to query by slug"
        if key is NewsPostKey.SLUG:
            key = None
        params = {"key": key}
        return self._get(NewsPost, f"/news/{news}", params=params)


    # /oauth
    # ------

    @request(scope=None, category="oauth")
    def revoke_token(self):
        """
        Revoke the current token. This will remove any authentication and leave
        you unable to make any more api calls until you re-authenticate.

        Notes
        -----
        Implements the `Revoke Current Token
        <https://osu.ppy.sh/docs/index.html#revoke-current-token>`__ endpoint.
        """
        self.session.delete(f"{self.BASE_URL}/oauth/tokens/current")
        self.remove_token(self.token_key, self.token_directory)


    # /rankings
    # ---------

    @request(Scope.PUBLIC, category="rankings")
    def ranking(self,
        mode: GameModeT,
        type: RankingTypeT,
        *,
        country: Optional[str] = None,
        cursor: Optional[Cursor] = None,
        filter_: RankingFilterT = RankingFilter.ALL,
        spotlight: Optional[int] = None,
        variant: Optional[str] = None
    ) -> Rankings:
        """
        Get current rankings for the specified game mode. Can specify ``type_``
        to get different types of rankings (performance, score, country, etc).

        Parameters
        ----------
        mode
            The mode to get rankings for.
        type
            The type of ranking to get.
        country
            Filter ranking by 2 letter country code. Only available for
            ``RankingType.PERFORMANCE``.
        cursor
            Cursor for pagination.
        filter_
            Filter ranking by specified filter.
        spotlight
            The id of the spotlight to return rankings for. Ranking for latest
            spotlight will be returned if not specified. Only available for
            ``RankingType.SPOTLIGHT``.
        variant
            Filter ranking by game mode variant. Either ``4k`` or ``7k`` for
            mania. Only available for ``RankingType.PERFORMANCE``.

        Notes
        -----
        Implements the `Get Ranking
        <https://osu.ppy.sh/docs/index.html#get-ranking>`__ endpoint.
        """
        params = {"country": country, "cursor": cursor, "filter": filter_,
            "spotlight": spotlight, "variant": variant}
        return self._get(Rankings, f"/rankings/{mode.value}/{type.value}",
            params=params)


    # /rooms
    # ------

    # TODO add test for this once I figure out values for room_id and
    # playlist_id that actually produce a response lol
    @request(Scope.PUBLIC, category="rooms")
    def multiplayer_scores(self,
        room_id: int,
        playlist_id: int,
        *,
        limit: Optional[int] = None,
        sort: Optional[MultiplayerScoresSortT] = None,
        cursor_string: Optional[str] = None
    ) -> MultiplayerScores:
        """
        Get scores on a playlist item in a room.

        Parameters
        ----------
        room_id
            The room to get the scores from.
        playlist_id
            The playlist to get the scores from.
        limit
            Maximum number of scores to get.
        sort
            How to sort the scores.
        cursor_string
            Cursor for pagination.

        Notes
        -----
        Implements the `Get Scores
        <https://osu.ppy.sh/docs/index.html#get-scores>`__ endpoint.
        """
        params = {"limit": limit, "sort": sort, "cursor_string": cursor_string}
        return self._get(MultiplayerScores,
            f"/rooms/{room_id}/playlist/{playlist_id}/scores", params=params)

    @request(Scope.PUBLIC, category="rooms")
    def room(self, room_id: RoomIdT) -> Room:
        """
        Get a room.

        Parameters
        ----------
        room_id
            The room to get.

        Notes
        -----
        Implements the `Get Room
        <https://osu.ppy.sh/docs/index.html#roomsroom>`__ endpoint.
        """
        return self._get(Room, f"/rooms/{room_id}")

    @request(Scope.PUBLIC, requires_user=True, category="rooms")
    def room_leaderboard(self, room_id: RoomIdT) -> RoomLeaderboard:
        """
        Get the leaderboard of a room.

        Parameters
        ----------
        room_id
            The room to get the leaderboard of.

        Notes
        -----
        Implements the `Get Room Leaderboard
        <https://osu.ppy.sh/docs/index.html#roomsroomleaderboard>`__ endpoint.
        """
        return self._get(RoomLeaderboard, f"/rooms/{room_id}/leaderboard")

    @request(Scope.PUBLIC, requires_user=True, category="rooms")
    def rooms(self, type: Optional[RoomSearchTypeT] = None) -> List[Room]:
        """
        Get the list of current rooms.

        Parameters
        ----------
        type
            Filter by room type. Default to all rooms.

        Notes
        -----
        Implements the `Get Rooms
        <https://osu.ppy.sh/docs/index.html#roomsmode>`__ endpoint.
        """
        return self._get(List[Room], f"/rooms/{type.value if type else ''}")


    # /scores
    # -------

    @request(Scope.PUBLIC, category="scores")
    def score(self,
        mode: GameModeT,
        score_id: int
    ) -> Score:
        """
        Get a score.

        Parameters
        ----------
        mode
            The mode the score was set on.
        score_id
            The score to get.

        Notes
        -----
        Implements the `Get Score
        <https://osu.ppy.sh/docs/index.html#scoresmodescore>`__ endpoint.
        """
        return self._get(Score, f"/scores/{mode.value}/{score_id}")

    @request(Scope.PUBLIC, requires_user=True, category="scores")
    def download_score(self,
        mode: GameModeT,
        score_id: int,
        *,
        raw: bool = False
    ) -> Replay:
        """
        Download the replay data of a score.

        Parameters
        ----------
        mode
            The mode of the score to download.
        score_id
            The score to download.
        raw
            If ``True``, will return the raw string response from the api
            instead of a :class:`~ossapi.replay.Replay` object.

        Notes
        -----
        Implements the `Download Score
        <https://osu.ppy.sh/docs/index.html#scoresmodescoredownload>`__
        endpoint.
        """
        url = f"{self.BASE_URL}/scores/{mode.value}/{score_id}/download"
        r = self.session.get(url)

        # if the response above succeeded, it will return a raw string
        # instead of json. If it didn't succeed, it will return json with an
        # error.
        # So always try parsing as json to check if there's an error. If parsin
        # fails, just assume the request succeeded and move on.
        try:
            json_ = r.json()
            self._check_response(json_, url)
        except json.JSONDecodeError:
            pass

        if raw:
            return r.content

        replay = osrparse.Replay.from_string(r.content)
        return Replay(replay, self)


    # seasonal backgrounds
    # --------------------

    @request(scope=None, category="seasonal backgrounds")
    def seasonal_backgrounds(self) -> SeasonalBackgrounds:
        """
        Get current seasonal backgrounds.

        Notes
        -----
        Implements the `Seasonal Backgrounds
        <https://osu.ppy.sh/docs/index.html#seasonal-backgrounds>`__ endpoint.
        """
        return self._get(SeasonalBackgrounds, "/seasonal-backgrounds")


    # /spotlights
    # -----------

    @request(Scope.PUBLIC, category="spotlights")
    def spotlights(self) -> List[Spotlight]:
        """
        Get active spotlights.

        Notes
        -----
        Implements the `Get Spotlights
        <https://osu.ppy.sh/docs/index.html#get-spotlights>`__ endpoint.
        """
        spotlights = self._get(Spotlights, "/spotlights")
        return spotlights.spotlights


    # /users
    # ------

    @request(Scope.PUBLIC, category="users")
    def user_kudosu(self,
        user_id: UserIdT,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[KudosuHistory]:
        """
        Get user kudosu history.

        Parameters
        ----------
        user_id
            User to get kudosu history of.
        limit
            Maximum number of history events to return.
        offset
            Offset for pagination.

        Notes
        -----
        Implements the `Get User Kudosu
        <https://osu.ppy.sh/docs/index.html#get-user-kudosu>`__ endpoint.
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[KudosuHistory], f"/users/{user_id}/kudosu",
            params)

    @request(Scope.PUBLIC, category="users")
    def user_scores(self,
        user_id: UserIdT,
        type: ScoreTypeT,
        *,
        include_fails: Optional[bool] = None,
        mode: Optional[GameModeT] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Score]:
        """
        Get scores of a user.

        user_id
            The user to get scores of.
        type
            Type of score to get.
        include_fails
            Whether to include failed scores.
        mode
            Filter scores by game mode. Defaults to the user's default mode.
        limit
            Maximum number of scores to return.
        offset
            Offset for pagination.

        Notes
        -----
        Implements the `Get User Scores
        <https://osu.ppy.sh/docs/index.html#get-user-scores>`__ endpoint.
        """
        # `include_fails` is actually a string in the api spec. We'll still
        # require a bool to be passed, and just do the conversion behind the
        # scenes.
        if include_fails is False:
            include_fails = 0
        if include_fails is True:
            include_fails = 1

        params = {"include_fails": include_fails, "mode": mode, "limit": limit,
            "offset": offset}
        return self._get(List[Score], f"/users/{user_id}/scores/{type.value}",
            params)

    @request(Scope.PUBLIC, category="users")
    def user_beatmaps(self,
        user_id: UserIdT,
        type: UserBeatmapTypeT,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Union[List[Beatmapset], List[BeatmapPlaycount]]:
        """
        Get beatmaps of a user.

        Parameters
        ----------
        user_id
            The user to get beatmaps of.
        type_
            The type of beatmaps to get.
        limit
            Maximum number of beatmaps to get.
        offset
            Offset for pagination.

        Notes
        -----
        Returns :class:`~.BeatmapPlaycount` for
        :data:`UserBeatmapType.MOST_PLAYED
        <ossapi.enums.UserBeatmapType.MOST_PLAYED>`, and :class:`~.Beatmapset`
        otherwise.

        Implements `Get User Beatmaps
        <https://osu.ppy.sh/docs/index.html#get-user-beatmaps>`__ endpoint.
        """
        params = {"limit": limit, "offset": offset}

        return_type = List[Beatmapset]
        if type is UserBeatmapType.MOST_PLAYED:
            return_type = List[BeatmapPlaycount]

        return self._get(return_type,
            f"/users/{user_id}/beatmapsets/{type.value}", params)

    @request(Scope.PUBLIC, category="users")
    def user_recent_activity(self,
        user_id: UserIdT,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Event]:
        """
        Get recent activity of a user.

        Parameters
        ----------
        user_id
            The user to get recent activity of.
        limit
            Maximum number of events to return.
        offset
            Offset for pagination.

        Notes
        -----
        Implements the `Get User Recent Activity
        <https://osu.ppy.sh/docs/index.html#get-user-recent-activity>`__
        endpoint.
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[_Event], f"/users/{user_id}/recent_activity/",
            params)

    @request(Scope.PUBLIC, category="users")
    def user(self,
        user: Union[UserIdT, str],
        *,
        mode: Optional[GameModeT] = None,
        key: Optional[UserLookupKeyT] = None
    ) -> User:
        """
        Get a user by id or username.

        user
            The user id or username of the user to get.
        mode
            The mode of the user to get details from. Default mode of the user
            will be used if not specified.
        key
            Whether to query by id or username. Defaults to automatic detection
            if not passed.

        Notes
        -----
        Implements the `Get User
        <https://osu.ppy.sh/docs/index.html#get-user>`__ endpoint.
        """
        params = {"key": key}
        return self._get(User, f"/users/{user}/{mode.value if mode else ''}",
            params)

    @request(Scope.PUBLIC, category="users")
    def users(self,
        user_ids: List[int]
    ) -> List[UserCompact]:
        """
        Batch get users by id. If you only want to retrieve a single user, or
        want to retrieve users by username instead of id, see :meth:`user`.

        Parameters
        ---------
        user_ids
            The users to get.

        Notes
        -----
        Implements the `Get Users
        <https://osu.ppy.sh/docs/index.html#get-users>`__ endpoint.
        """
        params = {"ids": user_ids}
        return self._get(Users, "/users", params).users

    # /wiki
    # -----

    @request(scope=None, category="wiki")
    def wiki_page(self,
        locale: str,
        path: str
    ) -> WikiPage:
        """
        Get a wiki page.

        Parameters
        ----------
        locale
            two letter language code of the wiki page.
        path
            The path name of the wiki page.

        Notes
        -----
        Implements the `Get Wiki Page
        <https://osu.ppy.sh/docs/index.html#get-wiki-page>`__ endpoint.
        """
        return self._get(WikiPage, f"/wiki/{locale}/{path}")
