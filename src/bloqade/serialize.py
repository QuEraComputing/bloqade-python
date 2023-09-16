import simplejson as json
from typing import Any
from beartype.typing import Type, Callable, Dict, Union, TextIO
from beartype import beartype


class Serializer(json.JSONEncoder):
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


def loads(s, use_decimal=True, **json_kwargs):
    return json.loads(
        s, object_hook=Serializer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


def load(fp: Union[TextIO, str], use_decimal=True, **json_kwargs):
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


def dumps(o, use_decimal=True, **json_kwargs):
    return json.dumps(o, cls=Serializer, use_decimal=use_decimal, **json_kwargs)


def save(o, fp: Union[TextIO, str], use_decimal=True, **json_kwargs):
    if isinstance(fp, str):
        with open(fp, "w") as f:
            return json.dump(
                o, f, cls=Serializer, use_decimal=use_decimal, **json_kwargs
            )
    else:
        return json.dump(o, fp, cls=Serializer, use_decimal=use_decimal, **json_kwargs)
