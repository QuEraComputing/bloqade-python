# Background

## Neutral Atom Qubits

The qubits that QuEra's neutral atom computer *Aquila* and Bloqade are designed to emulate are based on *neutral atoms*. As the name implies they are atoms that are neutrally charged but are also capable of achieving a [Rydberg state](https://en.wikipedia.org/wiki/Rydberg_atom) where a single electron can be excited to an incredibly high energy level without ionizing the atom.

This incredibly excited electron energy level $|r\rangle$ and its default ground state $|g\rangle$ create a two-level system where superposition can occur. For enabling interaction between two or more qubits and achieving entanglement, when the neutral atoms are in the Rydberg state a phenomenon known as the Rydberg blockade can occur where an atom in the Rydberg state prevents a neighboring atom from also being excited to the same state.

For a more nuanced and in-depth read about the neutral atoms that Bloqade and *Aquila* use, refer to QuEra's qBook section on [Qubits by puffing up atoms](https://qbook.quera.com/learn/?course=6630211af30e7d0013c66147&file=6630211af30e7d0013c66149).

## Analog vs Digital Quantum Computing

There are two modes of quantum computation that [neutral atoms](#neutral-atom-qubits) are capable of: [*Analog*](#analog-mode) and [*Digital*](#digital-mode). 

You can find a brief explanation of the distinction below but for a more in-depth explanation you can refer to QuEra's qBook section on [Analog vs Digital Quantum Computing](https://qbook.quera.com/learn/?course=6630211af30e7d0013c66147&file=6630211af30e7d0013c6614a)

### Analog Mode

In the analog mode (supported by Bloqade and Aquila) you control your computation through the parameters of a [time-dependent Hamiltonian](#rydberg-many-body-hamiltonian) that influences all the qubits at once. There are options for [local control](#local-control) of the Hamiltonian on certain qubits however.


### Digital Mode

In the Digital Mode individual or multiple groups of qubits are controlled by applying *gates* (individual unitary operations). For [neutral atoms](#neutral-atom-qubits), this digital mode can be accomplished with the introduction of hyperfine coupling, enabling a quantum state to be stored for long periods of time while also allowing for multi-qubit gates.

## Rydberg Many-Body Hamiltonian

When you emulate a program in Bloqade, you are emulating the time evolution of the Rydberg many-body Hamiltonian which looks like this:

$$
i \hbar \dfrac{\partial}{\partial t} | \psi \rangle = \hat{\mathcal{H}}(t) | \psi \rangle,  \\
$$

$$
\frac{\mathcal{H}(t)}{\hbar} = \sum_j \frac{\Omega_j(t)}{2} \left( e^{i \phi_j(t) } | g_j \rangle  \langle r_j | + e^{-i \phi_j(t) } | r_j \rangle  \langle g_j | \right) - \sum_j \Delta_j(t) \hat{n}_j + \sum_{j < k} V_{jk} \hat{n}_j \hat{n}_k,
$$

where: $\Omega_j$, $\phi_j$, and $\Delta_j$ denote the Rabi frequency, laser phase, and the detuning of the driving laser field on atom (qubit) $j$ coupling the two states  $| g_j \rangle$ (ground state) and $| r_j \rangle$ (Rydberg state); $\hat{n}_j = |r_j\rangle \langle r_j|$ is the number operator, and $V_{jk} = C_6/|\mathbf{x}_j - \mathbf{x}_k|^6$ describes the Rydberg interaction (van der Waals interaction) between atoms $j$ and $k$ where $\mathbf{x}_j$ denotes the position of the atom $j$; $C_6$ is the Rydberg interaction constant that depends on the particular Rydberg state used. For Bloqade, the default $C_6 = 862690 \times 2\pi \text{ MHz μm}^6$ for $|r \rangle = \lvert 70S_{1/2} \rangle$ of the $^{87}$Rb atoms; $\hbar$ is the reduced Planck's constant.

## Local Control

The [Rydberg Many-Body Hamiltonian](#rydberg-many-body-hamiltonian) already implies from its subscripts that you can also have local control over your atoms. In Bloqade this local control extends to any term in the Hamiltonian while on *Aquila* this is currently restricted to the $\Delta_j$ laser detuning term.

*Fields* in Bloqade give you local (single-atom) control over the many-body Rydberg Hamiltonian.

They are a sum of one or more *spatial modulations*, which can be thought of as a scaling factor per atom site, multiplied by a waveform:

$$
F_{i}(t) = \sum_{\alpha} C_{i}^{\alpha}f_{\alpha}(t) 
$$

$$
C_{i}^{\alpha} \in \mathbb{R} 
$$

$$
f_{\alpha}(t) \colon \mathbb{R} \to \mathbb{R}
$$

The $i$-th component of the field is used to generate the *drive* at the $i$-th site.

Note that the drive is only applied if the $i$-th site is filled with an atom.

You build fields in Bloqade by first specifying the spatial modulation followed by the waveform
it should be multiplied by.

In the case of a uniform spatial modulation, it can be interpreted as 
a constant scaling factor where $C_{i}^{\alpha} = 1.0$.

