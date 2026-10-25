"""AI-04 real HTTP consumer, QA ONLY: no real models, billing or publication."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from ai_hub.eligibility_breaker import CircuitBreaker, UpstreamOutcomeError, dispatch

class LoopbackTextConsumer:
    def __init__(self, candidates, breaker=None, timeout=0.15):
        if not candidates or not 0 < timeout <= 3:
            raise ValueError("invalid_qa_consumer_configuration")
        self.endpoints = {}
        self.policies = []
        for policy, url in candidates:
            parsed = urlsplit(url)
            if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username or parsed.password:
                raise ValueError("external_provider_forbidden_in_qa")
            if policy.name in self.endpoints:
                raise ValueError("duplicate_provider")
            self.policies.append(policy)
            self.endpoints[policy.name] = url
        self.breaker = breaker if breaker is not None else CircuitBreaker()
        self.timeout = timeout

    def text(self, prompt):
        if not isinstance(prompt, str) or not prompt.startswith("qa_") or len(prompt) > 256:
            raise ValueError("synthetic_qa_data_only")
        def http_call(name):
            body = json.dumps({"task": "text", "input": prompt}, sort_keys=True).encode()
            req = Request(self.endpoints[name], data=body, method="POST",
                          headers={"Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise UpstreamOutcomeError(response.status)
                    result = json.loads(response.read(4096))
                    if result.get("accepted") is not True or not isinstance(result.get("output"), str):
                        raise UpstreamOutcomeError(503)
                    return result["output"]
            except HTTPError as exc:
                code = exc.code
                exc.close()
                raise UpstreamOutcomeError(code) from exc
            except (TimeoutError, ConnectionError, URLError) as exc:
                raise TimeoutError("local_qa_upstream_timeout") from exc
        return dispatch("text", self.policies, self.breaker, http_call)
