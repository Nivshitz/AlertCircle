
# 🚨 AlertCircle - Real-Time Bylaw Violation Alert System

AlertCircle is a real-time alerting system that notifies nearby users when bylaw officers are spotted. It simulates user activity, processes geo-tagged alerts, enriches them with user proximity data, and visualizes everything in a live map and notification feed.

![Architecture](./docs/AlertCircle_FinalVersion.jpg)

---

## 🧠 Project Highlights

- ⚡ **Real-time stream processing** using Apache Kafka and Spark  
- 🌍 **Location-based enrichment** with MongoDB geospatial queries  
- ⏱️ **Airflow DAG** running every minute to simulate active users  
- 💾 **Amazon S3 integration** for archiving enriched alerts  
- 🗺️ **Streamlit dashboard** for live map and alert feed  
- ☁️ **Hybrid architecture** with EC2 and local services  

---

## 📂 Project Structure

```
AlertCircle/
│
├── airflow/                  # Airflow DAGs (runs on EC2)
    └── update_user_locations.py
│   └── dags/
│       └── update_user_locations_dag.py
│
├── kafka/                    # Kafka producers and consumers
│   └── user_report_simulator.py
│   └── enriched_alerts_to_mongo.py
│
├── spark/                    # Spark structured streaming job
│   └── process_alerts_stream.py
│
├── streamlit_app/            # Streamlit real-time dashboard
│   └── streamlit_live_map_app.py
│
├── requirements.txt          
├── README.md                 
└── .gitignore
```

---

## ⚙️ Component Overview

### 🧍 User Alert Simulation (Producer)

- Simulated users send alerts every **10 seconds**
- Published to Kafka topic: `raw_alerts`

### 🔥 Spark Enrichment (Stream Processor)

- Consumes `raw_alerts`
- Enriches alerts with nearby users from MongoDB within 500 meters from the alert point
- Publishes to:
  - Kafka topic: `enriched_alerts`
  - S3 bucket: `enriched-alerts`

### 🌐 Airflow DAG (on EC2)

- Runs every **1 minute**
- Simulates active users and locations
- Writes to MongoDB: `latest_user_location` (TTL = 5 minutes)

### 📥 Enriched Alert Consumer

- Consumes from `enriched_alerts`
- Writes to MongoDB: `alerts_live` (TTL = 10 minutes)

### 🗺️ Streamlit Dashboard

- Connects to `alerts_live` MongoDB collection
- Shows:
  - Real-time **alert map** for visualize
  - Live **notification feed** for users notifications simulation

![Dashboard](./docs/streamlit_dashboard.png)

---

## 🚀 Quickstart

### 🛠️ Requirements

- Python 3.10+
- Kafka + Zookeeper running locally
- MongoDB running (locally or on EC2)
- AWS credentials if writing to S3

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### ▶️ Run the System

#### 1. Start the Alert Producer

```bash
python kafka/user_report_simulator.py
```

#### 2. Run Spark Stream Processor

```bash
python spark/process_alerts_stream.py
```

#### 3. Start the Enriched Alert Consumer

```bash
python kafka/enriched_alerts_consumer.py
```

#### 4. Launch the Streamlit Dashboard

```bash
streamlit run streamlit_app/streamlit_live_map_app.py
```

> ✅ Airflow is already running on EC2 and updating user locations every minute.

---

## 🧭 Hybrid Deployment Notes

Due to local hardware limitations, this system uses a hybrid deployment model:

- **EC2 instance** hosts (via Docker Compose):
  - MongoDB
  - Apache Airflow (scheduling DAG)
  - Kafka & Zookeeper
- **Local machine** runs:
  - Spark job for stream processing
  - Kafka producers and consumers
  - Streamlit live dashboard

Due to performance limits on local hardware, this project runs with a hybrid model:

- **EC2** runs MongoDB, Kafka, and Airflow
- **Local machine** runs Spark, producers/consumers, and Streamlit

---

## 📈 Future Enhancements

- [ ] Docker Compose / Kubernetes setup
- [ ] Mobile app or PWA for live alerts
- [ ] User authentication & notification preferences
- [ ] Historical data analytics with AWS Athena

---

## 📬 Contact

Maintained by [Nivshitz](https://github.com/Nivshitz)  
For feedback, questions or collaboration – feel free to reach out!

---

🛡️ Built with ❤️ as a final project for the Cloud & Big Data Engineering course @ Naya College

---

## 🛠️ EC2 Deployment & Developer Notes

### 🔁 Docker Compose Setup (on EC2)
Kafka, Zookeeper, MongoDB, and Airflow are deployed via Docker Compose on the EC2 instance.

Use the cleaned Docker Compose:
```bash
docker compose up -d
```

### 🌐 Airflow Access
Airflow Web UI:  
http://<your-ec2-public-ip>:8082/

### 🔐 SSH & File Transfer Commands

- **SSH into EC2**
```bash
ssh -i alertcircle-key.pem ec2-user@<EC2-IP>
```

- **Copy file from EC2 to local**
```bash
scp -i alertcircle-key.pem ec2-user@<EC2-IP>:~/alertcircle/docker-compose.yaml .
```

- **Copy file from local to EC2**
```bash
scp -i alertcircle-key.pem <local-file> ec2-user@<EC2-IP>:<remote-path>
```

- **Enter dev_env container**
```bash
docker exec -it dev_env bash
```

### 🔁 On Every EC2 Reboot
Update Kafka’s public IP:
```bash
./update-kafka-ip.sh
```

---

