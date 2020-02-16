class Service:
    def __init__(self, name, connector_func, state_processor_method=None,
                 batch_size=1, tags=None, names_previous_services=None,
                 names_required_previous_services=None,
                 workflow_formatter=None, dialog_formatter=None, response_formatter=None,
                 label=None):
        self.name = name
        self.batch_size = batch_size
        self.state_processor_method = state_processor_method
        self.names_previous_services = names_previous_services or set()
        self.names_required_previous_services = names_required_previous_services or set()
        self.tags = set(tags or [])
        self.workflow_formatter = workflow_formatter
        self.dialog_formatter = dialog_formatter
        self.response_formatter = response_formatter
        self.connector_func = connector_func
        self.previous_services = set()
        self.required_previous_services = set()
        self.dependent_services = set()
        self.next_services = set()
        self.label = label or self.name

    def is_sselector(self):
        return 'selector' in self.tags

    def is_responder(self):
        return 'responder' in self.tags

    def is_input(self):
        return 'input' in self.tags

    def is_last_chance(self):
        return 'last_chance' in self.tags

    def is_timeout(self):
        return 'timeout' in self.tags

    def apply_workflow_formatter(self, payload):
        if not self.workflow_formatter:
            return payload
        return self.workflow_formatter(payload)

    def apply_dialog_formatter(self, payload):
        if not self.dialog_formatter:
            return [self.apply_workflow_formatter(payload)]
        return self.dialog_formatter(self.apply_workflow_formatter(payload))

    def apply_response_formatter(self, payload):
        if not self.response_formatter:
            return payload
        return self.response_formatter(payload)


def simple_workflow_formatter(workflow_record):
    return workflow_record['dialog'].to_dict()
