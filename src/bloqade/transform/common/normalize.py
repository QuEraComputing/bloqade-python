# import bloqade.ir.scalar as scalar
# import bloqade.ir.analog_circuit as analog_circuit

# import bloqade.ir.control.waveform as waveform
# import bloqade.ir.control.field as field
# import bloqade.ir.control.pulse as pulse
# import bloqade.ir.control.sequence as sequence
# from bloqade.ir.visitor.analog_circuit import AnalogCircuitVisitor

# from bloqade.builder.typing import LiteralType
# from beartype.typing import Any, Dict


# passes for compiling to hardware
# Transformations:
# 1. Assignment of variables (static and dynamic and record)
# 2. Validate assignments
# 3. flatten IR moving slices/appends to waveform level
# Scan and Validate
# 4. validate spatial modulations
# 5. validate waveform
# Code generation
# 6. generate IR for hardware
