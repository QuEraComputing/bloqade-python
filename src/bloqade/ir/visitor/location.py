from bloqade.ir.location import (
    AtomArrangement,
    Chain,
    Square,
    Rectangular,
    Honeycomb,
    Triangular,
    Lieb,
    Kagome,
    ListOfLocations,
    ParallelRegister,
)
from bloqade.ir.location.base import LocationInfo
from typing import Union, Any


AstType = Union[AtomArrangement, ParallelRegister]


class LocationVisitor:
    def visit_location_info(self, ast: LocationInfo) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for LocationInfo"
        )

    def visit_chain(self, ast: Chain) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Chain"
        )

    def visit_square(self, ast: Square) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Square"
        )

    def visit_rectangular(self, ast: Rectangular) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Rectangular"
        )

    def visit_honeycomb(self, ast: Honeycomb) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Honeycomb"
        )

    def visit_triangular(self, ast: Triangular) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Triangular"
        )

    def visit_lieb(self, ast: Lieb) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Lieb"
        )

    def visit_kagome(self, ast: Kagome) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for Kagome"
        )

    def visit_list_of_locations(self, ast: ListOfLocations) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for ListOfLocations"
        )

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        raise NotImplementedError(
            f"No visitor method implemented in {self.__class__} for ParallelRegister"
        )

    def visit(self, ast: AstType) -> Any:
        if isinstance(ast, Chain):
            return self.visit_chain(ast)
        elif isinstance(ast, Square):
            return self.visit_square(ast)
        elif isinstance(ast, Rectangular):
            return self.visit_rectangular(ast)
        elif isinstance(ast, Honeycomb):
            return self.visit_honeycomb(ast)
        elif isinstance(ast, Triangular):
            return self.visit_triangular(ast)
        elif isinstance(ast, Lieb):
            return self.visit_lieb(ast)
        elif isinstance(ast, Kagome):
            return self.visit_kagome(ast)
        elif isinstance(ast, ListOfLocations):
            return self.visit_list_of_locations(ast)
        elif isinstance(ast, ParallelRegister):
            return self.visit_parallel_register(ast)
        else:
            raise NotImplementedError(
                f"No visitor method implemented in {self.__class__} for {ast}"
            )
