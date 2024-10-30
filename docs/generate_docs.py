from enum import EnumMeta
import inspect
from pathlib import Path
from collections import defaultdict
import string
from typing import List, Union
from datetime import datetime
from dataclasses import is_dataclass
import textwrap
from enum import IntFlag

from typing_utils import get_type_hints, get_args, get_origin

from ossapi.utils import (
    EnumModel,
    Model,
    BaseModel,
    IntFlagModel,
    Datetime,
    is_base_model_type,
    is_model_type,
    Field,
)
from ossapi.models import _Event
from ossapi.ossapiv2 import ModT
from ossapi import Scope, Mod
import ossapi


# sentinel value
unset = object()

IGNORE_MODELS = [EnumModel, Model, BaseModel, IntFlagModel, _Event, Datetime]
IGNORE_MEMBERS = ["override_class", "override_attributes", "preprocess_data"]
BASE_TYPES = [int, str, float, bool, datetime]


def is_enum_model(Class):
    return type(Class) is EnumMeta


def is_model(Class):
    return is_model_type(Class) or is_base_model_type(Class) or is_dataclass(Class)


def is_base_type(type_):
    return is_model(type_) or type_ in BASE_TYPES


def type_to_string(type_):
    if type_ is type(None):
        return "None"

    # blatantly lie about the type of our Datetime wrapper class.
    if type_ is Datetime:
        return "~datetime.datetime"

    if is_base_type(type_):
        return type_.__name__

    origin = get_origin(type_)
    args = get_args(type_)
    if origin in [list, List]:
        assert len(args) == 1

        arg = args[0]
        return f"list[{type_to_string(arg)}]"

    if origin == Union:
        args = tuple(arg for arg in args if arg != type(None))
        if Union[args] == ModT:
            return "Mod"

        arg_strs = [type_to_string(arg) for arg in args]
        arg_strs.append("None")
        return " | ".join(arg_strs)

    return str(type_)


def get_members(Class):
    members = inspect.getmembers(Class)
    members = [m for m in members if not m[0].startswith("_")]
    members = [m for m in members if m[0] not in IGNORE_MEMBERS]
    return members


def get_parameters(function):
    params = list(inspect.signature(function).parameters)
    params = [p for p in params if p != "self"]
    return params


def endpoints_by_category(api):
    # category : list[(name, value)]
    endpoints = defaultdict(list)
    for name, value in get_members(api):
        if not callable(value):
            continue

        # set by @request decorator. If missing, this function isn't a
        # request/endpoint function
        category = getattr(value, "__ossapi_category__", None)
        if category is None:
            continue

        endpoints[category].append([name, value])

    # sort category names alphabetically
    endpoints = dict(sorted(endpoints.items()))
    return endpoints


class Generator:
    def __init__(self):
        self.result = ""
        self.processed = []

    def write(self, val):
        self.result += val

    def write_header(self, name, *, level="-"):
        self.write(f"\n{name}\n")
        self.write(level * len(name))
        self.write("\n\n")

    def process_module(self, module, name):
        self.write_header(name)

        # necessary for type links to actually work. also necessary for source
        # code link (https://stackoverflow.com/a/53991465), so it's definitely
        # good practice for us to put
        self.write(f".. module:: {module.__name__}")
        self.write("\n\n")

        model_classes = vars(module).values()
        for ModelClass in model_classes:
            if not is_model(ModelClass):
                continue

            if ModelClass in IGNORE_MODELS:
                continue
            self.process_model(ModelClass)

    def process_model(self, ModelClass):
        # don't include a model on the page twice. This means the order that you
        # process models in is important and determines which section they end
        # up in.
        if ModelClass in self.processed:
            return

        # custom handling for some models
        if ModelClass in [Mod]:
            self.write(f"   .. autoclass:: {ModelClass.__name__}\n")
            self.write("\n\n")
            return

        self.write(f".. py:class:: {ModelClass.__name__}\n\n")

        members = get_members(ModelClass)

        for name, value in members:
            doc_value = unset
            if is_enum_model(ModelClass):
                # IntFlag inherits from int and so gets some additional members
                # we don't want, including from_bytes which shows up on EnumType
                # and not int for some reason. Probably some metaclass bs.
                if issubclass(ModelClass, IntFlag):
                    if (name, value) in get_members(int) or name == "from_bytes":
                        continue
                # retrieve the type of the actual backing value
                type_ = type(value.value)
                doc_value = value.value
            else:

                if callable(value):
                    # will (almost?) always be "function"
                    type_ = type(value).__name__
                else:
                    # if we're not an enum model then we're a dataclass model.
                    # Retrieve the type from type annotations
                    for name_, value_ in get_type_hints(ModelClass).items():
                        if name_ == name:
                            type_ = value_
                            break

            self.write(f"   .. py:attribute:: {name}\n")

            type_str = type_to_string(type_)
            self.write(f"      :type: {type_str}\n")
            if doc_value is not unset:
                if type_ is str:
                    # surround string types with quotes
                    doc_value = f'"{doc_value}"'
                self.write(f"      :value: {doc_value}\n")

            # leave a special note for when our naming deviates from the api
            if isinstance(value, Field) and value.name is not None:
                note_text = (
                    f"``{name}`` is returned in the osu! api as " f"``{value.name}``."
                )
                self.write("\n")
                self.write(f"   .. note::\n      {note_text}\n")

            self.write("\n")

        self.processed.append(ModelClass)

    def process_class(self, class_name, file, *, members=True):
        self.write_header(class_name)
        self.write(f".. module:: ossapi.{file}\n\n")
        self.write(f".. autoclass:: {class_name}\n")
        if members:
            self.write("   :members:")
            self.write("\n   :undoc-members:")

    def write_to_path(self, path):
        with open(path, "w") as f:
            f.write(
                textwrap.dedent(
                    """
                ..
                   THIS FILE WAS AUTOGENERATED BY generate_docs.py.
                   DO NOT EDIT THIS FILE MANUALLY
            """
                )
            )
            f.write(self.result)

    def process_endpoints(self, api):
        endpoints = endpoints_by_category(api)
        for category, endpoint_values in endpoints.items():
            self.process_category(category, endpoint_values)

    def process_category(self, category, endpoint_values):
        self.write_header(string.capwords(category))

        for name, value in endpoint_values:
            self.write(f".. autofunction:: ossapi.ossapiv2.Ossapi.{name}")

            scope = value.__ossapi_scope__
            # endpoints implicitly require public scope, don't document it
            if scope is not None and scope is not Scope.PUBLIC:
                self.write(
                    "\n\n .. note::\n    This endpoint requires the "
                    f":data:`Scope.{scope.name} "
                    f"<ossapi.ossapiv2.Scope.{scope.name}>` scope."
                )

            self.write("\n\n")


p = Path(__file__).parent

generator = Generator()
generator.write_header("API Reference", level="=")
generator.process_module(ossapi.enums, "Enums")
generator.process_module(ossapi.models, "Models")
generator.process_class("Ossapi", "ossapiv2", members=False)
generator.process_class("OssapiAsync", "ossapiv2_async", members=False)
generator.process_class("Scope", "ossapiv2")
generator.process_class("Domain", "ossapiv2")
generator.process_class("Grant", "ossapiv2")
generator.process_class("Replay", "replay")
generator.write_to_path(p / "api-reference.rst")

for category, endpoints in endpoints_by_category(ossapi.Ossapi).items():
    generator = Generator()
    generator.process_category(category, endpoints)
    generator.write_to_path(p / f"{category}.rst")

generator = Generator()
generator.write_header("Endpoints")
generator.write(".. toctree::\n\n")

for category in endpoints_by_category(ossapi.Ossapi):
    generator.write(f"    {category}\n")

generator.write_to_path(p / "endpoints.rst")
