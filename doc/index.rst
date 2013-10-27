``libmunin`` Developer Manual
=============================

**libmunin** is a versatile python library that can do music recomnendations
based on datamining algorithms. You give it your music collection, some time
to learn in the background and in return it will give you some clever
recomnendations.

If you wonder what ravens have to do with this: Go to wikipedia_. 

    | *In Norse mythology, Hugin (from Old Norse "thought") and Munin (Old Norse "memory" or "mind")*
    | *are a pair of ravens that fly all over the world, Midgard, and bring information to the god Odin.*

.. _wikipedia: http://en.wikipedia.org/wiki/Huginn_and_Muninn

**Key Features:**

Ability to…

.. hlist::
    :columns: 2

    * …recomend *N* songs to a song *X*. 
    * …recomend *N* songs based on a certain attribute.
    * …do mood-analysis and keyword-extraction.
    * …create and honor Rules (like ``rock ==> metal = cool!``)
    * …monitor the user's behaviour by creating Rules.
    * …extend the API to fit your custom project.

.. sidebar:: Logo

   .. image:: _static/logo.png
       :width: 20%


=============================

Design
======

.. toctree::
    :glob: 
    :maxdepth: 1
    
    architecture/*
    glossary

Developer Section
=================

.. toctree::
    :glob:
    :maxdepth: 1

    api/*
    todo

User Section
============

.. toctree::

    cmdline

Indices and tables
==================

* :ref:`modindex`
* :ref:`search`
