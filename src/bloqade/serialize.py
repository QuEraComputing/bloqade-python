import simplejson as json
from typing import Any
from beartype.typing import Type, Callable, Dict, Union, TextIO
from beartype import beartype


class Serializer(json.JSONEncoder):
    types = ()
    type_to_str = {}
    str_to_type = {}
    serializers = {}
    deserializers = {}

    @staticmethod
    @beartype
    def register(cls: Type):
        @beartype
        def _deserializer(d: Dict[str, Any]) -> cls:
            return cls(**d)

        @beartype
        def _serializer(obj: cls) -> Dict[str, Any]:
            return obj.__dict__

        @beartype
        def set_serializer(f: Callable):
            # TODO: check function signature
            setattr(cls, "__bloqade_serializer__", staticmethod(f))
            Serializer.serializers[cls] = cls.__bloqade_serializer__

        @beartype
        def set_deserializer(f: Callable):
            # TODO: check function signature
            setattr(cls, "__bloqade_deserializer__", staticmethod(f))
            Serializer.deserializers[cls] = cls.__bloqade_deserializer__

        type_name = f"{cls.__module__}.{cls.__name__}"
        Serializer.type_to_str[cls] = type_name
        Serializer.str_to_type[type_name] = cls
        Serializer.types += (cls,)
        setattr(cls, "set_serializer", staticmethod(beartype(set_serializer)))
        setattr(cls, "set_deserializer", staticmethod(beartype(set_deserializer)))
        cls.set_deserializer(_deserializer)
        cls.set_serializer(_serializer)

        return cls

    @classmethod
    def object_hook(cls, d: Any) -> Any:
        if isinstance(d, dict) and len(d) == 1:
            ((key, value),) = d.items()
            if key in cls.str_to_type:
                obj_cls = cls.str_to_type[key]
                deserialize = cls.deserializers.get(obj_cls)

                return deserialize(value)

        return d

    def default(self, o: Any) -> Any:
        if type(o) in self.serializers:
            cls = type(o)
            serializer = self.serializers.get(cls)

            return {self.type_to_str[cls]: serializer(o)}

        return super().default(o)


@beartype
def loads(s: str, use_decimal: bool = True, **json_kwargs):
    """Load object from string

    Args:
        s (str): the string to load
        use_decimal (bool, optional): use decimal.Decimal for numbers. Defaults to True.
        **json_kwargs: other arguments passed to json.loads

    Returns:
        Any: the deserialized object
    """
    return json.loads(
        s, object_hook=Serializer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


@beartype
def load(fp: Union[TextIO, str], use_decimal: bool = True, **json_kwargs):
    """Load object from file

    Args:
        fp (Union[TextIO, str]): the file path or file object
        use_decimal (bool, optional): use decimal.Decimal for numbers. Defaults to True.
        **json_kwargs: other arguments passed to json.load

    Returns:
        Any: the deserialized object
    """
    if isinstance(fp, str):
        with open(fp, "r") as f:
            return json.load(
                f,
                object_hook=Serializer.object_hook,
                use_decimal=use_decimal,
                **json_kwargs,
            )
    else:
        return json.load(
            fp,
            object_hook=Serializer.object_hook,
            use_decimal=use_decimal,
            **json_kwargs,
        )


@beartype
def dumps(
    o: Any,
    use_decimal: bool = True,
    **json_kwargs,
) -> str:
    """Serialize object to string

    Args:
        o (Any): the object to serialize
        use_decimal (bool, optional): use decimal.Decimal for numbers. Defaults to True.
        **json_kwargs: other arguments passed to json.dumps

    Returns:
        str: the serialized object as a string
    """
    if not isinstance(o, Serializer.types):
        raise TypeError(
            f"Object of type {type(o)} is not JSON serializable. "
            f"Only {Serializer.types} are supported."
        )
    return json.dumps(o, cls=Serializer, use_decimal=use_decimal, **json_kwargs)


@beartype
def save(
    o: Any,
    fp: Union[TextIO, str],
    use_decimal=True,
    **json_kwargs,
) -> None:
    """Serialize object to file

    Args:
        o (Any): the object to serialize
        fp (Union[TextIO, str]): the file path or file object
        use_decimal (bool, optional): use decimal.Decimal for numbers. Defaults to True.
        **json_kwargs: other arguments passed to json.dump

    Returns:
        None
    """
    if not isinstance(o, Serializer.types):
        raise TypeError(
            f"Object of type {type(o)} is not JSON serializable. "
            f"Only {Serializer.types} are supported."
        )
    if isinstance(fp, str):
        with open(fp, "w") as f:
            json.dump(o, f, cls=Serializer, use_decimal=use_decimal, **json_kwargs)
    else:
        json.dump(o, fp, cls=Serializer, use_decimal=use_decimal, **json_kwargs)
