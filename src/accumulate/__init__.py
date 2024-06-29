"""Contains helpers to accumulate iterable class attributes."""

from collections.abc import Iterable, Mapping
from functools import partial
from itertools import chain
from typing import Literal

type Order = Literal["parent-first", "parent-last"]


class accumulate[T]:
    """Inherit iterable class attributes, accumulating values along the way.

    Implements a descriptor over iterable types that chains the current and parent class
    values together. Values are only retrieved from immediate parents, but `accumulate`
    can be used repeatedly at multiple inheritance levels to provide deep retrieval.

    Supports Mapping types (including defaultdict) Top level key collisions prefer the
    child-most value. If the mapping is ordered, the result will be ordered, but note
    that collisions will maintain the original position.

    The `order` parameter determines how the final output iterable will be created.
    - `parent-first`: `["base", "sub"]`; `{"base": 1, "sub": 2, "shared": "sub"}`
    - `parent-last`: `["sub", "base"]`; `{"base": 1, "sub": 2, "shared": "base"}`
    Note that for mappings, `parent-last` will prefer the parent key over the child key.

    >>> class Base:
    ...     fields = ["id"]
    ...     metadata = {"read_only_field": ("id",)}
    ...
    >>> class User(Base):
    ...     fields = accumulate(["name", "password"])
    ...     metadata = accumulate(
    ...         {
    ...             "filter_fields": ("name",),
    ...             "hidden_fields": ("password",),
    ...         }
    ...     )
    ...
    >>> User.fields
    ['id', 'name', 'password']
    >>> User.metadata
    {'read_only_field': ('id',), 'filter_fields': ('name',), 'hidden_fields': ('password',)}

    NOTE: The accumulation is "shallow": the root iterable from each class is merged,
    but any nested iterables are replaced.
    """

    def __init__(self, values: T, *, order: Order = "parent-first"):
        self.constructor = type(values)
        # Support constructors with factories, such as defaultdict
        if hasattr(values, "default_factory"):
            self.constructor = partial(self.constructor, values.default_factory)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        self.is_mapping = isinstance(values, Mapping)
        self.name: str | None = None
        self.order: Order = order  # Pyright infers `: str` without an explicit hint
        self.values = values
        # NOTE: We're checking last to avoid type narrowing, which would confuse pyright on subsequent access.
        if not isinstance(values, Iterable):
            raise TypeError(f"Expected an iterable type, got {type(values)}")

    def __get__(self, obj: object | None, type_: type | None = None) -> T:
        if type_ is None:
            type_ = type(obj)
        name = self.get_name(type_)
        # Prefer object local values from __set__
        if obj is not None and name in obj.__dict__:
            return obj.__dict__[name]
        collection = tuple(
            iterable
            for iterable in chain(
                (getattr(base, name, None) for base in type_.__bases__),
                [self.values],
            )
            if iterable
        )
        match self.order:
            case "parent-first":
                pass
            case "parent-last":
                collection = reversed(collection)
        if self.is_mapping:
            collection = (d.items() for d in tuple(collection))
        return self.constructor(chain.from_iterable(collection))  # pyright: ignore[reportCallIssue]

    def __set__(self, obj: object, values: T) -> None:
        name = self.get_name(type(obj))
        obj.__dict__[name] = values

    def __set_name__(self, type_: type, name: str):
        """Set the field name during class initialization.

        This will not be called if the attribute is set with `setattr`. `_infer_name` will be used instead if needed.
        """
        self.name = name

    def get_name(self, type_: type) -> str:
        """Infer a field name in case the descriptor is added with setattr, which won't call __set_name__."""
        if self.name is None:
            all_attributes = chain.from_iterable(dir(cls) for cls in type_.__mro__)
            attributes = {attr for attr in all_attributes if not attr.startswith("__")}
            for attr in attributes:
                if type_.__dict__[attr] is self:
                    self.name = attr
                    break
            else:
                raise ValueError(f"Unable to determine attribute name on {type_}.")
        return self.name
