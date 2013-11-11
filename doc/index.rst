.. title is not shown in flask theme:

libmununin docs
===============

**Introduction**

**libmunin** is a versatile python library that can do music recomnendations
based on datamining algorithms. You give it your music collection, some time
to learn in the background and in return it will give you some clever
recomnendations.

If you wonder what ravens have to do with this: Go to wikipedia_. 

    | *In Norse mythology, Hugin (from Old Norse "thought")*
    | *and Munin (Old Norse "memory" or "mind")*
    | *are a pair of ravens that fly all over the world Midgard,*
    | *and bring information to the god Odin.*

.. _wikipedia: http://en.wikipedia.org/wiki/Huginn_and_Muninn

**Key Features:**

*Ability to…*

* …recomend *N* songs to a song *X*. 
* …recomend *N* songs based on a certain attribute.
* …do mood-analysis and keyword-extraction.
* …create and honor Rules (like ``rock ==> metal = cool!``)
* …monitor the user's behaviour by creating Rules.
* …extend the API to fit your custom project.


..  .. sidebar:: Sidebar with the very first example!

**Quick Example**

I love early examples, so here's one:

.. code-block:: python
   
   from munin.session import Session
   from munin.provider import AtticProvider, GenreTreeProvider, StemProvider
   from munin.distance import GenreTreeDistance, WordlistDistance

   # Perhaps we already had an prior session?
   session = Session.from_name(__name__)
   if session is None:
       # Looks like it didn't exist yet.
       # Well, go and create it! (You gonna have to adapt your data)
       session = Session.create_default(__name__)
       with session.transaction():
           for your_song in your_database:
                session.database.add_values({
                    'artist': your_song.artist,
                    'album': your_song.album,
                    'title': your_song.title,
                    'genre': your_song.genre,
                    'mood': file_to_song(your_song)
                    # ...
                })

    # In any case: We have a running session now.
    # We can now use to do useful stuff like recomnendations:
    ten_recomnendations = session.recomned(some_song, 10)

    # You can feed also your lately listened songs:
    # libmunin will try to base newer recomnendations on this.
    session.feed_history(some_munin_song)

    # Rules can be created to add certain 
    session.add_rule_from_string('genre', 'metal <=> rock = 0.0')


That was quite a lot to grok for a *small* example. 
Don't worry we discuss every bit of this in the documentation.

=============================

.. sidebar:: Official Logo of ``libmunin``

   .. image:: _static/logo.png
      :width: 100%


**Design**

.. toctree::
    :glob: 
    :maxdepth: 1
    
    architecture/*
    glossary

**Developer Section**

.. toctree::
    :glob:
    :maxdepth: 1

    api/*
    todo
    logbuch

**User Section**

.. toctree::

    cmdline

**Indices and tables**

* :ref:`modindex`
* :ref:`search`
