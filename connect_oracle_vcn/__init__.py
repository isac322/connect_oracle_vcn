from __future__ import annotations

import logging

from connect_oracle_vcn import commands, config, usecases


def main():
    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)-8s] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
    log_handler.setFormatter(log_formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    cmd = config.load_command()

    if isinstance(cmd, commands.PeerInterTenancies):
        usecases.peer_inter_tenancies(cmd)
    elif isinstance(cmd, commands.PeerWithinTenant):
        usecases.peer_within_tenant(cmd)
    elif isinstance(cmd, commands.ListVCNs):
        usecases.list_vcns(cmd)
    elif isinstance(cmd, commands.ListGroups):
        usecases.list_groups(cmd)
    elif isinstance(cmd, commands.ListRouteTables):
        usecases.list_route_tables(cmd)
    else:
        logger.error(f'Unknown command: {cmd}')
