Domains
=======

It is possible to use ossapi to interact with the api of other deployments of the osu website, such as `dev.ppy.sh <https://dev.ppy.sh>`__. To do so, use the ``domain`` argument of :class:`~ossapi.ossapiv2.Ossapi`:

.. code-block:: python

    from ossapi import Ossapi, Domain

    api_dev = Ossapi(client_id, client_secret, domain="dev")
    # or
    api_dev = Ossapi(client_id, client_secret, domain=Domain.DEV)

    # top player on the dev server leaderboards. This is pearline06 as of 2023
    print(api_dev.ranking("osu", "performance").ranking[0].user.username)

This works with both the client credentials and authorization code grant, with the normal caveats of the two grants. E.g., you cannot send chat messages with the client credentials grant when in other domains, just like you cannot in the standard domain. See :doc:`Grants <grants>` for more about the differences between the two grants.

.. note::

    The dev domains has separate authentication from the osu domain. If you want to access the dev server's api, you will need to create an account and oauth client on the dev server. As of 2023, this is only possible by running lazer locally in debug mode and creating an account from the client.
