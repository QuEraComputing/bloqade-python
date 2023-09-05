from dataclasses import dataclass
from enum import Enum
import numpy as np
from numpy.typing import NDArray




@dataclass(frozen=True)
class AtomType:
    def string_to_integer(self, fock_state: str) -> int:
        state_string = fock_state.replace("|", "").replace(">", "")

        state_int = 0
        shift = 1
        for local_state in state_string:
            state_int += shift * self.str_to_int[local_state]
            shift *= self.n_level

        return state_int

    def integer_to_string(self, state_int: int, n_atoms: int) -> str:
        state_string = ""
        local_state = state_int % self.n_level

        state_string = state_string + self.int_to_str[local_state]
        state_int //= self.n_level

        while state_int > 0:
            local_state = state_int % self.n_level

            state_string = state_string + self.int_to_str[local_state]
            state_int //= self.n_level

        if len(state_string) < n_atoms:
            state_string = state_string + "g" * (n_atoms - len(state_string))

        return f"|{state_string}>"

    def is_rydberg_at(self, configurations: NDArray, index: int) -> NDArray:
        return self.is_state_at(configurations, index, self.State.Rydberg)

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: int, state_2: int
    ) -> NDArray:
        raise NotImplementedError

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: int, to: int
    ) -> NDArray:
        raise NotImplementedError

    def is_state_at(self, configurations: NDArray, index: int, state: int) -> NDArray:
        raise NotImplementedError

    def __hash__(self):
        return hash(self.__class__)


@dataclass(frozen=True)
class ThreeLevelAtomType(AtomType):
    n_level = 3
    str_to_int = {"g": 0, "h": 1, "r": 2}
    int_to_str = ["g", "h", "r"]

    class State(int, Enum):
        Ground = 0
        Hyperfine = 1
        Rydberg = 2

    def is_state_at(cls, configurations: NDArray, index: int, state):
        if not isinstance(state, cls.State):
            raise ValueError(f"state: {state} is not a valid state for {cls.__name__}.")

        mask = (configurations // 3**index) % 3
        return mask == state.value

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: State, state_2: State
    ) -> NDArray:
        state_1 = self.State(state_1)
        state_2 = self.State(state_2)

        output = configurations.copy()

        mask_1 = self.is_state_at(configurations, index, state_1)
        mask_2 = self.is_state_at(configurations, index, state_2)
        delta = state_2.value - state_1.value

        output[mask_1] += delta * 3**index
        output[mask_2] -= delta * 3**index

        np.logical_or(mask_1, mask_2, out=mask_1)

        return mask_1, output[mask_1]

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: State, to: State
    ) -> NDArray:
        fro = self.State(fro)
        to = self.State(to)

        input_configs = self.is_state_at(configurations, index, fro)
        output_configs = configurations[input_configs]

        delta = to.value - fro.value
        return (input_configs, output_configs + (delta * 3**index))


@dataclass(frozen=True)
class TwoLevelAtomType(AtomType):
    n_level = 2
    str_to_int = {"g": 0, "r": 1}
    int_to_str = ["g", "r"]

    class State(int, Enum):
        Ground = 0
        Rydberg = 1

    def is_state_at(self, configurations: NDArray, index: int, state: State):
        state = self.State(state)

        mask = ((configurations >> index) & 1) == 1

        if state == self.State.Ground:
            return np.logical_not(mask)

        return mask

    def swap_state_at(
        self, configurations: NDArray, index: int, state_1: State, state_2: State
    ) -> NDArray:
        state_1 = self.State(state_1)
        state_2 = self.State(state_2)
        return slice(None), configurations ^ (1 << index)

    def transition_state_at(
        self, configurations: NDArray, index: int, fro: State, to: State
    ) -> NDArray:
        fro = self.State(fro)
        to = self.State(to)

        input_configs = self.is_state_at(configurations, index, fro)
        output_configs = configurations[input_configs]
        return (input_configs, output_configs ^ (1 << index))


ThreeLevelAtom = ThreeLevelAtomType()
TwoLevelAtom = TwoLevelAtomType()
