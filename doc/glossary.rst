Glossary
========

.. glossary:: 

    Song

        In libmunin's Context a Song is a set of attributes that have a name and
        a value. For example a Song might have an ``artist`` attribute with the
        value **Amon Amarth**.

        Apart from the Attributes, every Song has a unique ID.

    Distance

        A distance is the similarity of two songs **a** and **b** expressed in a
        number between 0.0 and 1.0. The Distance is calculated by the
        :term:`DistanceFunction` and is cached in the :term:`DistanceMatrix`.

    DistanceFunction

        A **DF** is a function that takes two songs and calculates the
        :term:`Distance` between them. 

        More specifically, the **DF** looks at all Common Attributes of two
        songs **a** and **b** and calls a special **DF** attribute-wise.
        These results are weighted, so that e.g. ``genre`` gets a higher
        precedence, and summed up to one number.

    DistanceMatrix

        A **DM** caches all calculated Distances. The size of the matrix ``D``
        is the ``NxN`` if ``N`` is the number of songs loaded in a
        :term:`Context`.

        You can assume:

            :math:`D(i, j) = D(j, i) \forall i,j \in D`

            :math:`D(i, i) = 1.0 \forall i \in D`

    Context

        A Context is one handle of libmunin. One Context has one Music Database
        and one Listen History as Input and outputs Recomnendations based on
        that. 

        You can have more than one Context, and therefore more than one Stream
        of Recomnendations.

