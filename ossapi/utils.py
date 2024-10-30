from enum import Enum, IntFlag
from datetime import datetime, timezone
from typing import Any, Union
from dataclasses import dataclass

from typing_utils import issubtype, get_origin, get_args


def is_high_model_type(type_):
    """
    Whether ``type_`` is both a model type and not a base model type.

    "high" here is meant to indicate that it is not at the bottom of the model
    hierarchy, ie not a "base" model.
    """
    return is_model_type(type_) and not is_base_model_type(type_)


def is_model_type(type_):
    """
    Whether ``type_`` is a subclass of ``Model``.
    """
    if not isinstance(type_, type):
        return False
    return issubclass(type_, Model)


def is_base_model_type(type_):
    """
    Whether ``type_`` is a subclass of ``BaseModel``.
    """
    if not isinstance(type_, type):
        return False
    return issubclass(type_, BaseModel)


class Field:
    def __init__(self, *, name=None, type=None):
        self.name = name

        # We use annotations for two distinct purposes: deserialization, and
        # user-facing type hints. If the deserialize type does not match the
        # runtime type, these two annotations need to be different.
        #
        # For instance, events should deserialize as _Event, but have a runtime
        # type of Event.
        #
        # This field allows setting the runtime type via annotations and the
        # deserialize type via passing this field.
        self.type = type


class _Model:
    """
    Base class for all models in ``ossapi``. If you want a model which handles
    its own members and cleanup after instantion, subclass ``BaseModel``
    instead.
    """

    @staticmethod
    def override_attributes(data, api):
        """
        Sometimes, the types of attributes in models depends on the value of
        other fields in that model. By overriding this method, models can return
        "override types", which overrides the static annotation of attributes
        and tells ossapi to use the returned type to instantiate the attribute
        instead.

        This method should return a mapping of ``attribute_name`` to
        ``intended_type``. You can also return a class to use exactly the
        attributes of that class.
        """
        return None

    @staticmethod
    def preprocess_data(data, api):
        """
        A hook that allows model classes to modify data from the api before it
        is used to instantiate the model.

        For example, if a model attribute come as either a bool or an integer
        (0 for false and 1 for true), this method can be overridden to convert
        the integer to a boolean before model instantiation. This lets you
        define the attribute as type bool instead of type Union[int, bool].

        ``preprocess_data`` is called before ``override_class`` and
        ``override_types``, so changes to the data in ``preprocess_data`` will
        affect the data passed to those methods.
        """
        return data


class ModelMeta(type):
    def __new__(cls, name, bases, dct):
        model = super().__new__(cls, name, bases, dct)
        field_names = []
        for name, value in model.__dict__.items():
            if name.startswith("__") and name.endswith("__"):
                continue
            if isinstance(value, Field):
                field_names.append(name)

        for name in model.__annotations__:
            if name in field_names:
                continue
            setattr(model, name, None)

        return model


class Model(_Model, metaclass=ModelMeta):
    """
    A dataclass-style model. Provides an ``_api`` attribute.
    """

    def __init__(self, **kwargs):
        self._ossapi_data = kwargs

    def __getattribute__(self, key):
        data = super().__getattribute__("_ossapi_data")
        if key == "_ossapi_data":
            return data
        if key in data:
            return data[key]
        return super().__getattribute__(key)

    def __setattr__(self, key, value):
        if key == "_ossapi_data":
            return super().__setattr__(key, value)
        self._ossapi_data[key] = value

    def _foreign_key(self, fk, func, existing):
        if existing:
            return existing
        if fk is None:
            return None
        return func()

    def _fk_user(self, user_id, existing=None):
        func = lambda: self._api.user(user_id)
        return self._foreign_key(user_id, func, existing)

    def _fk_beatmap(self, beatmap_id, existing=None):
        func = lambda: self._api.beatmap(beatmap_id)
        return self._foreign_key(beatmap_id, func, existing)

    def _fk_beatmapset(self, beatmapset_id, existing=None):
        func = lambda: self._api.beatmapset(beatmapset_id)
        return self._foreign_key(beatmapset_id, func, existing)

    def __str__(self):
        # don't print internal values
        blacklisted_keys = ["_api"]
        items = [
            f"{k}={v!r}"
            for k, v in self._ossapi_data.items()
            if k not in blacklisted_keys
        ]
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return all(
            getattr(self, key) == getattr(other, key) for key in self._ossapi_data
        )

    __repr__ = __str__


class BaseModel(_Model):
    """
    A model which promises to take care of its own members and cleanup, after we
    instantiate it.

    Normally, for a high (non-base) model type, we recurse down its members to
    look for more model types after we instantiate it. We also resolve
    annotations for its members after instantion. None of that happens with a
    base model; we hand off the model's data to it and do nothing more.

    A commonly used example of a base model type is an ``Enum``. Enums have
    their own magic that takes care of cleaning the data upon instantiation
    (taking a string and converting it into one of a finite set of enum members,
    for instance). We don't need or want to do anything else with an enum after
    instantiating it, hence it's defined as a base type.
    """

    pass


class EnumModel(BaseModel, Enum):
    pass


class IntFlagModel(BaseModel, IntFlag):
    pass


class Datetime(datetime, BaseModel):
    """
    Our replacement for the ``datetime`` object that deals with the various
    datetime formats the api returns.
    """

    def __new__(cls, value):
        if value is None:
            raise ValueError("cannot instantiate a Datetime with a null value")
        # the api returns a bunch of different timestamps: two ISO 8601
        # formats (eg "2018-09-11T08:45:49.000000Z" and
        # "2014-05-18T17:22:23+00:00"), a unix timestamp (eg
        # 1615385278000), and others. We handle each case below.
        # Fully compliant ISO 8601 parsing is apparently a pain, and
        # the proper way to do this would be to use a third party
        # library, but I don't want to add any dependencies. This
        # stopgap seems to work for now, but may break in the future if
        # the api changes the timestamps they return.
        # see https://stackoverflow.com/q/969285.
        if value.isdigit():
            # see if it's an int first, if so it's a unix timestamp. The
            # api returns the timestamp in milliseconds but
            # `datetime.fromtimestamp` expects it in seconds, so
            # divide by 1000 to convert.
            value = int(value) / 1000
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if cls._matches_datetime(value, "%Y-%m-%dT%H:%M:%S.%f%z"):
            return value
        if cls._matches_datetime(value, "%Y-%m-%dT%H:%M:%S%z"):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
        if cls._matches_datetime(value, "%Y-%m-%d"):
            return datetime.strptime(value, "%Y-%m-%d")
        # returned by eg https://osu.ppy.sh/api/v2/rooms/257524
        if cls._matches_datetime(value, "%Y-%m-%d %H:%M:%S"):
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        raise ValueError(f"invalid datetime string {value}")

    @staticmethod
    def _matches_datetime(value, format_):
        try:
            _ = datetime.strptime(value, format_)
        except ValueError:
            return False
        return True


# typing utils
# ------------


def is_optional(type_):
    """
    Whether ``type(None)`` is a valid instance of ``type_``. eg,
    ``is_optional(Union[str, int, NoneType]) == True``.

    Exception: when ``type_`` is any, we return false. Strictly speaking, if
    ``Any`` is a subtype of ``type_`` then we return false, since
    ``Union[Any, str]`` is a valid type not equal to ``Any`` (in python), but
    representing the same set of types.
    """

    # issubtype is expensive as it requires normalizing the types. It's possible
    # we could improve performance there, but there is low hanging fruit for
    # is_optional in particular: the vast majority of calls are on very simple
    # types, such as primitive types (int, str, etc), model types (UserCompact),
    # or the simplest form of optional type (Optional[int]). For these cases,
    # we can do much better with faster checks.
    #
    # It's rare that complicated types such as Union[Union[int, None], str] come
    # up which  require normalization. However, we'll keep the issubtype check
    # as the "ground truth" fallback for when the optimizations fail.
    #
    # This method is used in tight deserialization loops, so it's important to
    # keep it inexpensive.

    # optimization for common case of primitive types
    if type_ in [int, float, str, bool]:
        return False

    # optimization for common case of simple optional - Optional[int] ie
    # Union[int, NoneType].
    if get_origin(type_) is Union:
        if get_args(type_)[1] is type(None):
            return True

    return issubtype(type(None), type_) and not issubtype(Any, type_)


def is_primitive_type(type_):
    if not isinstance(type_, type):
        return False
    return type_ in [int, float, str, bool]


def convert_primitive_type(value, type_):
    # In the json we receive, eg ``pp`` can have a value of ``15833``, which is
    # interpreted as an int by our json parser even though ``pp`` is a float.
    # Convert back to the correct typing here.
    # This is important as some consumers may rely on float-specific methods
    # (`#is_integer`)
    if type_ is float and isinstance(value, int):
        return float(value)
    return value
