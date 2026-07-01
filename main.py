from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "22f2000751@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-2q3lqm.example.com"

# Add your assigned origin plus the exam page origin
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

# Store request timestamps per client
clients = {}

LIMIT = 12
WINDOW = 10


@app.middleware("http")
async def middleware(request: Request, call_next):

    # ------------------------
    # Request Context
    # ------------------------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ------------------------
    # Rate Limit
    # ------------------------
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = clients.get(client, [])

    history = [t for t in history if now - t < WINDOW]

    if len(history) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    history.append(now)

    clients[client] = history

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
