Expandable Models
=================

A common pattern in the osu! api is to have a "compact" variant of a model with less attributes, for performance reasons. For instance, :class:`~ossapi.models.UserCompact` and :class:`~ossapi.models.User`. It is also common to want to "expand" a compact model into its full representation to access these additional attributes. To do so, use the ``expand`` method:

.. code-block:: python

    compact_user = api.search(query="tybug").users.data[0]
    # `statistics` is only available on `User` not `UserCompact`,
    # so expansion is necessary
    full_user = compact_user.expand()
    print(full_user.statistics.ranked_score)

.. note::
    Expanding a model requires an api call, so it is not free. Use only when necessary.

Here is the full list of expandable models:

- :class:`~ossapi.models.UserCompact` can expand into :class:`~ossapi.models.User` (see :meth:`UserCompact#expand <ossapi.models.UserCompact.expand>`)
- :class:`~ossapi.models.BeatmapCompact` can expand into :class:`~ossapi.models.Beatmap` (see :meth:`BeatmapCompact#expand <ossapi.models.BeatmapCompact.expand>`)
- :class:`~ossapi.models.BeatmapsetCompact` can expand into :class:`~ossapi.models.Beatmapset` (see :meth:`Beatmapset#expand <ossapi.models.Beatmapset.expand>`)
