from collections import defaultdict, Counter


class Pipeline:
    def __init__(self, services, input_service, responder_service, last_chance_service, timeout_service):
        self.last_chance_service = last_chance_service
        self.timeout_service = timeout_service
        wrong_names = [k for k, v in Counter([i.name for i in services]).items() if v != 1]
        if wrong_names:
            raise ValueError(f'there are some duplicate service names presented {wrong_names}')

        self.services = {i.name: i for i in services}
        wrong_links = self.process_service_names()
        if wrong_links:
            print('wrong links in config were detected: ', dict(wrong_links))

        self.add_input_service(input_service)
        self.add_responder_service(responder_service)
        self.fill_dependent_service_chains_and_required_services()

    def get_service_by_name(self, service_name):
        if not service_name:
            return None

        service = self.services.get(service_name, None)
        if not service:
            raise ValueError(f'service {service_name} does not exist')
        return service

    def process_service_names(self):
        wrong_names = defaultdict(list)
        for service in self.services.values():
            for name_prev_service in service.names_previous_services.union(service.names_required_previous_services):
                if name_prev_service not in self.services:
                    wrong_names[service.name].append(name_prev_service)
                    continue
                service.previous_services.add(self.services[name_prev_service])
                self.services[name_prev_service].next_services.add(service)
        return wrong_names  # wrong names means that some service_names, used in previous services don't exist

    def get_next_services(self, done: set = None, waiting: set = None, skipped: set = None):
        done = done or set()
        waiting = waiting or set()
        skipped = skipped or set()

        if (self.last_chance_service and self.last_chance_service.name in done) or \
           (self.timeout_service and self.timeout_service.name in done):
            return [service for service in self.services.values() if service.is_responder()]
        completed_names = done | skipped
        service_names = set(self.services.keys())
        next_service_names = set()
        while service_names:
            sn = service_names.pop()
            service = self.services[sn]
            if {i.name for i in service.previous_services} <= completed_names:
                next_service_names.add(sn)
            else:
                for i in service.next_services:
                    service_names.discard(i.name)

        next_service_names = next_service_names - completed_names - waiting

        next_services = []
        for sn in next_service_names:
            service = self.services[sn]
            if not {i.name for i in service.previous_services} <= skipped:
                next_services.append(service)

        if not next_services and not waiting:
            return [self.last_chance_service]

        return next_services

    def add_responder_service(self, service):
        if not service.is_responder():
            raise ValueError('service should be a responder')
        endpoints = [s for s in self.services.values() if not s.next_services and 'responder' not in s.tags]
        service.previous_services = set(endpoints)
        service.names_previous_services = {s.name for s in endpoints}
        self.services[service.name] = service

        for s in endpoints:
            self.services[s.name].next_services.add(service)

    def add_input_service(self, service):
        if not service.is_input():
            raise ValueError('service should be an input')
        starting_services = [s for s in self.services.values() if not s.previous_services]
        service.next_services = set(starting_services)
        self.services[service.name] = service

        for s in starting_services:
            self.services[s.name].previous_services.add(service)

    def topological_sort(self):
        order, nodes, state = [], set(self.services.keys()), {}

        def dfs(node, path):
            state[node] = 0
            for ns in self.services[node].next_services:
                ns_status = state.get(ns.name, None)
                if ns_status == 0:
                    raise ValueError(f'Pipeline cycle was found {path}')
                elif ns_status == 1:
                    continue
                nodes.discard(ns.name)
                dfs(ns.name, path + [ns.name])
            order.append(node)
            state[node] = 1

        starting_node = [i for i in self.services.values() if i.is_input()][0]
        nodes.discard(starting_node.name)
        dfs(starting_node.name, [])
        return order

    def fill_dependent_service_chains_and_required_services(self):
        for sn in self.topological_sort():
            service = self.services[sn]
            for i in service.names_required_previous_services:
                req = self.services[i]
                service.required_previous_services.add(req)
                req.dependent_services.add(service)
                for ds in service.dependent_services:
                    req.dependent_services.add(ds)
