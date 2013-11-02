GenreTree Distance
==================

Overview
--------

Compares the Paths created by :class:`munin.provider.genre.GenreTreeProvider`.

Example
-------

.. code-block:: python

   >>> dfunc = GenreTreeDistance(genre_tree_provider)
   >>> dfunc.compare_single_path((190, 1, 0), (190, 1, 1))
   0.333
   >>> dfunc.compare_single_path((190, 0, 1), (190, 1, 1))
   0.666
   >>> dfunc(
   ...     [(190, 1, 0), (190, 1, 1)],
   ...     [(190, 1, 1), (190, 0, 1)]
   ... )
   0.333 # Take the lowest possible distance. (Complete Link)

=============

Reference
---------

.. automodule:: munin.distance.genre
    :members: 
