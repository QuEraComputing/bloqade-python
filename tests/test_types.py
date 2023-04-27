# from bloqade.julia.types import Vector, Int64

# print(Vector[Int64]([1, 2, 3]))



class Vector:

    def __init__(self, *params) -> None:
        self.expr = 'Vector'
        self.params = params
    
    def __getitem__(self, *params) -> 'Vector':
        return Vector(*params)


Vector(int)