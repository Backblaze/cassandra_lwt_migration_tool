import argparse
import getpass

_parser = argparse.ArgumentParser()
_parser.add_argument('mode', choices=[
    'captureBaseline',
    'checkCompletion',
    'checkBaselineCompletion',
    'checkTargetingNodes'
], help='The mode of operation to run.')

# TODO: Re-enable these parameters.
# _parser.add_argument('nodeIpsFilePath', help='A path to a file containing the cassandra node IPs.')
# _parser.add_argument('baselineDirectory', help='The directory to store the baseline information to.')

options = _parser.parse_args()

# TODO: Env variable override.
_user = input('username: ').strip()
_pass = getpass.getpass(prompt='password: ').strip()
options.username = _user
options.password = _pass