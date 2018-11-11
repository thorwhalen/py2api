from __future__ import division

class ClientError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        super(ClientError, self).__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class BadRequest(ClientError):
    def __init__(self, message, payload=None):
        super(BadRequest, self).__init__(message, 400, payload)


class Forbidden(ClientError):
    def __init__(self, message, payload=None):
        super(Forbidden, self).__init__(message, 403, payload)

class ForbiddenAttribute(Forbidden):
    def __init__(self, attr, payload=None):
        super(ForbiddenAttribute, self).__init__("Forbidden attribute: " + attr, payload)

class ForbiddenProperty(Forbidden):
    def __init__(self, prop, payload=None):
        super(ForbiddenProperty, self).__init__("Forbidden property: " + prop, payload)

class MissingAttribute(BadRequest):
    def __init__(self, message="No attribute (method or property) was specified.", payload=None):
        super(MissingAttribute, self).__init__(message, payload)

# class EmptyResponse(ClientError):
#     status_code = 400
#
#     def __init__(self, message, payload=None):
#         super(EmptyResponse, self).__init__(message, self.status_code, payload)


# class ForbiddenMethod(Forbidden):
#     def __init__(self, method, payload=None):
#         super(self.__class__, self).__init__("Forbidden method: " + method, payload)
