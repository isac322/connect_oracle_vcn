import pytest

from connect_oracle_vcn import config


class TestConfig:
    @pytest.mark.parametrize(
        ('arguments', 'expected'),
        (
            (
                ('same', '--requestor-vcn-ocid', 'sample_ocid', '--acceptor-vcn-ocid', 'sample_ocid'),
                True,
            ),
            (
                (
                    'same',
                    '--api-config-file',
                    'file-path',
                    '--requestor-vcn-ocid',
                    'sample_ocid',
                    '--acceptor-vcn-ocid',
                    'sample_ocid',
                ),
                True,
            ),
            (
                (
                    'same',
                    '--api-config-file',
                    'file-path',
                    '--profile',
                    'profile1',
                    '--requestor-vcn-ocid',
                    'sample_ocid',
                    '--acceptor-vcn-ocid',
                    'sample_ocid',
                ),
                True,
            ),
            (
                (
                    'diff',
                    '--api-config-file',
                    'file-path',
                    '--requestor-vcn-ocid',
                    'sample_ocid',
                    '--acceptor-vcn-ocid',
                    'sample_ocid',
                    '--requestor-profile',
                    'profile1',
                    '--acceptor-profile',
                    'profile2',
                ),
                True,
            ),
            (
                (
                    'diff',
                    '--requestor-vcn-ocid',
                    'sample_ocid',
                    '--acceptor-vcn-ocid',
                    'sample_ocid',
                    '--requestor-profile',
                    'profile1',
                    '--acceptor-profile',
                    'profile2',
                ),
                True,
            ),
        ),
    )
    def test_cli_can_filter_out_invalid_arguments(self, arguments, expected):
        parser = config._get_arg_parser()

        try:
            parser.parse_args(arguments)
        except Exception:
            assert expected is True
        else:
            assert expected is False
