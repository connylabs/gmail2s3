class Gmail2S3Exception(Exception):
    status_code = 500
    errorcode = "internal-error"

    def __init__(self, message, payload=None):
        super().__init__()
        self.payload = dict(payload or ())
        self.message = message

    def to_dict(self):
        return {
            "code": self.errorcode,
            "message": self.message,
            "details": self.payload,
        }

    def __str__(self):
        return self.message


class InvalidUsage(Gmail2S3Exception):
    status_code = 400
    errorcode = "invalid-usage"


class InvalidParams(Gmail2S3Exception):
    status_code = 422
    errorcode = "invalid-parameters"


class ResourceNotFound(Gmail2S3Exception):
    status_code = 404
    errorcode = "resource-not-found"


class Forbidden(Gmail2S3Exception):
    status_code = 403
    errorcode = "forbidden"


class UnauthorizedAccess(Gmail2S3Exception):
    status_code = 401
    errorcode = "unauthorized-access"


class Unsupported(Gmail2S3Exception):
    status_code = 501
    errorcode = "unsupported"


class Unexpected(Gmail2S3Exception):
    status_code = 500
    errorcode = "unexpected-error"
