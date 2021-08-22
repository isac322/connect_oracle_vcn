from __future__ import annotations

from abc import ABCMeta
from typing import Optional

from pydantic import BaseModel

from connect_oracle_vcn import config


class Command(BaseModel, metaclass=ABCMeta):
    class Config:
        frozen = True


class PeerWithinTenant(Command):
    oci_config: config.OCI_CONFIG
    requestor_vcn: Optional[str] = ...
    acceptor_vcn: Optional[str] = ...
    requestor_group: Optional[str] = ...
    requestor_route_table: Optional[str] = ...
    acceptor_route_table: Optional[str] = ...
    requestor_cidr: str
    acceptor_cidr: str


class PeerInterTenancies(Command):
    requestor_oci_config: config.OCI_CONFIG
    acceptor_oci_config: config.OCI_CONFIG
    requestor_vcn: Optional[str] = ...
    acceptor_vcn: Optional[str] = ...
    requestor_group: Optional[str] = ...
    requestor_route_table: Optional[str] = ...
    acceptor_route_table: Optional[str] = ...
    requestor_cidr: str
    acceptor_cidr: str


class ListVCNs(Command):
    oci_config: config.OCI_CONFIG


class ListGroups(Command):
    oci_config: config.OCI_CONFIG


class ListRouteTables(Command):
    oci_config: config.OCI_CONFIG
    vcn_ocid: Optional[str] = ...
