from __future__ import annotations

from pydantic import BaseModel


class LPGMaterial(BaseModel):
    requestor_vcn: str
    acceptor_vcn: str
    requestor_group: str
    requestor_route_table: str
    acceptor_route_table: str
    requestor_cidr: str
    acceptor_cidr: str

    class Config:
        frozen = True
