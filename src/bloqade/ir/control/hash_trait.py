from functools import cached_property
from dataclasses import fields


class HashTrait:
    @cached_property
    def _hash_value(self):
        value = hash(self.__class__)
        for field in fields(self):
            field_value = getattr(self, field.name)
            if isinstance(field_value, list):
                value ^= hash(tuple(field_value))
            elif isinstance(field_value, dict):
                value ^= hash(frozenset(field_value.items()))
            else:
                value ^= hash(field_value)

        return value
