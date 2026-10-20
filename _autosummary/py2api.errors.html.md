# py2api.errors

Exception types raised by py2api wrappers (client/attribute-access errors).

### Exceptions

| [`BadRequest`](#py2api.errors.BadRequest)(message[, payload])               |    |
|-----------------------------------------------------------------------------------------------|----|
| [`ClientError`](#py2api.errors.ClientError)(message[, status_code, payload]) |    |
| [`Forbidden`](#py2api.errors.Forbidden)(message[, payload])                |    |
| [`ForbiddenAttribute`](#py2api.errors.ForbiddenAttribute)(attr[, payload])          |    |
| [`ForbiddenProperty`](#py2api.errors.ForbiddenProperty)(property[, payload])       |    |
| [`MissingAttribute`](#py2api.errors.MissingAttribute)([message, payload])         |    |

### *exception* py2api.errors.BadRequest(message, payload=None)

Bases: [`ClientError`](#py2api.errors.ClientError)

### *exception* py2api.errors.ClientError(message, status_code=None, payload=None)

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

### *exception* py2api.errors.Forbidden(message, payload=None)

Bases: [`ClientError`](#py2api.errors.ClientError)

### *exception* py2api.errors.ForbiddenAttribute(attr, payload=None)

Bases: [`Forbidden`](#py2api.errors.Forbidden)

### *exception* py2api.errors.ForbiddenProperty(property, payload=None)

Bases: [`Forbidden`](#py2api.errors.Forbidden)

### *exception* py2api.errors.MissingAttribute(message='No attribute (method or property) was specified.', payload=None)

Bases: [`BadRequest`](#py2api.errors.BadRequest)
