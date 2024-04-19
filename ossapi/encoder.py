import json
from json import JSONEncoder
from datetime import datetime
from enum import Enum

from ossapi.models import Model
from ossapi.mod import Mod


class ModelEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return 1000 * int(o.timestamp())
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, Mod):
            return o.value

        to_serialize = {}
        if isinstance(o, Model):
            for name, value in o.__dict__.items():
                # don't seriailize private attributes, like ``_api``.
                if name.startswith("_"):
                    continue
                to_serialize[name] = value
            return to_serialize

        return super().default(o)


def serialize_model(model, ensure_ascii=False, **kwargs):
    return json.dumps(model, cls=ModelEncoder, ensure_ascii=ensure_ascii, **kwargs)
