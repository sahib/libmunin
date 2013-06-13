===============
``history.rst``
===============

Description
-----------

The Listen History is the second Input to to *libmunin*. You can feed listened
songs as a hint to *libmunin* which will base the next recomnendations based on
them. These are the different scenarios:





    ========= ====================== ======
    Playcount Recent Recommendation? Effect
    ========= ====================== ======
    n         False                  
    n         True
    ========= ====================== ======

Usage Example
-------------

.. code-block:: c

    //

Reference
---------

**Functions:**

.. c:function:: bool munin_history_feed(MuninCtx * ctx, long song)

    Add a song the the History Buffer. *libmunin* will automatically check if
    the song was recomned lately and use this for further recomendations.    

    :ctx: The Context to operate on.
    :song: A song to feed.
    :returns: True if the song was in the recomendations recently given.
