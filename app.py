from fastapi import FastAPI

app = FastAPI(title="UACC Portal")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "UACC portal is alive"}

