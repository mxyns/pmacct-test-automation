
from library.py.configuration_file import KConfigurationFile
from library.py.setup_tools import KModuleParams
import library.py.scripts as scripts
import library.py.json_tools as jsontools
import library.py.helpers as helpers
import shutil, logging, pytest, sys, json, time
logger = logging.getLogger(__name__)

# The below two variables are used by setup_tools.prepare_test_env
testModuleParams = KModuleParams(sys.modules[__name__])
confFile = KConfigurationFile(testModuleParams.test_conf_file)

# Fixtures explained
# check_root_dir: makes sure pytest is run from the top level directory of the framework
# kafka_infra_setup_teardown: setup (and teardown) of kafka infrastructure
# prepare_test: creates results folder, pmacct_mount, etc. and copies all needed files there
#               edits pmacct config file with framework-specific details (IPs, ports, paths, etc.)
# prepare_pcap: edits pcap configuration file with framework-specific IPs and hostnames
# pmacct_setup_teardown: setup (and teardown) of pmacct container itself
def test(check_root_dir, kafka_infra_setup_teardown, prepare_test, pmacct_setup_teardown, prepare_pcap, consumer_setup_teardown):
    consumer = consumer_setup_teardown
    pcap_config_files, output_files, log_files = prepare_pcap
    assert len(pcap_config_files)>0 and len(output_files)>0 and len(log_files) > 0

    helpers.replace_in_file(log_files[0], '/etc/pmacct', testModuleParams.pmacct_mount_folder, 'Reading configuration file')
    helpers.replace_in_file(log_files[1], '/etc/pmacct', testModuleParams.pmacct_mount_folder)

    # Replaying traffic from folder pcap_mount_0 (traffic.pcap, traffic-reproducer.conf)
    assert scripts.replay_pcap_with_docker(testModuleParams.results_pcap_folders[0], '172.111.1.101')
    messages = consumer.get_messages(120, helpers.count_non_empty_lines(output_files[0])) # 35 lines
    assert messages != None and len(messages) > 0
    logger.info('Waiting 10 seconds')
    time.sleep(10)  # needed for the last message to exist in logs

    # Replace peer_ip_src with the correct IP address in files output-flow-00.json and output-flow-01.json
    helpers.replace_in_file(output_files[0], '192.168.100.1', '172.111.1.101')
    helpers.replace_in_file(output_files[1], '192.168.100.1', '172.111.1.101')

    # Comparing received json messages to output-flow-00.json
    ignore_fields = ['timestamp_start', 'timestamp_end', 'timestamp_arrival', 'timestamp_min',
                     'timestamp_max', 'stamp_inserted', 'stamp_updated']
    assert jsontools.compare_messages_to_json_file(messages, output_files[0], ignore_fields)

    # Make sure the expected logs (in output-log-00.log) exist in pmacct log
    assert helpers.check_file_regex_sequence_in_file(testModuleParams.results_log_file, log_files[0])
    # Check for ERRORs or WARNINGs
    assert not helpers.check_regex_sequence_in_file(testModuleParams.results_log_file, ['ERROR|WARNING'])

    # Replace 00 maps with 01 maps
    for mapfile in ['f2rd', 'pretag', 'sampling']:
        shutil.copyfile(testModuleParams.results_mount_folder + '/' + mapfile + '-00.map',
                        testModuleParams.results_mount_folder + '/' + mapfile + '-00.map.bak')
        shutil.move(testModuleParams.results_mount_folder + '/' + mapfile + '-01.map',
                    testModuleParams.results_mount_folder + '/' + mapfile + '-00.map')

    # Sending the signal to reload maps
    assert scripts.send_signal_to_pmacct('SIGUSR2')

    # Replaying traffic from folder pcap_mount_0 (traffic.pcap, traffic-reproducer.conf)
    assert scripts.replay_pcap_with_docker(testModuleParams.results_pcap_folders[0], '172.111.1.101')
    messages = consumer.get_messages(120, helpers.count_non_empty_lines(output_files[1]))  # 35 lines
    assert messages != None and len(messages) > 0
    logger.info('Waiting 10 seconds')
    time.sleep(10)  # needed for the last message to exist in logs

    # Comparing received json messages to output-flow-01.json
    assert jsontools.compare_messages_to_json_file(messages, output_files[1], ignore_fields)

    # Make sure the expected logs (in output-log-01.log) exist in pmacct log
    assert helpers.check_file_regex_sequence_in_file(testModuleParams.results_log_file, log_files[1])
    # Check for ERRORs or WARNINGs
    assert not helpers.check_regex_sequence_in_file(testModuleParams.results_log_file, ['ERROR|WARNING'])
