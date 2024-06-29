accumulate
----------

[![PyPI version](https://badge.fury.io/py/accumulate.svg)](https://badge.fury.io/py/accumulate)

Inheritance for iterable attributes.

`accumulate` eases inheritance of iterable class attributes by accumulating values along the MRO, for example:

```python
from accumulate import accumulate

class Base:
    fields = ["id"]
    metadata = {"read_only_field": ("id",)}

class User(Base):
    fields = accumulate(["name", "password"])
    metadata = accumulate(
        {
            "filter_fields": ("name",),
            "hidden_fields": ("password",),
        }
    )

assert User.fields == ["id", "name", "password"]
assert User.metadata == {
    "filter_fields": ("name",),
    "hidden_fields": ("password",),
    "read_only_field": ("id",),
}
```

# Installation

Install using `pip install -U accumulate`.
