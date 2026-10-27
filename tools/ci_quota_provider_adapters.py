"""Provider cancellation/status adapters. No network at import time.

Use ONLY after a confirmed quota signal for an exact owned run/pipeline.
Never print API authorization credentials or invoke fallback by itself.
"""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ProviderUncertain(Exception):
    pass


def http_json(method: str, url: str, headers: dict) -> tuple[int, dict]:
    req = Request(url, method=method, headers=headers)
    try:
        with urlopen(req, timeout=12) as resp:
            data = resp.read(262144)
            return resp.status, json.loads(data) if data else {}
    except HTTPError as err:
        return err.code, {}
    except (URLError, OSError, ValueError):
        raise ProviderUncertain("PROVIDER_API_UNCERTAIN") from None


class GitHubActionsRun:
    def __init__(self, owner, repo, run_id, token, request=http_json):
        if not (owner and repo and str(run_id).isdigit() and token):
            raise ValueError("INVALID_RUN_IDENTITY")
        self.url = ("https://api.github.com/repos/" + quote(owner,safe="") + "/" +
                    quote(repo,safe="") + "/actions/runs/" + str(run_id))
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer " + token,
        }
        self.request = request

    def cancel(self, _attempt_id):
        code, _ = self.request("POST", self.url + "/cancel", self.headers)
        # 409 means perhaps already completed; verify exact run before acknowledging.
        return code in (202, 204) or (code == 409 and self.status(_attempt_id) in ("CANCELLED","FAILED"))

    def status(self, _attempt_id):
        code, data = self.request("GET", self.url, self.headers)
        if code != 200:
            return "UNKNOWN"
        if data.get("status") != "completed":
            return "RUNNING"
        conclusion = data.get("conclusion")
        if conclusion in ("cancelled","skipped"): return "CANCELLED"
        if conclusion in ("failure","timed_out","action_required"): return "FAILED"
        if conclusion == "success": return "SUCCEEDED"
        return "UNKNOWN"


class GitLabPipeline:
    def __init__(self, project_id, pipeline_id, token, request=http_json):
        if not (str(project_id).strip() and str(pipeline_id).isdigit() and token):
            raise ValueError("INVALID_PIPELINE_IDENTITY")
        self.url = ("https://gitlab.com/api/v4/projects/" +
                    quote(str(project_id),safe="") + "/pipelines/" + str(pipeline_id))
        self.headers = {"PRIVATE-TOKEN": token, "Accept": "application/json"}
        self.request = request

    def cancel(self, _attempt_id):
        code, _ = self.request("POST", self.url + "/cancel", self.headers)
        return code == 200

    def status(self, _attempt_id):
        code, data = self.request("GET", self.url, self.headers)
        if code != 200:
            return "UNKNOWN"
        state = data.get("status")
        if state == "canceled": return "CANCELLED"
        if state == "failed": return "FAILED"
        if state == "success": return "SUCCEEDED"
        return "RUNNING" if state in ("running","pending","created","preparing","waiting_for_resource","scheduled") else "UNKNOWN"
