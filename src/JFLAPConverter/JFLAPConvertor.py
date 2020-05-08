import argparse
import xml.etree.ElementTree as xml


class JFLAPConvertor:
    DELTA = '\u03b4'
    SIGMA = '\u03a3'
    GAMMA = '\u0393'
    BLANK = '\u25a0'

    def __init__(self, filename: str):
        self.tree = xml.parse(filename).getroot()
        self.states = {}
        self.initial = ''
        self.final = []
        self.alphabet = set()
        self.transitions = []

        self.__load_states()
        self.__load_transitions()

    def __load_states(self):
        for state in self.tree.findall('./automaton/state'):
            name = state.attrib['name']
            self.states[state.attrib['id']] = name

            if state.find('initial') is not None:
                self.initial = name
            elif state.find('final') is not None:
                self.final.append(name)

    def __load_transitions(self):
        for trans in self.tree.findall('./automaton/transition'):
            start = self.states[trans.find('from').text]
            end = self.states[trans.find('to').text]

            read = trans.find('read').text or self.BLANK
            write = trans.find('write').text or self.BLANK
            move = trans.find('move').text
            self.alphabet.update([read, write])

            self.transitions.append(f"{self.DELTA}({start}, {read}) = ({end}, {write}, {move})")
        self.transitions.sort()

    @property
    def definition(self) -> str:
        return f"TM = (K, {self.SIGMA}, {self.GAMMA}, {self.DELTA}, {self.initial}, F)"

    @property
    def states_set(self) -> str:
        return f"K = {{{', '.join(sorted(self.states.values()))}}}"

    @property
    def alphabet_set(self) -> str:
        return f"{self.GAMMA} = {{{', '.join(sorted(self.alphabet))}}}"

    @property
    def final_states_set(self) -> str:
        return f"F = {{{', '.join(sorted(self.final))}}}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='JFLAP file to process')
    parser.add_argument('output', type=str, help='Text file for list of states')
    args = parser.parse_args()

    with open(args.output, 'w') as output:
        machine = JFLAPConvertor(args.input)

        print(machine.definition, file=output)
        print(machine.states_set, file=output)
        print(machine.alphabet_set, file=output)
        print(machine.final_states_set, file=output)

        for t in machine.transitions:
            print(t, file=output)
