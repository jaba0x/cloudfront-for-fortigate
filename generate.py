#!/usr/bin/env python3
### FrontGate: Amazon CloudFront address list generator for FortiGate Firewalls
### Author: Jaba Macharashvili
### Created: 24.02.2022
### Updated: 05.10.2026
### E-Mail: jaba@jaba.ge
### Webpage: https://jaba.ge

import argparse
import ipaddress
import json
import sys
import urllib.request

AWS_IP_RANGES_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
TIMEOUT_SECONDS = 30


def load_ranges(path=None):
    """Read ip-ranges.json from a local file, or download it from AWS."""
    if path:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    request = urllib.request.Request(AWS_IP_RANGES_URL, headers={"User-Agent": "frontgate"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)


def list_services(data):
    names = set()
    for key in ("prefixes", "ipv6_prefixes"):
        names.update(entry["service"] for entry in data.get(key, []))
    return sorted(names)


def select_networks(data, service, region, version):
    """Return the sorted, de-duplicated networks of one service and IP version."""
    key, field = ("prefixes", "ip_prefix") if version == 4 else ("ipv6_prefixes", "ipv6_prefix")
    found = set()
    for entry in data.get(key, []):
        if entry["service"] != service:
            continue
        if region and entry["region"].lower() != region.lower():
            continue
        found.add(ipaddress.ip_network(entry[field]))
    return sorted(found)


def object_name(prefix, network, index, naming):
    v6 = network.version == 6
    base = f"{prefix}_V6" if v6 else prefix
    if naming == "prefix":
        label = str(network).replace("/", "_").replace(":", "-")
        return f"{base}_{label}"
    return f"{base}_{index}" if v6 else f"{base}{index}"


def render(networks, prefix, group, naming):
    """Return the FortiOS CLI lines for one address family."""
    v6 = networks[0].version == 6
    address_table = "firewall address6" if v6 else "firewall address"
    group_table = "firewall addrgrp6" if v6 else "firewall addrgrp"
    group_name = f"{group}_V6" if v6 else group

    names = [object_name(prefix, net, i, naming) for i, net in enumerate(networks, 1)]

    lines = [f"config {address_table}"]
    for name, net in zip(names, networks):
        if v6:
            value = f"set ip6 {net}"
        else:
            value = f"set subnet {net.network_address} {net.netmask}"
        lines += [f'    edit "{name}"', f"        {value}", "    next"]
    lines.append("end")

    # "set member" replaces the whole list, "append member" adds to it. Starting
    # with set makes the group exactly match the current ranges on every run.
    lines += [f"config {group_table}", f'    edit "{group_name}"']
    lines.append(f'        set member "{names[0]}"')
    lines += [f'        append member "{name}"' for name in names[1:]]
    lines += ["    next", "end"]
    return lines


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="generate.py",
        description="Generate FortiGate address objects and an address group "
        "from the official AWS IP ranges.",
    )
    parser.add_argument("-s", "--service", default="CLOUDFRONT",
                        help="AWS service to read from ip-ranges.json (default: CLOUDFRONT)")
    parser.add_argument("-r", "--region",
                        help="only include prefixes of this AWS region, e.g. GLOBAL")
    parser.add_argument("-f", "--family", choices=["4", "6", "both"], default="4",
                        help="IP version to generate (default: 4)")
    parser.add_argument("-p", "--prefix",
                        help="name prefix of the address objects (default: the service name)")
    parser.add_argument("-g", "--group",
                        help="name of the address group (default: the name prefix)")
    parser.add_argument("-n", "--naming", choices=["index", "prefix"], default="index",
                        help="name objects by position (CLOUDFRONT1) or by network "
                        "(CLOUDFRONT_120.52.22.96_27); default: index")
    parser.add_argument("-i", "--input", metavar="FILE",
                        help="read a local ip-ranges.json instead of downloading it")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="write the configuration to a file instead of stdout")
    parser.add_argument("--list-services", action="store_true",
                        help="print the services available in ip-ranges.json and exit")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        data = load_ranges(args.input)
    except (OSError, ValueError) as exc:
        sys.exit(f"frontgate: could not read the AWS IP ranges: {exc}")

    if args.list_services:
        print("\n".join(list_services(data)))
        return 0

    service = args.service.upper()
    prefix = args.prefix or service
    group = args.group or prefix
    versions = {"4": [4], "6": [6], "both": [4, 6]}[args.family]

    blocks, summary = [], []
    for version in versions:
        networks = select_networks(data, service, args.region, version)
        if networks:
            blocks.append(render(networks, prefix, group, args.naming))
            summary.append(f"{len(networks)} IPv{version}")

    if not blocks:
        where = f" in region {args.region}" if args.region else ""
        sys.exit(f"frontgate: no prefixes found for {service}{where}\n"
                 f"available services: {', '.join(list_services(data))}")

    text = "\n".join(line for block in blocks for line in block) + "\n"
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            sys.exit(f"frontgate: could not write {args.output}: {exc}")
    else:
        sys.stdout.write(text)

    print(f"frontgate: {' + '.join(summary)} prefixes for {service} "
          f"(AWS syncToken {data.get('syncToken', '?')}, published {data.get('createDate', '?')})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
