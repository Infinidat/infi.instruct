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
        FixedSizeString("vendor_specific", 20), 
        BitFields(BitPadding(5), # reserved
                  Flag("ius"), # SPC-5 specific
                  Flag("qas"), # SPC-5 specific
                  Flag("clocking") # SPC-5 specific
        ),
        Padding(1), # reserved
        FixedSizeString("version_descriptors", 16),
        Padding(22)
    ]
    
class StandardInquiryData(Struct):
    def is_extended_data_exist(self, stream):
        return self.additional_length >= StandardInquiryExtendedData.sizeof()
    
    _fields_ = [
        Lazy(
            BitFields(
                BitField("peripheral_device_type", 5),  # 0-4
                BitField("peripheral_qualifier", 3),    # 5-7
            ),
            BitFields(
                BitPadding(7),
                Flag("rmb"),
            ),
            UBInt8("version"),
            BitFields(
                BitField("response_data_format", 4),
                Flag("hisup"),
                Flag("normaca"),
                BitPadding(2),      # 6-7: obsolete
            ),
            UBInt8("additional_length"),
            BitFields(
                Flag("protect"),
                BitPadding(2), # reserved
                Flag("3pc"),
                BitField("tpgs", 2),
                Flag("acc"),
                Flag("sccs"),
            ),
            BitFields(BitPadding(1), # obsolete
                      Flag("enc_serv"),
                      Flag("vs"),
                      Flag("multi_p"),
                      BitPadding(3), # obsolete
                      Flag("addr16")), # SPC-5 specific
            BitFields(BitPadding(2), # obsolete
                      Flag("wbus16"), # SPC-5 specific
                      Flag("sync"), # SPC-5 specific
                      BitPadding(2), # obsolete
                      Flag("cmd_que"),
                      Flag("vs")),
            FixedSizeString("t10_vendor_identification", 8),
            FixedSizeString("product_identification", 16),
            FixedSizeString("product_revision_level", 4),
        ),
        OptionalField("extended", StandardInquiryExtendedData, is_extended_data_exist)
   ]

def test_inquiry_create():
    command = InquiryCommand.create(evpd=0, page_code=0x0, allocation_length=96)
    assert InquiryCommand.instance_to_string(command) == '\x12\x00\x00\x00\x60\x00'

def test_standard_inquiry_parse():
    serialized_data = '\x00\x00\x05\x02[\x00\x00\x00ATA     ST9320423AS     0003\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00`\x03 \x02`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    data = StandardInquiryData.create_instance_from_string(serialized_data)

    assert data.t10_vendor_identification == 'ATA     '
    assert data.product_identification == 'ST9320423AS     '
    assert data.product_revision_level == '0003'
    assert data.extended is not None
    assert data.extended.version_descriptors == '\x00`\x03 \x02`\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
