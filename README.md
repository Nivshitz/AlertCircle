
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
│   └── dags/
│       └── update_user_locations_dag.py
│
├── kafka/                    # Kafka producers and consumers
│   └── user_report_simulator.py
│   └── enriched_alerts_consumer.py
│
├── spark/                    # Spark structured streaming job
│   └── process_alerts_stream.py
│
├── streamlit_app/            # Streamlit real-time dashboard
│   └── streamlit_live_map_app.py
│
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── .gitignore
```

---

## ⚙️ Component Overview

### 🧍 User Alert Simulation (Producer)

- Simulated user sends alerts every **10 seconds**
- Published to Kafka topic: `raw_alerts`

### 🔥 Spark Enrichment (Stream Processor)

- Consumes `raw_alerts`
- Enriches alerts with user proximity data from MongoDB
- Publishes to:
  - Kafka topic: `enriched_alerts`
  - S3 bucket: `enriched-alerts-bucket`

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
  - Real-time **alert map**
  - Live **notification feed**

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

Due to performance limits on local hardware, this project runs with a hybrid model:

- **EC2** runs MongoDB and Airflow
- **Local machine** runs Kafka, Spark, producers/consumers, and Streamlit

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
