from infi.exceptools import InfiException

class InstructError(InfiException):
    pass

class NotEnoughDataError(InstructError):
    pass

class StructNotWellDefinedError(InstructError):
    pass

class BitFieldNotInByteBoundry(InstructError):
    pass

class FieldTypeNotSupportedError(InstructError):
    pass

class InvalidValueError(InstructError):
    pass
