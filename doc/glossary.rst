Glossary
========

.. glossary:: 

    Song

        In libmunin's Context a Song is a set of attributes that have a name and
        a value. For example a Song might have an ``artist`` attribute with the
        value **Amon Amarth**.

        Apart from the Attributes, every Song has a unique ID.

    Distance

        A distance is the similarity of two songs or attributes **a** and **b**
        expressed in a number between 0.0 and 1.0, where 1.0 means maximal
        unsimilarity. Imagining a point space, two points are identical when
        their geometric distance is 0.0.
        
        The Distance is calculated by the :term:`DistanceFunction`.

    DistanceFunction

        A **DF** is a function that takes two songs and calculates the
        :term:`Distance` between them. 

        More specifically, the **DF** looks at all Common Attributes of two
        songs **a** and **b** and calls a special **DF** attribute-wise.
        These results are weighted, so that e.g. ``genre`` gets a higher
        precedence, and summed up to one number.

        The following must be true for a valid **DF**, when :math:`D` is the
        database:
   
            :math:`D(i, j) = D(j, i) \forall i,j \in D`

            :math:`D(i, i) = 0.0 \forall i \in D`

            :math:`D(i, j) \leq D(i, x) + (x, j)`

    Session

        A Session is the usage of *libmunin* over the time on one music
        collection. It can be saved to disk and later resumed.

    Mask

        Every :term:`Session` requires a Mapping where the possible keys 
        are defined that a single song may have. The **AM** stores this
        information as dictionary, the keys being the names of the possible
        attributes and the values being a tuple, conisting of the Provider for
        this Attribute, a fitting Distance Function and a weight.
