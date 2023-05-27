Foreign Keys
============

Following Foreign Keys
----------------------

The osu! api often returns models which contain an id which references another model. For instance, :data:`Beatmap.beatmapset_id <ossapi.models.Beatmap.beatmapset_id>` references the id of the :class:`~ossapi.models.Beatmapset` model. This is a similar concept to foreign keys in databases.

Where applicable, ossapi provides methods to "follow" these ids and retrieve the full model from the id:

.. code-block:: python

    beatmap = api.beatmap(221777)
    bmset = beatmap.beatmapset()

You can do the same for ``user()`` and ``beatmap()``, in applicable models:

.. code-block:: python

    disc = api.beatmapset_discussion_posts(2641058).posts[0]
    user = disc.user()

    bm_playcount = api.user_beatmaps(user_id=12092800, type="most_played")[0]
    beatmap = bm_playcount.beatmap()

.. note::

    Following a foreign key usually involves an api call, so it is not free.

Other Foreign Keys
------------------

Note that the id attribute and corresponding method isn't always called ``beatmap``, ``beatmapset``, or ``user``. For instance, :class:`~ossapi.models.BeatmapsetDiscussionPost` has the attributes :data:`last_editor_id <ossapi.models.BeatmapsetDiscussionPost.last_editor_id>` and :data:`deleted_by_id <ossapi.models.BeatmapsetDiscussionPost.deleted_by_id>`, referencing the users who last edited and deleted the discussion respectively.

In line with this, :class:`~ossapi.models.BeatmapsetDiscussionPost` defines the methods :meth:`last_editor <ossapi.models.BeatmapsetDiscussionPost.last_editor>` and :meth:`deleted_by <ossapi.models.BeatmapsetDiscussionPost.deleted_by>` to retrieve the full user objects:

.. code-block:: python

    disc = api.beatmapset_discussion_posts(2641058).posts[0]
    last_editor = disc.last_editor()
    deleted_by = disc.deleted_by()
    print(last_editor.username, deleted_by)

Models with similar attributes also define similar methods. The functions are almost always named by dropping ``_id`` from the attribute name.
