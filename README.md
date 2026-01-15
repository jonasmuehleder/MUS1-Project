# Smartmeter Visualiserung und Notifiziereung mit Dynatrace

## Problemstatement
Da wir zuhause seit einigen Jahren eine PV anlage haben und auch seit über einem Jahr ein Elektorauto mit einer einfachen Wallbox, welche nicht intelligent ist, ist es derzeit nur schwierig herauszufinden ob das Laden es Elektroautos gerade am effizientesten ist oder nicht. Weiteres haben wir keine Information darüber ob es gerade sinvoll ist z.B. eine Waschmaschine oder einen Elektroherd einzuschalten. Dies wäre zwar theoretisch möglich, dabei müsste man aber andauernd in der App des Wechselrichters schauen. In unserem fall ein Wechselrichter der Firma `ZCS Azzurro`.

## Lösungsansatz
Die Daten der PV-Anlage werden mittels RS485-Konverter ausgelesen und an den Rasperry Pi übertragen. 
Parallel dazu werden die Daten des `Netz-Smart-Meters (Netz OÖ)` mit einem `AMIS-Lesekopf (Infrarotsensor)` erfasst und ebenfalls über `MQTT` an den Raspberry Pi übertragen. Der Raspberry Pi verarbeitet die eingehenden Daten, formatiert sie und übermittelt sie als Custom Metrics in eine Dynatrace-Umgebung. Dort werden sie über `Dashboards` visualisiert und mithilfe der `Dynatrace Query Language (DQL)` analysiert. Anschließend wird ein Altering mit der `Dynatrace Anomaly Detection` umgesetz. Weiteres wird das umgesetze Projekt welches auf einem Rasperry Pi in einem Docker Container läuft vom `Dynatrace Oneagent` gemonitort.

## Ergebnisse
### Darstellung von Einspeisung/Netzbezug über einen gewissen Zeitraum
![Dynatrace Dashboards](docs/dashboard.png)

### Monitoring der Dockercontainer mittels Dynatrace One Agent
**Note:** Mittels Rasperry PI 3 nicht möglich, da die Architektur dieses Pi´s nicht vom Oneagent unterstützt wird. Monitoring wurde also nur Beispielhaft mit Docker Desktop umgesetzt um die mögliche verwendung darzustellen.

#### Overview
![Overview](docs/overview.png)
#### Importierte Metriken
| OBIS-Code | Metrikname | Beschreibung |
|-----------|------------|--------------|
| 1.8.0 | `smartmeter.energy.active.import.total` | Gesamte importierte Wirkenergie (kWh) |
| 2.8.0 | `smartmeter.energy.active.export.total` | Gesamte exportierte Wirkenergie (kWh) |
| 3.8.1 | `smartmeter.energy.reactive.import.total` | Gesamte importierte Blindenergie (kvarh) |
| 4.8.1 | `smartmeter.energy.reactive.export.total` | Gesamte exportierte Blindenergie (kvarh) |
| 1.7.0 | `smartmeter.power.active.import` | Aktuelle Wirkleistungsaufnahme (kW) |
| 2.7.0 | `smartmeter.power.active.export` | Aktuelle Wirkleistungsabgabe (kW) |
| 3.7.0 | `smartmeter.power.reactive.import` | Aktuelle Blindleistungsaufnahme (kvar) |
| 4.7.0 | `smartmeter.power.reactive.export` | Aktuelle Blindleistungsabgabe (kvar) |
| saldo | `smartmeter.power.active.saldo` | Netto-Wirkleistung (kW) |
| 1.128.0 | `smartmeter.inkasso` | Abrechnungs-/Inkassostatus |

![Imported Metrics](/docs/metrics.png)

#### Processes
![Processes](/docs/processes.png)
#### Hosts
![Hosts](/docs/hosts.png)
#### Alamierung falls Host nicht mehr erreichbar ist oder Probleme hat
![Problem](/docs/problem.png)

**TODO** Notifizierung!

## Projektstruktur
```
MUS1-Project/
├── docker-compose.yml          # Container-Orchestrierung
├── Dockerfile                  # Python-Anwendungscontainer
├── README.md                   # Dokumentaion
├── .env                        # Umgebungsvariablen
├── mosquitto/
│   ├── config/
│   │   ├── mosquitto.conf      # MQTT-Broker-Konfiguration
│   │   └── passwd              # MQTT-Benutzeranmeldedaten
│   ├── data/                   # Persistente MQTT-Daten
│   └── log/                    # MQTT-Broker-Protokolle
└── docs/ # Sources for documentation
└── src/
    └── dynatrace-metrics-ingest.py  # Hauptanwendung
```

## Implementierung

### Verwendete Technologien

| Technologie | Zweck |
|-------------|-------|
| **Python** | Implementierung des Python Clients |
| **MQTT** | Kommunikation zwischen Sensor und Python Client |
| **Docker** | Containerisierung |
| **Docker Compose** | Multi-Container-Orchestrierung |
| **Rasperry PI 3** | Ausführung der Docker Container |
| **AMIS Smartreader** | Auslesen der Smartmeterdaten |
| **Dynatrace Platform** | Auswertungen, Notifizierung, Monitoring |

## Architektur

```
┌─────────────────────┐      MQTT       ┌───────────────────┐      HTTP/REST      ┌─────────────┐
│   Smart Meter Reader│ ──────────────► │  Mosquitto Broker │  ◄───────────────── │  Dynatrace  │
│   (Publisher)       │                 │    (Port 1883)    │                     │   Tenant    │
└─────────────────────┘                 └─────────┬─────────┘                     └──────▲──────┘
                                                  │                                      │
                                                  │ Abonnieren                           │
                                                  ▼                                      │
                                        ┌─────────────────────┐                          │
                                        │  Metric Ingest App  │ ─────────────────────────┘
                                        │  (Python Container) │   Metrics Ingest API v2
                                        └─────────────────────┘
```



## Dynatrace-Integration

### Metrics Ingest API

Die Anwendung verwendet die **Dynatrace Metrics Ingest API v2** (`/api/v2/metrics/ingest`), um Smart-Meter-Metriken direkt in Ihre Dynatrace-Umgebung zu übertragen.

**Erforderliche API-Token-Berechtigungen:**
- `metrics.ingest` - Metriken einspeisen

### Konfiguration

Die folgenden Umgebungsvariablen müssen für Dynatrace konfiguriert werden:

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `TENANT_HOST` | Ihre Dynatrace-Tenant-URL (ohne https://) | `abc12345.live.dynatrace.com` |
| `API_TOKEN` | API-Token mit `metrics.ingest`-Berechtigung | `dt0c01.XXX...` |

---

## MQTT-Konfiguration

Die Anwendung verbindet sich mit einem Eclipse Mosquitto MQTT-Broker zum Empfang von Smart-Meter-Daten.

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `MQTT_BROKER` | MQTT-Broker-Hostname | `mosquitto` (Container-Name) |
| `MQTT_PORT` | MQTT-Broker-Port | `1883` |
| `MQTT_USER` | MQTT-Benutzername | - |
| `MQTT_PASSWORD` | MQTT-Passwort | - |
| `MQTT_CLIENT_ID` | Eindeutige Client-Kennung | - |
| `MQTT_TOPIC` | Zu abonnierendes Topic | - |

---

## Dynatrace OneAgent

Die `docker-compose.yml` enthält einen Dynatrace OneAgent-Container für Full-Stack-Monitoring.

### Konfiguration

| Variable | Beschreibung |
|----------|--------------|
| `DT_ONEAGENT_URL` | OneAgent-Installer-Skript-URL aus Ihrer Dynatrace-Umgebung |

### OneAgent-Container-Einstellungen

Der OneAgent läuft mit:
- **Privilegierter Modus**: Erforderlich für vollen Systemzugriff
- **Host-Netzwerkmodus**: Für die Überwachung von Host-Level-Metriken
- **Host-PID-Namespace**: Für Prozesssichtbarkeit
- **Root-Dateisystem-Mount**: Für vollständige Host-Überwachung

---

## ⚠️ Raspberry Pi 3 Einschränkung

> **Wichtig:** Der Dynatrace OneAgent-Container **funktioniert NICHT auf Raspberry Pi 3**-Geräten.

### Grund

Der Raspberry Pi 3 verwendet eine **ARMv7 (32-Bit)**-Architektur, die von Dynatrace OneAgent **nicht unterstützt** wird. OneAgent erfordert:
- **x86_64 (AMD64)**-Architektur, oder
- **ARM64 (AArch64)**-Architektur (Raspberry Pi 4 und neuer)

### Workaround für Raspberry Pi 3

Bei der Bereitstellung auf Raspberry Pi 3:

1. **Entfernen oder kommentieren Sie den OneAgent-Dienst** in `docker-compose.yml` aus
2. **Verlassen Sie sich auf die Metrics Ingest API** zum Senden von Daten an Dynatrace (dies funktioniert unabhängig von der Architektur)

Die Kernfunktionalität (MQTT → Dynatrace-Metrikeinspeisung) funktioniert auf Raspberry Pi 3, nur das OneAgent-basierte Host-Monitoring ist nicht verfügbar.

## Bereitstellung und starten der Applikation

### Voraussetzungen

1. Docker und Docker Compose installiert
2. Eine Dynatrace-Umgebung mit API-Zugang ist vorhanden
3. Ein API-Token mit `metrics.ingest`-Berechtigung ist vorhanden
4. Smartmetersensor mit ESP32 und Rasperry Pi befinden sich im selben LAN

### Einrichtung

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd MUS1-Project
   ```

2. **Erstellen Sie eine `.env`-Datei** im Projektstammverzeichnis:
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

3. **Starten der Container auf Windows**
   ```bash
   docker-compose up -d
   ```

4. **Für Raspberry Pi 3** verwenden Sie einen modifizierten Compose-Befehl:
   ```bash
   docker-compose up -d mosquitto smartmeter-metric-ingest
   ```

## Verwendete Technologien und nützliche Dokumentation
[Dynatrace Metrics Ingest](https://docs.dynatrace.com/docs/discover-dynatrace/references/dynatrace-api/environment-api/metric-v2/post-ingest-metrics)  
[Dynatrace Dashboards](https://docs.dynatrace.com/docs/analyze-explore-automate/dashboards-and-notebooks/dashboards-new)  
[Dynatrace Oneagent](https://docs.dynatrace.com/docs/ingest-from/dynatrace-oneagent)  
[Dynatrace DQL](https://docs.dynatrace.com/docs/discover-dynatrace/platform/grail/dynatrace-query-language)  
[Smartmeter Auslesung des NetzOÖ Smartmeters](https://github.com/mgerhard74/amis_smartmeter_reader)  
[Oneagent for Linux](https://docs.dynatrace.com/docs/ingest-from/dynatrace-oneagent/installation-and-operation/linux/installation/install-oneagent-on-linux)  

