import ossapi
import inspect
from collections import defaultdict
import string

endpoints = defaultdict(list)
for name, value in inspect.getmembers(ossapi.Ossapi):
    if not callable(value):
        continue
    category = getattr(value, "__ossapi_category__", None)
    if category is None:
        continue

    endpoints[category].append(name)

# sort alphabetically by category
endpoints = dict(sorted(endpoints.items()))
for category, names in endpoints.items():

    fragment = category.replace(" ", "-")
    # special case double capital for oauth
    if category == "oauth":
        title = "OAuth"
    else:
        title = string.capwords(category)

    print(f"* {title}<a name=\"endpoints-{fragment}\"></a>")

    for name in names:
        print(f"  * [`api.{name}`](https://tybug.github.io/ossapi/endpoints.html#ossapi.ossapiv2.Ossapi.{name})")
