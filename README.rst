==============
 Introduction
==============
Instruct is a Python library for declaring object structure and then serializing/deserializing it.

Writer:
  write_to_stream(self, obj, stream)

ReaderBase:
  sizeof
  min_sizeof
  is_fixed_size

InitializingReader:
  create_from_stream(self, stream, ...)

ModifyingReader:
  read_into_from_stream(self, obj, stream, ...)


==============
 Installation
==============
Install using the regular setup.py
::

  python setup.py install

=========
 Running
=========
To run the simulator in its simplest mode, just run:
::

  run_infinidat_simulator -v -F

=============
 Development
=============

The Command Interface
=====================
(work in progress)
