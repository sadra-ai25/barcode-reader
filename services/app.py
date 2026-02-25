import logging
import uvicorn
from fastapi import FastAPI
from endpoint import router, start_cameras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await start_cameras()

if __name__ == "__main__":
    logger.info("Starting FastAPI server on port 5004...")
    uvicorn.run(app, host="0.0.0.0", port=5004)