"""
AutoNestedBaseModel extends SQLModel to automatically handle nested submodels.
This is especially useful when dealing with complex JSON structures or when you want
to map nested attributes directly to your database entities.

Features:
- Automatic detection of nested SQLModel fields via annotated types.
- Optional auto-creation of nested objects in the database, if no existing record is found.
- Flattening capabilities for both string representation (__str__) and JSON dumping (model_dump_flat_json).
- Basic masking of fields that include certain sensitive keywords (password, secret, token).

Usage:
1. Instantiate with a session (optional) and data that may contain nested attributes separated by dots.
2. Use auto_create_nested=True to automatically create new rows if none are found for nested data.
3. Use __str__, __repr__, and model_dump_flat_json to inspect object state in different formats.

Example:
    class Address(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        street: str
        number: str

    class User(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        address: Optional[Address] = Relationship()

    # Suppose we receive flattened data for a user and address
    user_data = {"name": "Alice", "address.street": "Main St", "address.number": "123"} 

    # Creating a new user with nested address automatically
    new_user = AutoNestedBaseModel(session=session, auto_create_nested=True, **user_data)

Requirements:
- python >= 3.8
- pydantic
- sqlmodel
"""

import logging
from pydantic import BaseModel
from sqlmodel import SQLModel, Session

class AutoNestedBaseModel(SQLModel):
    """
    The AutoNestedBaseModel extends SQLModel to provide nested model initialization.
    It looks for fields that are themselves SQLModels and automatically resolves them
    from incoming data (both flattened and nested) and optionally from the database.
    """

    def __init__(self, session: Session=None, auto_create_nested: bool=False, **data):
        """
        Initialize an AutoNestedBaseModel instance, optionally using a database Session.
        Automatically detects nested SQLModel fields in the `data` and:
        1. Separates flattened keys of the form <field>.<nested_field> into a dict.
        2. Looks up existing rows in the database if session is provided and the model is table-backed.
        3. Optionally creates missing rows if `auto_create_nested=True`.

        Args:
            session (Session, optional): SQLAlchemy session for database interactions.
            auto_create_nested (bool, optional): Whether to create nested records if none exist.
            **data: Arbitrary keyword arguments that map to model fields (including nested fields).
        """
        logging.debug('Initializing AutoNestedBaseModel')
        for f, t in self.__annotations__.items():
            if isinstance(t, type) and issubclass(t, SQLModel):
                nd = {k.split('.', 1)[1]: v for k, v in list(data.items()) if k.startswith(f'{f}.')}
                if f in data and not isinstance(data[f], dict):
                    pf = list(t.__annotations__.keys())[0]
                    nd[pf] = data.pop(f)
                if nd:
                    for k in nd:
                        data.pop(f'{f}.{k}', None)
                    if session and getattr(t, '__table__', None):
                        cols = t.__table__.columns.keys()
                        nd = {k: v for k, v in nd.items() if k in cols}
                        q = session.query(t).filter_by(**nd).first()
                        if not q and auto_create_nested:
                            q = t(**nd)
                            session.add(q)
                            session.commit()
                        data[f] = q
                    else:
                        data[f] = t(**nd)
                elif f in data and isinstance(data[f], dict):
                    data[f] = t(**data[f])
        super().__init__(**data)
        logging.debug('AutoNestedBaseModel initialized')

    def __str__(self):
        """
        Return a flattened string representation of the model's attributes.
        Nested models are recursively processed, and fields containing 'password',
        'secret', or 'token' are masked.

        Returns:
            str: Flattened string with dot-separated keys.
        """
        def flatten(m, p=''):
            out = []
            for fn, v in m.__dict__.items():
                if isinstance(v, BaseModel):
                    out += flatten(v, f'{p}{fn}.')
                else:
                    mask = "***" if any(x in fn.lower() for x in ['password','secret','token']) else v
                    out.append(f'{p}{fn}={mask}')
            return out
        return ' '.join(flatten(self))

    def __repr__(self):
        """
        Return a programmer-friendly representation of the model, showing all fields.
        If a field is another BaseModel, calls its __repr__ recursively.

        Returns:
            str: String that includes all annotated fields and their representations.
        """
        def r(v):
            return v.__repr__() if isinstance(v, BaseModel) else repr(v)
        return f'{self.__class__.__name__}(' + ', '.join(f'{f}={r(getattr(self, f))}' for f in self.__annotations__) + ')'

    def model_dump_flat_json(self):
        """
        Return a flattened JSON representation of the model's attributes,
        masking any field with 'password', 'secret', or 'token' in its name.
        Nested models are processed recursively.

        Returns:
            str: JSON string that includes flattened dot-separated keys.
        """
        from json import dumps

        def flatten_json(m, p=''):
            d = {}
            for fn, v in m.__dict__.items():
                if isinstance(v, BaseModel):
                    d |= flatten_json(v, f'{p}{fn}.')
                else:
                    mask = "***" if any(x in fn.lower() for x in ['password','secret','token']) else v
                    d[f'{p}{fn}'] = mask
            return d
        return dumps(flatten_json(self), indent=2, ensure_ascii=False)