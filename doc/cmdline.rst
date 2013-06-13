====================
Command Line Utility
====================

This document is about the command utility of *libmunin* called *naglfar*. 

Options
-------

.. program:: naglfar


.. code-block:: bash

    Synopsis: 
        naglfar [genopts] [command] [options]

    Usage:
        naglfar -h | --help
        naglfar -v | --version
        naglfar database [-f|--file <FILE>] [--subsitute|-s]
        naglfar history  [-f|--file <FILE>]

``database:``

    .. option:: -f | --file <FILE>

        Read Database from <FILE>. 
        If no file is specified, read from stdin.

        Format:

            .. todo:: Specify format

    .. option:: -s | --subsitute

        Subistute current database contents with this 
