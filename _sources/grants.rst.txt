Grant Types
===========

Authenticating with the osu! api comes in two flavors: the **Client Credentials** grant and the **Authorization Code** grant. Client credentials gives you access to most of the api, but you won't be able to do anything that requires a user, like posting to the forums or sending a pm.

The authorization code grant does not have any such restrictions on the endpoints you can access. However, using the authorization code grant requires manual user interaction the first time you authenticate, in order to authorizate your OAuth application. The client credentials grant, in contrast, authenticates automatically and silently.

In short, if you are writing a simple script or bot, or need the script to run in a headless environment, use the client credentials grant. If you need access to any endpoint which requires a user, use the authorization code grant.

Specifying a Grant
------------------

:class:`~ossapi.ossapiv2.Ossapi` determines the grant type to use based on the parameters you instantiate it with. If you pass just the client id and secret, as in the previous example, it will use the client credentials grant. If you additionally pass the callback url, it will use the authorization code grant.

.. code-block:: python

    from ossapi import Ossapi

    client_id = None
    client_secret = None
    callback_url = None
    # will authenticate with authorization code grant and open a
    # browser window for you to authorize the client
    api = Ossapi(client_id, client_secret, callback_url)

.. note::
    You can also use the ``grant`` parameter to force a particular grant. See :class:`~ossapi.ossapiv2.Ossapi` for details.


Scopes
------

Some endpoints require a scope other than the default :data:`Scope.PUBLIC <ossapi.ossapiv2.Scope.PUBLIC>`. For instance, the :meth:`~ossapi.ossapiv2.Ossapi.friends` endpoint requires the :data:`Scope.FRIENDS_READ <ossapi.ossapiv2.Scope.FRIENDS_READ>` scope. To be able to access this endpoint, specify the relevant scope when you instantiate :class:`~ossapi.ossapiv2.Ossapi`:

.. code-block:: python

    from ossapi import Ossapi, Scope

    client_id = None
    client_secret = None
    callback_url = None
    scopes = [Scope.PUBLIC, Scope.FRIENDS_READ]
    api = Ossapi(client_id, client_secret, callback_url, scopes=scopes)
    print(api.friends())

.. note::
    Scopes are only relevant for the authorization code grant, because the scope for client credentials is always :data:`Scope.PUBLIC <ossapi.ossapiv2.Scope.PUBLIC>`. Client credentials will not be able to access any endpoint which requires a scope other than :data:`Scope.PUBLIC <ossapi.ossapiv2.Scope.PUBLIC>`.

Endpoints which require a scope other than :data:`Scope.PUBLIC <ossapi.ossapiv2.Scope.PUBLIC>` will say so. For instance, endpoints which send chat messages will have the following note:

.. note::

    This endpoint requires the :data:`Scope.CHAT_WRITE <ossapi.ossapiv2.Scope.CHAT_WRITE>` scope.
