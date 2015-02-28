import json
from math import pi, sin
import wave
import logging
import struct
import time
import os

__all__ = ['create_dtmf_wave_file']

ROW_FREQ = (697, 770, 852, 941)
COL_FREQ = (1209, 1336, 1477, 1633)
SAMPLE_RATE = 44100  # hz
SAMPLE_WIDTH = 2
NUMBER_OF_CHANNELS = 1
COMPRESSION_TYPE = "NONE"
COMPRESSION_NAME = "Uncompressed"

FREQUENCY_MAP = dict()
FREQUENCY_MAP['1'] = (697, 1209)
FREQUENCY_MAP['2'] = (697, 1336)
FREQUENCY_MAP['3'] = (697, 1477)
FREQUENCY_MAP['A'] = (697, 1633)
FREQUENCY_MAP['4'] = (770, 1209)
FREQUENCY_MAP['5'] = (770, 1336)
FREQUENCY_MAP['6'] = (770, 1477)
FREQUENCY_MAP['B'] = (770, 1633)
FREQUENCY_MAP['7'] = (852, 1209)
FREQUENCY_MAP['8'] = (852, 1336)
FREQUENCY_MAP['9'] = (852, 1477)
FREQUENCY_MAP['C'] = (852, 1633)
FREQUENCY_MAP['*'] = (941, 1209)
FREQUENCY_MAP['0'] = (941, 1336)
FREQUENCY_MAP['#'] = (941, 1477)
FREQUENCY_MAP['D'] = (941, 1633)
FREQUENCY_MAP['S'] = (0, 0)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s <%(levelname)s> %(module)s.%(funcName)s() %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

log = logging.getLogger(__name__)


class DTMF:
    VALID_SEQUENCE_TYPES = [list, tuple, set]

    def __init__(self, input_string=None, input_list=None):
        """
        Initializes a DTMF instance with an option DTMF sequence. This can be a list of lists or a json string.
        If both are supplied, it tries to parse the json_string. If it does, it uses that. If there are errors, it
        validates the list and tries to use that. Basically input_string takes precedence.

        :param input_list: list of lists or tuples of the form [['A', 100], ['S', 50], ['2', 100], ['S', 50]]
        :param input_string: json_string of the form '[["A", 100], ["S", 50], ["2", 100], ["S", 50]]'
        """
        log.debug("Creating instance of DTMF")
        log.debug("input_string = {}".format(input_string))
        log.debug("input_list = {}".format(input_list))

        self._dtmf_sequence = None
        self._raw_data = None

        if input_string is not None:
            converted_json_sequence = self.parse_json_string(input_string)
            self.dtmf_sequence = converted_json_sequence
        elif input_list is not None:
            self.dtmf_sequence = input_list


    @property
    def dtmf_sequence(self):
        return self._dtmf_sequence

    @dtmf_sequence.setter
    def dtmf_sequence(self, input_sequence):
        if type(input_sequence) == str:
            input_sequence = self.parse_json_string(input_sequence)
        if type(input_sequence) == list:
            if self.dtmf_sequence_is_valid(input_sequence):
                self._dtmf_sequence = input_sequence
        log.debug("Set _dtmf_sequence to {}".format(self._dtmf_sequence))

    def parse_json_string(self, input_string):
        return json.loads(input_string)

    @staticmethod
    def dtmf_sequence_is_valid(input_list):
        """
        Validates an input sequence for proper structure and contents.

        :param input_list:
        :return:
        """
        if type(input_list) is not list:
            log.warning('input_list must be a list instance')
            return False

        if [(type(item) in DTMF.VALID_SEQUENCE_TYPES) for item in input_list].count(False) != 0:
            log.warning('input_list contains invalid sequence type')
            return False

        for item in input_list:
            if type(item[0]) != str or type(item[1]) != int:
                log.debug("Type list[0]: {}".format(type(item[0])))
                log.debug("Type list[1]: {}".format(type(item[1])))
                log.warning('input_list must contain a list of sequences of [str, int]')
                return False
        return True

    def generate_raw_data(self):
        """
        Generates raw data that can be saved into a .wav file. This can take some time to generate.

        :raise AttributeError: If no dtmf sequence has been set
        """
        _data = list()
        if self._dtmf_sequence is None:
            raise AttributeError("No dtmf sequence set")

        for tone_tuple in self._dtmf_sequence:
            key = tone_tuple[0]
            tone_duration = tone_tuple[1]
            f1 = FREQUENCY_MAP[key][0]
            f2 = FREQUENCY_MAP[key][1]
            _data += (self.generate_tone(f1, f2, tone_duration))
        self._raw_data = _data

    def save_wave_file(self, file_path):
        if self._raw_data is None or len(self._raw_data) < 1:
            self.generate_raw_data()

        f = wave.open(file_path, 'w')
        f.setnchannels(NUMBER_OF_CHANNELS)
        f.setsampwidth(SAMPLE_WIDTH)
        f.setframerate(SAMPLE_RATE)
        f.setnframes(len(self._raw_data))
        f.setcomptype(COMPRESSION_TYPE, COMPRESSION_NAME)
        log.info("Saving wav file {} THIS MAY TAKE A WHILE".format(file_path))
        for i in self._raw_data:
            f.writeframes(struct.pack('i', i))
        log.info("Saved file to {0}".format(file_path))
        f.close()

    @staticmethod
    def generate_tone(f1, f2, _duration_in_ms):
        """
        Generates a single value representing a sample of two combined frequencies.
        :param f1:
        :param f2:
        :param _duration_in_ms:
        :return:
        """
        assert f1 in ROW_FREQ or f1 == 0
        assert f2 in COL_FREQ or f2 == 0
        number_of_samples = int(SAMPLE_RATE * _duration_in_ms / 1000)
        scale = 32767  # signed int / 2

        result = list()
        for i in range(number_of_samples):
            p = i * 1.0 / SAMPLE_RATE
            result.append(int((sin(p * f1 * pi * 2) + sin(p * f2 * pi * 2)) / 2 * scale))
        log.info(
            "Generated {0}ms tone of {1} samples with F1: {2} F2: {3}".format(_duration_in_ms, number_of_samples, f1, f2))
        return result

    def create_dtmf_wave_file(self, input_sequence, file_path, dump_to_csv=False):
        """
        A convenience method. Validates and assigns a dtmf_sequence, then generates data and saves to a .wav

        :param input_sequence: list of lists or tuples of the form [['A', 100], ['S', 50], ['2', 100], ['S', 50]] or json_string of the form '[["A", 100], ["S", 50], ["2", 100], ["S", 50]]'
        :param file_path: the full path of the wav file that will be saved
        """
        self.dtmf_sequence=input_sequence
        self.generate_raw_data()

        try:
            os.remove('dtmf_dump.csv')
        except:
            pass #file doesn't exist

        if dump_to_csv:
            with open('dtmf_dump.csv', 'w') as f:
                for d in self._raw_data:
                    f.write(str(d))
                    f.write(",")

        self.save_wave_file(file_path)


if __name__ == '__main__':
    d = 100
    sample_input = [('1', d), ('S', d), ('2', d), ('S', d), ('A', d), ('S', d)]
    d = DTMF()
    d.create_dtmf_wave_file(sample_input, file_path='test.wav',dump_to_csv=True)