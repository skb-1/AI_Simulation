"""Pure Python 3.10 fallback implementation of Pydantic v2 core features.

Used when pydantic is not installed, so the project works with zero extra downloads.
"""

from __future__ import annotations

import json
import sys
import typing
from typing import Any, Literal, Union, get_args, get_origin


class ValidationError(ValueError):
    """Raised when field validation fails."""


class FieldInfo:
    """Stores metadata for a model field."""

    def __init__(self, default: Any = ..., default_factory: Any = None, **kwargs: Any) -> None:
        self.default = default
        self.default_factory = default_factory
        self.extra = kwargs


def Field(default: Any = ..., *, default_factory: Any = None, **kwargs: Any) -> FieldInfo:
    """Declare field defaults and metadata."""
    return FieldInfo(default=default, default_factory=default_factory, **kwargs)


class BaseModelMeta(type):
    """Metaclass that extracts field annotations and defaults."""

    @property
    def _fields(cls) -> dict[str, tuple[Any, FieldInfo]]:
        if "_computed_fields" in cls.__dict__:
            return cls._computed_fields
        try:
            mod = sys.modules.get(cls.__module__)
            global_ns = mod.__dict__ if mod else None
            hints = typing.get_type_hints(cls, global_ns)
        except Exception:
            hints = getattr(cls, "__annotations__", {})

        fields = {}
        for fname, ftype in hints.items():
            val = getattr(cls, fname, ...)
            if isinstance(val, FieldInfo):
                fields[fname] = (ftype, val)
            elif val is not ...:
                fields[fname] = (ftype, FieldInfo(default=val))
            else:
                fields[fname] = (ftype, FieldInfo(default=...))

        cls._computed_fields = fields
        return fields


class BaseModel(metaclass=BaseModelMeta):
    """Lightweight pure-Python base model mimicking Pydantic v2 API."""

    def __init__(self, **kwargs: Any) -> None:
        fields = self.__class__._fields
        for fname, (ftype, finfo) in fields.items():
            if fname in kwargs:
                val = kwargs[fname]
            elif finfo.default_factory is not None:
                val = finfo.default_factory()
            elif finfo.default is not ...:
                val = finfo.default
            else:
                raise ValidationError(f"Missing required field: {fname}")
            val = self._validate_field(fname, ftype, val)
            setattr(self, fname, val)

    @classmethod
    def _validate_field(cls, fname: str, ftype: Any, val: Any) -> Any:
        origin = get_origin(ftype)
        args = get_args(ftype)

        if origin is Literal:
            if val not in args:
                raise ValidationError(f"Field {fname}: value {val!r} not in {args}")
            return val

        if origin is tuple:
            if not isinstance(val, (list, tuple)):
                raise ValidationError(f"Field {fname}: expected tuple, got {type(val)}")
            if args:
                if len(args) == 2 and args[1] is ...:
                    return tuple(args[0](x) for x in val)
                if len(val) != len(args):
                    raise ValidationError(
                        f"Field {fname}: expected {len(args)} items, got {len(val)}"
                    )
                return tuple(t(x) for t, x in zip(args, val))
            return tuple(val)

        if origin is list:
            if not isinstance(val, (list, tuple)):
                raise ValidationError(f"Field {fname}: expected list, got {type(val)}")
            elem_type = args[0] if args else Any
            if elem_type is not Any:
                return [elem_type(x) for x in val]
            return list(val)

        if origin is dict:
            if not isinstance(val, dict):
                raise ValidationError(f"Field {fname}: expected dict, got {type(val)}")
            k_type = args[0] if len(args) > 0 else Any
            v_type = args[1] if len(args) > 1 else Any
            res = {}
            for k, v in val.items():
                rk = k_type(k) if k_type is not Any else k
                rv = v_type(v) if v_type is not Any else v
                res[rk] = rv
            return res

        if origin is Union:
            for sub_t in args:
                try:
                    return cls._validate_field(fname, sub_t, val)
                except Exception:
                    continue
            raise ValidationError(
                f"Field {fname}: value {val!r} does not match Union {args}"
            )

        if ftype in (int, float, str, bool):
            return ftype(val)

        return val

    def model_dump(self) -> dict[str, Any]:
        """Dump model fields to dict."""
        d = {}
        for k in self.__class__._fields:
            v = getattr(self, k, None)
            if isinstance(v, BaseModel):
                d[k] = v.model_dump()
            elif isinstance(v, tuple):
                d[k] = list(v)
            elif isinstance(v, list):
                d[k] = [x.model_dump() if isinstance(x, BaseModel) else x for x in v]
            else:
                d[k] = v
        return d

    def dict(self) -> dict[str, Any]:
        """Pydantic v1 backward compatibility."""
        return self.model_dump()

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> Any:
        """Instantiate and validate model from dict."""
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data)}")
        return cls(**data)

    @classmethod
    def model_validate_json(cls, json_str: str) -> Any:
        """Parse JSON string and validate into model."""
        data = json.loads(json_str)
        return cls.model_validate(data)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        """Generate JSON schema matching Pydantic v2 format."""
        properties = {}
        required = []
        for fname, (ftype, finfo) in cls._fields.items():
            origin = get_origin(ftype)
            args = get_args(ftype)
            prop: dict[str, Any] = {}

            if origin is Literal:
                if len(args) == 1:
                    prop["const"] = args[0]
                    prop["type"] = "string" if isinstance(args[0], str) else "number"
                else:
                    prop["enum"] = list(args)
                    prop["type"] = "string"
            elif origin is tuple:
                prop["type"] = "array"
                prop["prefixItems"] = [
                    {"type": "number" if t in (int, float) else "string"} for t in args
                ]
                prop["items"] = False
                prop["minItems"] = len(args)
                prop["maxItems"] = len(args)
            elif origin is list:
                prop["type"] = "array"
                elem = args[0] if args else Any
                prop["items"] = {"type": "number" if elem in (int, float) else "string"}
            elif origin is dict:
                prop["type"] = "object"
            elif ftype is int:
                prop["type"] = "integer"
            elif ftype is float:
                prop["type"] = "number"
            elif ftype is str:
                prop["type"] = "string"
            elif ftype is bool:
                prop["type"] = "boolean"
            else:
                prop["type"] = "string"

            if finfo.default is not ...:
                prop["default"] = finfo.default
            elif finfo.default_factory is not None:
                prop["default"] = finfo.default_factory()
            else:
                required.append(fname)

            properties[fname] = prop

        return {
            "title": cls.__name__,
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def __repr__(self) -> str:
        pairs = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__class__._fields)
        return f"{self.__class__.__name__}({pairs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()
