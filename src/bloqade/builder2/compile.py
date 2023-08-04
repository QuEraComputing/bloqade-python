from dataclasses import dataclass
from .base import Builder


@dataclass
class BuildState:
    pass


class BuilderVisitor:
    def visit(self, ast: Builder):
        pass
