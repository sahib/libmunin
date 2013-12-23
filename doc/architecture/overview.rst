Overview
========


Integration Diagram
-------------------

.. figure:: /_static/integration.svg
    :width: 100%
    :alt: How *libmunin* fits in the world.


Architecture Diagram
--------------------

.. figure:: /_static/arch.svg
    :width: 100%
    :alt: Architecture Overview of libmunin.

Inputs
------

*libmunin* requires three inputs from you, although one is optional:

1) **How your music data looks like.**

    Every music database is different. Some have different tags filled, some use
    different formats and some have the same tags but under different names.
    *libmunin* copes with that by letting you specify a :term:`Mask` that models
    the structure of your **Music Database**.

    .. note:: 

       It's still in your responsibility to load your database. Either from
       file, from a music server like ``mpd`` or an artifical music database 
       like last.fm or musicbrainz without any real audiodata - that's not
       *libmunin's* job.

    Additionally each :term:`Attribute` should have a weight attached that tells us how
    much a similar value would be worth. As an example, a similar Artistname
    might not be very interesting (and has a very small weight therefore) but a
    similar Genre has a high meaning (and should be weighted much higher).

    To each :term:`Attribute` we have a :term:`Provider`, a
    :term:`DistanceFunction` and as mentioned above the weight. 

2) **The Music Database**

    The Database is defined as a set of :term:`Song` s. What tags these songs
    have is defined by the :term:`Mask`. For each song you have you fill the
    required :term:`Attribute` s.

    .. note:: 

        If a song does not specify certain :term:`Attribute` s, then we *punish*
        them by . We have to do this to adhere to the Trinale Inequality which
        is a prequisite of a :term:`Distance`:

            http://en.wikipedia.org/wiki/Triangle_inequality

    After adding all attributes a :term:`Graph` is built where each :term:`Song`
    has other :term:`Song` as neighbors that are similar to the original one.

2) **Listen History**

    This is the optional input. 

    The history of the user's listening habits is recorded and stored in little
    *packages* of Songs, each being maximally, for example, 5 songs big. If some
    time passed a new *package* is openened even if the previous *package* was
    not yet full. 

    These *packages* are used to derive :term:`Rule` from them that associate some
    :term:`Song` with a group of other songs. These are used to *navigate* the
    graph and get more accuarate :term:`Recommendation` s that are based on the actual
    habits of the user. This way the library learns from the user.

    Future versions might implement rules that do not associate songs with each
    other, but more generally, different attributes. As an example: ::
   
       'metal' <=> ['rock', 'country']  

    This would tell us that ``metal`` was listened often in conjunction with the
    genres ``rock`` *and* ``country`` (but not necessarily with each on their own.)

Outputs
-------

The output will always be :term:`Recommendation` s and in future versions perhaps a
reasoning how these :term:`Recommendation` s were found. 

Currently there are 3 ways of creating them:

1) **By a seed song:**

     :term:`Recommendation` based on a certain :term:`Song`. The song is located
     in the :term:`Graph` and a breadth-first-search is done in order to get it's
     similar neighbors. If :term:`Rule` s are known which affect this :term:`Song`,
     these are taken as addiotnal seeds with lower priority.

2) **By heuristics:** 

     Selects a seed song in this order: 
        
     * Find the best rated rule, take the associated :term:`Song`.
     * Find the :term:`Song` with the highest playcount.
     * If all that fails a random song is picked from the :term:`Graph`.

   Proceed as in **1**.

3) **By a subset:**

   Search the best matching song with a certain subset of :term:`Attribute` s as
   seed. For example one could search by a certain *Genre* which would roughly
   translate to the query *Give me a similar song with this Genre.*

   Proceed as in **1**.

Apart from that the *Playcount* of a certain song can be given which is a useful
measure on it's self sometimes.
