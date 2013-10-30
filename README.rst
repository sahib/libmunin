Introduction
============

``libmunin`` is a fancy music recomnendations library which is based on
datamining algorithms of all kind. `Bonus:` It's able to learn from you!
I write it for my bachelor thesis and therefore it's still in developement.

Documentation is build on every commit http://www.readthedocs.org:

    http://libmunin-api.readthedocs.org/en/latest/

Tests are run on every commit via http://travis-ci.org:

    https://travis-ci.org/sahib/libmunin

Installation
============

.. image:: https://travis-ci.org/sahib/libmunin.png?branch=master   
    :target: https://travis-ci.org/sahib/libmunin

Required externam programs
--------------------------

The ``moodbar`` binary is required for gthe mood-analysis. 
Future versions might implement the mood-analysis themselves, 
or at least package it along libmunin.

Your distribution might package it or you can compile it from here:

    http://pwsp.net/~qbob/moodbar-0.1.2.tar.gz

The moodbar is not strictly required but recomnended.

Required Python Modules
-----------------------

All modules are Python3 compatible: 

.. code-block:: bash

    $ sudo pip install -r pip_requirements.txt --use-mirrors"

Optional modules and modules useful for Data-Retrieval
------------------------------------------------------

.. code-block:: bash

    $ sudo pip install -r pip_optional_requirements.txt --use-mirrors"
