class CanonicalizeTrait:
    @staticmethod
    def canonicalize(expr):
        from bloqade.compiler.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)
