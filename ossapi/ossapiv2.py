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

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import (BackendApplicationClient, TokenExpiredError,
    AccessDeniedError)
from oauthlib.oauth2.rfc6749.errors import InsufficientScopeError
import osrparse
from typing_utils import issubtype, get_type_hints, get_origin, get_args

from ossapi.models import (Beatmap, BeatmapCompact, BeatmapUserScore,
    ForumTopicAndPosts, Search, CommentBundle, Cursor, Score,
    BeatmapsetSearchResult, ModdingHistoryEventsBundle, User, Rankings,
    BeatmapScores, KudosuHistory, Beatmapset, BeatmapPlaycount, Spotlight,
    Spotlights, WikiPage, _Event, Event, BeatmapsetDiscussionPosts, Build,
    ChangelogListing, MultiplayerScores, MultiplayerScoresCursor,
    BeatmapsetDiscussionVotes, CreatePMResponse, BeatmapsetDiscussions,
    UserCompact, NewsListing, NewsPost, SeasonalBackgrounds, BeatmapsetCompact,
    BeatmapUserScores, DifficultyAttributes, Users, Beatmaps)
from ossapi.enums import (GameMode, ScoreType, RankingFilter, RankingType,
    UserBeatmapType, BeatmapDiscussionPostSort, UserLookupKey,
    BeatmapsetEventType, CommentableType, CommentSort, ForumTopicSort,
    SearchMode, MultiplayerScoresSort, BeatmapsetDiscussionVote,
    BeatmapsetDiscussionVoteSort, BeatmapsetStatus, MessageType,
    BeatmapsetSearchCategory, BeatmapsetSearchMode,
    BeatmapsetSearchExplicitContent, BeatmapsetSearchGenre,
    BeatmapsetSearchLanguage)
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

BeatmapIdT = Union[int, BeatmapCompact]
UserIdT = Union[int, UserCompact]
BeatmapsetIdT = Union[int, BeatmapCompact, BeatmapsetCompact]

def request(scope, *, requires_login=False):
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
    requires_login: bool
        Whether this endpoint requires a "logged-in" client to retrieve it.
        Currently, only authtorization code grants can access these endpoints.
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

            if requires_login and self.grant is Grant.CLIENT_CREDENTIALS:
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
        return wrapper
    return decorator


class Grant(Enum):
    CLIENT_CREDENTIALS = "client"
    AUTHORIZATION_CODE = "authorization"

class Scope(Enum):
    CHAT_WRITE = "chat.write"
    DELEGATE = "delegate"
    FORUM_WRITE = "forum.write"
    FRIENDS_READ = "friends.read"
    IDENTIFY = "identify"
    PUBLIC = "public"


class OssapiV2:
    """
    A wrapper around osu api v2.

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
        Currently the api offers the client credentials (pass "client" for this
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
        self.token_directory: Path = (
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

        self.session = self.authenticate()

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

    def authenticate(self):
        """
        Returns a valid OAuth2Session, either from a saved token file associated
        with this OssapiV2's parameters, or from a fresh authentication if no
        such file exists.
        """
        if self.token_file.exists():
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
        self.token_directory.mkdir(parents=True, exist_ok=True)
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

        self.log.info(f"made {method} request to {r.request.url}")
        json_ = r.json()
        self.log.debug(f"received json: \n{json.dumps(json_, indent=4)}")
        self._check_response(json_, url)

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
        # we need a special case to handle when `type_` is a
        # `_GenericAlias`. I don't fully understand why this exception is
        # necessary, and it's likely the result of some error on my part in our
        # type handling code. Nevertheless, until I dig more deeply into it,
        # we need to extract the type to use for the init signature and the type
        # hints from a `_GenericAlias` if we see one, as standard methods
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

    @request(Scope.PUBLIC)
    def beatmap_user_score(self,
        beatmap_id: BeatmapIdT,
        user_id: UserIdT,
        mode: Optional[GameModeT] = None,
        mods: Optional[ModT] = None
    ) -> BeatmapUserScore:
        """
        https://osu.ppy.sh/docs/index.html#get-a-user-beatmap-score
        """
        params = {"mode": mode, "mods": mods}
        return self._get(BeatmapUserScore,
            f"/beatmaps/{beatmap_id}/scores/users/{user_id}", params)

    @request(Scope.PUBLIC)
    def beatmap_user_scores(self,
        beatmap_id: BeatmapIdT,
        user_id: UserIdT,
        mode: Optional[GameModeT] = None
    ) -> List[BeatmapUserScore]:
        """
        https://osu.ppy.sh/docs/index.html#get-a-user-beatmap-scores
        """
        params = {"mode": mode}
        scores = self._get(BeatmapUserScores,
            f"/beatmaps/{beatmap_id}/scores/users/{user_id}/all", params)
        return scores.scores

    @request(Scope.PUBLIC)
    def beatmap_scores(self,
        beatmap_id: BeatmapIdT,
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

    @request(Scope.PUBLIC)
    def beatmap(self,
        beatmap_id: Optional[BeatmapIdT] = None,
        checksum: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Beatmap:
        """
        combines https://osu.ppy.sh/docs/index.html#get-beatmap and
        https://osu.ppy.sh/docs/index.html#lookup-beatmap
        """
        if not (beatmap_id or checksum or filename):
            raise ValueError("at least one of beatmap_id, checksum, or "
                "filename must be passed")
        params = {"checksum": checksum, "filename": filename, "id": beatmap_id}
        return self._get(Beatmap, "/beatmaps/lookup", params)

    @request(Scope.PUBLIC)
    def beatmaps(self,
        beatmap_ids: List[BeatmapIdT]
    ) -> List[Beatmap]:
        params = {"ids": beatmap_ids}
        return self._get(Beatmaps, "/beatmaps", params).beatmaps


    # /beatmapsets
    # ------------

    @request(Scope.PUBLIC)
    def beatmapset_discussion_posts(self,
        beatmapset_discussion_id: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort: Optional[BeatmapDiscussionPostSortT] = None,
        user_id: Optional[UserIdT] = None,
        with_deleted: Optional[bool] = None
    ) -> BeatmapsetDiscussionPosts:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-posts
        """
        params = {"beatmapset_discussion_id": beatmapset_discussion_id,
            "limit": limit, "page": page, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussionPosts,
            "/beatmapsets/discussions/posts", params)

    @request(Scope.PUBLIC)
    def beatmapset_discussion_votes(self,
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
        https://osu.ppy.sh/docs/index.html#get-beatmapset-discussion-votes
        """
        params = {"beatmapset_discussion_id": beatmapset_discussion_id,
            "limit": limit, "page": page, "receiver": receiver_id,
            "score": vote, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussionVotes,
            "/beatmapsets/discussions/votes", params)

    @request(Scope.PUBLIC)
    def beatmapset_discussions(self,
        beatmapset_id: Optional[int] = None,
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
        https://osu.ppy.sh/docs/index.html#get-beatmapset-discussions
        """
        params = {"beatmapset_id": beatmapset_id, "beatmap_id": beatmap_id,
            "beatmapset_status": beatmapset_status, "limit": limit,
            "message_types": message_types, "only_unresolved": only_unresolved,
            "page": page, "sort": sort, "user": user_id,
            "with_deleted": with_deleted}
        return self._get(BeatmapsetDiscussions,
            "/beatmapsets/discussions", params)

    @request(Scope.PUBLIC)
    def beatmap_attributes(self,
        beatmap_id: int,
        mods: Optional[ModT] = None,
        ruleset: Optional[GameModeT] = None,
        ruleset_id: Optional[int] = None
    ) -> DifficultyAttributes:
        """
        https://osu.ppy.sh/docs/index.html#get-beatmap-attributes
        """
        data = {"mods": mods, "ruleset": ruleset, "ruleset_id": ruleset_id}
        return self._post(DifficultyAttributes,
            f"/beatmaps/{beatmap_id}/attributes", data=data)


    # /changelog
    # ----------

    @request(scope=None)
    def changelog_build(self,
        stream: str,
        build: str
    ) -> Build:
        """
        https://osu.ppy.sh/docs/index.html#get-changelog-build
        """
        return self._get(Build, f"/changelog/{stream}/{build}")

    @request(scope=None)
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

    @request(scope=None)
    def changelog_lookup(self,
        changelog: str,
        key: Optional[str] = None
    ) -> Build:
        """
        https://osu.ppy.sh/docs/index.html#lookup-changelog-build
        """
        params = {"key": key}
        return self._get(Build, f"/changelog/{changelog}", params)


    # /chat
    # -----

    @request(Scope.CHAT_WRITE)
    def create_pm(self,
        user_id: UserIdT,
        message: str,
        is_action: Optional[bool] = False
    ) -> CreatePMResponse:
        """
        https://osu.ppy.sh/docs/index.html#create-new-pm
        """
        data = {"target_id": user_id, "message": message,
            "is_action": is_action}
        return self._post(CreatePMResponse, "/chat/new", data=data)


    # /comments
    # ---------

    @request(Scope.PUBLIC)
    def comments(self,
        commentable_type: Optional[CommentableTypeT] = None,
        commentable_id: Optional[int] = None,
        cursor: Optional[Cursor] = None,
        parent_id: Optional[int] = None,
        sort: Optional[CommentSortT] = None
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

    @request(scope=None)
    def comment(self,
        comment_id: int
    ) -> CommentBundle:
        """
        https://osu.ppy.sh/docs/index.html#get-a-comment
        """
        return self._get(CommentBundle, f"/comments/{comment_id}")


    # /forums
    # -------

    @request(Scope.PUBLIC)
    def forum_topic(self,
        topic_id: int,
        cursor: Optional[Cursor] = None,
        sort: Optional[ForumTopicSortT] = None,
        limit: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> ForumTopicAndPosts:
        """
        A topic and its posts.

        https://osu.ppy.sh/docs/index.html#get-topic-and-posts
        """
        params = {"cursor": cursor, "sort": sort, "limit": limit,
            "start": start, "end": end}
        return self._get(ForumTopicAndPosts, f"/forums/topics/{topic_id}",
            params)


    # / ("home")
    # ----------

    @request(Scope.PUBLIC)
    def search(self,
        mode: Optional[SearchModeT] = None,
        query: Optional[str] = None,
        page: Optional[int] = None
    ) -> Search:
        """
        https://osu.ppy.sh/docs/index.html#search
        """
        params = {"mode": mode, "query": query, "page": page}
        return self._get(Search, "/search", params)


    # /me
    # ---

    @request(Scope.IDENTIFY)
    def get_me(self,
        mode: Optional[GameModeT] = None
    ):
        """
        https://osu.ppy.sh/docs/index.html#get-own-data
        """
        return self._get(User, f"/me/{mode.value if mode else ''}")


    # /news
    # -----

    @request(scope=None)
    def news_listing(self,
        limit: Optional[int] = None,
        year: Optional[int] = None,
        cursor: Optional[Cursor] = None
    ) -> NewsListing:
        """
        https://osu.ppy.sh/docs/index.html#get-news-listing
        """
        params = {"limit": limit, "year": year, "cursor": cursor}
        return self._get(NewsListing, "/news", params=params)

    @request(scope=None)
    def news_post(self,
        news: str,
        key: Optional[str] = None
    ) -> NewsPost:
        """
        https://osu.ppy.sh/docs/index.html#get-news-post
        """
        params = {"key": key}
        return self._get(NewsPost, f"/news/{news}", params=params)


    # /rankings
    # ---------

    @request(Scope.PUBLIC)
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

    @request(Scope.PUBLIC)
    def spotlights(self) -> List[Spotlight]:
        """
        https://osu.ppy.sh/docs/index.html#get-spotlights
        """
        spotlights = self._get(Spotlights, "/spotlights")
        return spotlights.spotlights


    # /rooms
    # ------

    # TODO add test for this once I figure out values for room_id and
    # playlist_id that actually produce a response lol
    @request(Scope.PUBLIC)
    def multiplayer_scores(self,
        room_id: int,
        playlist_id: int,
        limit: Optional[int] = None,
        sort: Optional[MultiplayerScoresSortT] = None,
        cursor: Optional[MultiplayerScoresCursor] = None
    ) -> MultiplayerScores:
        """
        https://osu.ppy.sh/docs/index.html#get-scores
        """
        params = {"limit": limit, "sort": sort, "cursor": cursor}
        return self._get(MultiplayerScores,
            f"/rooms/{room_id}/playlist/{playlist_id}/scores", params=params)


    # /users
    # ------

    @request(Scope.PUBLIC)
    def user_kudosu(self,
        user_id: UserIdT,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[KudosuHistory]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-kudosu
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[KudosuHistory], f"/users/{user_id}/kudosu",
            params)

    @request(Scope.PUBLIC)
    def user_scores(self,
        user_id: UserIdT,
        type_: ScoreTypeT,
        include_fails: Optional[bool] = None,
        mode: Optional[GameModeT] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Score]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-scores
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
        return self._get(List[Score], f"/users/{user_id}/scores/{type_.value}",
            params)

    @request(Scope.PUBLIC)
    def user_beatmaps(self,
        user_id: UserIdT,
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

        return self._get(return_type,
            f"/users/{user_id}/beatmapsets/{type_.value}", params)

    @request(Scope.PUBLIC)
    def user_recent_activity(self,
        user_id: UserIdT,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Event]:
        """
        https://osu.ppy.sh/docs/index.html#get-user-recent-activity
        """
        params = {"limit": limit, "offset": offset}
        return self._get(List[_Event], f"/users/{user_id}/recent_activity/",
            params)

    @request(Scope.PUBLIC)
    def user(self,
        user: Union[UserIdT, str],
        mode: Optional[GameModeT] = None,
        key: Optional[UserLookupKeyT] = None
    ) -> User:
        """
        https://osu.ppy.sh/docs/index.html#get-user
        """
        params = {"key": key}
        return self._get(User, f"/users/{user}/{mode.value if mode else ''}",
            params)

    @request(Scope.PUBLIC)
    def users(self,
        user_ids: List[UserIdT]
    ) -> List[UserCompact]:
        """
        https://osu.ppy.sh/docs/index.html#get-users
        """
        params = {"ids": user_ids}
        return self._get(Users, "/users", params).users

    # /wiki
    # -----

    @request(scope=None)
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

    @request(Scope.PUBLIC)
    def score(self,
        mode: GameModeT,
        score_id: int
    ) -> Score:
        return self._get(Score, f"/scores/{mode.value}/{score_id}")

    @request(Scope.PUBLIC, requires_login=True)
    def download_score(self,
        mode: GameModeT,
        score_id: int,
        *,
        raw: bool = False
    ) -> Replay:
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

    @request(Scope.PUBLIC)
    def search_beatmapsets(self,
        query: Optional[str] = None,
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
        cursor: Optional[Cursor] = None
    ) -> BeatmapsetSearchResult:
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
            "c": general}

        # BeatmapsetSearchGenre.ANY is the default and doesn't have a correct
        # corresponding value
        if genre is BeatmapsetSearchGenre.ANY:
            del params["g"]

        # same for BeatmapsetSearchLanguage.ANY
        if language is BeatmapsetSearchLanguage.ANY:
            del params["l"]

        return self._get(BeatmapsetSearchResult, "/beatmapsets/search/", params)

    @request(Scope.PUBLIC)
    def beatmapset(self,
        beatmapset_id: Optional[BeatmapsetIdT] = None,
        beatmap_id: Optional[BeatmapIdT] = None
    ) -> Beatmapset:
        """
        Combines https://osu.ppy.sh/docs/index.html#beatmapsetslookup and
        https://osu.ppy.sh/docs/index.html#beatmapsetsbeatmapset.
        """
        if not bool(beatmap_id) ^ bool(beatmapset_id):
            raise ValueError("exactly one of beatmap_id and beatmapset_id must "
                "be passed.")
        if beatmap_id:
            params = {"beatmap_id": beatmap_id}
            return self._get(Beatmapset, "/beatmapsets/lookup", params)
        return self._get(Beatmapset, f"/beatmapsets/{beatmapset_id}")

    @request(Scope.PUBLIC)
    def beatmapset_events(self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        user_id: Optional[UserIdT] = None,
        types: Optional[List[BeatmapsetEventTypeT]] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None
    ) -> ModdingHistoryEventsBundle:
        """
        https://osu.ppy.sh/beatmapsets/events
        """
        # limit is 5-50
        params = {"limit": limit, "page": page, "user": user_id,
            "min_date": min_date, "max_date": max_date, "types": types}
        return self._get(ModdingHistoryEventsBundle, "/beatmapsets/events",
            params)

    @request(Scope.FRIENDS_READ)
    def friends(self) -> List[UserCompact]:
        return self._get(List[UserCompact], "/friends")

    @request(scope=None)
    def seasonal_backgrounds(self) -> SeasonalBackgrounds:
        return self._get(SeasonalBackgrounds, "/seasonal-backgrounds")

    # /oauth
    # ------

    def revoke_token(self):
        self.session.delete(f"{self.BASE_URL}/oauth/tokens/current")
        self.remove_token(self.token_key, self.token_directory)
