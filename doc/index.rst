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

.. sidebar:: Sidebar with the very first example!

   I love to see examples of the library on the frontpage! 
   That's why here's a simple example to get you up and running:

   .. code-block:: python
   
       from munin.session import Session
       from munin.provider import AtticProvider, GenreTreeProvider, StemProvider
       from munin.distance import GenreTreeDistance, WordlistDistance

       
       # Perhaps we already had an prior session?
       session = Session.from_name(__name__)
       if session is None:
           # Looks like it didn't exist yet.
           # Well, go and create it!
           session = Session(
                name='MyNameIsSession',
                attribute_mask={
                    # Each line goes like this:
                    # 'the-key-you-want-have-in-your-song': (Provider, DistanceFunction, Weighting)
                    'genre': (GenreTreeProvider, GenreTreeDistance, 0.5),
                    'title': (StemProvider, WordlistDistance, 0.1),
                    'artist': (AtticProvider, None, 0.1)

                }
           )

           # TODO: Make this somewhat clearer.
           with session.transaction():
               for song in your_database:
                    session.add(song)

        # In any case: We have a running session now.
        # We can now use to do useful stuff like recomnendations:
        pass


   Oh, oh. That was a lot of stuff for a small example. That's because
   ``libmunin`` is really freaking modular. :)

   Don't worry we discuss every bit of this in the documentation.

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
    logbuch

User Section
============

.. toctree::

    cmdline

Indices and tables
==================

* :ref:`modindex`
* :ref:`search`
