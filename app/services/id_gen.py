import uuid, time

def new_id(prefix: str = "q") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def new_session_id() -> str:
    return f"sess_{int(time.time())}_{uuid.uuid4().hex[:6]}"
