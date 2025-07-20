from fastapi import FastAPI

app = FastAPI(title="Interview Coach API (Skeleton)")

@app.get("/health")
def health():
    return {"status": "ok", "message": "API skeleton running"}
