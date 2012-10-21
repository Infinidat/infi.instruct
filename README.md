Instruct is a Python library for creating serializable objects in a (more) declarative way. It is based on ctypes__ view of defining a struct as a class, and on Construct__'s method of declaring var-sized fields.

__ http://docs.python.org/library/ctypes.html
__ http://construct.wikispaces.com/

What makes Instruct different from ctypes?
 * ctypes does not handle serialization/deserialization.
 * ctypes isn't really suitable for variable length structs.

What makes Instruct different from construct?
 * With Instruct your struct is a first-class object, in the sense that it's a class so you can add methods, initializer, and even customize the serialization/deserialization process.
 * There's no "Container" object to initialize fields. You simply create your own object and take it from there.

Some of the things you gain by using Instruct:
 * Help with instance construction. You can set default values to fields, set values on construction and write your own constructor.
 * Object sizing. You can determine how many bytes an instance will occupy when serializing, or estimate the number of bytes a class will take.
 * Nice representation. No more writing your own ``__repr__`` implementation.
