#!/usr/bin/env python3
"""Cloud-only, fail-closed Oracle Always Free A1 availability watcher.

Authenticated exclusively from GitHub Actions encrypted secrets; never copies
the OCI API key to Windows, logs, or repository source. Does not publish Kwai.
"""
import json
import os
import re
import sys

import oci
from oci.exceptions import ServiceError

A1 = "VM.Standard.A1.Flex"
NAME = "anthares-android-redroid-free"
REGION = "sa-saopaulo-1"
CPU, MEMORY_GB, BOOT_GB = 1, 6, 50


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
    if state != "AVAILABLE":
        return 0

    if os.getenv("OCI_A1_AUTO_PROVISION") != "1" or \
       os.getenv("OCI_A1_LAUNCH_GUARD") != "ALWAYS_FREE_SINGLE_A1":
        report("STATE", "CAPACITY_AVAILABLE_PROVISIONING_NOT_ARMED")
        return 0

    subnet_id, sshkey = d.get("subnet_id", ""), d.get("ssh_public_key", "")
    if not re.fullmatch(r"ocid1\.subnet\.[a-z0-9.]+", subnet_id) or \
       not sshkey.startswith(("ssh-ed25519 ", "ssh-rsa ")):
        raise ValueError("SUBNET_OR_SSH_KEY_MISSING")
    subnet = network.get_subnet(subnet_id).data
    if subnet.compartment_id != tenancy or subnet.lifecycle_state != "AVAILABLE":
        raise ValueError("SUBNET_NOT_ELIGIBLE")
    if not private_network_egress_ready(network, subnet):
        report("STATE", "PRIVATE_NAT_EGRESS_UNAVAILABLE")
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
        allocated_storage_gb += sum(int(x.size_in_gbs or 0) for x in pages(
            block.list_boot_volumes, compartment_id=compartment, availability_domain=ad)
            if x.lifecycle_state not in ("TERMINATED", "TERMINATING"))
        allocated_storage_gb += sum(int(x.size_in_gbs or 0) for x in pages(
            block.list_volumes, compartment_id=compartment)
            if x.lifecycle_state not in ("TERMINATED", "TERMINATING"))
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
            subnet_id=subnet_id, assign_public_ip=False),
        metadata={"ssh_authorized_keys": sshkey},
        freeform_tags={"anthares-purpose": "android-redroid-standby",
                       "cost-policy": "always-free-single-a1"},
    )
    try:
        instance = compute.launch_instance(request).data
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
