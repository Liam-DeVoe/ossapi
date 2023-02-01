Pagination
==========

Some endpoints in the osu! api are paginated. These endpoints return models with either a ``cursor`` or ``cursor_string`` attribute, depending on the endpoint. To access the next page, pass along this attribute to the api call:

.. code-block:: python

    r = api.ranking("osu", RankingType.PERFORMANCE)
    cursor = r.cursor
    print(r.ranking[-1].global_rank) # 50

    r = api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
    print(r.ranking[-1].global_rank) # 100

Skipping Pages
--------------

If you know exactly what page you want, you can skip to it by constructing your own ``Cursor`` with the ``page`` attribute:

.. code-block:: python

    cursor = Cursor(page=19)
    r = api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
    print(r.ranking[-1].global_rank) # 950

Checking for the Last Page
--------------------------

If there are no more pages, the ``cursor`` (or ``cursor_string``) object of the response will be ``None``:

.. code-block:: python

    cursor = Cursor(page=199)
    r = api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
    print(r.cursor) # Cursor(page=200)

    cursor = Cursor(page=200) # there are only 200 rankings pages
    r = api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
    print(r.cursor) # None
