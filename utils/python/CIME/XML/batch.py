"""
Interface to the config_batch.xml file.  This class inherits from GenericXML.py

The batch_system type="foo" blocks define most things. Machine-specific overrides
can be defined by providing a batch_system MACH="mach" block.
"""

from CIME.XML.standard_module_setup import *
from CIME.XML.generic_xml import GenericXML
from CIME.utils import expect, get_cime_root, get_model

logger = logging.getLogger(__name__)

class Batch(GenericXML):

    def __init__(self, batch_system=None, machine=None, infile=None):
        """
        initialize an object
        """
        if infile is None:
            infile = os.path.join(get_cime_root(), "cime_config", get_model(), "machines", "config_batch.xml")

        GenericXML.__init__(self, infile)

        self.batch_nodes  = None # List from last to first
        self.batch_system = batch_system
        self.machine      = machine

        if self.batch_system is not None:
            self.set_batch_system(self.batch_system, machine=machine)

    def get_batch_system(self):
        """
        Return the name of the batch system
        """
        return self.batch_system

    def get_optional_batch_node(self, nodename, attributes=None):
        """
        Return data on a node for a batch system
        """
        expect(self.batch_nodes is not None, "Batch system not set, use parent get_node?")

        for batch_node in self.batch_nodes:
            result = self.get_optional_node(nodename, attributes, root=batch_node)
            if result is None:
                return result

        return None

    def _is_compatible(self, node, batch_system, machine):
        for xmlid, value in [ ("type", batch_system), ("MACH", machine) ]:
            if value is not None and xmlid in node.attrib and value != node.get(xmlid):
                return False

        return True

    def set_batch_system(self, batch_system, machine=None):
        """
        Sets the batch system block in the Batch object
        """
        machine = machine if machine is not None else self.machine
        if self.batch_system != batch_system or self.batch_nodes is None or self.machine != machine:
            self.batch_nodes = []
            all_batch_nodes = self.get_nodes("batch_system")
            for batch_node in all_batch_nodes:
                if self._is_compatible(batch_node, batch_system, machine):
                    self.batch_nodes.append(batch_node)

            self.batch_nodes.reverse()
            expect(self.batch_nodes, "No batch system '%s' found for machine '%s'" % (batch_system, machine))

            self.machine = machine

    def get_value(self, name, resolved=True):
        """
        Get Value of fields in the config_batch.xml file
        """
        expect(self.batch_nodes is not None, "Batch object has no batch system defined")
        value = None

        node = self.get_optional_batch_node(name)
        if node is not None:
            value = node.text

        if value is None:
            # if all else fails
            value = GenericXML.get_value(self, name)

        if resolved:
            if value is not None:
                value = self.get_resolved_value(value)
            elif name in os.environ:
                value = os.environ[name]

        return value

    def get_batch_directives(self, batch_maker):
        """
        """
        result = []
        directive_prefix = self.get_value("batch_directive")
        directive_prefix = "" if directive_prefix is None else directive_prefix
        for batch_node in reversed(self.batch_nodes):
            directive_nodes = self.get_nodes("directive", root=batch_node)
            for directive_node in directive_nodes:
                directive = self.get_resolved_value("" if directive_node.text is None else directive_node.text)
                directive = batch_maker.transform_vars(directive, default=directive_node.get("default"))

                result.append("%s %s" % (directive_prefix, directive))

        return result

    def get_batch_jobs(self):
        """
        Return a dict of jobs with the first element the name of the case script
        and the second the template to start from, third the task count
        """
        jobs = list()
        jnode = self.get_node("batch_jobs")
        for child in jnode:
            if child.tag == "job":
                name = child.get("name")
                template_node = self.get_node("template",root=child)
                task_count_node = self.get_node("task_count",root=child)
                jobs.append((name, template_node.text, task_count_node.text))

        return jobs
