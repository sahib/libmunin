==========
``song.h``
==========

Description
-----------

A Song is the elementar node in *libmunin*.

In order to be fully threadsafe there is no structure named ``MuninCtx``, since
it may be freed behind your back when you look. If you'd continue to use it,
BadThings™ would happen. Instead a Song is identified by a unique Integer-ID.

The main purpose of a Song is to set attributes to it. You can set all
attributes you previously set in the :term:`Context`'s AttributeMask. 

The ususal attributes are: 

.. hlist::

    * ``artist``
    * ``album``
    * ``title``
    * ``releaseartist``
    * ``duration``
    * ``genre``
    * ``mood``
    * ``track``
    * ``rating``
    * ``date``

It is recomned to use these as a convention. You can of course define tags as
you wish to. Here's a list of attributes you can get inspiration from:

    http://wiki.musicbrainz.org/MusicBrainz_Picard/Tags/Mapping

.. warning:: **Memory Management:**

    *libmunin* will **NOT** copy the attributes you set. BadThings™ will happen if
    you free the data you set. This decision was made in order to be able to
    handle very large sets of songs without memory penality. If you wish to copy
    the attribute use ``strdup()`` and register a free function when creating
    the AttributeMask.
            

Usage Example
-------------

.. code-block:: c 

    long song = munin_song_create(ctx);

    munin_song_begin(ctx, song);
    munin_song_set(ctx, song, "artist", "Debauchery");
    munin_song_set(ctx, song, "artist", "Death Metal Warmachine");
    munin_song_commit(ctx, song);

    printf("%s\n", munin_song_get(ctx, "artist"));

    /* Add it to the set */
    munin_ctx_feed(ctx, song);
    
    /* Oh, crap didn't want to feed it actually */
    munin_ctx_remove(ctx, song);


Reference
---------

**Functions:**

    .. c:function:: long munin_song_create(MuninCtx *ctx)
            
        Create a new song. 

        :ctx: The context to operate on.
        :returns: An ID that references a Song.

    .. c:function:: void munin_song_begin(MuninCtx *ctx, long song)

        Begin editing a song.

        :ctx: The context to operate on.
        :song: a SongID

    .. c:function:: void munin_song_commit(MuninCtx *ctx, long song)

        Commit edits to a song. Causes every :term:`Distance` to be rebuild 
        for this song.

        :ctx: The context to operate on.
        :song: a SongID

    .. c:function:: const char * mn_song_get(MuninCtx *ctx, long song, const char *key)

        Get an Attribute from a song. 

        :ctx: The context to operate on.
        :song: a SongID
        :key: The attribute name

    .. c:function:: void munin_song_set(MuninCtx *ctx, long song, const char *key, const char *value)

        Set an attribute of the song.

        :ctx: The context to operate on.
        :song: a SongID
        :key: The attribute name
        :value: The value to set

    .. c:function:: bool munin_song_is_valid(MuninCtx *ctx, long song)
    
        Check if the ID passed as **song** is actually valid, i.e. if the ID
        exists and the song was not removed.

        :ctx: The context to operate on.
        :song: a SongID
        :returns: True if the Song is valid

.. todo:: Define API for MuninAttrIter
