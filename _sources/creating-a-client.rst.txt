Creating a Client
=================

Before we can use ossapi, we'll need to create an OAuth client.

Navigate to your `settings page <https://osu.ppy.sh/home/account/edit#oauth>`__ and click "New OAuth Application". You can name it anything you like, but choose a callback url on localhost. For example, ``http://localhost:3914/`` or ``http://localhost:727/``. Any port is fine as long as you don't choose something another application is using.

When you create the application, it will show you a client id and secret. Take note of these two values.

With this information in hand, we're ready to instantiate an :class:`~ossapi.ossapiv2.Ossapi` instance:

.. code-block:: python

    from ossapi import Ossapi

    client_id = None
    client_secret = None
    api = Ossapi(client_id, client_secret)

Using ``api``
-------------

Let's make a simple api call to make sure things are working:

.. code-block:: python

    from ossapi import Ossapi, UserLookupKey

    client_id = None
    client_secret = None
    api = Ossapi(client_id, client_secret)
    user = api.user("tybug2", key=UserLookupKey.USERNAME)
    print(user.id)

With that, you're ready to go! Take a look at :doc:`Endpoints <endpoints>` to see documentation for all endpoints, grouped by category (or look at the left sidebar).

ossapi's documentation follows the style of `osu-web's documentation <https://osu.ppy.sh/docs/index.html>`__ very closely, and models in ossapi match osu-web almost 1:1, so you can use the docs of one to supplement the other.

.. note::
    There are rare exceptions where ossapi's models have different attribute names from osu-web. For example, :data:`ChangelogSearch.from_ <ossapi.enums.ChangelogSearch.from_>` is returned as ``from`` in the api, which is a keyword in python.

You can also continue reading about scopes and grants in :doc:`Grants <grants>`.
