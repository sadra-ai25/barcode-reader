## state-test.py: this file saves barcodes even barcodes are repeated.....

import os
import json
import time
import logging
import multiprocessing
from dotenv import load_dotenv
import pyodbc
import numpy as np
import ffmpeg
import cv2
import pika
import csv
from datetime import datetime
import sqlite3  # Added for local SQLite database
from processor import process_frame

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()
SQL_DRIVER = os.getenv("SQL_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_HEARTBEAT = int(os.getenv("RABBITMQ_HEARTBEAT", "60")) 

CONFIG_PATH = "config/config.json"
CSV_LOG_PATH = "logs/barcode_log.csv"
CROPPED_IMAGES_PATH = "cropped_images"
camera_processes = {}  
consumer_processes = []
camera_running = False

os.makedirs(CROPPED_IMAGES_PATH, exist_ok=True)

def save_image_to_folder(cropped_image, barcode):
    cv2.putText(cropped_image, barcode, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    image_filename = os.path.join(CROPPED_IMAGES_PATH, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    cv2.imwrite(image_filename, cropped_image)
    logger.info(f"Saved cropped image with barcode {barcode} to {image_filename}")

def save_to_db(camera_id, barcode, frame_datetime, frame_data, memo):
    try:
        conn_str = f"DRIVER={SQL_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={USERNAME};PWD={PASSWORD}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "EXEC aiStpInsertFrameBarcode @cameraId=?, @barcode=?, @frameDateTime=?, @frame=?, @memo=?",
            (camera_id, barcode, frame_datetime, frame_data, memo)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Data for camera {camera_id} saved to database")
    except Exception as e:
        logger.warning("⚠️ Connection to SQL database failed, data will only be saved to local database.")
        logger.error(f"🚫 SQL database error: {e}")

def save_to_local_db(conn, camera_id, barcode, frame_datetime, frame_data, memo):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO frame_barcodes (camera_id, barcode, frame_datetime, frame_data, memo)
            VALUES (?, ?, ?, ?, ?)
        ''', (camera_id, barcode, frame_datetime, frame_data, memo))
        conn.commit()
        logger.info(f"Data for camera {camera_id} saved to local database")
    except sqlite3.Error as e:
        logger.error(f"Error saving to local database: {e}")

def connect_to_rabbitmq():
    while True:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    heartbeat=RABBITMQ_HEARTBEAT
                )
            )
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}, retrying in 5 seconds...")
            time.sleep(5)

def rabbitmq_worker():
    # Initialize SQLite database connection and table
    conn = sqlite3.connect('/app/database/local.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frame_barcodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            barcode TEXT,
            frame_datetime TEXT,
            frame_data BLOB,
            memo TEXT
        )
    ''')
    conn.commit()

    while True:
        try:
            connection = connect_to_rabbitmq()
            channel = connection.channel()
            channel.queue_declare(queue='frame_queue', durable=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    frame = cv2.imdecode(
                        np.frombuffer(bytes.fromhex(data['frame']), np.uint8), cv2.IMREAD_COLOR
                    )
                    source_id = data['source_id']
                    timestamp = data['timestamp']
                    frame_datetime = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    with open(CONFIG_PATH, 'r') as f:
                        config = json.load(f)
                    cam_cfg = config.get("cameras", {}).get(source_id, {})
                    bbox = cam_cfg.get("bbox", config.get("default_bbox"))
                    barcode, cropped = process_frame(frame, bbox)
                    if barcode:
                        logger.info(f"🟢 8-digit barcode detection: {barcode}")
                        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                        save_image_to_folder(cropped, barcode)
                        _, buf = cv2.imencode('.jpg', cropped)
                        frame_data = buf.tobytes()
                        save_to_db(source_id, barcode, frame_datetime, frame_data, "")
                        save_to_local_db(conn, source_id, barcode, frame_datetime, frame_data, "")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error in consumer callback: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue='frame_queue', on_message_callback=callback)
            logger.info("Starting RabbitMQ consumer...")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"❌ RabbitMQ consumer error: {e}, reconnecting in 5 seconds...")
            time.sleep(5)
        finally:
            if 'connection' in locals() and not connection.is_closed:
                connection.close()

def start_consumers():
    global consumer_processes
    NUM_CONSUMERS = 1  # با توجه به ۲ هسته، فعلاً ۱ مصرف‌کننده کافیه
    for _ in range(NUM_CONSUMERS):
        if not consumer_processes or not consumer_processes[-1].is_alive():
            p = multiprocessing.Process(target=rabbitmq_worker, daemon=True)
            p.start()
            consumer_processes.append(p)
            logger.info("✅ Started RabbitMQ consumer process")

def process_stream(source, source_id):
    logger.info(f"Starting stream for {source_id}, camera_running={camera_running}")
    connection = None
    channel = None
    try:
        while camera_running:
            try:
                if connection is None or connection.is_closed:
                    connection = connect_to_rabbitmq()
                    channel = connection.channel()
                    channel.queue_declare(queue='frame_queue', durable=True)
                probe = ffmpeg.probe(source)
                vs = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                width, height = int(vs['width']), int(vs['height'])
            except Exception as e:
                logger.error(f"Error probing {source_id}: {e}")
                time.sleep(5)
                continue

            try:
                process = (
                    ffmpeg
                    .input(source, rtsp_transport='tcp')
                    .output('pipe:', format='rawvideo', pix_fmt='bgr24', r=2) 
                    .run_async(pipe_stdout=True)
                )
                while camera_running and process.poll() is None:
                    in_bytes = process.stdout.read(width * height * 3)
                    if not in_bytes:
                        break
                    frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = buffer.tobytes()
                    frame_info = {
                        'frame': frame_data.hex(),
                        'source_id': source_id,
                        'timestamp': time.time()
                    }
                    try:
                        channel.basic_publish(
                            exchange='', routing_key='frame_queue', body=json.dumps(frame_info)
                        )
                    except Exception as e:
                        logger.error(f"Error publishing to RabbitMQ for {source_id}: {e}")
                        break
                    time.sleep(0.5)  # تنظیم برای ۲ فریم در ثانیه
                process.stdout.close()
                process.wait()
                if not camera_running:
                    break
                logger.info(f"🔴 Stream for {source_id} disconnected, retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in stream processing for {source_id}: {e}")
                time.sleep(5)
    finally:
        if channel and not channel.is_closed:
            channel.close()
        if connection and not connection.is_closed:
            connection.close()
        logger.info(f"ℹ️ Stream for {source_id} stopped, camera_running={camera_running}")