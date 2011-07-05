from docutils import nodes
from docutils.parsers.rst import directives
from infi.vendata.msim.infra.rest import REST_API_ROOT
from infi.vendata.msim.utils.protocol_conformance.example_formatter import format_http_json_request_response

from sphinx.util.compat import Directive


class APIExampleCase(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    def run(self):
        name = self.arguments[0]
        case = self._get_case(name)
        returned = []
        for action in case.get_action_sequence():
            request, response = format_http_json_request_response(action, path_prefix=REST_API_ROOT)
            returned.extend([
                    nodes.strong(text="SEND:"),
                    nodes.literal_block(text=request),
                    nodes.strong(text="RECEIVE:"),
                    nodes.literal_block(text=response),
                    ])
        return returned
    def _get_case(self, name):
        if ":" not in name:
            raise ValueError("Invalid example name: {!r}".format(name))
        module_name, object_name = name.rsplit(":", 1)
        module = self._get_module(module_name)
        return getattr(module, object_name).CASE
    def _get_module(self, module_name):
        returned = __import__(module_name)
        path = module_name.split(".")
        for p in path[1:]:
            returned = getattr(returned, p)
        return returned

def setup(app):
    directives.register_directive('api_example_case', APIExampleCase)

