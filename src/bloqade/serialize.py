import simplejson as json
from typing import Any
from beartype.typing import Dict, Type, Union, List
from beartype import beartype


class Serializer(json.JSONEncoder):
    types = ()

    def default(self, o: Any) -> Any:
        if type(o) in self.types:  # do not check inheritance
            return o._bloqade_serialize()

        return super().default(o)


class Deserialzer:
    types = {}

    @classmethod
    def object_hook(cls, d):
        if isinstance(d, dict) and len(d) == 1:
            ((key, value),) = d.items()
            if key in cls.types:
                return cls.types[key](**value)

        return d


def loads(s, use_decimal=True, **json_kwargs):
    return json.loads(
        s, object_hook=Deserialzer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


def load(fp, use_decimal=True, **json_kwargs):
    return json.load(
        fp, object_hook=Deserialzer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


def dumps(o, use_decimal=True, **json_kwargs):
    return json.dumps(o, cls=Serializer, use_decimal=use_decimal, **json_kwargs)


def dump(o, fp, use_decimal=True, **json_kwargs):
    return json.dump(o, fp, cls=Serializer, use_decimal=use_decimal, **json_kwargs)


@beartype
def register_serializer(field_aliases: Union[List[str], Dict[str, str]]):
    """Register a class to be serialized and deserialized by bloqade.

    Args:
        field_aliases (Dict[str, str]): A dictionary mapping the names of the
            fields of the class to the names of the fields in the serialized
            form. Note that the serialized name will be passed into the class's
            constructor as a keyword argument. The serialized name must be a
            valid Python identifier (i.e. it must start with a letter or
            underscore and contain only letters, numbers, and underscores).
    """

    if isinstance(field_aliases, list):
        field_aliases = {field_alias: field_alias for field_alias in field_aliases}

    def _bloqade_serialize(self):
        return {
            self.__bloqade_type_name__: {
                field_alias: getattr(self, field_name)
                for field_name, field_alias in self.__bloqade_field_aliases.items()
            }
        }

    @beartype
    def _wrapper(cls: Type):
        from inspect import getmodule

        # Check that the field aliases are valid Python identifiers.
        for field_alias in field_aliases.values():
            assert field_alias.isidentifier(), (
                f"Serialized field alias {field_alias} is not a valid Python "
                "identifier."
            )

        __bloqade_type_name__ = f"{getmodule(cls).__name__}.{cls.__name__}"

        cls.__bloqade_type_name__ = __bloqade_type_name__
        cls.__bloqade_field_aliases = field_aliases
        cls._bloqade_serialize = _bloqade_serialize
        Serializer.types += (cls,)
        Deserialzer.types[__bloqade_type_name__] = cls

        return cls

    return _wrapper
