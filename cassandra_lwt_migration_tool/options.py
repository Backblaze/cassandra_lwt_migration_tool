import argparse
import getpass
import pathlib
from typing import Union

# from typing import Literal

# uncomment in the future for 3.8
# OPERATION_MODE = Literal[
#    "captureBaseline",
#    "checkCompletion",
#    "checkBaselineCompletion",
#    "checkTargetingNodes",
# ]


class ClmtOptions(argparse.Namespace):
    """
    Represents the commandline options for this program. Call populate() to fill it
    by parsing sys.argv
    """

    #    mode: OPERATION_MODE = "captureBaseline"
    node_ips_file_path: pathlib.Path = pathlib.Path("")
    baseline_directory: pathlib.Path = pathlib.Path("")
    cassandra_username: Union[str, None] = ""
    cassandra_password: Union[str, None] = ""

    def populate(self):
        """Call this to parse STDIN and populate the arguments for the program."""

        _parser = argparse.ArgumentParser()
        _parser.add_argument(
            "mode",
            choices=[
                "captureBaseline",
                "checkCompletion",
                "checkBaselineCompletion",
                "checkTargetingNodes",
            ],
            help="The mode of operation to run.",
        )

        _parser.add_argument(
            "node_ips_file_path",
            default=".",
            help="A path to a file containing the cassandra node IPs.",
            type=pathlib.Path,
        )
        _parser.add_argument(
            "baseline_directory",
            default=".",
            help="The directory to store the baseline information to.",
            type=pathlib.Path,
        )

        _parser.add_argument(
            "--cassandra-username",
            default=None,
            help="The username to authenticate to cassandra with.",
        )
        _parser.add_argument(
            "--cassandra-password",
            default=None,
            help="The password to authenticate to cassandra with.",
        )

        ns = _parser.parse_args(namespace=self)

        if not ns.cassandra_username:
            ns.cassandra_username = input("username: ").strip()
        if not ns.cassandra_password:
            ns.cassandra_password = getpass.getpass(prompt="password: ").strip()


options = ClmtOptions()
