from typing import Dict

from fastapi import FastAPI


app = FastAPI()


@app.post("/respond")
async def respond(body: Dict):
    print(f"Received from Dream:\n{body}")
