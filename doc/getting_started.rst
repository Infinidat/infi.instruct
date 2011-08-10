=============================
Getting Started with Instruct
=============================

Defining a struct
-----------------

Here's a very simple definition::

  from infi.instruct import *

  class RGBA(Struct):
    _fields_ = [ UBInt8("red"), UBInt8("green"), UBInt8("blue"), UBInt8("alpha") ]

Let's go over the code and explain what we've done. First, we subclassed :ref:`Struct`, which is the basis for every structure you define. More later on what you get when inheriting from it. Next, we see there's a class attribute called *_fields_*. This is where Instruct learns what fields you want in your structure. Here we needed 4 fields, each an 8-bit Unsigned Big-endian (not that it matters with 8-bits) integer. See that we have named each field (*red*, *green*, *blue*, *alpha*).

.. note::

   The order of the fields is important - this will be the order they are read from a stream or written to a stream.

Let's see what happens when we create a new instance:

  >>> rgba = RGBA()
  >>> print(repr(rgba))
  RGBA(red=<not set>, green=<not set>, blue=<not set>, alpha=<not set>)

As you can see, inheriting from Struct implictly makes a nice representation of the instance. Since we have not set any of the fields, we see in the printout that they're not set. Let's change that.

  >>> rgba.red = 12
  >>> print(repr(rgba))
  RGBA(red=12, green=<not set>, blue=<not set>, alpha=<not set>)

What happens if we simply print ``rgba``? We'll get an error::

  InstructError: Error occurred while writing field 'green' for class <class '__main__.RGBA'>

We got this error because ``UBInt8`` cannot hold a ``None`` value, so the serialization failed.

.. note::

   There's a big difference between *repr* and *str* with Structs. *repr* is a human-friendly representation and *str* serializes the object into a string.

What else do we get from :ref:`Struct`? We can get the size in bytes of an *instance*:
  
  >>> RGBA.sizeof(rgba)
  4
  >>> Struct.sizeof(rgba)
  4

If we don't have an instance, and we want to get an estimation of the expected size of a struct we can generally determine the minimum and maximum size in bytes. This is an estimation that can be used to know how many bytes to reserve, read, etc.

  >>> RGBA.min_max_sizeof()
  MinMax(min=4, max=4)

We can set fields when initializing an instance (more on this in `Instance Construction Assistance`_):

  >>> rgba = RGBA(red=10, green=15, blue=20, alpha=255)

Now let's see how to serialize/deserialize a struct (more on this in `Serializing Structs`_):

  >>> rgba.write_to_string()
  '\n\x0f\x14\xff'
  >>> RGBA.create_from_string('\x20\x30\x40\xff')
  RGBA(red=32, green=48, blue=64, alpha=255)

We can of course serialize/deserialize from a stream:
  >>> from cStringIO import StringIO
  >>> RGBA.create_from_stream(StringIO('\x20\x30\x40\xff'))
  RGBA(red=32, green=48, blue=64, alpha=255)

Instance Construction Assistance
--------------------------------

Let's use `MyStruct` defined here as a basis for our discussion::

  class MyStruct(Struct):
    _fields_ = [ UBInt8("size"), PaddedString("name", size=16, default="foo") ]

Here we created a new instance with two fields *size* and *name*. *size* is an Unsigned Big-endian 8-bit integer (hence UBInt8). *name* is a 16-byte long string, padded with zeroes if shorter. Also, *name* gets a default value "foo".

Let's create a new instance:

>>> my_struct = MyStruct(size=10)
>>> print("my_struct(size=%d, name=%s)" % (my_struct.size, my_struct.name))
my_struct(size=10, name=foo)

What happened here? the field *name* was assigned the default value of *"foo"* so ``my_struct.name`` equals to *"foo"*. The *size* field was initialized by the (implicit) constructor.
This is an interesting feature of ``Struct``: whenever a class inherits from it, it gets a magical initialization code that takes all the keyword arguments with the same name as fields declared in ``_fields_`` and assigns them.

So for example, this is a valid initialization as well:

>>> my_struct = MyStruct(size=5, name="LeChuck")
>>> print("my_struct(size=%d, name=%s)" % (my_struct.size, my_struct.name))
my_struct(size=1, name=LeChuck)

Now, what if you wanted your own __init__ method? no problem, simply write one::

  class MyStruct(Struct):
    _fields_ = [ UBInt8("size"), PaddedString("name", size=16, default="foo") ]
    
    def __init__(self, my_arg):
        super(MyStruct, self).__init__()
        self.my_arg = my_arg

And we can see now that the following works:

>>> my_struct = MyStruct(10, size=5, name="LeChuck")
>>> my_struct = MyStruct(my_arg=10, size=5, name="LeChuck")

Given that __init__ method, how does this work? Well, there's a little metaclasses magic involved here, aimed to help you with two tasks:
 - Ability to set field values in construction without writing code to do it
 - Allow your init code to have its own arguments

So for example, the following will raise an error:

>>> my_struct = MyStruct(size=5, name="LeChuck")
File ".../infi/instruct/struct/__init__.py", line 133, in __instance_init__
    user_init(self, *args, **kwargs)
TypeError: __init__() takes exactly 2 arguments (1 given)

Say you want to set some fields in your initializer. That can be done by two methods::

  ...
  def __init__(self):
     super(MyStruct, self).__init__(size=255, name="Guybrush")

Or simply set them::

  ...
  def __init__(self):
      super(MyStruct, self).__init__()
      self.size = 255
      self.name = "Guybrush"

Stuff to write about:
 * _fields_
 * sizeof()
 * min_max_sizeof()
 * repr()
 * write_to_stream
 * create_from_stream
 * magical construction
