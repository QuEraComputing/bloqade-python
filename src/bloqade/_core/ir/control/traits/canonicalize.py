class CanonicalizeTrait:
    @staticmethod
    def canonicalize(expr):
        from bloqade._core.compiler.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)
