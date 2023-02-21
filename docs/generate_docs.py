from enum import EnumMeta
import inspect
from pathlib import Path
from collections import defaultdict
import string
from typing import List, Union
from datetime import datetime
from dataclasses import is_dataclass
import textwrap

from typing_utils import get_type_hints, get_args, get_origin

from ossapi.utils import (EnumModel, Model, BaseModel, IntFlagModel,
    Datetime, is_base_model_type, is_model_type, Field)
from ossapi.models import _Event
from ossapi.ossapiv2 import ModT
from ossapi import Scope, Mod
import ossapi



# sentinel value
unset = object()

IGNORE_MODELS = [EnumModel, Model, BaseModel, IntFlagModel, _Event, Datetime]
IGNORE_MEMBERS = ["override_class", "override_types", "preprocess_data"]
BASE_TYPES = [int, str, float, bool, datetime]

def is_enum_model(Class):
    return type(Class) is EnumMeta

def is_model(Class):
    return (
        is_model_type(Class) or
        is_base_model_type(Class) or
        is_dataclass(Class)
    )

def is_base_type(type_):
    return is_model(type_) or type_ in BASE_TYPES

def type_to_string(type_,):
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
        return ' | '.join(arg_strs)

    return str(type_)


class Generator:
    def __init__(self):
        self.result = ""
        self.processed = []

    def add_header(self, name):
        self.result += f"{name}\n"
        self.result += "=" * len(name)
        self.result += "\n\n"

    def process_module(self, module, name):
        self.add_header(name)

        # necessary for type links to actually work. also necessary for source
        # code link (https://stackoverflow.com/a/53991465), so it's definitely
        # good practice for us to put
        self.result += f".. module:: {module.__name__}"
        self.result += "\n\n"

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
            self.result += f"   .. autoclass:: {ModelClass.__name__}\n"
            self.result += "\n\n"
            return

        self.result += f".. py:class:: {ModelClass.__name__}\n\n"

        members = self.get_members(ModelClass)

        for name, value in members:
            doc_value = unset
            if is_enum_model(ModelClass):
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


            self.result += f"   .. py:attribute:: {name}\n"

            type_str = type_to_string(type_)
            self.result += f"      :type: {type_str}\n"
            if doc_value is not unset:
                if type_ is str:
                    # surround string types with quotes
                    doc_value = f"\"{doc_value}\""
                self.result += f"      :value: {doc_value}\n"

            # leave a special note for when our naming deviates from the api
            if isinstance(value, Field):
                note_text = (f"``{name}`` is returned in the osu! api as "
                    f"``{value.name}``.")
                self.result += "\n"
                self.result += f"   .. note::\n      {note_text}\n"

            self.result += "\n"

        self.processed.append(ModelClass)

    def get_members(self, Class):
        members = inspect.getmembers(Class)
        members = [m for m in members if not m[0].startswith("_")]
        members = [m for m in members if m[0] not in IGNORE_MEMBERS]
        return members

    def get_parameters(self, function):
        params = list(inspect.signature(function).parameters)
        params = [p for p in params if p != "self"]
        return params

    def write_to_path(self, path):
        with open(path, "w") as f:
            f.write(textwrap.dedent("""
                ..
                   THIS FILE WAS AUTOGENERATED BY generate_docs.py.
                   DO NOT EDIT THIS FILE MANUALLY

            """))
            f.write(self.result)

    def process_endpoints(self, api):
        # category : list[(name, value)]
        endpoints = defaultdict(list)
        for name, value in self.get_members(api):
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

        for category, endpoint_values in endpoints.items():
            self.add_header(string.capwords(category))

            for name, value in endpoint_values:
                self.result += f".. autofunction:: ossapi.ossapiv2.Ossapi.{name}"

                scope = getattr(value, "__ossapi_scope__")
                # endpoints implicitly require public scope, don't document it
                if scope is not None and scope is not Scope.PUBLIC:
                    self.result += ("\n\n .. note::\n    Requires the "
                        f":data:`Scope.{scope.name} "
                        f"<ossapi.ossapiv2.Scope.{scope.name}>` scope.")

                self.result += "\n\n"



p = Path(__file__).parent

generator = Generator()
generator.process_module(ossapi.enums, "Enums")
generator.process_module(ossapi.models, "Models")
generator.write_to_path(p / "appendix.rst")

generator = Generator()
generator.result += ("|br| |br| All functions in this file are methods of the "
    ":class:`~ossapi.ossapiv2.Ossapi` class.\n\n")
generator.process_endpoints(ossapi.Ossapi)
generator.write_to_path(p / "endpoints.rst")

def write_class(file, class_name, *, members=True):
    with open(p / "appendix.rst", "a") as f:
        f.write("\n\n")
        f.write(f"{class_name}\n")
        f.write(f"{'=' * len(class_name)}\n\n")
        f.write(f".. module:: ossapi.{file}\n\n")
        f.write(f".. autoclass:: {class_name}\n")
        if members:
            f.write("   :members:")
            f.write("\n   :undoc-members:")

write_class("ossapiv2", "Ossapi", members=False)
write_class("ossapiv2_async", "OssapiAsync", members=False)
write_class("ossapiv2", "Scope")
write_class("ossapiv2", "Grant")
write_class("replay", "Replay")
