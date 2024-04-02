from typing import Any, Optional

from fastapi import HTTPException as FastHTTPException
from starlette import status

from .response import Code


class HTTPException(FastHTTPException):
    def __init__(
        self,
        code: int,
        status_code: int = status.HTTP_200_OK,
        detail: Any = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.headers = headers
        self.code = code

    def __call__(self, description: Optional[str] = None):
        cloned: HTTPException = HTTPException(
            status_code=self.status_code, code=self.code, detail=self.detail
        )
        if description is not None:
            cloned.detail = description
        return cloned


NotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Not Found.",
    code=Code.NOT_FOUND,
)

ServerException = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Server Error",
    code=Code.SERVER_ERROR,
)

ValidationException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Validation Error",
    code=Code.VALIDATION_ERROR,
)

PermissionException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permission Deny",
    code=Code.PERMISSION_ERROR,
)

UnauthorizedException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not Authenticated",
    code=Code.UNAUTHORIZED,
)
