from __future__ import annotations

import logging
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Optional

import oci
import pydantic

from peer_oracle_vcn import repository, values

_log = logging.getLogger(__name__)


@contextmanager
def wrap_with_log(msg: str) -> None:
    _log.info(msg.capitalize())

    try:
        yield
    except oci.exceptions.ServiceError as e:
        _log.error(f'Failed {msg}. {e.args[0]}')
        raise e


def build_requestor_policy_statements(
    requestor_compartment_id: str,
    acceptor_compartment_id: str,
    requestor_group: str,
) -> Sequence[str]:
    return (
        f'Define tenancy Acceptor as {acceptor_compartment_id}',
        (
            f'Allow group id {requestor_group} to manage local-peering-from '
            f'in compartment id {requestor_compartment_id}'
        ),
        f'Endorse group id {requestor_group} to manage local-peering-to in tenancy Acceptor',
        (
            f'Endorse group id {requestor_group} to associate local-peering-gateways '
            f'in compartment id {requestor_compartment_id} with local-peering-gateways in tenancy Acceptor'
        ),
    )


def build_acceptor_policy_statements(
    requestor_compartment_id: str,
    acceptor_compartment_id: str,
    requestor_group: str,
) -> Sequence[str]:
    return (
        f'Define tenancy Requestor as {requestor_compartment_id}',
        f'Define group RequestorGrp as {requestor_group}',
        (
            'Admit group RequestorGrp of tenancy Requestor to manage local-peering-to '
            f'in compartment id {acceptor_compartment_id}'
        ),
        (
            'Admit group RequestorGrp of tenancy Requestor to associate local-peering-gateways '
            f'in tenancy Requestor with local-peering-gateways in compartment id {acceptor_compartment_id}'
        ),
    )


def build_lpg_materials(
    requestor_repo: repository.OCIRepository,
    acceptor_repo: repository.OCIRepository,
    requestor_vcn: Optional[str],
    acceptor_vcn: Optional[str],
    requestor_group: Optional[str],
    requestor_route_table: Optional[str],
    acceptor_route_table: Optional[str],
    requestor_cidr: Optional[str],
    acceptor_cidr: Optional[str],
) -> Optional[values.LPGMaterial]:
    def get_main_vcn(repo: repository.OCIRepository, parameter_name: str) -> Optional[str]:
        vcns = repo.list_vcns()
        if len(vcns) > 1:
            _log.error(
                f'Multiple VCNs are found on compartment {repo.compartment_id}. '
                f'Please specify VCN OCID via `{parameter_name}`. '
                'You can list up all VCNs using `peer_oracle_vcn list_vcn`.'
            )
            return None
        return vcns[0].id

    def get_main_group(repo: repository.OCIRepository, parameter_name: str) -> Optional[str]:
        groups = repo.list_groups()
        if len(groups) > 1:
            _log.error(
                f'Multiple Groups are found on compartment {repo.compartment_id}. '
                f'Please specify Group OCID via `{parameter_name}`. '
                'You can list up all Groups using `peer_oracle_vcn list_group`.'
            )
            return None
        return groups[0].id

    def get_main_route_table(repo: repository.OCIRepository, parameter_name: str, vcn_ocid: str) -> Optional[str]:
        route_tables = repo.list_route_tables(vcn_ocid=vcn_ocid)
        if len(route_tables) > 1:
            _log.error(
                f'Multiple Route Tables are found on VCN {vcn_ocid}. '
                f'Please specify Route Table via `{parameter_name}`. '
                'You can list up all Route Table using `peer_oracle_vcn list_route_table`.'
            )
            return None
        return route_tables[0].id

    def get_main_vcn_cidr(repo: repository.OCIRepository, parameter_name: str, vcn_ocid: str) -> Optional[str]:
        vcn = repo.get_vcn(vcn_ocid=vcn_ocid)
        if len(vcn.cidr_blocks) > 1:
            _log.error(f'Multiple CIDRs are found on VCN {vcn_ocid}. ' f'Please specify CIDR via `{parameter_name}`.')
            return None
        return vcn.cidr_blocks[0]

    if requestor_vcn is None:
        requestor_vcn = get_main_vcn(repo=requestor_repo, parameter_name='--requestor-vcn-ocid')

    if acceptor_vcn is None:
        acceptor_vcn = get_main_vcn(repo=acceptor_repo, parameter_name='--acceptor-vcn-ocid')

    if requestor_group is None:
        requestor_group = get_main_group(repo=requestor_repo, parameter_name='--requestor-group-ocid')

    if requestor_route_table is None:
        requestor_route_table = get_main_route_table(
            repo=requestor_repo,
            parameter_name='--requestor-route-table-ocid',
            vcn_ocid=requestor_vcn,
        )

    if acceptor_route_table is None:
        acceptor_route_table = get_main_route_table(
            repo=acceptor_repo,
            parameter_name='--acceptor-route-table-ocid',
            vcn_ocid=acceptor_vcn,
        )

    if requestor_cidr is None:
        requestor_cidr = get_main_vcn_cidr(
            repo=requestor_repo,
            parameter_name='--requestor-cidr',
            vcn_ocid=requestor_vcn,
        )

    if acceptor_cidr is None:
        acceptor_cidr = get_main_vcn_cidr(
            repo=acceptor_repo,
            parameter_name='--acceptor-cidr',
            vcn_ocid=acceptor_vcn,
        )

    try:
        return values.LPGMaterial(
            requestor_vcn=requestor_vcn,
            acceptor_vcn=acceptor_vcn,
            requestor_group=requestor_group,
            requestor_route_table=requestor_route_table,
            acceptor_route_table=acceptor_route_table,
            requestor_cidr=requestor_cidr,
            acceptor_cidr=acceptor_cidr,
        )
    except pydantic.ValidationError:
        return None
