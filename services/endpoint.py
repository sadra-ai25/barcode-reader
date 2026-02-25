import os
import json
import logging
from fastapi import APIRouter
import state
from multiprocessing import Process

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    logger.info("Health check request")
    return {"status": "healthy", "cameras_running": state.camera_running}

@router.post("/start_cameras")
async def start_cameras():
    if state.camera_running:
        logger.warning("Cameras are already running")
        return {"message": "Cameras are already running"}
    logger.info("Starting all cameras")
    state.camera_running = True
    with open(state.CONFIG_PATH, 'r') as f:
        config = json.load(f)
    for cam_id, cam_info in config["cameras"].items():
        if cam_id not in state.camera_processes or not state.camera_processes[cam_id].is_alive():
            p = Process(
                target=state.process_stream,
                args=(cam_info["rtsp"], cam_id),
                daemon=True
            )
            state.camera_processes[cam_id] = p
            p.start()
            logger.info(f"Process for {cam_id} started")
    # شروع مصرف‌کننده‌ها
    state.start_consumers()
    return {"message": "All cameras started"}

@router.post("/stop_cameras")
async def stop_cameras():
    if not state.camera_running:
        logger.warning("Cameras are already stopped")
        return {"message": "Cameras are already stopped"}
    logger.info("Stopping all cameras")
    state.camera_running = False
    for cam_id, p in list(state.camera_processes.items()):
        if p.is_alive():
            p.terminate()
            p.join()
            logger.info(f"Process for {cam_id} stopped")
    state.camera_processes.clear()
    # متوقف کردن مصرف‌کننده‌ها
    for p in state.consumer_processes:
        if p.is_alive():
            p.terminate()
            p.join()
    state.consumer_processes.clear()
    return {"message": "All cameras stopped"}