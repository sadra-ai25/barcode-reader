# Barcode Reader System

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-green) ![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.x-orange) ![Docker](https://img.shields.io/badge/Docker-Compose-blue) ![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-orange)

Real-time barcode reading system for industrial use. Reads 8-digit barcodes from IP camera streams using PaddleOCR, deduplicates results, and logs to SQL Server — designed for steel production tracking.

## Features

- **RTSP multi-camera** — monitor multiple camera streams simultaneously
- **PaddleOCR-based reading** — robust text recognition optimized for industrial barcodes
- **8-digit barcode extraction** — regex-based filtering ensures only valid barcodes are captured
- **Duplicate prevention** — configurable deduplication window prevents logging the same barcode twice
- **Configurable ROI** — define exact crop region (bounding box) per camera via JSON config
- **SQL Server logging** — each scan event is persisted with timestamp and camera ID
- **REST API** — start/stop cameras and retrieve scan history

## Tech Stack

| Component | Technology |
|---|---|
| OCR Engine | PaddleOCR (EN PP-OCRv4) |
| API Server | FastAPI + Uvicorn |
| Message Queue | RabbitMQ |
| Database | Microsoft SQL Server (pyodbc) |
| Containerization | Docker Compose |
| Camera Capture | OpenCV |

## Architecture

```
IP Camera (RTSP)
      │
      ▼
 Camera Producer (Process)
   - Captures frames
   - Sends to RabbitMQ
      │
      ▼
  RabbitMQ Queue
      │
      ▼
 Frame Consumer (Process)
   - Crops frame to ROI bbox
   - Runs PaddleOCR
   - Extracts 8-digit barcode via regex
   - Deduplication check
      │
      ▼
 SQL Server  ←→  FastAPI REST API
```

## Prerequisites

- Docker & Docker Compose
- PaddleOCR model weights (placed in `weights/` directory)
- Microsoft SQL Server (reachable from container)
- ODBC Driver 17 for SQL Server
- Camera configuration JSON at `config/cameras.json`

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/sadra-ai25/barcode-reader.git
cd barcode-reader

# 2. Configure environment
cp .env.example .env   # then edit with your values

# 3. Set up camera config
mkdir -p config
cat > config/cameras.json << 'EOF'
{
  "cameras": {
    "cam1": {
      "rtsp": "rtsp://username:password@192.168.1.100:554/",
      "bbox": {"x_min": 100, "y_min": 50, "x_max": 600, "y_max": 200}
    }
  }
}
EOF

# 4. Start services
docker compose up -d --build
```

## Configuration

Edit `.env` before starting:

| Key | Description | Example |
|---|---|---|
| `DB_SERVER` | SQL Server hostname | `192.168.1.100\sqlserver` |
| `DB_NAME` | Database name | `BarcodeDB` |
| `USERNAME` | SQL login | `sa` |
| `PASSWORD` | SQL password | `your_password_here` |

Camera ROI is configured in `config/cameras.json`:

```json
{
  "cameras": {
    "cam1": {
      "rtsp": "rtsp://username:password@ip:554/stream",
      "bbox": { "x_min": 100, "y_min": 50, "x_max": 600, "y_max": 200 }
    }
  }
}
```

## Usage

```bash
# Health check
curl http://localhost:5003/

# Start all configured cameras
curl -X POST http://localhost:5003/start_cameras

# Stop all cameras
curl -X POST http://localhost:5003/stop_cameras
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns camera running status |
| `POST` | `/start_cameras` | Start all cameras from config file |
| `POST` | `/stop_cameras` | Stop all running camera processes |

## Docker Quick Start (offline / pre-loaded images)

If the Docker images are pre-built and saved as `.tar` files:

```bash
sudo docker load -i barcode.tar
sudo docker load -i rabbit.tar
docker compose up -d
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT
- sudo docker copmpose up -d

# if you need send a request, rename "services-with-request" to "services" and the alreeady services should rename to "services-old"
# then send a request in terminal for any requirements
- start camera:
            curl -X POST "http://localhost:5004/start_cameras"

- stop camera:
            curl -X POST "http://localhost:5004/stop_cameras"

- upload a video file:
            curl -X POST "http://localhost:5004/upload_video" \
                  -F "video=@/path/to/your/video.mp4"

------------------------------------------------------------------------------------

# 'restart-service.sh' restarts service every 30 minutes (30 minutes is changable)
for enabling you should run:
      - sudo chmod +x restart-service.sh
      - sudo ./restart-service.sh

for disabling you should run:
      - sudo systemctl disable --now restart-barcode-service.timer
      - sudo rm /etc/systemd/system/restart-barcode-service.timer
      - sudo rm /etc/systemd/system/restart-barcode-service.service
      - sudo systemctl daemon-reload
      - sudo systemctl reset-failed

------------------------------------------------------------------------------------
# if you find the .env file please uncomment the items:
      - Abhar databse:
            # SQL_DRIVER={ODBC Driver 17 for SQL Server}
            # DB_SERVER=192.168.1.11\sqlsadra
            # DB_NAME=DBSadraafzar001
            # USERNAME=AI
            # PASSWORD=S@dra123
            
      - local databse:
            # SQL_DRIVER={ODBC Driver 17 for SQL Server}
            # DB_SERVER=192.168.1.11\sqlsadra
            # DB_NAME=DBSadraafzar001
            # USERNAME=AI
            # PASSWORD=S@dra123

# if you dont find .env file please make it via the below command in the directory:
      - sudo touch .env
      - copy and paste the below items for Abhar database:

            SQL_DRIVER={ODBC Driver 17 for SQL Server}
            DB_SERVER=192.168.50.113\sql2019
            DB_NAME=DBAILog
            USERNAME=sa
            PASSWORD=S@draAfzar

      - copy and paste it for sql local database:

            SQL_DRIVER={ODBC Driver 17 for SQL Server}
            DB_SERVER=192.168.50.113\sql2019
            DB_NAME=DBAILog
            USERNAME=sa
            PASSWORD=S@draAfzar