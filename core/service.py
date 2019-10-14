class Service:
    def __init__(self, name, connector_func, state_processor_method=None,
                 batch_size=1, tags=None, names_previous_services=None,
                 workflow_formatter=None):
        self.name = name
        self.batch_size = batch_size
        self.state_processor_method = state_processor_method
        self.names_previous_services = names_previous_services or set()
        self.tags = tags or []
        self.workflow_formatter = workflow_formatter
        self.connector_func = connector_func
        self.previous_services = set()
        self.next_services = set()

    def is_sselector(self):
        return 'selector' in self.tags

    def is_responder(self):
        return 'responder' in self.tags

    def is_input(self):
        return 'input' in self.tags

    def apply_workflow_formatter(self, workflow_record):
        if not self.workflow_formatter:
            return workflow_record
        return self.workflow_formatter(workflow_record)
