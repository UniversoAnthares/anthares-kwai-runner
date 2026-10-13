#!/usr/bin/env python3
"""Cross-branch ARA contract guard; static checks, no credentials or device access."""
import argparse
import pathlib
import re
import sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mcp", required=True, type=pathlib.Path)
    p.add_argument("--agent", required=True, type=pathlib.Path)
    p.add_argument("--control", required=True, type=pathlib.Path)
    args = p.parse_args()
    mcp, agent, control = (x.read_text(encoding="utf-8") for x in (args.mcp, args.agent, args.control))
    tools = re.findall(r"registerTool\(['\"]([^'\"]+)", mcp)
    operations = sorted(set(re.findall(r"\bexecute\(['\"]([^'\"]+)", mcp)))
    failures = []
    if not tools: failures.append("MCP exposes no registerTool definitions")
    if len(tools) != len(set(tools)): failures.append("duplicate MCP tool names")
    if '/v1/control/execute' not in mcp: failures.append("MCP control execute route missing")
    if '/v1/control/execute' not in control: failures.append("control execute route missing")
    if 'timeout_seconds' not in control: failures.append("control timeout contract missing")
    if 'timeout_seconds' not in agent: failures.append("Windows agent timeout contract missing")
    # Agent operations can be implemented in sibling Go files; concatenate them in CI.
    for op in operations:
        if not re.search(r"['\"]" + re.escape(op) + r"['\"]", agent):
            failures.append("MCP operation not recognized by Windows source: " + op)
    print("MCP tools:", len(tools))
    print("MCP Windows operations:", ", ".join(operations))
    print("Control execute endpoint: present" if '/v1/control/execute' in control else "Control execute endpoint: missing")
    if failures:
        for f in failures: print("FAIL:", f, file=sys.stderr)
        return 1
    print("PASS: static cross-branch contracts; NOT a live end-to-end test")
    return 0

if __name__ == "__main__":
    sys.exit(main())
