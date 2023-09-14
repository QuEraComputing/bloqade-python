import json
from typing import Any
from beartype.typing import Dict, Type, Union, List
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
        def set_serializer(f: Callable):
            type_name = f"{cls.__module__}.{cls.__name__}"
            Serializer.serializers[cls] = f
            Serializer.type_to_str[cls] = type_name
            Serializer.str_to_type[type_name] = cls

            return f
        
        @beartype
        def set_deserializer(f: Callable):
            Serializer.deserializers[cls] = f

            return f

        Serializer.methods[cls] = None

        setattr(cls, "set_serializer", set_serializer)
        setattr(cls, "set_deserializer", set_deserializer)

        return cls
    
    def object_hook(self, d: Any) -> Any:
        if isinstance(d, dict) and len(d) == 1:
            ((key, value),) = d.items()
            if key in self.str_to_type:
                return self.str_to_type[key](**value)
            


    def default(self, o: Any) -> Any:
        if type(o) in self.methods:
            cls = type(o)
            if self.methods[cls] is None:
                raise TypeError(f"no serializer registered for type {cls}")
            

            method = getattr(o, self.methods[type(o)])
            return {self.type_to_str[cls]: method(o)}

        return super().default(o)


def loads(s, use_decimal=True, **json_kwargs):
    return json.loads(
        s, object_hook=Serializer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


def load(fp, use_decimal=True, **json_kwargs):
    return json.load(
        fp, object_hook=Serializer.object_hook, use_decimal=use_decimal, **json_kwargs
    )


def dumps(o, use_decimal=True, **json_kwargs):
    return json.dumps(o, cls=Serializer, use_decimal=use_decimal, **json_kwargs)


def dump(o, fp, use_decimal=True, **json_kwargs):
    return json.dump(o, fp, cls=Serializer, use_decimal=use_decimal, **json_kwargs)
