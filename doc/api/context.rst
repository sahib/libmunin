=============
``context.h``
=============

Description
-----------

A :term:`Context` is a Handle to libmunin. You can generate recomnendations by 
feeding a *Context* with a set of songs and, optionally, with the listening
history. The structure on C-side is called :c:type:`MuninCtx`.

You can create a :c:type:`MuninCtx` with :c:func:`munin_ctx_create`. 
When done you should pass it to :c:func:`munin_ctx_destroy`

The main purpose of a *Context* is holding the set of songs you want to generate
recomnendations from. In order to add *Songs* to the *Context* you can use
:c:func:`munin_ctx_feed`, but it is very advisable to call
:c:func:`munin_ctx_begin`/:c:func:`munin_ctx_commit` before/after if you add
many songs. You should be aware that adding a song means calculating quite some
stuff. Packing it in a Transaction reduces this overhead significantly.

.. todo:: Tell reader about AttributeMask.

Usage Example
-------------

.. code-block:: c

    #include <stdlib.h>
    #include <munin/context.h>

    int main(void) 
    {
        /* Create a new Context */
        MuninCtx *ctx = munin_ctx_create();
    
        /* Begin a new Transaction */
        munin_ctx_begin(ctx);
    
        for(int i = 0; i < 100; ++i) {
            long song_id = munin_song_new();
            muning_song_set(song_id, "artist", "Amon Amarth");
            munin_ctx_feed(ctx, song_id);
        }

        /* Commit all feeded songs to the db */
        munin_ctx_commit(ctx);

        /* Kill all associated ressources */
        munin_ctx_destroy(ctx);
        return EXIT_SUCCESS;
    }



Reference
---------

**Types:**

    .. c:type:: MuninCtx

        Member of this structure should not be accessed directly.
        
-----

**Functions:**

    .. c:function:: MuninCtx * munin_ctx_create(void)

        Allocates a new :term:`Context`.

        :returns: A MuninCtx, pass it to :c:func:`munin_ctx_destroy` when done

    .. c:function:: void munin_ctx_destroy(MuninCtx * ctx)

        Destroys a :term:`Context` and all associated memory.

        :ctx: On what context to operate.

    .. c:function:: void munin_ctx_begin(MuninCtx * ctx)
        
        Before adding songs to the database a transaction has to be opened. 
        This speeds up adding many songs (like the initial import) quite a bit since 
        adding a song involves calculating a :term:`Distance` to every other :term:`Song`.

        You can call :c:func:`munin_ctx_feed` in a begin/commit block.

        :ctx: On what context to operate.

    .. c:function:: void munin_ctx_commit(MuninCtx * ctx)
    
        Add all feeded songs to the database at once. 

        Calling this without :c:func:`munin_ctx_begin` before is an error.

        :ctx: On what context to operate.

    .. c:function:: void munin_ctx_feed(MuninCtx * ctx, long song_id)

        Feed a Song to the Context. Future Recomnendations might contain this song
        now.

        :ctx: On what context to operate.
        :song_id: The Song to add, it is referenced by an ID.

    .. c:function:: void munin_ctx_remove(MuninCtx *ctx, long song)

        Removes a song from the Context.

        :ctx: The context to operate on.
        :song: a SongID
