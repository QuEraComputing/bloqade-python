import json
from typing import Any
from beartype.typing import Type, Callable, Dict
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

                if deserialize is None:
                    raise TypeError(f"no deserializer registered for type {cls}")

                return deserialize(value)

        return d

    def default(self, o: Any) -> Any:
        if type(o) in self.serializers:
            cls = type(o)
            serializer = self.serializers.get(cls)
            if serializer is None:
                raise TypeError(f"no serializer registered for type {cls}")

            return {self.type_to_str[cls]: serializer(o)}

        return super().default(o)


def loads(s, **json_kwargs):
    return json.loads(s, object_hook=Serializer.object_hook, **json_kwargs)


def load(fp, **json_kwargs):
    return json.load(fp, object_hook=Serializer.object_hook, **json_kwargs)


def dumps(o, **json_kwargs):
    return json.dumps(o, cls=Serializer, **json_kwargs)


def dump(o, fp, **json_kwargs):
    return json.dump(o, fp, cls=Serializer, **json_kwargs)
