# MUS1-Project

A smart meter data ingestion service that bridges MQTT messaging with Dynatrace monitoring. This application subscribes to smart meter readings via MQTT and forwards the metrics to Dynatrace for visualization and analysis.

## Core Functionality

This application provides a data pipeline for smart meter telemetry:

1. **MQTT Subscription**: Connects to an MQTT broker and subscribes to smart meter data topics
2. **Data Transformation**: Parses incoming JSON messages and maps OBIS codes to meaningful metric names
3. **Dynatrace Ingestion**: Sends processed metrics to Dynatrace via the Metrics Ingest API v2

### Supported Metrics

| OBIS Code | Metric Name | Description |
|-----------|-------------|-------------|
| 1.8.0 | `smartmeter.energy.active.import.total` | Total active energy imported (kWh) |
| 2.8.0 | `smartmeter.energy.active.export.total` | Total active energy exported (kWh) |
| 3.8.1 | `smartmeter.energy.reactive.import.total` | Total reactive energy imported (kvarh) |
| 4.8.1 | `smartmeter.energy.reactive.export.total` | Total reactive energy exported (kvarh) |
| 1.7.0 | `smartmeter.power.active.import` | Current active power import (kW) |
| 2.7.0 | `smartmeter.power.active.export` | Current active power export (kW) |
| 3.7.0 | `smartmeter.power.reactive.import` | Current reactive power import (kvar) |
| 4.7.0 | `smartmeter.power.reactive.export` | Current reactive power export (kvar) |
| saldo | `smartmeter.power.active.saldo` | Net active power (kW) |
| 1.128.0 | `smartmeter.inkasso` | Billing/collection status |

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3.11** | Core application runtime |
| **paho-mqtt** | MQTT client library for broker communication |
| **requests** | HTTP client for Dynatrace API calls |
| **python-dotenv** | Environment variable management |
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Eclipse Mosquitto** | MQTT message broker |

---

## Architecture

```
┌─────────────────┐      MQTT       ┌───────────────────┐      HTTP/REST      ┌─────────────┐
│   Smart Meter   │ ──────────────► │  Mosquitto Broker │ ◄───────────────── │  Dynatrace  │
│   (Publisher)   │                 │    (Port 1883)    │                     │   Tenant    │
└─────────────────┘                 └─────────┬─────────┘                     └──────▲──────┘
                                              │                                      │
                                              │ Subscribe                            │
                                              ▼                                      │
                                    ┌─────────────────────┐                          │
                                    │  Metric Ingest App  │ ─────────────────────────┘
                                    │  (Python Container) │   Metrics Ingest API v2
                                    └─────────────────────┘
```

---

## Dynatrace Integration

### Metrics Ingest API

The application uses the **Dynatrace Metrics Ingest API v2** (`/api/v2/metrics/ingest`) to push smart meter metrics directly to your Dynatrace environment.

**Required API Token Permissions:**
- `metrics.ingest` - Ingest metrics

### Configuration

The following environment variables must be configured for Dynatrace:

| Variable | Description | Example |
|----------|-------------|---------|
| `TENANT_HOST` | Your Dynatrace tenant URL (without https://) | `abc12345.live.dynatrace.com` |
| `API_TOKEN` | API token with `metrics.ingest` scope | `dt0c01.XXX...` |

---

## MQTT Configuration

The application connects to an Eclipse Mosquitto MQTT broker for receiving smart meter data.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | MQTT broker hostname | `mosquitto` (container name) |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_USER` | MQTT username | - |
| `MQTT_PASSWORD` | MQTT password | - |
| `MQTT_CLIENT_ID` | Unique client identifier | - |
| `MQTT_TOPIC` | Topic to subscribe to | - |

---

## Dynatrace OneAgent

The `docker-compose.yml` includes a Dynatrace OneAgent container for full-stack monitoring.

### Configuration

| Variable | Description |
|----------|-------------|
| `DT_ONEAGENT_URL` | OneAgent installer script URL from your Dynatrace environment |

### OneAgent Container Settings

The OneAgent runs with:
- **Privileged mode**: Required for full system access
- **Host network mode**: For monitoring host-level metrics
- **Host PID namespace**: For process visibility
- **Root filesystem mount**: For complete host monitoring

---

## ⚠️ Raspberry Pi 3 Limitation

> **Important:** The Dynatrace OneAgent container **will NOT work on Raspberry Pi 3** devices.

### Reason

The Raspberry Pi 3 uses an **ARMv7 (32-bit)** architecture, which is **not supported** by Dynatrace OneAgent. OneAgent requires:
- **x86_64 (AMD64)** architecture, or
- **ARM64 (AArch64)** architecture (Raspberry Pi 4 and newer)

### Workaround for Raspberry Pi 3

When deploying on Raspberry Pi 3:

1. **Remove or comment out the OneAgent service** from `docker-compose.yml`
2. **Rely on the Metrics Ingest API** for sending data to Dynatrace (this works regardless of architecture)

The core functionality (MQTT → Dynatrace metrics ingestion) will work on Raspberry Pi 3, only the OneAgent-based host monitoring is unavailable.

```yaml
# Comment out or remove the oneagent service for Raspberry Pi 3
# oneagent:
#   image: dynatrace/oneagent:latest
#   ...
```

---

## Deployment

### Prerequisites

1. Docker and Docker Compose installed
2. A Dynatrace environment with API access
3. An API token with `metrics.ingest` permission

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MUS1-Project
   ```

2. **Create a `.env` file** in the project root:
   ```env
   # Dynatrace
   TENANT_HOST=your-tenant.live.dynatrace.com
   API_TOKEN=dt0c01.your-api-token
   DT_ONEAGENT_URL=https://your-tenant.live.dynatrace.com/api/v1/deployment/installer/agent/unix/default/latest?Api-Token=...

   # MQTT
   MQTT_PORT=1883
   MQTT_USER=your-mqtt-user
   MQTT_PASSWORD=your-mqtt-password
   MQTT_CLIENT_ID=smartmeter-ingest
   MQTT_TOPIC=smartmeter/data
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **For Raspberry Pi 3**, use a modified compose command:
   ```bash
   docker-compose up -d mosquitto smartmeter-metric-ingest
   ```

---

## Project Structure

```
MUS1-Project/
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Python application container
├── README.md                   # This documentation
├── .env                        # Environment variables (create this)
├── mosquitto/
│   ├── config/
│   │   ├── mosquitto.conf      # MQTT broker configuration
│   │   └── passwd              # MQTT user credentials
│   ├── data/                   # Persistent MQTT data
│   └── log/                    # MQTT broker logs
└── src/
    └── dynatrace-metrics-ingest.py  # Main application
```

---

## License

[Add your license here]