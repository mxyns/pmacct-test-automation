
from library.py.setup_tools import KModuleParams
import library.py.scripts as scripts
import library.py.helpers as helpers
import logging, pytest, sys
import library.py.test_tools as test_tools
logger = logging.getLogger(__name__)

testParams = KModuleParams(sys.modules[__name__], ipv4_subnet='192.168.100.')

def test(test_core, consumer_setup_teardown):
    main(consumer_setup_teardown[0])

def main(consumer):
    for i in range(len(testParams.pcap_folders)):
        assert scripts.replay_pcap_detached(testParams.pcap_folders[i], i)

    assert test_tools.read_and_compare_messages(consumer, testParams, 'flow-00',
        ['timestamp_max', 'timestamp_arrival', 'stamp_inserted',
         'timestamp_min', 'stamp_updated', 'timestamp_start', 'timestamp_end', 'peer_ip_src'])

    assert not helpers.check_regex_sequence_in_file(testParams.pmacct_log_file, ['ERROR|WARNING'])
