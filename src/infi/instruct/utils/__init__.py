import traceback
import itertools

def format_exception(exc_info, indent=""):
    line_groups = [ line.strip("\n") for line in traceback.format_exception(*exc_info) ]
    lines = itertools.chain(*[ lines.split("\n") for lines in line_groups ])
    return "\n".join([ "{0}{1}".format(indent, line) for line in lines ])
