import binascii
from infi.instruct import *

class OperationCode(Struct):
    _fields_ = BitFields(
        BitField("command_code", 5, default=None),
        BitField("group_code", 3, default=None)
    )

# sam5r07: 5.2 (page 70)
class Control(Struct):
    _fields_ = BitFields(BitPadding(2), # 0-1: obsolete
                         BitField("naca", 1, 0),
                         BitPadding(3), # 3-5: reserved
                         BitField("vendor_specific", 2, 0), # 6-7: vendor specific
                    )

class InquiryCommand(Struct):
    _fields_ = [
        ConstField("opcode", OperationCode(command_code=0x12, group_code=0)),
        BitFields(
            BitField("evpd", 1),
            BitPadding(7)
        ),
        UBInt8("page_code"),
        Padding(1),
        UBInt8("allocation_length"),
        Field("control", Control, Control())
    ]

class StandardInquiryExtendedData(Struct):
    _fields_ = [
        PaddedString("vendor_specific", 20), 
        BitFields(BitPadding(5), # reserved
                  BitFlag("ius"), # SPC-5 specific
                  BitFlag("qas"), # SPC-5 specific
                  BitFlag("clocking") # SPC-5 specific
        ),
        Padding(1), # reserved
        FixedSizeBuffer("version_descriptors", 16),
        Padding(22)
    ]
    
class StandardInquiryData(Struct):
    def is_extended_data_exist(self, stream, context):
        return self.additional_length >= StandardInquiryExtendedData.min_max_sizeof().min
    
    _fields_ = [
        Lazy(
            BitFields(
                BitField("peripheral_device_type", 5),  # 0-4
                BitField("peripheral_qualifier", 3),    # 5-7
            ),
            BitFields(
                BitPadding(7),
                BitFlag("rmb"),
            ),
            UBInt8("version"),
            BitFields(
                BitField("response_data_format", 4),
                BitFlag("hisup"),
                BitFlag("normaca"),
                BitPadding(2),      # 6-7: obsolete
            ),
            UBInt8("additional_length"),
            BitFields(
                BitFlag("protect"),
                BitPadding(2), # reserved
                BitFlag("3pc"),
                BitField("tpgs", 2),
                BitFlag("acc"),
                BitFlag("sccs"),
            ),
            BitFields(BitPadding(1), # obsolete
                      BitFlag("enc_serv"),
                      BitFlag("vs"),
                      BitFlag("multi_p"),
                      BitPadding(3), # obsolete
                      BitFlag("addr16")), # SPC-5 specific
            BitFields(BitPadding(2), # obsolete
                      BitFlag("wbus16"), # SPC-5 specific
                      BitFlag("sync"), # SPC-5 specific
                      BitPadding(2), # obsolete
                      BitFlag("cmd_que"),
                      BitFlag("vs")),
            PaddedString("t10_vendor_identification", 8),
            PaddedString("product_identification", 16),
            PaddedString("product_revision_level", 4),
        ),
        OptionalField("extended", StandardInquiryExtendedData, is_extended_data_exist)
   ]

def test_inquiry_create():
    command = InquiryCommand(evpd=0, page_code=0x0, allocation_length=96)
    assert InquiryCommand.write_to_string(command) == '\x12\x00\x00\x00\x60\x00'

def test_standard_inquiry_parse():
    serialized_data = '\x00\x00\x05\x02[\x00\x00\x00ATA     ST9320423AS     0003\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`\x03 \x02`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    data = StandardInquiryData.create_from_string(serialized_data)

    assert data.t10_vendor_identification == 'ATA     ', data.t10_vendor_identification
    assert data.product_identification == 'ST9320423AS     '
    assert data.product_revision_level == '0003'
    assert data.extended is not None
    assert data.extended.version_descriptors == '\x00`\x03 \x02`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', repr(data.extended.version_descriptors)
    
