# Lesson 9: Eye of Agamotto & The Watcher (Monitoring & Logging)

**Objective:** Instrument our application to expose metrics for Prometheus monitoring and implement structured logging for aggregation with Fluentd and Loki.

**Analogy:** To truly understand the battlefield (our cluster and application), Doctor Strange uses the Eye of Agamotto (Prometheus) to see metrics and potential futures (performance trends, resource usage). Simultaneously, The Watcher (Fluentd/Loki) observes and records every event (log entry) across all timelines (Pods) for later analysis.

## Concepts Introduced

### 1. Application Metrics & Prometheus

*   **What are Metrics?** Numerical measurements of application or system behavior over time (e.g., request counts, latency, error rates, CPU/memory usage).
*   **Prometheus:** An open-source systems monitoring and alerting toolkit. It works by *scraping* (pulling) metrics from configured endpoints exposed by applications or exporters.
*   **Exposition Format:** Applications expose metrics in a simple text-based format on an HTTP endpoint (commonly `/metrics`).
*   **Instrumentation:** The process of adding code to your application to track and expose relevant metrics. Libraries like `prometheus-fastapi-instrumentator` make this easy for FastAPI.
*   **Prometheus Operator / Scraping Config:** Your Prometheus instance (likely installed via a Helm chart like `kube-prometheus-stack` or similar) needs to be configured to discover and scrape the `/metrics` endpoint of our application Pods. This is often done via annotations on the Pods (`prometheus.io/scrape: "true"`, etc.) or by configuring Prometheus `ServiceMonitor` or `PodMonitor` custom resources.
*   **Grafana:** A visualization tool commonly used with Prometheus to create dashboards displaying the collected metrics.
*   **Analogy:** The `prometheus-fastapi-instrumentator` installs sensors in the Hero Registry HQ. These sensors report data (request counts, duration) to a specific comms channel (`/metrics`). The Eye of Agamotto (Prometheus) is configured (via annotations/ServiceMonitor) to listen to this channel, collect the data, and store it. Doctor Strange (you) then uses a viewing portal (Grafana) to see visualizations of this data.

### 2. Structured Logging

*   **What it is:** Logging application events in a consistent, machine-readable format, typically JSON, instead of plain text strings. Each log entry contains key-value pairs (e.g., `{"timestamp": "...", "level": "INFO", "message": "User logged in", "user_id": 123}`).
*   **Why use it:** Makes logs much easier to parse, filter, query, and analyze by log aggregation systems. Avoids complex regex parsing.
*   **Implementation:** Using libraries like `python-json-logger` to automatically format Python's standard `logging` output as JSON.
*   **Analogy:** Instead of writing mission reports in free-form text, agents now fill out standardized digital forms (JSON logs) with specific fields (timestamp, level, message, user_id). This makes it much easier for S.H.I.E.L.D. analysts (log aggregation tools) to search and correlate reports.

### 3. Log Aggregation: Fluentd & Loki

*   **The Problem:** In Kubernetes, Pods are ephemeral, and their logs disappear when they die. Accessing logs via `kubectl logs` is manual and doesn't scale for many Pods or long-term storage/analysis.
*   **Log Aggregation:** The process of collecting logs from multiple sources (like all Pods on all Nodes), processing them, and forwarding them to a centralized storage and analysis system.
*   **Fluentd:** A popular open-source data collector (often deployed as a DaemonSet in Kubernetes) that can tail log files (including container logs written to standard output/error), parse them, buffer them, and forward them to various destinations.
*   **Loki:** A horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus. It indexes metadata (labels like Pod name, namespace) rather than the full log content, making it efficient for storage and querying. Often used with Grafana for visualization.
*   **The Flow:**
    1.  Our FastAPI app writes structured JSON logs to standard output.
    2.  Kubernetes directs container stdout/stderr to log files on the Node (e.g., in `/var/log/pods/...`).
    3.  Fluentd (running as a DaemonSet, one per Node) tails these log files.
    4.  Fluentd parses the JSON logs and adds Kubernetes metadata (Pod name, namespace, labels).
    5.  Fluentd forwards the processed logs to Loki.
    6.  Loki stores the logs and indexes the metadata.
    7.  You query and view the logs in Grafana using Loki's query language (LogQL).
*   **Analogy:** The Watcher (Fluentd DaemonSet) has an instance on every planet (Node). Each instance observes all events (container logs) happening on its planet. It understands the standardized reports (JSON logs), adds context (Pod name, namespace), and transmits them to a central cosmic library (Loki). You then use a universal translator/viewer (Grafana) to search and read the library's contents.

## Practical Exercise: Implementing Monitoring & Logging

**Part 1: Update Code, Requirements & Image (CI/CD)**

1.  **Update Local Code:**
    *   Replace `hero-academy/lesson-01-recruit/requirements.txt` with the content from `hero-academy/lesson-09-monitoring-logging/requirements.txt`.
    *   Replace `hero-academy/lesson-01-recruit/main.py` with the content from `hero-academy/lesson-09-monitoring-logging/main.py`.
    *   *(Optional but Recommended)* Update the image tag in `.gitlab-ci.yml` and `lesson-09-monitoring-logging/deployment.yaml` (e.g., `hero-registry:lesson-09`). We'll assume `:latest`.
2.  **Commit & Push:** Add changes to Git and push to GitLab.
    ```bash
    # Assuming you copied the new main.py and requirements.txt over the old ones
    git add hero-academy/lesson-01-recruit/main.py
    git add hero-academy/lesson-01-recruit/requirements.txt
    # Add the new lesson 9 manifests
    git add hero-academy/lesson-09-monitoring-logging/
    git commit -m "Feat: Update app for Lesson 9 (Monitoring/Logging) and add manifests"
    git push
    ```
3.  **Monitor CI/CD:** Ensure the pipeline builds the new image (with instrumentation and logging libraries/code) and pushes it to Harbor.

**Part 2: Configure Prometheus Scraping**

1.  **Ensure Prometheus is Running:** You mentioned having Prometheus running. Verify it's configured to scrape targets based on Pod annotations. This is common in setups like `kube-prometheus-stack`. Check your Prometheus configuration (`prometheus.yaml` scrape_configs) or the `Prometheus` CRD if using Prometheus Operator. It might have a job similar to this:
    ```yaml
    # Example Prometheus scrape config for Pod annotations
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      # Only scrape pods with prometheus.io/scrape=true annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      # Use annotation for scrape path, default to /metrics
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      # Use annotation for port, default to container port
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
      # Standard Kubernetes labels
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name
    ```
    *(If Prometheus isn't configured for annotation scraping, you'll need to adjust its config or create a `ServiceMonitor`/`PodMonitor` resource instead of relying on annotations in the Deployment.)*

2.  **Apply Updated Deployment:** Apply the modified deployment file (`lesson-09-monitoring-logging/deployment.yaml`) which includes the `prometheus.io/*` annotations.
    ```bash
    # Make sure image tag and project name are correct!
    kubectl apply -f deployment.yaml --namespace=default
    ```

3.  **Verify Metrics Endpoint:**
    *   Wait for the new Pod to roll out: `kubectl rollout status deployment/hero-registry-deployment -n default`
    *   Port-forward to the Pod (or Service):
        ```bash
        POD_NAME=$(kubectl get pods -l app=hero-registry -n default -o jsonpath='{.items[0].metadata.name}')
        kubectl port-forward pod/$POD_NAME 8080:8000 -n default
        ```
    *   Access the metrics endpoint in another terminal:
        ```bash
        curl http://localhost:8080/metrics
        ```
        You should see Prometheus-formatted metrics (lines starting with `fastapi_`, `http_`, `python_`). Stop the port-forward.

4.  **Verify in Prometheus/Grafana:**
    *   Go to your Prometheus UI -> Status -> Targets. Look for a job (e.g., `kubernetes-pods`) and check if it shows an endpoint for your `hero-registry-deployment` Pod with State `UP`.
    *   Go to your Grafana UI. Explore metrics or create a dashboard using metrics like `fastapi_requests_total`, `fastapi_request_duration_seconds`.

**Part 3: Install & Configure Logging Aggregation (Fluentd + Loki)**

*   **Note:** Installing and configuring Fluentd and Loki is a significant task itself. We'll outline the steps, but you might need to consult specific Helm chart documentation (like the official Loki stack chart) for detailed values.

1.  **Install Loki:** Use the official Helm chart (often includes Promtail/Fluentd/Grafana).
    ```bash
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    # Example install (minimal, adjust values as needed)
    helm install loki grafana/loki-stack \
      --namespace=loki --create-namespace \
      # --set fluent-bit.enabled=false # If you want to install Fluentd separately
      # --set promtail.enabled=true # Promtail is another common agent, often bundled
      # Configure persistence, etc. via values.yaml or --set
    ```
2.  **Install Fluentd (if not bundled with Loki stack):** Use a community Fluentd Helm chart configured for Kubernetes log collection.
    *   You'll typically deploy it as a `DaemonSet`.
    *   Configure its input plugin to tail container logs (e.g., from `/var/log/containers/*.log` or `/var/log/pods/*/*.log`).
    *   Configure the `kubernetes_metadata` filter plugin to add Pod/Namespace labels.
    *   Configure the parser for JSON logs (since our app outputs JSON).
    *   Configure the output plugin to send logs to your Loki service endpoint (e.g., `http://loki-write.loki.svc.cluster.local:3100/loki/api/v1/push`).
    *   Example chart: `fluent/fluentd`, `bitnami/fluentd` (check their specific values for Loki output).

3.  **Configure Grafana Loki Data Source:**
    *   In Grafana, go to Configuration -> Data Sources -> Add data source.
    *   Select "Loki".
    *   Set the URL to your Loki service endpoint (e.g., `http://loki-read.loki.svc.cluster.local:3100`).
    *   Save & Test.

**Part 4: Verify Logging**

1.  **Generate Logs:** Access your application via the Ingress URL (`https://hero-registry.komebacklab.local`) or port-forward to generate some request logs. Add/get heroes.
2.  **Check Fluentd Logs (Optional):** If troubleshooting, check the logs of the Fluentd pods (`kubectl logs -n <fluentd-namespace> <fluentd-pod-name>`) to see if they are collecting and forwarding logs.
3.  **Query Logs in Grafana:**
    *   Go to Grafana -> Explore.
    *   Select the Loki data source.
    *   Use LogQL queries to find your application's logs. Examples:
        *   `{container="hero-registry-api"}`
        *   `{namespace="default", pod=~"hero-registry-deployment.*"}`
        *   `{app="hero-registry"} | json | line_format "{{.message}}"` (To parse JSON and show the message field)
        *   `{app="hero-registry"} | json | level="error"` (Filter by log level)
    *   You should see the JSON log entries generated by the application.

## Problem-Solving Framework: Monitoring & Logging Issues

1.  **Identify the Symptom:** Metrics not appearing in Prometheus/Grafana? Logs not appearing in Loki/Grafana? Fluentd pods crashing? High resource usage by logging components? Incorrect log format?
2.  **Locate the Problem Area:**
    *   **Metrics:**
        *   *App-Level:* Does the `/metrics` endpoint work via `port-forward`? Is the instrumentator library installed (`requirements.txt`) and initialized (`main.py`)?
        *   *Scraping Config:* Are the Prometheus annotations correct in `deployment.yaml`? Does Prometheus have a scrape job configured for annotations/ServiceMonitors? Is Prometheus actually scraping the target (check Prometheus UI -> Status -> Targets)? Network policies blocking scrape?
        *   *Prometheus/Grafana:* Is Prometheus running? Is Grafana configured with Prometheus as a data source? Query syntax correct?
    *   **Logging:**
        *   *App-Level:* Is the app actually logging? Is it logging to standard output/error? Is it using the structured JSON format (`python-json-logger` configured correctly)? Check `kubectl logs <app-pod-name>`.
        *   *Fluentd:* Is the DaemonSet running on all nodes? Check Fluentd pod logs (`kubectl logs -n <fluentd-ns> <fluentd-pod>`). Errors parsing logs? Errors connecting to Loki? Correct input path configuration? Correct parser config (JSON)? Correct Loki output URL? RBAC permissions to read logs/metadata? High CPU/memory usage?
        *   *Loki:* Is Loki running? Check its logs (`kubectl logs -n loki <loki-pod>`). Receiving logs from Fluentd? Storage issues (if using persistence)? Query performance issues?
        *   *Grafana:* Is the Loki data source configured correctly (URL)? LogQL query syntax correct? Time range correct?

3.  **Consult the Blueprints/Manuals:**
    *   *`main.py`:* Check instrumentator setup, logging configuration (`jsonlogger`, levels).
    *   *`deployment.yaml`:* Check Prometheus annotations.
    *   *Prometheus Config/CRDs:* Check scrape job definitions.
    *   *Fluentd Config:* Check input sources, parsers, filters (kubernetes metadata), output plugins (Loki URL, format).
    *   *Loki Config:* Check storage, ingestion rules.
    *   *Helm Chart Values:* Review values used for Prometheus, Grafana, Loki, Fluentd installations.
    *   *Logs:* App logs, Prometheus logs, Grafana logs, Fluentd logs, Loki logs.

4.  **Isolate and Test:**
    *   *Metrics:* Can Prometheus scrape a simple known exporter (e.g., `node-exporter`)?
    *   *Logging:* Deploy a simple Pod that just prints JSON to stdout. Does Fluentd pick it up and send it to Loki? Configure Fluentd output to stdout temporarily instead of Loki to verify parsing/collection. Send a test log message directly to Loki's API.

5.  **Verify Assumptions:** Did you assume Prometheus annotation scraping was enabled? Did you assume Fluentd was configured to parse JSON? Did you assume the Loki service URL was correct? Did you assume Fluentd had permissions? Did you assume the app was logging to stdout?

**Your application now has enhanced visibility! You can monitor its performance with Prometheus and Grafana, and analyze its behavior through structured logs aggregated in Loki. Next, we'll learn how to package our application for easier deployment using Helm.**
