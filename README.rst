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

The moodbar is not strictly required but recomnend.

Required Python Modules
-----------------------

All modules are Python3 compatible: 

.. code-block:: bash

    $ sudo pip install:
        parse     # Easy string parsing.
        PyStemmer # Stemming Library (Attention: Wrapper around C-Library)
        igraph    # Graph Building and Plotting Framework

Optional modules:

.. code-block:: bash

    $ sudo pip install < 
        pyxdg    # Adhering to XDG_CACHE_HOME (works fine without).
        colorlog # Colorful messages for the commandline.

Useful modules for Data-Retrieval:

.. code-block:: bash

    $ sudo pip install
        plyr    # Wrapper around libglyr for retrieving lyrics
