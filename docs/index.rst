ossapi
======

ossapi is an api wrapper for osu `api v2 <https://osu.ppy.sh/docs/index.html>`__ and `api v1 <https://github.com/ppy/osu-api/wiki>`__.

ossapi is developed and maintained by `tybug <https://github.com/tybug>`__.

Installation
------------

ossapi can be installed from pip:

.. code-block:: console

    $ pip install ossapi

Links
-----

| Github: https://github.com/circleguard/ossapi
| Documentation: https://circleguard.github.io/ossapi/
| Discord: https://discord.gg/VNnkTjm

Pages
-----

Check out :doc:`Creating a Client <creating-a-client>` for a quickstart, or :doc:`Endpoints <endpoints>` for documentation of all endpoints, if you already know how to authenticate.

.. toctree::
    :hidden:

    self

.. toctree::
    :caption: Quickstart

    creating-a-client
    grants

.. toctree::
    :caption: Advanced

    pagination
    expandable-models
    foreign-keys
    serializing-models
    async

.. toctree::
    :maxdepth: 3
    :caption: Endpoints

    endpoints

.. toctree::
    :caption: Appendix
    :hidden:

    appendix
