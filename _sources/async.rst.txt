Async
=====

.. note::

    To use :class:`~ossapi.ossapiv2_async.OssapiAsync`, you must install the async requirements with ``pip install ossapi[async]``.

ossapi provides :class:`~ossapi.ossapiv2_async.OssapiAsync`, an async equivalent of :class:`~ossapi.ossapiv2.Ossapi`. The interfaces are identical, except you must ``await`` any endpoint calls:

.. code-block:: python

    import asyncio
    from ossapi import OssapiAsync

    client_id = None
    client_secret = None
    api = OssapiAsync(client_id, client_secret)

    async def main():
        await api.user("tybug")

    asyncio.run(main())

It is possible that the async version may lag behind the sync version in terms of features, as I generally focus on the sync version first. If you run into any issues using the async version, please open an issue! I likely just forgot to copy some improvement from the sync version.
