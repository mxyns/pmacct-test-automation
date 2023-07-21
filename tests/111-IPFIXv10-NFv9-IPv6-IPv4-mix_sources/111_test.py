
from library.py.setup_tools import KModuleParams
import library.py.scripts as scripts
import library.py.helpers as helpers
import logging, pytest, sys
import library.py.test_tools as test_tools
logger = logging.getLogger(__name__)

testParams = KModuleParams(sys.modules[__name__], ipv4_subnet='192.168.100.', ipv6_subnet='cafe::')

def test(test_core, consumer_setup_teardown):
    main(consumer_setup_teardown[0])

def main(consumer):
    assert scripts.replay_pcap_detached(testParams.pcap_folders[0], 0)
    assert scripts.replay_pcap_detached(testParams.pcap_folders[1], 1)

    assert test_tools.read_and_compare_messages(consumer, testParams, 'flow-00',
        ['timestamp_start', 'timestamp_end', 'timestamp_max', 'timestamp_arrival', 'stamp_inserted',
        'timestamp_min', 'stamp_updated'])

    assert not helpers.check_regex_sequence_in_file(testParams.pmacct_log_file, ['ERROR|WARNING'])
