from collections import defaultdict
from collections import deque


# TODO(pugin): refactor after tasks will be introduced
class CurrentLoadStatsClass:
    def __init__(self):
        self.services_load = defaultdict(int)
        self.services_response_time = dict()

    async def register_stats(self, service_name, val, req_type, **kwargs):
        if service_name == 'input':
            if req_type == 'send':
                self.services_load['agent'] += 1
        elif service_name.endswith('responder'):
            if req_type == 'done':
                self.services_load['agent'] -= 1
        else:
            if req_type == 'send':
                self.services_load[service_name] += 1
            elif req_type == 'done':
                self.services_load[service_name] -= 1
                if 'service_send_time' in kwargs and 'service_response_time' in kwargs:
                    if service_name not in self.services_response_time:
                        self.services_response_time[service_name] = deque(maxlen=20)
                    self.services_response_time[service_name].append(
                        kwargs['service_response_time'] - kwargs['service_send_time']
                    )

    def get_current_load(self):
        response = {
            'current_load': dict(self.services_load),
            'response_time': {}
        }
        for k, v in self.services_response_time.items():
            sm = sum(v)
            ct = len(v)
            if ct:
                response['response_time'][k] = sm / ct
        return response
