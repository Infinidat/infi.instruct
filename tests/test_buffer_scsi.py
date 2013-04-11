from infi.unittest import TestCase
from infi.instruct.buffer import (Buffer, be_int_field, str_field, list_field, bytes_ref, total_size, b_uint8,
                                  bytearray_field, after_ref, member_func_ref, str_type)

SES_PAGE_SAMPLE = \
    ("\x01\x00\x00\xCC" +
     "\x00\x00\x00\x01\x12\x00\x08\x24\x50\x00\x93\xD0\x00\x6A\x70\x00" +
     "\x4E\x45\x57\x49\x53\x59\x53\x20\x4E\x44\x53\x2D\x34\x36\x30\x30" +
     "\x2D\x4A\x44\x20\x20\x20\x20\x20\x42\x35\x30\x37\x17\x3C\x00\x10" +
     "\x9E\x01\x00\x10\x02\x02\x00\x10\x03\x04\x00\x10\x04\x06\x00\x10" +
     "\x06\x01\x00\x10\x07\x02\x00\x10\x18\x06\x00\x10\x41\x72\x72\x61" +
     "\x79\x20\x44\x65\x76\x20\x53\x6C\x6F\x74\x20\x20\x34\x36\x30\x30" +
     "\x20\x45\x6E\x63\x6C\x6F\x73\x75\x72\x65\x20\x20\x50\x6F\x77\x65" +
     "\x72\x20\x53\x75\x70\x70\x6C\x79\x20\x20\x20\x20\x43\x6F\x6F\x6C" +
     "\x69\x6E\x67\x20\x46\x61\x6E\x20\x20\x20\x20\x20\x54\x65\x6D\x70" +
     "\x20\x53\x65\x6E\x73\x6F\x72\x20\x20\x20\x20\x20\x42\x75\x7A\x7A" +
     "\x65\x72\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x45\x53\x20\x50" +
     "\x72\x6F\x63\x65\x73\x73\x6F\x72\x20\x20\x20\x20\x53\x41\x53\x20" +
     "\x45\x78\x70\x61\x6E\x64\x65\x72\x20\x20\x20\x20")

# Output from sg_ses -p 0x1:
#
#   NEWISYS   NDS-4600-JD       B507
# Configuration diagnostic page:
#   number of secondary subenclosures: 0
#   generation code: 0x1
#   enclosure descriptor list
#     Subenclosure identifier: 0 (primary)
#       relative ES process id: 1, number of ES processes: 2
#       number of type descriptor headers: 8
#       enclosure logical identifier (hex): 500093d0006a7000
#       enclosure vendor: NEWISYS   product: NDS-4600-JD       rev: B507
#   type descriptor header/text list
#     Element type: Array device slot, subenclosure id: 0
#       number of possible elements: 60
#       text: Array Dev Slot
#     Element type: vendor specific [0x9e], subenclosure id: 0
#       number of possible elements: 1
#       text: 4600 Enclosure
#     Element type: Power supply, subenclosure id: 0
#       number of possible elements: 2
#       text: Power Supply
#     Element type: Cooling, subenclosure id: 0
#       number of possible elements: 4
#       text: Cooling Fan
#     Element type: Temperature sensor, subenclosure id: 0
#       number of possible elements: 6
#       text: Temp Sensor
#     Element type: Audible alarm, subenclosure id: 0
#       number of possible elements: 1
#       text: Buzzer
#     Element type: Enclosure services controller electronics, subenclosure id: 0
#       number of possible elements: 2
#       text: ES Processor
#     Element type: SAS expander, subenclosure id: 0
#       number of possible elements: 6
#       text: SAS Expander


class EnclosureDescriptor(Buffer):
    enclosure_services_processes_num = be_int_field(where=bytes_ref[0].bits[0:3])
    relative_enclosure_services_process_identifier = be_int_field(where=bytes_ref[0].bits[4:7])
    subenclosure_identifier = be_int_field(where=bytes_ref[1])
    type_descriptor_headers_num = be_int_field(where=bytes_ref[2])
    enclosure_descriptor_length = be_int_field(where=bytes_ref[3])
    enclosure_logical_identifier = bytearray_field(where=bytes_ref[4:12])  # FIXME use NAA stuff
    enclosure_vendor_identification = str_field(where=bytes_ref[12:20])
    product_identification = str_field(where=bytes_ref[20:36])
    product_revision_level = str_field(where=bytes_ref[36:40])  # FIXME use INQUIRY stuff
    vendor_specific_enclosure_information = bytearray_field(where_when_pack=bytes_ref[40:],
                                                            where_when_unpack=bytes_ref[40:enclosure_descriptor_length + 4])


class TypeDescriptorHeader(Buffer):
    element_type = be_int_field(where=bytes_ref[0])
    possible_elements_num = be_int_field(where=bytes_ref[1])
    subenclosure_identifier = be_int_field(where=bytes_ref[2])
    type_descriptor_text_length = be_int_field(where=bytes_ref[3])


class ConfigurationDiagnosticPage(Buffer):
    def _calc_num_type_descriptor_headers(self):
        return sum(desc.type_descriptor_headers_num for desc in self.enclosure_descriptor_list)

    def _unpack_type_descriptor_text(self, buffer, index, **kwargs):
        l = self.type_descriptor_header_list[index].type_descriptor_text_length
        return str(buffer[0:l]), l

    page_code = be_int_field(where=bytes_ref[0])
    secondary_subenclosures_num = be_int_field(where=bytes_ref[1])
    page_length = be_int_field(where=bytes_ref[2:4], set_before_pack=total_size - 4)
    generation_code = be_int_field(where=bytes_ref[4:8])
    enclosure_descriptor_list = list_field(type=EnclosureDescriptor,
                                           where=bytes_ref[8:],
                                           n=secondary_subenclosures_num + 1)
    type_descriptor_header_list = list_field(where=bytes_ref[after_ref(enclosure_descriptor_list):],
                                             type=TypeDescriptorHeader,
                                             n=member_func_ref(_calc_num_type_descriptor_headers))
    type_descriptor_text_list = list_field(where=bytes_ref[after_ref(type_descriptor_header_list):],
                                           type=str_type,
                                           unpack_selector=_unpack_type_descriptor_text,
                                           n=member_func_ref(_calc_num_type_descriptor_headers))

    def _calc_num_type_descriptor_headers(self):
        return sum(o.type_descriptor_headers_num for o in self.enclosure_descriptor_list)


class BufferSCSITestCase(TestCase):
    def test_configuration_diagnostics_page(self):
        raw = SES_PAGE_SAMPLE
        page = ConfigurationDiagnosticPage()
        page.unpack(raw)
        self.assertEquals(len(page.enclosure_descriptor_list), 1)
        self.assertEquals(len(page.type_descriptor_header_list), 8)
        self.assertEquals(len(page.type_descriptor_text_list), 8)
        # print(page)
