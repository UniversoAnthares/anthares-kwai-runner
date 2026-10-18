"""Parse both tab-separated and padded `adb devices -l` output."""


def online_devices(output):
    rows = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue
        row = {"serial": parts[0]}
        for part in parts[2:]:
            if ":" in part:
                key, value = part.split(":", 1)
                row[key] = value
        rows.append(row)
    return rows
