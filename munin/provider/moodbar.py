#!/usr/bin/env python
# encoding: utf-8

# Stdlib:
from collections import deq

# Internal:
from munin.utils import grouper

# External:
from numpy import 


def read_moodbar_values(path):
    with open(path, 'rb') as f:
        return [tuple(c / 0xff for c in rgb)) for rgb in grouper(f.read(), n=3)]


def compute(vector):

