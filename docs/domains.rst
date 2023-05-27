Domains
=======

Lazer Domain
------------

It is possible to retrieve information from `lazer.ppy.sh <https://lazer.ppy.sh/home>`__ via the api. For instance, a user's top lazer scores, or the lazer leaderboard. To do so, specify the ``domain`` argument to :class:`~ossapi.ossapiv2.Ossapi`:

.. code-block:: python

    from ossapi import Ossapi, Domain

    api_lazer = Ossapi(client_id, client_secret, domain="lazer")
    # or
    api_lazer = Ossapi(client_id, client_secret, domain=Domain.LAZER)

    # best score on the lazer server (lazer + osu scores combined)
    scores = api_lazer.user_scores(12092800, "best")
    print(scores[0].pp)

This works with both the client credentials and authorization code grant, with the normal caveats of the two grants. E.g., you cannot send chat messages with the client credentials grant when in the lazer domain, just like you cannot in the normal domain. See :doc:`Grants <grants>` for more about the differences between the two grants.

.. note::

    The lazer and osu domains share credentials, so your same oauth application from osu.ppy.sh will work in the lazer domain.

Other Domains
-------------

The standard domain is :data:`Domain.OSU <ossapi.ossapiv2.Domain.OSU>` and retrieves information from `osu.ppy.sh <https://osu.ppy.sh/home>`__. This is the default domain used by ossapi.

There is a third domain, besides :data:`Domain.LAZER <ossapi.ossapiv2.Domain.LAZER>` and :data:`Domain.OSU <ossapi.ossapiv2.Domain.OSU>`: :data:`Domain.DEV <ossapi.ossapiv2.Domain.DEV>`. This corresponds to `dev.ppy.sh <https://dev.ppy.sh/home>`__, the dev server. Use this domain to retrieve information from the dev server:

.. code-block:: python

    from ossapi import Ossapi, Domain

    api = Ossapi(client_id, client_secret, domain="dev")
    # pearline06 as of 2023
    print(api.ranking("osu", "performance").ranking[0].user.username)

.. note::

    The dev domains has separate authentication from the osu/lazer domains. If you want to access the dev server's api, you will need to create an account and oauth client on the dev server. As of 2023, this is only possible by running lazer locally in debug mode and creating an account from the client.
