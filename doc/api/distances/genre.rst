GenreTree Distance
==================

Overview
--------

Compares the Paths created by :class:`munin.provider.genre.GenreTreeProvider`.

Example
-------

.. code-block:: python

   >>> prov = GenreTreeDistance(genre_tree_provider)
   >>> prov.compare_single_path((190, 1, 0), (190, 1, 1))
   0.333
   >>> prov.compare_single_path((190, 0, 1), (190, 1, 1))
   0.666
   >>> prov.calculate_distance(
   ...     [(190, 1, 0), (190, 1, 1)],
   ...     [(190, 1, 1), (190, 0, 1)]
   ... )
   0.333 # Take the lowest possible distance. (Complete Link)

=============

Reference
---------

.. automodule:: munin.distance.genre
    :members: 
