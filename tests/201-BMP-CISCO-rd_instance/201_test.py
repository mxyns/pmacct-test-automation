
from library.py.configuration_file import KConfigurationFile
from library.py.setup_tools import KModuleParams
from library.py.kafka_consumer import KMessageReader
import library.py.scripts as scripts
import library.py.json_tools as jsontools
import library.py.helpers as helpers
import os, logging, pytest, sys, shutil, json
logger = logging.getLogger(__name__)

# The below two variables are used by setup_tools.prepare_test_env
testModuleParams = KModuleParams(sys.modules[__name__])
confFile = KConfigurationFile(testModuleParams.test_conf_file)

# Changes in pmacctd.conf (or nfaccctd.conf), which are test case specific
@pytest.fixture(scope="module")
def prepare_config_local(request):
    confFile.replace_value_of_key('bgp_daemon_tag_map', testModuleParams.pmacct_mount_folder + '/pretag-00.map')
    confFile.replace_value_of_key('bmp_daemon_ip', '0.0.0.0')
    confFile.replace_value_of_key('bmp_daemon_port', '8989')
    confFile.replace_value_of_key('bmp_daemon_msglog_kafka_topic', testModuleParams.kafka_topic_name)
    confFile.replace_value_of_key('bmp_daemon_msglog_kafka_config_file', '/var/log/pmacct/librdkafka.conf')
    confFile.replace_value_of_key('bmp_daemon_msglog_kafka_avro_schema_registry', 'http://schema-registry:8081')
    confFile.replace_value_of_key('bmp_daemon_msglog_avro_schema_output_file', testModuleParams.pmacct_output_folder) # + '/flow_avroschema.avsc')
    confFile.print_to_file(testModuleParams.results_conf_file)

# Fixtures explained
# check_root_dir: makes sure pytest is run from the top level directory of the framework
# kafka_infra_setup_teardown: setup (and teardown) of kafka infrastructure
# prepare_test: creates results folder, pmacct_mount, etc. and copies all needed files there
#               edits pmacct config file with framework-specific details (IPs, ports, paths, etc.)
# prepare_config_local: edits pmacct config file with test-case-specific things (not covered in prepare_test)
# prepare_pcap: edits pcap configuration file with framework-specific IPs and hostnames
# pmacct_setup_teardown: setup (and teardown) of pmacct container itself
def test(check_root_dir, kafka_infra_setup_teardown, prepare_test, prepare_config_local, prepare_pcap, pmacct_setup_teardown):
    consumer = KMessageReader(testModuleParams.kafka_topic_name, testModuleParams.results_msg_dump)
    pcap_config_files, output_files, log_files = prepare_pcap
    pcap_config_file = pcap_config_files[0]
    output_file = output_files[0]

    # following didn't work (possibly because the order is changed when dumped back?)
    # import yaml
    # with open(pcap_config_file) as f:
    #     data = yaml.load(f, Loader=yaml.FullLoader)
    # data['network']['map'][0]['repro_ip'] = '127.0.0.1'
    # data['bmp']['collector']['ip'] = '127.0.0.1'
    # data['bmp']['collector']['port'] = '2929'
    # with open(pcap_config_file, 'w') as f:
    #     data = yaml.dump(data, f)

    # Important to keep the indenting due to yaml notation
    confPcap = KConfigurationFile(pcap_config_file)
    confPcap.replace_value_of_key('    repro_ip', '127.0.0.1')
    confPcap.replace_value_of_key('    ip', '127.0.0.1')
    confPcap.replace_value_of_key('    port', '2929')
    confPcap.print_to_file(pcap_config_file)

    assert os.path.isfile(pcap_config_file)
    scripts.replay_pcap_file(pcap_config_file)
    messages = consumer.get_messages(120, 670)

    import time
    time.sleep(60) # needed for the last regex (WARNIN) to be found in the logs!

    with open(log_files[0]) as f:
        regexes = f.read().split('\n')
    logger.info('Checking for ' + str(len(regexes)) + ' regexes')
    assert helpers.check_regex_sequence_in_file(testModuleParams.results_log_file, regexes)
    logger.info('All regexes found!')

    # Check for ERRORs or WARNINGs (but not the warning we want)
    assert not helpers.check_regex_sequence_in_file(testModuleParams.results_log_file, ['ERROR|WARNING(?!.*Unable to get kafka_host)'])

    assert messages!=None and len(messages) > 0
    with open(output_file) as f:
        lines = f.readlines()
    jsons = [json.dumps(msg.value()) for msg in messages]
    ignore_fields = ['timestamp', 'bmp_router', 'bmp_router_port', 'timestamp_arrival', 'peer_ip', \
                     'local_ip', 'bgp_nexthop']
    assert jsontools.compare_json_lists(jsons, lines, ignore_fields)
