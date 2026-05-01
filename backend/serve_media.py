from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create media directory if it doesn't exist
os.makedirs("./media", exist_ok=True)

# Mount static files
app.mount("/media", StaticFiles(directory="./media"), name="media")

@app.get("/")
def root():
    return {"message": "Media server ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
