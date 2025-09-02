# dummy_service.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# Simple state variable to simulate recovery
service_recovered = False

@app.post("/recover")
def recover():
    global service_recovered
    service_recovered = True
    return JSONResponse(content={"status": "recovered"}, status_code=200)

@app.get("/health")
def health():
    if service_recovered:
        return JSONResponse(content={"status": "healthy"}, status_code=200)
    else:
        return JSONResponse(content={"status": "starting"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
