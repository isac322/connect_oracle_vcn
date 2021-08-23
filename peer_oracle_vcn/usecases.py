from __future__ import annotations

import logging
import time

import oci.exceptions

from peer_oracle_vcn import commands, helpers
from peer_oracle_vcn.repository import OCIRepository

_log = logging.getLogger(__name__)


def create_lpg_intra_tenant(cmd: commands.CreateLPGIntraTenant) -> None:
    with OCIRepository(oci_config=cmd.oci_config) as repo:
        req_vcn = repo.get_vcn(vcn_ocid=cmd.requestor_vcn)
        act_vcn = repo.get_vcn(vcn_ocid=cmd.acceptor_vcn)

        # create policies to peer
        with helpers.wrap_with_log(f'creating Policy on requestor ({req_vcn.display_name})'):
            _ = repo.create_policy(
                name=f'request_lpg_to_vcn_{act_vcn.display_name}',
                description=f'request_lpg_to_vcn_{act_vcn.display_name}',
                statements=(
                    f'Allow group id {cmd.requestor_group} to manage local-peering-from '
                    f'in compartment id {repo.compartment_id}'
                ),
            )

        with helpers.wrap_with_log(f'creating Policy on acceptor ({act_vcn.display_name})'):
            _ = repo.create_policy(
                name=f'accept_lpg_of_vcn_{req_vcn.display_name}',
                description=f'accept_lpg_of_vcn_{req_vcn.display_name}',
                statements=(
                    f'Allow group id {cmd.requestor_group} to manage local-peering-to in compartment id {repo.compartment_id}',
                    f'Allow group id {cmd.requestor_group} to inspect vcns in compartment id {repo.compartment_id}',
                    f'Allow group id {cmd.requestor_group} to inspect local-peering-gateways in compartment id {repo.compartment_id}',
                ),
            )

        with helpers.wrap_with_log(f'creating LPG on requestor ({req_vcn.display_name})'):
            requestor_lpg = repo.create_lpg(
                vcn_ocid=cmd.requestor_vcn,
                lpg_name=f'{req_vcn.display_name}_to_{act_vcn.display_name}',
            )

        with helpers.wrap_with_log(f'creating LPG on acceptor ({act_vcn.display_name})'):
            acceptor_lpg = repo.create_lpg(
                vcn_ocid=cmd.acceptor_vcn,
                lpg_name=f'{act_vcn.display_name}_to_{req_vcn.display_name}',
            )

        _log.info('Waiting to acceptor\' LPG is accessible from requestor...')
        while True:
            try:
                repo.get_lpg(lpg_ocid=acceptor_lpg.id)
            except oci.exceptions.ServiceError as e:
                if e.code != 'NotAuthorizedOrNotFound':
                    _log.error(f'Requestor failed to fetch acceptor\'s LPG info. {e.args[0]}')
                    raise e
            else:
                time.sleep(1)
                break

        with helpers.wrap_with_log('connecting two LPGs'):
            repo.connect_lpg_to(
                requestor_lpg_ocid=requestor_lpg.id,
                acceptor_lpg_ocid=acceptor_lpg.id,
            )

        with helpers.wrap_with_log('adding LPG route rule to requestor\'s Route Table'):
            repo.add_lpg_to_route_table(
                route_table_ocid=cmd.requestor_route_table,
                lpg_ocid=requestor_lpg.id,
                peer_cidr=cmd.acceptor_cidr,
            )

        with helpers.wrap_with_log('adding LPG route rule to acceptor\'s Route Table'):
            repo.add_lpg_to_route_table(
                route_table_ocid=cmd.acceptor_route_table,
                lpg_ocid=acceptor_lpg.id,
                peer_cidr=cmd.requestor_cidr,
            )


def create_lpg_inter_tenant(cmd: commands.CreateLPGInterTenant) -> None:
    req_config = cmd.requestor_oci_config
    act_config = cmd.acceptor_oci_config

    with OCIRepository(oci_config=req_config) as req_repo, OCIRepository(oci_config=act_config) as act_repo:
        lpg_material = helpers.build_lpg_materials(
            requestor_repo=req_repo,
            acceptor_repo=act_repo,
            requestor_vcn=cmd.requestor_vcn,
            acceptor_vcn=cmd.acceptor_vcn,
            requestor_group=cmd.requestor_group,
            requestor_route_table=cmd.requestor_route_table,
            acceptor_route_table=cmd.acceptor_route_table,
        )
        if lpg_material is None:
            return

        # get tenancy names
        requestor_tenancy_name = req_repo.get_tenancy_name()
        acceptor_tenancy_name = act_repo.get_tenancy_name()

        # create policies to peer
        with helpers.wrap_with_log(f'creating Policy on requestor ({requestor_tenancy_name})'):
            _ = req_repo.create_policy(
                name=f'request_lpg_to_{acceptor_tenancy_name}',
                description=f'request_lpg_to_{acceptor_tenancy_name}',
                statements=helpers.build_requestor_policy_statements(
                    requestor_compartment_id=req_repo.compartment_id,
                    acceptor_compartment_id=act_repo.compartment_id,
                    requestor_group=lpg_material.requestor_group,
                ),
            )

        with helpers.wrap_with_log(f'creating Policy on acceptor ({acceptor_tenancy_name})'):
            _ = act_repo.create_policy(
                name=f'accept_lpg_of_{requestor_tenancy_name}',
                description=f'accept_lpg_of_{requestor_tenancy_name}',
                statements=helpers.build_acceptor_policy_statements(
                    requestor_compartment_id=req_repo.compartment_id,
                    acceptor_compartment_id=act_repo.compartment_id,
                    requestor_group=lpg_material.requestor_group,
                ),
            )

        with helpers.wrap_with_log(f'creating LPG on requestor ({requestor_tenancy_name})'):
            requestor_lpg = req_repo.create_lpg(
                vcn_ocid=lpg_material.requestor_vcn,
                lpg_name=f'{requestor_tenancy_name}_to_{acceptor_tenancy_name}',
            )

        with helpers.wrap_with_log(f'creating LPG on acceptor ({acceptor_tenancy_name})'):
            acceptor_lpg = act_repo.create_lpg(
                vcn_ocid=lpg_material.acceptor_vcn,
                lpg_name=f'{acceptor_tenancy_name}_to_{requestor_tenancy_name}',
            )

        _log.info('Waiting to acceptor\' LPG is accessible from requestor...')
        while True:
            try:
                req_repo.get_lpg(lpg_ocid=acceptor_lpg.id)
            except oci.exceptions.ServiceError as e:
                if e.code != 'NotAuthorizedOrNotFound':
                    _log.error(f'Requestor failed to fetch acceptor\'s LPG info. {e.args[0]}')
                    raise e
            else:
                time.sleep(1)
                break

        with helpers.wrap_with_log('connecting two LPGs'):
            req_repo.connect_lpg_to(
                requestor_lpg_ocid=requestor_lpg.id,
                acceptor_lpg_ocid=acceptor_lpg.id,
            )

        with helpers.wrap_with_log('adding LPG route rule to requestor\'s Route Table'):

            req_repo.add_lpg_to_route_table(
                route_table_ocid=lpg_material.requestor_route_table,
                lpg_ocid=requestor_lpg.id,
                peer_cidr=cmd.acceptor_cidr,
            )

        with helpers.wrap_with_log('adding LPG route rule to acceptor\'s Route Table'):
            act_repo.add_lpg_to_route_table(
                route_table_ocid=lpg_material.acceptor_route_table,
                lpg_ocid=acceptor_lpg.id,
                peer_cidr=cmd.requestor_cidr,
            )


def list_vcns(cmd: commands.ListVCNs) -> None:
    repo = OCIRepository(oci_config=cmd.oci_config)
    for vcn in repo.list_vcns():
        _log.info(f'VCN {vcn.display_name} - {vcn.id}')


def list_groups(cmd: commands.ListGroups) -> None:
    repo = OCIRepository(oci_config=cmd.oci_config)
    for group in repo.list_groups():
        _log.info(f'Group {group.name} - {group.id}')


def list_route_tables(cmd: commands.ListRouteTables) -> None:
    repo = OCIRepository(oci_config=cmd.oci_config)
    for route_table in repo.list_route_tables(vcn_ocid=cmd.vcn_ocid):
        _log.info(f'Route Table {route_table}')
