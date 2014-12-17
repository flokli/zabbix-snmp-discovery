#!/usr/bin/env python2

import argparse
import sys
import os
import os.path
import netsnmp
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from slugify import slugify


# define CLI
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--version", choices=["1", "2c"], default="2c", help="The SNMP version to use")
parser.add_argument("-c", "--community", default="public", help="The community string to use")
parser.add_argument("agent", metavar="AGENT", help="The remote SNMP entity with which to communicate")
parser.add_argument("walk_oid", metavar="WALK_OID",
                    help="An OID that is used for snmpwalking. adds #SNMPINDEX and #SNMPVALUE to the output")
parser.add_argument("addn_oids", metavar="OID", nargs="*",
                    help="A list of additonal OIDs you want to include in the output. It is also possible to specify" +
                         " a custom key, by prefixing the OID with \"KEYNAME=\".")

args = parser.parse_args()

# calculate keys of addn_oids
addn_oids = dict()
for addn_oid in args.addn_oids:
    if "=" in addn_oid:
        (key, value) = addn_oid.split("=")
        addn_oids[key] = value
    else:
        addn_oids[slugify(addn_oid)] = addn_oid

args.addn_oids = addn_oids


# open session to snmp server
snmp_version = 1 if args.version == "1" else 2 if args.version == "2c" else None
session = netsnmp.Session(DestHost=args.agent, Community=args.community, Version=snmp_version)

def varlist(oid):
    """consumes a list or a single oid, returns a Varlist"""
    varbinds = []
    if oid is list:
        varbinds = (netsnmp.VarBind(e) for e in oid)
    else:
        varbinds = [netsnmp.Varbind(oid)]
    return netsnmp.VarList(* varbinds)

# walk over walk_oid
resp = session.walk(varlist(args.walk_oid))

data = []
for idx, value in enumerate(resp):
    data.append({
        "#SNMPINDEX": idx,
        "#SNMPVALUE": value
    })

# get additional values
for addn_key, addn_oid in args.addn_oids.items():
    resp = session.walk(varlist(addn_oid))
    # walk over response
    for idx, value in enumerate(resp):
        data[idx][addn_key] = value

if sys.stdout.isatty():
    print(json.dumps(data, sort_keys=True, indent=2))
else:
    print(json.dumps(data))