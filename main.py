from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "22f2000751@ds.study.iitm.ac.in"

clients = {}
LIMIT = 12
WINDOW = 10

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-2q3lqm.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# -------------------------
# Request Context Middleware
# -------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if request_id is None:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -------------------------
# Rate Limit Middleware
# -------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):

    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = clients.get(client, [])

    history = [t for t in history if now - t < WINDOW]

    if len(history) >= LIMIT:

        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

        response.headers["X-Request-ID"] = request.state.request_id

        return response

    history.append(now)

    clients[client] = history

    return await call_next(request)


@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }