from fastapi import APIRouter
from backend.schemas import (
    LoginRequest,
    LoginResponse,
    AuthorizationRequest,
    AuthorizationResponse
)

from backend.services.auth_service import (
    authenticate_user,
    authorize_request
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Authorization"]
)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):

    result = authenticate_user(
        request.username,
        request.password
    )

    if not result["authenticated"]:
        return LoginResponse(
            authenticated=False,
            message="Invalid username or password"
        )

    return LoginResponse(
        authenticated=True,
        agent_id=result["agent_id"],
        role=result["role"],
        token=result["token"],
        message="Login successful"
    )


@router.post(
    "/authorize",
    response_model=AuthorizationResponse
)
def authorize(request: AuthorizationRequest):

    result = authorize_request(
        request.agent_id,
        request.action,
        request.resource
    )

    return AuthorizationResponse(**result)