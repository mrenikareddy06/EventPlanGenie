# shared/server.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from shared.tool_registry import get_tool
import uvicorn

app = FastAPI()

# Allow cross-origin (if using with Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.post("/tool/{name}")
async def call_tool(name: str, request: Request):
    func = get_tool(name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
    try:
        params = await request.json()
        result = func(**params)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run/{name}")
async def run_tool(name: str, request: Request):
    return await call_tool(name, request)

# For local testing: `python shared/server.py`
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
