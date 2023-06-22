
import library.py.scripts as scripts
import library.py.setup_tools as setup_tools
import logging, pytest, os
from library.py.kafka_consumer import KMessageReader
logger = logging.getLogger(__name__)


def setup_kafka_infra():
    assert not scripts.check_broker_running()
    assert scripts.start_kafka_containers()
    assert scripts.wait_schemaregistry_healthy(120)


@pytest.fixture(scope="session")
def kafka_infra_setup_teardown():
    setup_kafka_infra()
    yield
    scripts.stop_and_remove_kafka_containers()


# For troubleshooting/debugging only!
@pytest.fixture(scope="session")
def kafka_infra_setup():
    setup_kafka_infra()


def setup_pmacct(request):
    params = request.module.testModuleParams
    assert os.path.isfile(params.results_conf_file)
    assert params.kafka_topic_name != None
    #    assert scripts.delete_registered_schemas()
    assert scripts.create_or_clear_kafka_topic(params.kafka_topic_name)
    assert scripts.start_pmacct_container(params.results_conf_file, params.results_mount_folder)
    assert scripts.wait_pmacct_running(5)  # wait 5 seconds
    params.pmacct_ip = scripts.find_pmacct_ip()
    logger.info('Pmacct IP: ' + params.pmacct_ip)
    assert params.pmacct_ip != None


@pytest.fixture(scope="module")
def pmacct_setup_teardown(request):
    setup_pmacct(request)
    yield
    scripts.stop_and_remove_pmacct_container()


# For troubleshooting/debugging only!
@pytest.fixture(scope="module")
def pmacct_setup(request):
    setup_pmacct(request)


# Makes sure the framework is run from the right directory
@pytest.fixture(scope="session")
def check_root_dir():
    logger.debug('Framework runs from directory: ' + os.getcwd())
    assert os.path.basename(os.getcwd())=='net_ana'


@pytest.fixture(scope="module")
def consumer_setup_teardown(request):
    params = request.module.testModuleParams
    consumer = KMessageReader(params.kafka_topic_name, params.results_msg_dump)
    consumer.connect()
    logger.debug('Local setup Consumer ' + str(consumer))
    yield consumer
    logger.debug('Local teardown Consumer ' + str(consumer))
    if consumer:
        consumer.disconnect()


# Prepares results folder to receive logs and output from pmacct
@pytest.fixture(scope="module")
def prepare_test(request):
    assert setup_tools.prepare_test_env(request.module)

# Prepares
@pytest.fixture(scope="module")
def prepare_pcap(request):
    yield setup_tools.prepare_pcap(request.module)

