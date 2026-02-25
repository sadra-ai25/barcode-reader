# execute this code for runing automatically cameras withour requesting to the endpoint (already services)
- sudo docker load -i barcode.tar
- sudo docker load -i rabbit.tar
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