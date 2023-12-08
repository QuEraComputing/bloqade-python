class CanonicalizeTrait:
    @staticmethod
    def canonicalize(expr):
        from bloqade.rewrite.common.canonicalize import Canonicalizer

        return Canonicalizer().visit(expr)
