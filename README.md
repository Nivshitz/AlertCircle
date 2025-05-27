
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
---

## 🐳 Docker Deployment (for EC2)

If you're deploying the backend infrastructure on an EC2 instance, you can use Docker Compose for setup.

### 🔧 Prerequisites on EC2

Make sure your EC2 has:
- Docker installed
- Docker Compose installed
- The `docker-compose.yaml` file cloned in the project root

### ▶️ 2. Start Services

```bash
cd alertcircle
docker compose up -d
```

This will start:
- Kafka & Zookeeper
- MongoDB
- Airflow (webserver + scheduler + PostgreSQL)
- `dev_env` container for development

---

✅ After the containers are running:
- Airflow UI will be accessible via `http://<your-ec2-public-ip>:8082`
- MongoDB and Kafka will be available to local services (ensure security group allows connections)

---

### 🔧 MongoDB Setup

Create the following collections:
- alerts_live:
  

### 🛠️ Requirements

- Python 3.10+
- Kafka + Zookeeper running
- MongoDB running
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
python kafka/enriched_alerts_to_mongo.py
```

#### 4. Launch the Streamlit Dashboard

```bash
streamlit run streamlit_app/streamlit_live_map_app.py
```

> ✅ Airflow is already running on EC2 and updating user locations every minute.

---

## 🧭 Hybrid Deployment Notes

Due to local hardware limitations, this system uses a hybrid deployment model:

- **EC2 instance** hosts:
  - MongoDB
  - Apache Airflow (scheduling DAG)
  - Kafka & Zookeeper
- **Local machine** runs:
  - Spark job for stream processing
  - Kafka producers and consumers
  - Streamlit live dashboard

---

## 📈 Future Enhancements

- [ ] Setting up the full project on EC2 with Docker
- [ ] Developing a mobile app for live alerts
- [ ] User authentication & notification preferences
- [ ] Historical data analytics with AWS Athena/ETL to a DWH -> BI Tool for dashboards

---

## 📬 Contact

Maintained by [Nivshitz](https://github.com/Nivshitz)  
For feedback, questions or collaboration – feel free to reach out!

---

🛡️ Built as a final project for the Cloud & Big Data Engineering course @ Naya College

---

