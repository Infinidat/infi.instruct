Instruct is a Python library for marshalling objects in a (more) declarative way, especially suited for
packing/unpacking protocols such as networking, SCSI, etc.

It is based on [ctypes](http://docs.python.org/library/ctypes.html) view of defining a struct as a class, and on
[Construct](http://construct.wikispaces.com/)'s method of declaring var-sized fields.

Instruct provides two different philosophies on marshalling:

  * _Stream-based_. This way-of-thinking is suited to unpack objects that are read from streams and their entire
    serialized representation cannot be read before the deserialization process can begin.
    This was how Instruct started, but is now superceeded by the new buffer-based approach that's far more convenient.
  * _Buffer-based_. This way-of-thinking is suited to unpack objects that have their entire packed representation
    available before unpacking (think IP packets, etc.).


What makes Instruct different from ctypes?

  * ctypes does not handle serialization/deserialization
  * ctypes isn't really suitable for variable length structs

What makes Instruct different from Construct?

  * With Instruct your struct is a first-class object, in the sense that it's a class so you can add methods,
    initializers, and even customize the serialization/deserialization process.
  * There's no "Container" object to initialize fields. You simply create your own object and take it from there.
  * Instruct provides also a buffer-view on serialization and deserialization.

Some of the things you gain by using Instruct:

  * Symoblic-declarative method to declare a structure, resulting in a very concise representation of most types of
    structures.
  * Help with instance construction. You can set default values to fields, set values on construction and write your own constructor.
  * Object sizing. You can determine how many bytes an instance will occupy when serializing, or estimate the number of bytes a class will take.
  * Nice representation. No more writing your own ``__repr__`` implementation.


Buffer
======

Let's see how we declare an [IPv4 packet](http://en.wikipedia.org/wiki/IPv4#Header) with Instruct's Buffer. For this
example we assume:

   * We want to be able to unpack and pack a valid IP packet, so we don't want to do all the length calculations
     manually.
   * To keep this example simple, we don't define sub-structures in the header.


So here's the IPv4 packet representation:

    from instruct.buffer import *

    class IPv4Packet(Buffer):
        version                = be_int_field(where=bytes_ref[0].bits[0:4], set_before_pack=4)
        internet_header_length = be_int_field(where=bytes_ref[0].bits[4:8], set_before_pack=self._calc_header_length)
        dscp                   = be_int_field(where=bytes_ref[1].bits[0:6])
        ecn                    = be_int_field(where=bytes_ref[1].bits[6:8])
        total_length           = be_int_field(where=bytes_ref[2:4],
                                              set_before_pack=lambda self: self.byte_offset_after('data'))
        identification         = be_int_field(where=bytes_ref[4:6])
        flags                  = be_int_field(where=bytes_ref[6].bits[0:3])
        fragment_offset        = be_int_field(where=bytes_ref[6:7].bits[3:16])
        time_to_live           = be_int_field(where=bytes_ref[8])
        protocol               = be_int_field(where=bytes_ref[9])
        header_checksum        = be_int_field(where=bytes_ref[10:12])  # FIXME
        source_ip_address      = list_field(where=bytes_ref[12:16], n=4, type=uint8)
        destination_ip_address = list_field(where=bytes_ref[16:20], n=4, type=uint8)
        options                = list_field(where_when_pack=bytes_ref[20:],
                                            where_when_unpack=bytes_ref[20:20 + internet_header_length * ]





Struct
======

`Struct` is now deprecated and where possible should be migrated to using the new `Buffer`.


Checking out the code
=====================

Run the following:

    easy_install -U infi.projector
    projector devenv build
