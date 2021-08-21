Out of Band (OOB)
==================

Inherit from the abstract base class

    programy.oob.oob.OutOfBandProcessor

This class is the base class for a OOB processors. A single method must be implemented in your versions. This method
execute_oob_command should process the xml object contained in _xml object attribute.

    class OutOfBandProcessor(object):

    def __init__(self):
        self._xml = None

    # Override this method to extract the data for your command
    # See actual implementations for details of how to do this
    def parse_oob_xml(self, oob: ET.Element):
        self._xml = oob
        return True

    # Override this method in your own class to do something
    # useful with the command data
    def execute_oob_command(self, bot, clientid):
        return ""

    def process_out_of_bounds(self, bot, clientid, oob: ET.Element):
        if self.parse_oob_xml(oob) is True:
            return self.execute_oob_command(bot, clientid)
        else:
            return ""
