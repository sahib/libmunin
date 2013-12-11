Distances and Distance Calculation
==================================

Introduction
------------

Generally spoken a distance is a number between `0.0 (highest similarity)` and
`1.0 (lowest similarity)` that tells you about the *similarity* of two items. 

In our case, when speaking of a **Distance**, we sometimes mean
:class:`munin.distance.Distance`, which gathers single distances (in the general
meaning) and combines them to one value by weighting them and calculating the
average. But in most cases both terms can be used interchangeably.


.. seealso:: :term:`Distance` in the Glossary.

A **DistanceFunction** is a something that calculates a **Distance**. Let's
explain this with some examples. Imagine you have to compare the following
values and tell about their `similarity`:

.. seealso:: :term:`DistanceFunction` in the Glossary.


**Stupid and simple:**
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> 1.0 - float('Elch' == 'Pech')
    1.0
    >>> 1.0 - float('Elch' == 'Elch')
    0.0

This will yield to nobodie's surprise only two values 0.0 and 1.0,
which is nothing but unsatisfying. We need a way to get values in between.
And what about comparasions like ``elch == Elch``?

**I-googled-and-found-stuff-on-Stackoverflow:**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from difflib import SequenceMatcher
    >>> 1 - SequenceMatcher(a='Elch', b='Pech').ratio()
    0.5
    >>> 1 - SequenceMatcher(a='Elch', b='elch').ratio()
    0.25
    >>> 1 - SequenceMatcher(a='Elch'.lower(), b='elch'.lower()).ratio()
    0.0
    >>> 1 - SequenceMatcher(a='PECH', b='Stuff').ratio()
    1.0

Now, that's a lot better already. We can see that we always have a normalization
(:func:`str.lower`) and an actual comparasion (:func:`difflib.SequenceMatcher`).

The *Normalization* part is done by something called a **Provider**. We learn 
about that in the next chapter (:ref:`provider_chapter`).

**Real life version:**
~~~~~~~~~~~~~~~~~~~~~~

A bit more sophisticated comparasion:

.. code-block:: python

   >>> # This needs PyStemmer and pyxDamerauLevenshtein
   >>> from pyxdameraulevenshtein import * 
   >>> damerau_levenshtein_distance('elch', 'Pech')
   2  # Number of adds., subs. and del. to get from 'elch' to 'pech'
   >>> normalized_damerau_levenshtein_distance('elch', 'Pech')
   0.5  # With string length taken into account - like difflib!

Now with addtional normalization:

.. code-block:: python

   >>> from Stemmer import Stemmer
   >>> normalize = lambda word: Stemmer('english').stemWord(word.lower().strip())
   >>> normalized_damerau_levenshtein_distance(normalize('elch'), normalize('Elchy'))
   0.2

This makes use of the *DamereauLevenshtein-Distance* (`levenshtein on wikipedia
<http://en.wikipedia.org/wiki/Levenshtein_distance>`_) and of the *Porter
Stemming* (`stemming on wikipedia
<http://en.wikipedia.org/wiki/Porter_stemmer>`_) algorithm to normalize a single
word to it's `Wordstem` (`kindness` becomes `kind`).

.. note:: The input value needs to be stemmed only once, which can save a lot time.

Implementation in ``libmunin``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have a base-class for distance calculation there:

    :class:`munin.distance.DistanceFunction`

From this many subclasses in the `munin/distance/` directory are inherited.
Usually we have a certain `Provider` and a `DistanceFunction` that knows how to
compare those values produced by the concrete `Provider.`

.. note:: **DistanceFunction** use two list of values as input. Even for single
   values.

===========

List of concrete DistanceFunctions
----------------------------------

.. toctree::
    :glob:

    distances/*

===========

Example: 

.. code-block:: python

   pass
   
.. todo:: Write a decent example

===========
 
Reference
---------

.. automodule:: munin.distance
    :members:
