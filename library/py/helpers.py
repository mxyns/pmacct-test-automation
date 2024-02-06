###################################################
# Automated Testing Framework for Network Analytics
# Helpers file for python auxiliary functions
# nikolaos.tsokas@swisscom.com 26/02/2023
###################################################

import os, re, logging, time, json, yaml
from typing import Callable
from typing import List, Dict

logger = logging.getLogger(__name__)


class KFileList(list):
    def getFileLike(self, txt):
        for filename in self:
            basename = os.path.basename(filename)
            if txt in basename:
                return filename
        return None

# Returns true if "text" exists anywhere in the "file_path" file, false otherwise
def file_contains_string(file_path: str, text: str) -> bool:
    retVal = False
    with open(file_path, 'r') as file:
        retVal = text in file.read()
    return retVal

# Return true if all regular expressions in "regexes" are matched against the content of file "file_path"
# in the given order, false otherwise
def check_regex_sequence_in_file(file_path: str, regexes: List[str]) -> bool:
    logger.debug('Checking file ' + file_path + ' for regex patterns')
    with open(file_path, 'r') as file:
        text = file.read()
        start = 0
        for pattern in regexes:
            logger.debug('Checking regex: ' + pattern)
            match = re.search(pattern, text[start:])
            if not match:
                logger.debug('No match')
                return False
            logger.debug('Matched')
            start = match.end()
        return True

# File "file_regexes" is supposed to be a file, whose lines are regular expressions
# Returns true if all regular expressions in file are matched against the content of file "file_path"
# in the given order, false otherwise
def check_file_regex_sequence_in_file(file_path: str, file_regexes: str) -> bool:
    with open(file_regexes) as f:
        regexes = f.read().split('\n')
    regexes = [regex for regex in regexes if len(regex)>0 and not regex.startswith('#')]
    logger.info('Checking for ' + str(len(regexes)) + ' regexes')
    retval = check_regex_sequence_in_file(file_path, regexes)
    if retval:
        logger.info('All regexes found!')
    return retval

# Returns a short version of the file path, that is only the parent folder and the filename itself
def short_name(filename: str) -> str:
    return os.path.basename(os.path.dirname(filename))+'/'+os.path.basename(filename)

# In file "filename", it replaces all occurrences of "search_pattern" with "replace_pattern",
# except for lines containing string "exclude_if_line_contains", which are excluded from this process
# If "exclude_if_line_contains" is None (left with default value), no line is excluded
def replace_in_file(filename: str, search_pattern: str, replace_pattern: str, exclude_if_line_contains: str = None):
    repl_text = '<nothing>' if replace_pattern=='' else replace_pattern
    logger.debug('Replacing ' + search_pattern + ' with ' + repl_text + ' in file ' + short_name(filename))
    with open(filename) as f:
        lines = f.readlines()
    with open(filename + '.bak', 'w') as f:
        for line in lines:
            if exclude_if_line_contains and exclude_if_line_contains in line:
                f.write(line)
            else:
                f.write(line.replace(search_pattern, replace_pattern))
    os.rename(filename + '.bak', filename)

# Given a folder "folder_path", returns a list of files, whose names match the regular expression "regex_pattern"
def select_files(folder_path: str, regex_pattern: str) -> List[str]:
    regex = re.compile(regex_pattern)
    files = os.listdir(folder_path)
    # Select matching files
    selected_files = []
    for file_name in files:
        if regex.match(file_name):
            selected_files.append(file_name)
    return [folder_path + '/' + fn for fn in sorted(selected_files)]

# Counts non-empty lines in file "file_path"
def count_non_empty_lines(file_path: str) -> int:
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            if len(line.strip()):
                count += 1
    return count

# Checks if the checkfunc function returns True. Repeats every sec_repeat seconds until it returns True, or until
# time reaches max_seconds
def retry_until_true(checkmessage: str, checkfunc: Callable, max_seconds: int, sec_repeat: int =1) -> bool:
    logger.info('Waiting for: ' + checkmessage)
    out = checkfunc()
    while not out:
        max_seconds -= sec_repeat
        if max_seconds < 0:
            logger.info('Timed out: ' + checkmessage)
            return False
        time.sleep(sec_repeat)
        logger.info('Still waiting for: ' + checkmessage + ' (remaining ' + str(max_seconds) + ' seconds)')
        out = checkfunc()
    logger.info('Succeeded: ' + checkmessage)
    return True

# Loads a conf file (key=value) into a dictionary
def read_config_file(filename: str) -> Dict:
    conf_data = {}
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                conf_data[key] = value
    return conf_data

# Loads container resources information into a list of strings, for display
def container_resources_string(json_str: str) -> List:
    dct = json.loads(json_str)
    ret = []
    ret.append('Memory usage (used/available): ' + dct['MemUsage'])
    ret.append('Network usage (input/output): ' + dct['NetIO'])
    ret.append('Processes created: ' + dct['PIDs'])
    ret.append('Host CPU consumption: ' + dct['CPUPerc'])
    ret.append('Host memory consumption: ' + dct['MemPerc'])
    return ret

# Returns the version of pmacct from the fist log line
def read_pmacct_version(logfile: str) -> str:
    with open(logfile) as f:
        lines = f.read().splitlines()
    if len(lines)<1:
        return None
    parts = lines[0].split('): ')
    if len(parts)<2:
        return None
    return parts[1]

# Takes a folder with pcap information and returns the IP address of the traffic reproducer,
# as found in traffic-reproducer.yml
def get_repro_ip_from_pcap_folder(pcap_folder: str) -> str:
    with open(pcap_folder + '/docker-compose.yml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    net = data['services']['traffic-reproducer']['networks']['pmacct_test_network']
    if 'ipv4_address' in net.keys():
        return net['ipv4_address']
    elif 'ipv6_address' in net.keys():
        return net['ipv6_address']
    raise Exception('No IP information in file: ' + pcap_folder + '/docker-compose.yml')

# Replaces IPs in file, so that they reflect the framework subnet (which may or may not be
# different than the ones provided with the test case)
def replace_IPs(params, filename: str):
    if params.test_subnet_ipv4!='' and file_contains_string(filename, params.test_subnet_ipv4):
        replace_in_file(filename, params.test_subnet_ipv4, '172.21.1.10')
    if params.test_subnet_ipv6!='' and file_contains_string(filename, params.test_subnet_ipv6):
        replace_in_file(filename, params.test_subnet_ipv6, 'fd25::10')

# Returns reproduction IP, i.e., IP of the traffic repro container, and BGP ID from a pcap folder
def get_REPRO_IP_and_BGP_ID(pcap_mount_folder: str):
    with open(pcap_mount_folder + '/pcap0/traffic-reproducer.yml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    repro_info = [data['network']['map'][0]['repro_ip'], None]
    if 'bgp_id' in data['network']['map'][0]:
        repro_info[1] = data['network']['map'][0]['bgp_id']
    return repro_info