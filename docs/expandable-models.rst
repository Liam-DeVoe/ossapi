Expandable Models
=================

Expansion
---------

A common pattern in the osu! api is to have a "compact" variant of a model with less attributes, for performance reasons. For instance, :class:`~ossapi.models.UserCompact` is the compact version of :class:`~ossapi.models.User`. it is sometimes desirable to "expand" a compact model into its full representation in order to access the ommitted attributes. To do so, use the ``expand`` method:

.. code-block:: python

    compact_user = api.search(query="tybug2").users.data[0]
    # `statistics` is only available on `User`, not `UserCompact`,
    # so expansion is necessary.
    full_user = compact_user.expand()
    print(full_user.statistics.ranked_score)

.. warning::

    Expanding a model incurs an api call. It is not free.


Here is the full list of expandable models:

- :class:`~ossapi.models.UserCompact` can expand into :class:`~ossapi.models.User` (see :meth:`UserCompact#expand <ossapi.models.UserCompact.expand>`)
- :class:`~ossapi.models.BeatmapCompact` can expand into :class:`~ossapi.models.Beatmap` (see :meth:`BeatmapCompact#expand <ossapi.models.BeatmapCompact.expand>`)
- :class:`~ossapi.models.BeatmapsetCompact` can expand into :class:`~ossapi.models.Beatmapset` (see :meth:`Beatmapset#expand <ossapi.models.Beatmapset.expand>`)
