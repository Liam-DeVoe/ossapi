Foreign Keys
============

Following Foreign Keys
----------------------

The osu! api often returns models which contain an id which references another model. For instance, :data:`Beatmap.beatmapset_id <ossapi.models.Beatmap.beatmapset_id>` references the id of the :class:`~ossapi.models.Beatmapset` model. This is a similar concept to foreign keys in databases.

Ossapi automatically adds properties such as `user`, `beatmap`, and `beatmapset` to models with the relevant id. These properties make an api call using the that id, retrieving the full model:

.. code-block:: python

    beatmap = api.beatmap(221777)
    # foreign key: beatmap.beatmapset
    print(beatmap.beatmapset.id)

You can do the same for ``user`` and ``beatmap``, in applicable models:

.. code-block:: python

    disc = api.beatmapset_discussion_posts(2641058).posts[0]
    # foreign key: disc.user
    print(disc.user.username)

    bm_playcount = api.user_beatmaps(user_id=12092800, type="most_played")[0]
    # foreign key: bm_playcount.beatmap
    print(bm_playcount.beatmap.id)

.. warning::

    Although you are "just" accessing a property of the model, following foreign keys incurs an api call and is not free. Be wary of treating your code as fast simply because it only does dot accesses - you may be using hidden foreign key calls!

    Properties which are also foreign keys are clearly marked on the docs.

Foreign keys are cached, so you don't need to worry about incurring multiple api calls for a single attribute:

.. code-block:: python
    # +1 api call (initial call)
    beatmap = api.beatmap(221777)
    # +1 api call (foreign key)
    beatmapset = beatmap.beatmapset

    # free: attributes of beatmapset
    print(beatmapset.title, beatmapset.id)
    # free: beatmap.beatmapset was cached above
    print(beatmap.beatmapset.status)

    # total cost: 2 api calls


Other Foreign Keys
------------------

This concept of foreign keys isn't only applicable to ``beatmap``, ``beatmapset``, or ``user``. For instance, :class:`~ossapi.models.BeatmapsetDiscussionPost` has the attributes :data:`last_editor_id <ossapi.models.BeatmapsetDiscussionPost.last_editor_id>` and :data:`deleted_by_id <ossapi.models.BeatmapsetDiscussionPost.deleted_by_id>`, referencing the users who last edited and deleted the discussion respectively.

In line with this, :class:`~ossapi.models.BeatmapsetDiscussionPost` defines the properties :meth:`last_editor <ossapi.models.BeatmapsetDiscussionPost.last_editor>` and :meth:`deleted_by <ossapi.models.BeatmapsetDiscussionPost.deleted_by>` to retrieve the full user objects:

.. code-block:: python

    disc = api.beatmapset_discussion_posts(2641058).posts[0]
    last_editor = disc.last_editor
    deleted_by = disc.deleted_by
    print(last_editor.username, deleted_by)

Models with similar attributes also define similar properties. These properties are almost always named by dropping ``_id`` from the end of the attribute name.
