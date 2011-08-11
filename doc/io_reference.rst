I/O Handler Reference
=====================

.. currentmodule:: infi.instruct.numeric

Numeric I/O handlers
--------------------

Numeric handlers serialize and deserialize primitive numeric types (int and float). Each handler has an associated
field macro that can be used to simplify field definition.

The following for example are equivalent:

>>> UBInt8("my_field", default=5)

and

>>> Field("my_field", UBInt8IO, default=5)

+---------------------------------------------------------------+
| Macro Name    | I/O Name   | Numeric Type     | Bits | Endian |
+===============+============+==================+======+========+
| UBInt8        | UBInt8IO   | Unsigned Integer | 8    | Big    |
+---------------+------------+------------------+------+--------+
| SBInt8        | SBInt8IO   | Signed Integer   | 8    | Big    |
+---------------+------------+------------------+------+--------+
| ULInt8        | ULInt8IO   | Unsigned Integer | 8    | Little |
+---------------+------------+------------------+------+--------+
| SLInt8        | SLInt8IO   | Signed Integer   | 8    | Little |
+---------------+------------+------------------+------+--------+
| UNInt8        | UNInt8IO   | Unsigned Integer | 8    | Native |
+---------------+------------+------------------+------+--------+
| SNInt8        | SNInt8IO   | Signed Integer   | 8    | Native |
+---------------+------------+------------------+------+--------+
| UBInt16       | UBInt16IO  | Unsigned Integer | 16   | Big    |
+---------------+------------+------------------+------+--------+
| SBInt16       | SBInt16IO  | Signed Integer   | 16   | Big    |
+---------------+------------+------------------+------+--------+
| ULInt16       | ULInt16IO  | Unsigned Integer | 16   | Little |
+---------------+------------+------------------+------+--------+
| SLInt16       | SLInt16IO  | Signed Integer   | 16   | Little |
+---------------+------------+------------------+------+--------+
| UNInt16       | UNInt16IO  | Unsigned Integer | 16   | Native |
+---------------+------------+------------------+------+--------+
| SNInt16       | SNInt16IO  | Signed Integer   | 16   | Native |
+---------------+------------+------------------+------+--------+
| UBInt32       | UBInt32IO  | Unsigned Integer | 32   | Big    |
+---------------+------------+------------------+------+--------+
| SBInt32       | SBInt32IO  | Signed Integer   | 32   | Big    |
+---------------+------------+------------------+------+--------+
| ULInt32       | ULInt32IO  | Unsigned Integer | 32   | Little |
+---------------+------------+------------------+------+--------+
| SLInt32       | SLInt32IO  | Signed Integer   | 32   | Little |
+---------------+------------+------------------+------+--------+
| UNInt32       | UNInt32IO  | Unsigned Integer | 32   | Native |
+---------------+------------+------------------+------+--------+
| SNInt32       | SNInt32IO  | Signed Integer   | 32   | Native |
+---------------+------------+------------------+------+--------+
| UBInt64       | UBInt64IO  | Unsigned Integer | 64   | Big    |
+---------------+------------+------------------+------+--------+
| SBInt64       | SBInt64IO  | Signed Integer   | 64   | Big    |
+---------------+------------+------------------+------+--------+
| ULInt64       | ULInt64IO  | Unsigned Integer | 64   | Little |
+---------------+------------+------------------+------+--------+
| SLInt64       | SLInt64IO  | Signed Integer   | 64   | Little |
+---------------+------------+------------------+------+--------+
| UNInt64       | UNInt64IO  | Unsigned Integer | 64   | Native |
+---------------+------------+------------------+------+--------+
| SNInt64       | SNInt64IO  | Signed Integer   | 64   | Native |
+---------------+------------+------------------+------+--------+
| BFloat32      | BFloat32IO | IEEE Float       | 32   | Big    |
+---------------+------------+------------------+------+--------+
| LFloat32      | LFloat32IO | IEEE Float       | 32   | Little |
+---------------+------------+------------------+------+--------+
| NFloat32      | NFloat32IO | IEEE Float       | 32   | Native |
+---------------+------------+------------------+------+--------+
| BFloat64      | BFloat64IO | IEEE Float       | 64   | Big    |
+---------------+------------+------------------+------+--------+
| LFloat64      | LFloat64IO | IEEE Float       | 64   | Little |
+---------------+------------+------------------+------+--------+
| NFloat64      | NFloat64IO | IEEE Float       | 64   | Native |
+---------------+------------+------------------+------+--------+
