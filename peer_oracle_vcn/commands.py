from __future__ import annotations

from abc import ABCMeta
from typing import Optional

from pydantic import BaseModel

from peer_oracle_vcn import config


class Command(BaseModel, metaclass=ABCMeta):
    class Config:
        frozen = True


class CreateLPGIntraTenant(Command):
    oci_config: config.OCI_CONFIG
    requestor_vcn: str
    acceptor_vcn: str
    requestor_group: str
    requestor_route_table: str
    acceptor_route_table: str
    requestor_cidr: str
    acceptor_cidr: str


class CreateLPGInterTenant(Command):
    requestor_oci_config: config.OCI_CONFIG
    acceptor_oci_config: config.OCI_CONFIG
    requestor_vcn: Optional[str] = ...
    acceptor_vcn: Optional[str] = ...
    requestor_group: Optional[str] = ...
    requestor_route_table: Optional[str] = ...
    acceptor_route_table: Optional[str] = ...
    requestor_cidr: Optional[str] = ...
    acceptor_cidr: Optional[str] = ...


class ListVCNs(Command):
    oci_config: config.OCI_CONFIG


class ListGroups(Command):
    oci_config: config.OCI_CONFIG


class ListRouteTables(Command):
    oci_config: config.OCI_CONFIG
    vcn_ocid: Optional[str] = ...
