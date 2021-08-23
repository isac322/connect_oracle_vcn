from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import MutableSequence, Sequence
from functools import cached_property
from types import TracebackType
from typing import ContextManager, Optional, Type

import oci.exceptions
from oci.core import VirtualNetworkClient
from oci.core.models import (
    ConnectLocalPeeringGatewaysDetails,
    CreateLocalPeeringGatewayDetails,
    LocalPeeringGateway,
    RouteRule,
    RouteTable,
    UpdateRouteTableDetails,
    Vcn,
)
from oci.identity import IdentityClient
from oci.identity.models import CreatePolicyDetails, Group, Policy

from connect_oracle_vcn import config

_log = logging.getLogger(__name__)


class OCIRepository(ContextManager):
    _cfg: config.OCI_CONFIG
    _identity_client: IdentityClient
    _network_client: VirtualNetworkClient
    _created_lpgs: set[str]
    _created_policies: set[str]
    _added_route_rules: dict[str, MutableSequence[RouteRule]]

    def __init__(self, oci_config: config.OCI_CONFIG) -> None:
        super().__init__()

        self._cfg = oci_config
        self._identity_client = IdentityClient(oci_config)
        self._network_client = VirtualNetworkClient(oci_config)
        self._created_lpgs = set()
        self._created_policies = set()
        self._added_route_rules = defaultdict(list)

    def __enter__(self) -> OCIRepository:
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if __exc_value is not None:
            self.cleanup_all_resources()
        return super().__exit__(__exc_type, __exc_value, __traceback)

    @cached_property
    def compartment_id(self) -> str:
        return self._cfg['tenancy']

    def get_tenancy_name(self) -> str:
        res = self._identity_client.get_tenancy(self.compartment_id)
        return res.data.name

    def create_lpg(self, vcn_ocid: str, lpg_name: str) -> LocalPeeringGateway:
        res = self._network_client.create_local_peering_gateway(
            create_local_peering_gateway_details=CreateLocalPeeringGatewayDetails(
                compartment_id=self.compartment_id,
                display_name=lpg_name,
                vcn_id=vcn_ocid,
            )
        )
        self._created_lpgs.add(res.data.id)
        return res.data

    def delete_lpg(self, lpg_ocid: str) -> None:
        self._network_client.delete_local_peering_gateway(lpg_ocid)
        if lpg_ocid in self._created_lpgs:
            self._created_lpgs.remove(lpg_ocid)

    def get_lpg(self, lpg_ocid: str) -> LocalPeeringGateway:
        res = self._network_client.get_local_peering_gateway(local_peering_gateway_id=lpg_ocid)
        return res.data

    def create_policy(self, name: str, description: str, statements: Sequence[str]) -> Policy:
        res = self._identity_client.create_policy(
            create_policy_details=CreatePolicyDetails(
                compartment_id=self.compartment_id,
                name=name,
                description=description,
                statements=tuple(statements),
            ),
        )
        self._created_policies.add(res.data.id)
        return res.data

    def delete_policy(self, policy_ocid: str) -> None:
        self._identity_client.delete_policy(policy_id=policy_ocid)
        if policy_ocid in self._created_policies:
            self._created_policies.remove(policy_ocid)

    def connect_lpg_to(self, requestor_lpg_ocid: str, acceptor_lpg_ocid: str) -> None:
        self._network_client.connect_local_peering_gateways(
            local_peering_gateway_id=requestor_lpg_ocid,
            connect_local_peering_gateways_details=ConnectLocalPeeringGatewaysDetails(peer_id=acceptor_lpg_ocid),
        )

    def get_vcn(self, vcn_ocid: str) -> Vcn:
        return self._network_client.get_vcn(vcn_id=vcn_ocid).data

    def list_vcns(self) -> Sequence[Vcn]:
        return self._network_client.list_vcns(compartment_id=self.compartment_id).data

    def list_groups(self) -> Sequence[Group]:
        return self._identity_client.list_groups(compartment_id=self.compartment_id).data

    def get_route_table(self, route_table_ocid: str) -> RouteTable:
        res = self._network_client.get_route_table(rt_id=route_table_ocid)
        return res.data

    def add_lpg_to_route_table(self, route_table_ocid: str, lpg_ocid: str, peer_cidr: str) -> None:
        route_table = self.get_route_table(route_table_ocid=route_table_ocid)
        lpg_route_rule = RouteRule(
            destination_type=RouteRule.DESTINATION_TYPE_CIDR_BLOCK,
            destination=peer_cidr,
            network_entity_id=lpg_ocid,
        )
        route_table.route_rules.append(lpg_route_rule)

        self._update_route_table(route_table)
        self._added_route_rules[route_table.id].append(lpg_route_rule)

    def _update_route_table(self, route_table: RouteTable) -> None:
        self._network_client.update_route_table(
            rt_id=route_table.id,
            update_route_table_details=UpdateRouteTableDetails(
                defined_tags=route_table.defined_tags,
                display_name=route_table.display_name,
                freeform_tags=route_table.freeform_tags,
                route_rules=route_table.route_rules,
            ),
        )

    def list_route_tables(self, vcn_ocid: Optional[str] = None) -> Sequence[RouteTable]:
        return self._network_client.list_route_tables(compartment_id=self.compartment_id, vcn_id=vcn_ocid).data

    def cleanup_all_resources(self) -> None:
        for lpg_id in tuple(self._created_lpgs):
            try:
                self.delete_lpg(lpg_id)
            except oci.exceptions.ServiceError as e:
                _log.warning(f'Failed to delete LPG. {e.args[0]}')

        for policy_id in tuple(self._created_policies):
            try:
                self.delete_policy(policy_id)
            except oci.exceptions.ServiceError as e:
                _log.warning(f'Failed to delete Policy. {e.args[0]}')

        if len(self._added_route_rules) != 0:
            for table_id, rules in tuple(self._added_route_rules.items()):
                route_table = self.get_route_table(route_table_ocid=table_id)
                for rule in rules:
                    try:
                        route_table.route_rules.remove(rule)
                    except ValueError:
                        pass
                try:
                    self._update_route_table(route_table)
                except oci.exceptions.ServiceError as e:
                    _log.warning(f'Failed to Route Rules. {e.args[0]}')
                else:
                    del self._added_route_rules[table_id]
