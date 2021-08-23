# Automate connecting two VCN on Oracle Cloud

![Docker Pulls](https://img.shields.io/docker/pulls/isac322/peer_oracle_vcn?logo=docker&style=flat-square)
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/isac322/peer_oracle_vcn/latest?logo=docker&style=flat-square)
![PyPI](https://img.shields.io/pypi/v/oci?label=oci&logo=python&style=flat-square)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/isac322/docker_image_deluged/master?logo=github&style=flat-square)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/isac322/docker_image_deluged/ci/master?logo=github&style=flat-square)
![Dependabpt Status](https://flat.badgen.net/github/dependabot/isac322/docker_image_deluged?icon=github)

Supported platform: `linux/amd64`, `linux/arm64/v8`, `linux/arm/v7`

## Overview

It will automate peering two VCN using Python SDK.

You have to add Oracle API Key. please follow [Official Instruction](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm#Required_Keys_and_OCIDs)

[한글 문서](https://velog.io/@isac322/%EC%98%A4%EB%9D%BC%ED%81%B4-%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C%EC%97%90%EC%84%9C-%EA%B3%84%EC%A0%95%EA%B0%84-%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC-%EA%B3%B5%EC%9C%A0-%EC%9E%90%EB%8F%99%ED%99%94)

## Tag format

`isac322/peer_oracle_vcn:<app_version>`

## Command

### `peer_oracle_vcn --help`

```
usage: peer_oracle_vcn [-h] {lpg_intra_tenant,lpg_inter_tenant,list_vcn,list_group,list_route_table} ...

optional arguments:
  -h, --help            show this help message and exit

Sub Command:
  {lpg_intra_tenant,lpg_inter_tenant,list_vcn,list_group,list_route_table}
```

### `peer_oracle_vcn lpg_intra_tenant --help`

```
usage: peer_oracle_vcn lpg_intra_tenant [-h] [--api-config-file API_CONFIG_FILE] [--profile PROFILE] --requestor-vcn-ocid REQUESTOR_VCN_OCID --acceptor-vcn-ocid ACCEPTOR_VCN_OCID --requestor-group-ocid REQUESTOR_GROUP_OCID --requestor-route-table-ocid REQUESTOR_ROUTE_TABLE_OCID --acceptor-route-table-ocid
                                        ACCEPTOR_ROUTE_TABLE_OCID --requestor-cidr REQUESTOR_CIDR --acceptor-cidr ACCEPTOR_CIDR

optional arguments:
  -h, --help            show this help message and exit
  --api-config-file API_CONFIG_FILE
                        OCI API config file path
  --profile PROFILE
  --requestor-vcn-ocid REQUESTOR_VCN_OCID
                        VCN OCID of requestor
  --acceptor-vcn-ocid ACCEPTOR_VCN_OCID
                        VCN OCID of acceptor
  --requestor-group-ocid REQUESTOR_GROUP_OCID
                        Group OCID of requestor
  --requestor-route-table-ocid REQUESTOR_ROUTE_TABLE_OCID
                        Route Table OCID of requestor to register LGP
  --acceptor-route-table-ocid ACCEPTOR_ROUTE_TABLE_OCID
                        Route Table OCID of acceptor to register LGP
  --requestor-cidr REQUESTOR_CIDR
                        CIDR of requestor to add acceptor's Route Table
  --acceptor-cidr ACCEPTOR_CIDR
                        CIDR of acceptor to add requestor's Route Table
```

### `peer_oracle_vcn lpg_inter_tenant --help`

```
usage: peer_oracle_vcn lpg_inter_tenant [-h] [--api-config-file API_CONFIG_FILE] [--requestor-vcn-ocid REQUESTOR_VCN_OCID] [--acceptor-vcn-ocid ACCEPTOR_VCN_OCID] [--requestor-group-ocid REQUESTOR_GROUP_OCID] [--requestor-route-table-ocid REQUESTOR_ROUTE_TABLE_OCID]
                                        [--acceptor-route-table-ocid ACCEPTOR_ROUTE_TABLE_OCID] --requestor-cidr REQUESTOR_CIDR --acceptor-cidr ACCEPTOR_CIDR --requestor-profile REQUESTOR_PROFILE --acceptor-profile ACCEPTOR_PROFILE

optional arguments:
  -h, --help            show this help message and exit
  --api-config-file API_CONFIG_FILE
                        OCI API config file path
  --requestor-vcn-ocid REQUESTOR_VCN_OCID
                        VCN OCID of requestor
  --acceptor-vcn-ocid ACCEPTOR_VCN_OCID
                        VCN OCID of acceptor
  --requestor-group-ocid REQUESTOR_GROUP_OCID
                        Group OCID of requestor
  --requestor-route-table-ocid REQUESTOR_ROUTE_TABLE_OCID
                        Route Table OCID of requestor to register LGP
  --acceptor-route-table-ocid ACCEPTOR_ROUTE_TABLE_OCID
                        Route Table OCID of acceptor to register LGP
  --requestor-cidr REQUESTOR_CIDR
                        CIDR of requestor to add acceptor's Route Table
  --acceptor-cidr ACCEPTOR_CIDR
                        CIDR of acceptor to add requestor's Route Table
  --requestor-profile REQUESTOR_PROFILE
  --acceptor-profile ACCEPTOR_PROFILE
```

## How to run

`docker run -v <your_oci_key_path>:/root/.oci:ro -ti isac322/peer_oracle_vcn lpg_inter_tenant --requestor-profile profile1 --acceptor-profile profile2`

Will peer VCN of tenant `profile1` with VCN of tenant `profile2`. It will automatically find main VCN and main Route Table using each OCI API Profile.
If there are multiple VCN or Route Table, you have to manually set OCID using sub-command arguments.

You can list up VCN, Route Table, Group using sub-command `list_vcn`, `list_route_table`, `list_group` respectively.
