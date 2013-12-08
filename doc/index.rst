.. title is not shown in flask theme:

libmununin docs
===============

Introduction
------------

**libmunin** is a versatile python library that can do music recommendations
based on datamining algorithms. You give it your music collection, some time
to learn in the background and in return it will give you some clever
recommendations.

If you wonder what ravens have to do with this: Go to wikipedia_. 

    | *In Norse mythology, Hugin (from Old Norse "thought")*
    | *and Munin (Old Norse "memory" or "mind")*
    | *are a pair of ravens that fly all over the world Midgard,*
    | *and bring information to the god Odin.*

.. _wikipedia: http://en.wikipedia.org/wiki/Huginn_and_Muninn

Key Features
------------

*Ability to…*

* …recommend songs to a certain song. 
* …find uninion recommendations for two songs.
* …recommend any song from using habits.
* …do mood-analysis and keyword-extraction.
* …create and honor Rules mined from the listening history.
* …extend the API to fit your custom project.

=============================

Table of Contents
-----------------

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

=============================

Minimal Example
---------------

.. code-block:: python
   
    from munin.easy import EasySession

    MY_DATABASE = [
        ('Akrea', 'Lebenslinie', 'Trugbild', 'death metal'),
        ('Vogelfrey', 'Wiegenfest', 'Heldentod', 'folk metal'),
        ('Letzte Instanz', 'Götter auf Abruf', 'Salve te', 'folk rock'),
        ('Debauchery', 'Continue to Kill', 'Apostle of War', 'brutal death')
    ]

    session = EasySession()
    with session.transaction():
        for idx, (artist, album, title, genre) in enumerate(MY_DATABASE):
             session.mapping[session.add({
                 'artist': artist,
                 'album': album,
                 'title': title,
                 'genre': genre
             })] = idx

    for munin_song in session.recommend_from_song(session.lookup(0), 2):
        print(MY_DATABASE[munin_song.uid])

    # -> Prints 2nd and 4th song, because of the similar genre.
