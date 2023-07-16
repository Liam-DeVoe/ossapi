Serializing Models
==================

If you need to access the original json returned by the api, you can serialize a model back into a json string with ``serialize_model``:

.. code-block:: python

    from ossapi import serialize_model
    print(serialize_model(api.user("tybug")))

Note that this is not guaranteed to be identical to the json returned by the api. For instance, there may be additional attributes in the serialized json which are optional in the api spec, not returned by the api, and set to null. But it should be essentially the same.

There are various reasons why this approach was chosen over storing the raw json returned by the api, or some other solution. Please open an issue if this approach is not sufficient for your use case.
