###################################################
# Automated Testing Framework for Network Analytics
#
# helpers file for python auxiliary functions
#
###################################################

import os
import re, time, logging

logger = logging.getLogger(__name__)

#
#
def find_value_in_config_file(filename: str, keyname: str) -> str:
    relevant_lines = []
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if '#' in line:
            line = line.split('#')[0].strip()
            if len(line)<1:
                continue
        if '!' in line:
            line = line.split('!')[0].strip()
            if len(line) < 1:
                continue
        matches = re.findall(r"(?<=" + keyname + ": ).+", line)
        if len(matches) > 0:
            return matches[0].strip()
        # Handling plugins
        if line.startswith(keyname):
            parts = line.split('[')
            if len(parts)>1 and parts[0]==keyname:
                parts = line.split(':')
                if len(parts)>1:
                    return parts[1].strip()
    return None

def get_current_time_in_milliseconds() -> int:
    return round(time.time()*1000)

def file_contains_string(file_path: str, text: str) -> bool:
    retVal = False
    with open(file_path, 'r') as file:
        retVal = text in file.read()
    return retVal

def check_regex_sequence_in_file(file_path, regexes):
    logger.debug('Checking file ' + file_path + ' for patterns ' + str(regexes))
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

# Untested - not used currently
def check_string_sequence_in_file(file_path, strings):
    logger.debug('Checking file ' + file_path + ' for patterns ' + str(strings))
    with open(file_path, 'r') as file:
        text = file.read()
        start = 0
        for pattern in strings:
            logger.debug('Checking string: ' + pattern)
            idx = text[start:].find(pattern)
            if idx<0:
                logger.debug('No match')
                return False
            logger.debug('Matched')
            start = idx + len(pattern)
        return True

def check_file_regex_sequence_in_file(file_path, file_regexes):
    with open(file_regexes) as f:
        regexes = f.read().split('\n')
    regexes = [regex for regex in regexes if len(regex)>0 and not regex.startswith('#')]
    logger.info('Checking for ' + str(len(regexes)) + ' regexes')
    retval = check_regex_sequence_in_file(file_path, regexes)
    if retval:
        logger.info('All regexes found!')
    return retval

# Untested - not used currently
def check_file_string_sequence_in_file(file_path, file_strings):
    with open(file_strings) as f:
        strings = f.read().split('\n')
    strings = [_string for _string in strings if len(_string)>0 and not _string.startswith('#')]
    logger.info('Checking for ' + str(len(strings)) + ' regexes')
    retval = check_string_sequence_in_file(file_path, strings)
    if retval:
        logger.info('All strings found!')
    return retval

def short_name(filename):
    return os.path.basename(os.path.dirname(filename))+'/'+os.path.basename(filename)

def replace_in_file(filename, search_pattern, replace_pattern, exclude_if_line_contains = None):
    logger.debug('Replacing ' + search_pattern + ' with ' + replace_pattern + ' in file ' + short_name(filename))
    with open(filename) as f:
        lines = f.readlines()
    with open(filename + '.bak', 'w') as f:
        for line in lines:
            if exclude_if_line_contains and exclude_if_line_contains in line:
                f.write(line)
            else:
                f.write(line.replace(search_pattern, replace_pattern))
    os.rename(filename + '.bak', filename)

# Given a folder, returns a list of files matching a regular expression
def select_files(folder_path, regex_pattern):
    regex = re.compile(regex_pattern)
    files = os.listdir(folder_path)
    # Select matching files
    selected_files = []
    for file_name in files:
        if regex.match(file_name):
            selected_files.append(file_name)
    return sorted(selected_files)

# Counts non-empty lines in a file
def count_non_empty_lines(file_path):
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            if len(line.strip()):
                count += 1
    return count
