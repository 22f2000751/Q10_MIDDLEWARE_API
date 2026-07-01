from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "22f2000751@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-2q3lqm.example.com"

# Allow your assigned origin and the exam origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        "https://exam.sanand.workers.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit settings
LIMIT = 12
WINDOW = 10  # seconds

# Store request timestamps per client
clients = {}


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # -----------------------------
    # Request Context
    # -----------------------------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -----------------------------
    # Rate Limiting
    # -----------------------------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = clients.get(client_id, [])

    # Keep only requests in last 10 seconds
    history = [t for t in history if now - t < WINDOW]

    if len(history) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

        # VERY IMPORTANT
        response.headers["X-Request-ID"] = request_id

        return response

    history.append(now)
    clients[client_id] = history

    response = await call_next(request)

    # VERY IMPORTANT
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }