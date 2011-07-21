from infi.exceptools import InfiException

class InstructError(InfiException):
    pass

class NotEnoughDataError(InstructError):
    def __init__(self, expected, actually_read):
        super(NotEnoughDataError, self).__init__("expected to read %d bytes but read only %d bytes instead" %
                                                 (expected, actually_read))

class StructNotWellDefinedError(InstructError):
    pass

class BitFieldNotInByteBoundry(InstructError):
    pass

class FieldTypeNotSupportedError(InstructError):
    pass

class InvalidValueError(InstructError):
    pass

class ValidationValueIsNoneError(InstructError):
    def __init__(self):
        super(ValidationValueIsNoneError, self).__init__("Value cannot be None")
