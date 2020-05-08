import argparse
import xml.etree.ElementTree as xml
from collections import defaultdict
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
        self.transitions = defaultdict(list)

    @property
    def delta_function(self):
        delta = []
        for state in sorted(self.transitions):
            for trans in self.transitions[state]:
                delta.append(trans)
        return delta

    def new_alphabet_symbol(self, symbol):
        if symbol is not None:
            self.alphabet.add(symbol)

    def new_state(self, state: xml.Element):
        name = state.attrib['name']
        self.states[state.attrib['id']] = name

        if state.find('initial') is not None:
            self.initial = name
        if state.find('final') is not None:
            self.final.append(name)

    def entity(self, element: xml.Element, name: str) -> str:
        return element.find(name).text

    def alphabet_set(self, label) -> str:
        return f"{label} = {{{', '.join(sorted(self.alphabet))}}}"

    def states_set(self, label) -> str:
        s = [self.states[key] for key in sorted(self.states)]
        return f"{label} = {{{', '.join(s)}}}"

    def final_states_set(self, label) -> str:
        return f"{label} = {{{', '.join(self.final)}}}"


class FiniteAutomaton(Automaton):

    def __init__(self):
        super().__init__()

    def new_transition(self, transition: xml.Element):
        q1 = self.states[self.entity(transition, 'from')]
        q2 = self.states[self.entity(transition, 'to')]

        read = self.entity(transition, 'read')
        self.new_alphabet_symbol(read)

        transition = f"{self.DELTA}({q1}, {read or self.EPSILON}) = {q2}"
        self.transitions[q1].append(transition)

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

    def new_stack_symbol(self, symbol):
        if symbol is not None:
            self.stack_alphabet.update(symbol)

    def new_transition(self, transition):
        q1 = self.states[self.entity(transition, 'from')]
        q2 = self.states[self.entity(transition, 'to')]

        read = self.entity(transition, 'read')
        pop = self.entity(transition, 'pop')
        push = self.entity(transition, 'push')

        self.new_alphabet_symbol(read)
        self.new_stack_symbol(pop)
        self.new_stack_symbol(push)

        transition = (f'{self.DELTA}({q1}, {read or self.EPSILON}, {pop or self.EPSILON})'
                      f'= ({q2}, {push or self.EPSILON})')
        self.transitions[q1].append(transition)

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

        self.new_alphabet_symbol(read)
        self.new_alphabet_symbol(write)

        transition = (f"{self.DELTA}({q1}, {read or self.BLANK}) = "
                      f"({q2}, {write or self.BLANK}, {move})")
        self.transitions[q1].append(transition)

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
            for t in jflap.machine.delta_function:
                print(t, file=output)

        except UnsupportedAutomataError:
            print("Supplied automaton type is not supported")
