
import re, logging
logger = logging.getLogger(__name__)

class KConfigurationFile:
    def __init__(self, filename):
        self.data = {}
        self.read_conf_file(filename)

    def read_conf_file(self, filename):
        self.data = {}
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if '#' in line:
                    line = line.split('#')[0].strip()
                if '!' in line:
                    line = line.split('!')[0].strip()
                if len(line) < 1:
                    continue
                if ':' in line:
                    key_value = line.split(':', 1)
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    match = re.match(r'^([^\[]+)\[([^\]]+)\]', key)
                    if match:
                        main_key = match.group(1)
                        sub_key = match.group(2)
                    else:
                        main_key = key
                        sub_key = ''
                    if main_key not in self.data:
                        self.data[main_key] = {}
                    self.data[main_key][sub_key] = value

    # subkey='' means all subkeys values will be replaced
    def replace_value_of_key(self, key, value, subkey=None):
        if key not in self.data:
            return False
        if len(self.data[key])<1:
            return False
        for sk in self.data[key]:
            if subkey is None or sk==subkey:
                self.data[key][sk] = value
        return True

    def print_key_to_stringlist(self, key):
        lines = []
        for k in self.data[key]:
            if k=='':
                lines.append(key + ': ' + self.data[key][k])
            else:
                lines.append(key + '[' + k + ']: ' + self.data[key][k])
        return lines

    def print_to_file(self, filename):
        logger.debug('Dumping configuration to file: ' + filename)
        with open(filename, 'w') as f:
            for key in self.data:
                lines = self.print_key_to_stringlist(key)
                for line in lines:
                    f.write(line + '\n')
