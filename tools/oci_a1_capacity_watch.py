#!/usr/bin/env python3
"""Cloud-only, fail-closed Oracle Always Free A1 availability watcher.

Authenticated exclusively from GitHub Actions encrypted secrets; never copies
the OCI API key to Windows, logs, or repository source. Does not publish Kwai.
"""
import base64
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

import oci
from oci.exceptions import ServiceError

A1 = "VM.Standard.A1.Flex"
NAME = "anthares-android-redroid-free"
REGION = "sa-saopaulo-1"
CPU, MEMORY_GB, BOOT_GB = 1, 6, 50
REDROID_ARM64_IMAGE = "redroid/redroid@sha256:3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb"
REDROID_AMD64_IMAGE = "redroid/redroid@sha256:e6f799d56b9a9a2bbc6224b5b7a6dc744c9b4d878ac856f27f0c4ec793ef55d3"
APPROVED_SUBNET_NAME = "anthares-android-subnet"
APPROVED_SUBNET_CIDR = "10.92.1.0/24"
APPROVED_SSH_KEY_SHA256 = "SHA256:g6uknj0s8zT/en4AJDmf/1+TjcwCKYrM5xRjYA3hM2w"



def report(key, value):
    print("ANTHARES_A1_{}={}".format(key, value), flush=True)


def pages(call, **kwargs):
    items, cursor = [], None
    while True:
        if cursor:
            kwargs["page"] = cursor
        response = call(**kwargs)
        items.extend(response.data)
        cursor = response.headers.get("opc-next-page")
        if not cursor:
            return items


def auth():
    raw = os.getenv("OCI_A1_WATCH_AUTH_JSON", "")
    if not raw:
        report("STATE", "UNCONFIGURED_GITHUB_SECRET")
        return None
    d = json.loads(raw)
    required = ("user", "tenancy", "fingerprint", "private_key", "region")
    if not isinstance(d, dict) or any(not d.get(k) for k in required):
        raise ValueError("AUTH_FIELDS_MISSING")
    if d["region"] != REGION or "-----BEGIN" not in d["private_key"]:
        raise ValueError("AUTH_REGION_OR_KEY_INVALID")
    signer = oci.signer.Signer(
        tenancy=d["tenancy"], user=d["user"],
        fingerprint=d["fingerprint"], private_key_file_location=None,
        private_key_content=d["private_key"]
    )
    # OCI SDK 2.187.1 validates the required config fields even with an
    # explicit oci.signer.Signer. The key_file sentinel is never accessed:
    # the signer signs using the in-memory encrypted Actions secret material.
    b = {"region": REGION, "tenancy": d["tenancy"], "user": d["user"],
         "fingerprint": d["fingerprint"], "key_file": "/dev/null"}
    kwargs = {"signer": signer, "retry_strategy": oci.retry.NoneRetryStrategy()}
    return d, oci.core.ComputeClient(b, **kwargs), \
        oci.core.VirtualNetworkClient(b, **kwargs), \
        oci.core.BlockstorageClient(b, **kwargs), \
        oci.identity.IdentityClient(b, **kwargs)


def private_network_egress_ready(network, subnet):
    """Require private subnet + healthy NAT before allocating no-public-IP VM.

    An internet gateway does not route outbound IPv4 from a VNIC without
    a public address, so allocating on the current Android public subnet
    would create an inaccessible Linux VM unable to fetch ReDroid packages.
    """
    if subnet.prohibit_public_ip_on_vnic is not True:
        return False
    routes = network.get_route_table(subnet.route_table_id).data.route_rules or []
    default = [r for r in routes if r.destination == "0.0.0.0/0"
               and r.destination_type == "CIDR_BLOCK"]
    if len(default) != 1:
        return False
    target = default[0].network_entity_id or ""
    if not target.startswith("ocid1.natgateway."):
        return False
    nat = network.get_nat_gateway(target).data
    return (nat.lifecycle_state == "AVAILABLE" and
            nat.vcn_id == subnet.vcn_id and
            nat.block_traffic is False)


def safe_instance_network_mode(network, subnet):
    """Choose only an audited, internet-reachable OCI network topology.

    PRIVATE_NAT: no public IPv4, private subnet with healthy NAT.
    LOCKED_PUBLIC: ephemeral public IPv4, with a single ingress rule: SSH
    from exactly one IPv4 /32. No exposed ADB/Kwai/Android services.
    Additional lists, protocols, ingress, stale gateway or ambiguous routes
    reject the launch. This does not modify live network resources.
    """
    import ipaddress

    routes = network.get_route_table(subnet.route_table_id).data.route_rules or []
    defaults = [r for r in routes if r.destination == "0.0.0.0/0"
                and r.destination_type == "CIDR_BLOCK"]
    if len(defaults) != 1:
        return None
    gateway_id = defaults[0].network_entity_id or ""

    if subnet.prohibit_public_ip_on_vnic is True:
        if not gateway_id.startswith("ocid1.natgateway."):
            return None
        nat = network.get_nat_gateway(gateway_id).data
        if (nat.lifecycle_state == "AVAILABLE" and
                nat.vcn_id == subnet.vcn_id and nat.block_traffic is False):
            return "PRIVATE_NAT"
        return None

    if subnet.prohibit_public_ip_on_vnic is not False:
        return None
    if not gateway_id.startswith("ocid1.internetgateway."):
        return None
    igw = network.get_internet_gateway(gateway_id).data
    if (igw.lifecycle_state != "AVAILABLE" or igw.vcn_id != subnet.vcn_id
            or igw.is_enabled is not True):
        return None
    if not subnet.security_list_ids or len(subnet.security_list_ids) != 1:
        return None
    firewall = network.get_security_list(subnet.security_list_ids[0]).data
    ingress = firewall.ingress_security_rules or []
    egress = firewall.egress_security_rules or []
    if len(ingress) != 1:
        return None
    rule = ingress[0]
    try:
        cidr = ipaddress.ip_network(rule.source, strict=True)
    except (ValueError, TypeError):
        return None
    tcp = rule.tcp_options
    port_range = tcp.destination_port_range if tcp else None
    if (cidr.version != 4 or cidr.prefixlen != 32 or
            rule.protocol != "6" or rule.is_stateless is not False or
            rule.source_type not in ("CIDR_BLOCK", None) or
            not port_range or port_range.min != 22 or port_range.max != 22):
        return None
    if not any(r.destination == "0.0.0.0/0" and r.protocol == "all"
               and r.destination_type in ("CIDR_BLOCK", None) for r in egress):
        return None
    return "LOCKED_PUBLIC"


def redroid_cloud_init_data():
    """Load the reviewed first-boot contract into OCI user_data, never a secret."""
    path = Path(__file__).resolve().parents[1] / (
        "infra/oci-android/redroid-firstboot.cloud-config.yml")
    data = path.read_bytes()
    if (not data.startswith(b"#cloud-config\n") or
            len(data) > 12_000 or
            b"127.0.0.1:5555:5555" not in data or
            b"0.0.0.0:5555" in data or
            b"--privileged" not in data or
            REDROID_ARM64_IMAGE.encode("ascii") not in data or
            REDROID_AMD64_IMAGE.encode("ascii") not in data or
            b'--platform "$PLATFORM"' not in data or
            b"/etc/modules-load.d/anthares-redroid.conf" not in data or
            b"options binder_linux devices=binder,hwbinder,vndbinder" not in data or
            b"docker start anthares-redroid" not in data):
        raise ValueError("UNSAFE_OR_MISSING_REDR0ID_BOOTSTRAP")
    return base64.b64encode(data).decode("ascii")


def approved_ssh_public_key():
    """Load a pinned public administrator SSH key; never load the private key."""
    key_file = Path(__file__).resolve().parents[1] / (
        "infra/oci-android/approved-admin-ssh.pub")
    parts = key_file.read_text(encoding="ascii").strip().split()
    if len(parts) not in (2, 3) or parts[0] != "ssh-ed25519":
        raise ValueError("APPROVED_SSH_KEY_TYPE_INVALID")
    try:
        blob = base64.b64decode(parts[1], validate=True)
    except (ValueError, base64.binascii.Error):
        raise ValueError("APPROVED_SSH_KEY_BASE64_INVALID") from None
    fingerprint = "SHA256:" + base64.b64encode(
        hashlib.sha256(blob).digest()).decode("ascii").rstrip("=")
    if fingerprint != APPROVED_SSH_KEY_SHA256:
        raise ValueError("APPROVED_SSH_KEY_FINGERPRINT_MISMATCH")
    return "ssh-ed25519 " + parts[1] + " anthares-oci-admin"


def approved_subnet(network, tenancy, optional_subnet_id=""):
    """Discover exactly one already-audited subnet; allocate nothing."""
    subnets = pages(network.list_subnets, compartment_id=tenancy)
    matches = [s for s in subnets
               if s.display_name == APPROVED_SUBNET_NAME
               and s.compartment_id == tenancy
               and s.cidr_block == APPROVED_SUBNET_CIDR
               and s.lifecycle_state == "AVAILABLE"]
    if len(matches) != 1:
        raise ValueError("ANDROID_SUBNET_NOT_UNIQUE_OR_NOT_APPROVED")
    subnet_id = matches[0].id
    if optional_subnet_id and optional_subnet_id != subnet_id:
        raise ValueError("SUBNET_OVERRIDE_DIFFERS_FROM_APPROVED")
    subnet = network.get_subnet(subnet_id).data
    if (subnet.id != subnet_id or subnet.compartment_id != tenancy
            or subnet.display_name != APPROVED_SUBNET_NAME
            or subnet.cidr_block != APPROVED_SUBNET_CIDR
            or subnet.lifecycle_state != "AVAILABLE"):
        raise ValueError("ANDROID_SUBNET_CHANGED_SINCE_DISCOVERY")
    return subnet


def approved_boot_access(network, tenancy, auth_data):
    """Validate the target network and SSH key without creating resources.

    Existing encrypted GitHub secret contains the five OCI signer fields.
    Optional legacy subnet/key overrides must match the pinned resources.
    """
    subnet = approved_subnet(
        network, tenancy, auth_data.get("subnet_id", ""))
    sshkey = approved_ssh_public_key()
    override = auth_data.get("ssh_public_key", "").strip()
    if override and override.split()[:2] != sshkey.split()[:2]:
        raise ValueError("SSH_KEY_OVERRIDE_DIFFERS_FROM_APPROVED")
    mode = safe_instance_network_mode(network, subnet)
    if mode is None:
        raise ValueError("NETWORK_EGRESS_OR_INGRESS_GUARD")
    return subnet, sshkey, mode


def launch_retry_token(tenancy, subnet_id):
    """Stable OCI idempotency token for this one approved Always Free VM.

    The token is tenant/subnet/shape scoped, excludes credentials, and OCI
    deduplicates matching launch requests for up to 24 hours. The separate
    full-tenancy inventory still gates every attempt.
    """
    scope = "|".join((REGION, tenancy, subnet_id, A1, NAME,
                      str(CPU), str(MEMORY_GB), str(BOOT_GB)))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, scope))


def occupied_block_volume_gib(volumes):
    """Count all active boot/block volumes; unknown sizes fail closed."""
    total = 0
    for volume in volumes:
        if volume.lifecycle_state in ("TERMINATED", "TERMINATING"):
            continue
        size = volume.size_in_gbs
        if size is None:
            raise ValueError("UNKNOWN_ACTIVE_VOLUME_SIZE")
        try:
            size = int(size)
        except (TypeError, ValueError):
            raise ValueError("INVALID_ACTIVE_VOLUME_SIZE") from None
        if size <= 0:
            raise ValueError("INVALID_ACTIVE_VOLUME_SIZE")
        total += size
    return total


def guarded_launch(compute, request, tenancy, subnet_id):
    """No automatic HTTP retry; one idempotent OCI launch request."""
    return compute.launch_instance(
        request, opc_retry_token=launch_retry_token(tenancy, subnet_id))


def main():
    session = auth()
    if session is None:
        return 0
    d, compute, network, block, identity = session
    tenancy = d["tenancy"]
    regions = pages(identity.list_region_subscriptions, tenancy_id=tenancy)
    if len([r for r in regions if r.region_name == REGION and r.status == "READY"]) != 1:
        raise ValueError("HOME_REGION_UNAVAILABLE")
    if any(r.region_name != REGION and r.status == "READY" for r in regions):
        raise ValueError("TENANCY_REGION_TOPOLOGY_CHANGED")
    ads = pages(identity.list_availability_domains, compartment_id=tenancy)
    if len(ads) != 1:
        raise ValueError("AD_TOPOLOGY_CHANGED")
    ad = ads[0].name
    cap_req = oci.core.models.CreateComputeCapacityReportDetails(
        compartment_id=tenancy, availability_domain=ad,
        shape_availabilities=[
            oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=A1,
                instance_shape_config=oci.core.models.CapacityReportInstanceShapeConfig(
                    ocpus=CPU, memory_in_gbs=MEMORY_GB))
        ]
    )
    response = compute.create_compute_capacity_report(cap_req)
    shape_states = [r.availability_status for r in response.data.shape_availabilities
                    if r.instance_shape == A1]
    if len(shape_states) != 1:
        raise ValueError("INVALID_CAPACITY_REPORT")
    state = shape_states[0]
    report("CAPACITY", state)
    # Preflight validates SSH, subnet and firewall even when A1 is out of stock.
    subnet, sshkey, mode = approved_boot_access(network, tenancy, d)
    subnet_id = subnet.id
    report("NETWORK_MODE", mode)
    report("PROVISION_PREFLIGHT", "READY_SSH_SUBNET_NETWORK")
    if state != "AVAILABLE":
        return 0

    if os.getenv("OCI_A1_AUTO_PROVISION") != "1" or \
       os.getenv("OCI_A1_LAUNCH_GUARD") != "ALWAYS_FREE_SINGLE_A1":
        report("STATE", "CAPACITY_AVAILABLE_PROVISIONING_NOT_ARMED")
        return 0

    # Fail closed on any uncertain inventory; never allocate over free limits.
    compartments = [tenancy]
    compartments.extend(c.id for c in pages(
        identity.list_compartments, compartment_id=tenancy,
        compartment_id_in_subtree=True, access_level="ACCESSIBLE")
        if c.lifecycle_state == "ACTIVE")
    active_a1, allocated_storage_gb = [], 0
    for compartment in compartments:
        active_a1.extend(x for x in pages(
            compute.list_instances, compartment_id=compartment)
            if x.shape == A1 and x.lifecycle_state not in ("TERMINATED", "TERMINATING"))
        allocated_storage_gb += occupied_block_volume_gib(pages(
            block.list_boot_volumes, compartment_id=compartment, availability_domain=ad))
        allocated_storage_gb += occupied_block_volume_gib(pages(
            block.list_volumes, compartment_id=compartment))
    if active_a1 or allocated_storage_gb + BOOT_GB > 200:
        report("STATE", "EXISTING_A1_OR_STORAGE_QUOTA_GUARD")
        return 0

    images = pages(compute.list_images, compartment_id=tenancy,
                   operating_system="Canonical Ubuntu")
    images = [x for x in images if "Ubuntu-24.04" in x.display_name
              and "aarch64" in x.display_name
              and "Minimal" not in x.display_name
              and x.lifecycle_state == "AVAILABLE"]
    if not images:
        report("STATE", "NO_ELIGIBLE_UBUNTU_24_04_ARM_IMAGE")
        return 0
    images.sort(key=lambda x: x.time_created, reverse=True)
    request = oci.core.models.LaunchInstanceDetails(
        availability_domain=ad, compartment_id=tenancy,
        display_name=NAME, shape=A1,
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=CPU, memory_in_gbs=MEMORY_GB),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id=images[0].id, boot_volume_size_in_gbs=BOOT_GB),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=subnet_id, assign_public_ip=(mode == "LOCKED_PUBLIC"),
            nsg_ids=[]),
        metadata={"ssh_authorized_keys": sshkey,
                  "user_data": redroid_cloud_init_data()},
        freeform_tags={"anthares-purpose": "android-redroid-standby",
                       "cost-policy": "always-free-single-a1"},
    )
    try:
        instance = guarded_launch(compute, request, tenancy, subnet_id).data
    except ServiceError as e:
        if "Out of host capacity" in str(e.message):
            report("STATE", "HOST_CAPACITY_DISAPPEARED")
            return 0
        raise
    report("STATE", "INSTANCE_CREATED_" + str(instance.lifecycle_state))
    # Never represent Linux creation as Android/Kwai readiness.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, TypeError, KeyError, ServiceError) as exc:
        report("ERROR_CLASS", type(exc).__name__)
        sys.exit(2)
