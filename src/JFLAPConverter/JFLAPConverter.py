import argparse
import xml.etree.ElementTree as xml
from typing import List


class UnsupportedAutomataError(Exception):
    pass


class Automaton:
    DELTA = '\u03b4'
    SIGMA = '\u03a3'
    GAMMA = '\u0393'
    EPSILON = '\u03b5'
    BLANK = '\u25a1'

    def __init__(self):
        self.states = {}
        self.initial = ''
        self.final = []
        self.alphabet = set()
        self.transitions = []

    def new_state(self, state: xml.Element):
        name = state.attrib['name']
        self.states[state.attrib['id']] = name

        if state.find('initial') is not None:
            self.initial = name
        if state.find('final') is not None:
            self.final.append(name)

    def entity(self, element: xml.Element, name: str) -> str:
        return element.find(name).text or self.EPSILON

    def alphabet_set(self, label) -> str:
        return f"{label} = {{{', '.join(sorted(self.alphabet))}}}"

    def states_set(self, label) -> str:
        return f"{label} = {{{', '.join(sorted(self.states.values()))}}}"

    def final_states_set(self, label) -> str:
        return f"{label} = {{{', '.join(sorted(self.final))}}}"


class FiniteAutomaton(Automaton):

    def __init__(self):
        super().__init__()

    def new_transition(self, transition: xml.Element):
        q1 = self.states[self.entity(transition, 'from')]
        q2 = self.states[self.entity(transition, 'to')]
        read = self.entity(transition, 'read')

        transition = f"{self.DELTA}({q1}, {read}) = {q2}"

        self.alphabet.update(read)
        self.transitions.append(transition)

    @property
    def definition(self) -> List[str]:
        return [
            f'FA = (K, {self.SIGMA}, {self.DELTA}, {self.initial}, F)',
            self.states_set('K'),
            self.alphabet_set(self.SIGMA),
            self.final_states_set('F')
        ]


class PushdownAutomaton(Automaton):

    def __init__(self):
        super().__init__()
        self.stack_alphabet = set()

    def new_transition(self, transition):
        q1 = self.states[self.entity(transition, 'from')]
        q2 = self.states[self.entity(transition, 'to')]
        read = self.entity(transition, 'read')
        pop = self.entity(transition, 'pop')
        push = self.entity(transition, 'push')

        transition = f"{self.DELTA}({q1}, {read}, {pop}) = ({q2}, {push})"

        self.stack_alphabet.update(pop)
        self.stack_alphabet.update(push)

        self.alphabet.update(read)
        self.transitions.append(transition)

    @property
    def definition(self) -> List[str]:
        return [
            f'PDA = (K, {self.SIGMA}, {self.GAMMA}, {self.DELTA}, {self.initial}, Z, F)',
            self.states_set("K"),
            self.alphabet_set(self.SIGMA),
            f"{self.GAMMA} = {{{', '.join(sorted(self.stack_alphabet))}}}",
            self.final_states_set("F")
        ]


class TuringMachine(Automaton):

    def __init__(self):
        super().__init__()

    def new_transition(self, transition: xml.Element):
        q1 = self.states[self.entity(transition, 'from')]
        q2 = self.states[self.entity(transition, 'to')]
        read = self.entity(transition, 'read')
        write = self.entity(transition, 'write')
        move = self.entity(transition, 'move')

        transition = f"{self.DELTA}({q1}, {read}) = ({q2}, {write}, {move})"

        self.alphabet.update([read, write])
        self.transitions.append(transition)

    def entity(self, element: xml.Element, name: str) -> str:
        return element.find(name).text or self.BLANK

    @property
    def definition(self) -> List[str]:
        sets = [
            f"TM = (K, {self.SIGMA}, {self.GAMMA}, {self.DELTA}, {self.initial}, F)",
            self.states_set('K'),
            f"{self.SIGMA} = {{...}}",
            self.alphabet_set(self.GAMMA),
            self.final_states_set('F')
        ]

        return sets


class JFLAPConverter:

    def __init__(self, filename: str):
        self.tree = xml.parse(filename).getroot()
        self.automata = {
            'fa': FiniteAutomaton,
            'pda': PushdownAutomaton,
            'turing': TuringMachine
        }

        try:
            self.automaton = self.automata[self.tree.find('type').text]()
        except KeyError:
            raise UnsupportedAutomataError()

        for state in self.tree.findall('./automaton/state'):
            self.automaton.new_state(state)
        for trans in self.tree.findall('./automaton/transition'):
            self.automaton.new_transition(trans)

    @property
    def machine(self) -> Automaton:
        return self.automaton


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='JFLAP file to process')
    parser.add_argument('output', type=str, help='Text file for list of states')
    args = parser.parse_args()

    with open(args.output, 'w', encoding='utf-8') as output:
        try:
            jflap = JFLAPConverter(args.input)

            for d in jflap.machine.definition:
                print(d, file=output)
            for t in jflap.machine.transitions:
                print(t, file=output)

        except UnsupportedAutomataType:
            print("Supplied automaton type is not supported")
