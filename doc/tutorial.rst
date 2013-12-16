A Humble Beginner's Manual
==========================

You should read this first before proceeding to the more detailled chapters that
will explain a certain topic, but won't give you an overview on *libmunin's*
capabillities. This should give you a quick introduction on what is what and
where what is when where is not defined. Consfused? Me too. Let's just dive in!



Part 1: Minimal Example
-----------------------
 
Let's start with the pretty minimal example you may have seen already on the
frontpage. But let's go through it more detailed this time.

.. code-block:: python
   :linenos:
   :emphasize-lines: 1,3,11,12,14,21

    from munin.easy import EasySession

    MY_DATABASE = [
        # Artist:            Album:               Title:             Genre:
        ('Akrea'          , 'Lebenslinie'      , 'Trugbild'       , 'death metal'),
        ('Vogelfrey'      , 'Wiegenfest'       , 'Heldentod'      , 'folk metal'),
        ('Letzte Instanz' , 'Götter auf Abruf' , 'Salve te'       , 'folk rock'),
        ('Debauchery'     , 'Continue to Kill' , 'Apostle of War' , 'brutal death')
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

    for munin_song in session.recommend_from_seed(session[0], 2):
        print(MY_DATABASE[munin_song.uid])


The output of this little wonder should be: ::

    ('Vogelfrey'  , 'Wiegenfest'       , 'Heldentod'      , 'folk metal'),
    ('Debauchery' , 'Continue to Kill' , 'Apostle of War' , 'brutal death')

We can somewhat explain this, since the only thing those songs have in common 
is the genre - at least partially.

But well, let's look at the higlighted lines:

* **Line 1:** 
  
    Everytime you work with this library you gonna need a session.
    In this simple case we just use the easisest and shorted possibillity: 
    The :class:`munin.easy.EasySession`. You can imagine it as a preconfigured
    Session with defaults that will work fine in many cases.

    You can read more at Part 2_ & 10_.

* **Line 3:**

    Here we fake a databse. You should be aware that *libmunin* will only eat
    data. The only thing it might do is helping you on that process with some
    utilites (as seen in Part 9_). But still, you're on your own here.

* **Line 11:** 

    As mentioned above we need a Session to talk with libmunin. Before using 
    a Session we need to fill it with data. This data consists of songs and
    history information - we only use the basic adding of songs here.

* **Line 12:**

    When adding songs to a session we need to builup quite some internal
    data-structures. If we rebuild after every add it would take a lot of time
    till you get your first recommendation. Therefore the ``transaction``
    contextmanager will immediately yield and call a rebuild on the database
    after you added all the songs.

    By the way, if you want to add songs at some late point it is recommended to
    use :func:`munin.database.Database.insert`.

* **Line 14:**

    This is perhaps the hardest line to grok. With ``session.add`` we add a
    single song to the Session. ``session.add`` expects a dictionary with keys 
    (the keys are pre-defined in the case of ``EasySession``, but can be
    configured in the normal session) and the values you want to set per song.

    Internally for each dictionary a :class:`munin.song.Song` will be created -
    a readonly mapping with normalized version of the values you passed.
    *Normalized* you ask? How? Well, let's introduce a new verb: A *Provider*
    can normalize a value for a certain *Attribute* (e.g. ``'artist'``) in a way
    that comparing values with each other gets faster and easier. More on that
    later.

    Now, what about that ``session.mapping`` thing? You might not have noticed
    it, but *libmunin* has an internal representation of songs which differs
    from the songs in ``MY_DATABASE``. Since recommendations are given in the
    internal representation, you gonna need to have a way to map those back to
    the actual values. ``session.mapping`` is just a dictionary with the only
    plus that it gets saved along with the session. In our example we take the
    return value from ``session.add`` (the *UID* of a song - which is an
    integer) and map it to the index in ``MY_DATABASE``.

    More on that in Part 4_.

    *Tip:* Try to keep the database index and the *UID* in sync.

* **Line 21:**

    In these two lines we do what *libmunin* is actually for - recommending songs.
    Most API-calls take either a song (a :class:`munin.song.Song`) or the *UID* we
    got from :func:`add`. ``session.recommend_from_seed`` takes two arguments. A
    song we want to get recommendations from, and how many we want. In this case
    we want two recommendations from the first song in the database (the one by
    *Akrea*). If we want to transform an *UID* to a full-fledged Song, wen can use 
    the ``__getattr__`` of Session::

      >>> session[0]
      <munin.song.Song(...)>

    But since we can pass either *UIDs* or the lookuped song, these two lines 
    are completely equal::

      >>> session.recommend_from_seed(session[0], 2)
      >>> session.recommend_from_seed(0, 2)

    The function will return an iterator that will lazily yield a
    :class:`munin.song.Song` as a recommendation.

.. _2:

Part 2: Creating a session
--------------------------

A Session needs to know how the data looks like you feed it. ``EasySession``
does this by assuming some sane defaults, but you can always configure every
last bit of how you want *libmunin* to eat your data.

You do this by specifying an *AttriuteMask* where you carefully select a pairs of
providers (thing that preproces values) and distancefunctions (things that
calculate the similarity or *distance* of those preprocessed values ). Apart
from that you give a weighting of that attribute, telling us how important that
attribute is. (*Tip:* If you expect an attribute to not always be filled, i.e.
for lyrics, do not overweight it, since we "punish" unfilled attributes). 

The *Mask* looks like this: 

.. code-block:: python


    {
        'keyname': (
            # Let's assume we instanced this before
            some_provider_instance,
            # Distance Functions need to know their provider:
            SomeDistanceFunction(provider_instance),
            # The importance of this attribute as a float of your choice
            # libmunin will only use relative weights.
            weight
        ),
        # ...
    }

But instancing providers beforehand is tedious, therefore we have a cleaner
version: 

.. code-block:: python
   :emphasize-lines: 4

    {
        # Use the pairup function from munin.helpers
        # to set the Provider to the DistanceFunction automatically.
        'keyname': pairup(
            SomeProvider(),
            DistanceFunction(),
            weight
        ),
        # ...
    }

Here's a full example of how this plays together:

.. literalinclude:: ../munin/__main__.py


The output in the first run is: 

.. code-block:: bash

   TODO

And in the second run: 

.. code-block:: bash

   TODO


.. seealso:: 

   * :ref:`provider_chapter` for a list of available Provider and whay they do.
   * :ref:`distance_chapter` for a list of available DistanceFunction and what they do.


.. note::

    **Later parts of this turorial will only give you a sneak-peek into the most importannt features.**

Part 3: Loading a session
-------------------------
.. _4:

A Session can always be saved with it's ``save`` method. Currently the saving is
very simple in the respect that recursively all objects in the session are
pickled and written to disk. The resulting pickle file is additionally zipped.
You only pass the directory where to save the Session - if you do not specify
one *XDG_CACHE_HOME* is used (which is, in most cases *~/.cache/*).

But how can be load that thing again? 

Well, if you chose to pass no path use ``Session.from_name()``, if you didn't
specify the full path with ``Session.from_archive_path()``.
These *staticmethods* will unpickle the session object from disk. You can use
this idiom: ::

    >>> session = Session.from_name('moosecat') or create_session('moosecat')


Part 4: Mapping your songs to munin's internal songs
----------------------------------------------------

Okay, I lied to you. ``session.mapping`` is no ordinary dict... it's a
bidict_! Assuming we have a mapping like in our first example we can do
something like this: ::

    >>> session.mapping[0]  # get the database idx from the uid 0 
    >>> session.mapping[:0] # get the uid from the database idx 0 
    >>> session.mapping[0:] # same as the first.

.. _bidict: https://pypi.python.org/pypi/bidict

Part 5: Getting recommendations
-------------------------------

There are different methods to get recommendations that differ in details:

* ``recommendations_from_seed(song, N)``

    Get N recommendations from a certain song.
    There are some more details in Part 8_.

* ``recommendations_from_heuristic(N)``

    Like above, but try to choose a good seed song in this order:

        1) Get the song from the rule with the globally best rating.
        2) Get the song with the highest playcount.
        3) If all that fails a random song is chosen.

    The resulting seed song is given to ``recommendations_from_seed``.

* ``recommendations_from_attributes(subset, N)``

    This finds a seed song by a subset of attributes. Take this as example: ::

        >>> recommendations_from_attributes({'genre': 'death metal'})

    This works by first finding a suitalbe seed song with this subset of
    required values (you can even pass more than one key, i.e. restricting the
    artist!) and passing the resulting seed song to ``recommendations_from_seed``.

Part 6: Feeding the History
---------------------------

A cool feature of *libmunin* is that it can learn from your input. You do this
by feeding the song you listened to the session. They will be saved and counted. 
And if we can recognize a frequent pattern in it we create a so called Rule
(More in Part 8_). 

Feeding a song is very simple: ::

    >>> session.feed_history(some_munin_song_or_uid)

Part 7: Adding/Removing single songs
------------------------------------

You can insert and remove songs after you build the graph out of your database
by using ``Session.insert`` and ``Session.remove``. Instead inside the
``Session.transaction`` you should call these functions inside of
``Session.fix_graph``::

    >>> with session.fix_graph():
    ...     session.insert({'key1': 'value1'})

Or::

    >>> with session.fix_graph():
    ...     session.remove(some_munin_song_or_uid)

.. note:: 

   It is not advisable to call insert or remove very often. Sometimes, after say
   100, insert operations the internal graph might have small errors. These can
   be fixed by doing a rebuild at this point.

.. _8: 

Part 8: Accessing rules
-----------------------

Rules are *libmunin's* way of learning your habits. Internally a large graph is
built out of your songs - each song has neighbors which are, in theory at least, 
are similar to the song in the centre. Without rules the recommendations
algorithm will just do a breadth-first search from a seed song. Rules help here 
by providing a way to help navigating the graph. For a single song we might have
quite some rules (Imagine we represent our songs by numbers)::

    #01:            [5] <-> [4]             
    #02:         [5, 4] <-> [3]             
    #03:            [4] <-> [3]             
    #04:            [2] <-> [3]             
    #05:            [2] <-> [4, 3]          
    #06:            [5] <-> [3]             
    #07:            [4] <-> [5, 3]          
    #08:            [5] <-> [4, 3]          
    #09:            [1] <-> [2]             
    #10:            [2] <-> [4]             
    #11:         [2, 5] <-> [3]             

If we want to recommend songs based on the Song ``5`` we lookup the rules that
affect it - and the songs that are mentioned in these rules. These are: ``[4, 3, 2]``.
Instead of taking a single song we take these as additional seeds - with lower
priority though. 

You can iterate over all rules and lookup rules that are affected by certain
songs: 

.. code-block:: python

    >>> for rule in session.rule_index:
    >>>     print(rule)
    ([5, 4], [4], supp=74, conf=0.83, kulc=0.87 irat=0.07 rating=0.8)
    >>> # The numbers in the number (2 - 7) describe the quality of the rule.
    >>> # Basically you only need to know about the rating - 1.0 would be perfect.

.. code-block:: python

   >>> for rule in session.rule_index.lookup(some_munin_song):
   >>>     print(rule)

.. _9:

Part 9: Data-Retrieval Helpers (scripts)
----------------------------------------

For some attributes you might need the path to audio files, or the lyrics of a 
song - stuff you can't get in a oneliner for sure.

Here are some recipes for making these kind of tasks easier.

Recursively getting all audio files from a directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from munin.helper import AudioFileWalker
    >>> for path in AudioFileWalker('/home/sahib/music'):
    ...     print(path)
    /home/sahib/music/Artist/Album/Song01.ogg
    /home/sahib/music/Artist/Album/Song02.ogg
    ...

Paralellize expensive calculations using ProcessPoolExecutor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This will iterate over a music collection and calculate (and cache) the moodbar
of these songs. The description (an internal base for comparasion) of these
moodbars will be printed to the screen.

.. code-block:: python

    from concurrent.futures import ProcessPoolExecutor
    from munin.provider.moodbar import MoodbarAudioFileProvider
    from munin.helper import AudioFileWalker

    provider = MoodbarAudioFileProvider()
    moodbar_files = list(AudioFileWalker('/home/sahib/music/')
    with ProcessPoolExecutor(max_workers=10) as executor:
        futured = executor.map(MoodbarAudioFileProvider.do_process, moodbar_files)
        for description, *_ futured:
            print(description)

This was used in an example script that ships with libmunin:

    https://github.com/sahib/libmunin/blob/master/munin/scripts/moodbar_walk.py

Getting Lyrics and other Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For any kind of music related metadata there's libglyr_, and it's pythonic
(†) wrapper plyr_. 

*Tiny Example:* 

.. code-block:: python

    >>> import plyr
    >>> qry = plyr.Query(artist='Akrea', title='Trugbild', get_type='lyrics')
    >>> items = qry.commit()
    >>> print(items[0].data.decode('utf-8'))
    ...
    Nun zeigst du dich unser
    Enthüllst dein wahres Ich
    Letztendlich nur ein Trugbild
    Welches spöttisch deiner Eigen glich
    ...
    
*More Information:*

    http://sahib.github.io/python-glyr/index.html


† Now that's shameless self-advertisement. I recommend libglyr_ since I wrote it.

.. _libglyr: https://github.com/sahib/glyr
.. _plyr: https://github.com/sahib/python-glyr

.. _10:

Part 10: EasySession
--------------------

.. currentmodule:: munin.easy

We've learned about :class:`EasySession` already in the very first chapter.
We now know it's just a Session with some sane defaults and some predefined 
attributes. 

Here is a table describing how the :class:`EasySession` is configured:

.. currentmodule:: munin.provider

+-------------+---------------+-----------------------------------+-----------------------------+----------+
| *Attribute* | *Takes*       | *Provider*                        | *DistanceFunction*          | *Weight* |
+=============+===============+===================================+=============================+==========+
| **artist**  | Artist        | :class:`StemProvider`             | :class:`LevnshteinDistance` |     3    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **album**   | Album         | :class:`WordlistProvider`         | :class:`WordListDistance`   |     5    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **title**   | Title         | :class:`WordlistProvider`         | :class:`WordListDistance`   |     7    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **genre**   | Genre         | :class:`GenreTreeProvider`        | :class:`GenreTreeDistance`  |    20    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **bpm**     | AudioFilePath | :class:`BPMCacheProvider`         | :class:`BPMDistance`        |    25    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **moodbar** | AudioFilePath | :class:`MoodbarAudioFileProvider` | :class:`MoodbarDistance`    |    30    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
| **lyrics**  | Lyrics        | :class:`KeywordProvider`          | :class:`KeywordDistance`    |    15    |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
|             |               |                                   |    *Total Weight:*          | 100      |
+-------------+---------------+-----------------------------------+-----------------------------+----------+
