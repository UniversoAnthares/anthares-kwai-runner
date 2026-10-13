class JobsProxy:
    def __init__(self, relay, device):
        self.relay = relay
        self.device = device

    def __setitem__(self, job_id, job):
        existing = self.relay.get_job(self.device, job_id)
        if existing:
            return
        self.relay._store().enqueue(
            self.device,
            job.get("type") or "unknown",
            job.get("args") or {},
            job.get("timeout_seconds") or 30,
            job_id=job_id,
        )

    def get(self, job_id, default=None):
        return self.relay.get_job(self.device, job_id) or default


class QueueProxy:
    def append(self, job_id):
        # JobsProxy already inserted the durable job. Kept for legacy API compatibility.
        return None

    def __len__(self):
        return 0


class DeviceProxy:
    def __init__(self, relay, device):
        self.relay = relay
        self.device = device
        self.jobs = JobsProxy(relay, device)
        self.queue = QueueProxy()

    def __getitem__(self, key):
        if key == "jobs":
            return self.jobs
        if key == "queue":
            return self.queue
        if key == "heartbeat":
            return self.relay.device_status(self.device).get("heartbeat")
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key == "heartbeat":
            self.relay._store().heartbeat(self.device, value or {})
            return
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class DevicesProxy:
    def __init__(self, relay):
        self.relay = relay
        self._proxies = {}

    def setdefault(self, device, default=None):
        if device not in self._proxies:
            self._proxies[device] = DeviceProxy(self.relay, device)
        return self._proxies[device]
