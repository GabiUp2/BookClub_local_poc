# Grafana Tasks Mapping

## Phase 1: Observability

- [x] Send dev logs to Loki — logs from both app and development environment visible
  - Topics:
    - [x] [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)
    - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
    - [ ] [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)
    - [ ] [Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides)
- [x] Send function execution timings as Prometheus metrics
  - Topics:
    - [ ] [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)
    - [ ] [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)
    - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
    - [ ] [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)
    - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
- [x] Optional: send test execution time metrics to Prometheus (via Pushgateway)
  - Topics:
    - [ ] [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)
    - [ ] [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)
    - [ ] [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)
    - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
- [ ] Add Tempo service and Grafana Tempo datasource
  - Topics:
    - [ ] [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)
    - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
    - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
    - [ ] [Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)
    - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
- [ ] Enable OTEL: instrument FastAPI/app with OpenTelemetry SDK
  - Topics:
    - [ ] [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)
    - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
    - [ ] [Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)
    - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
  - [ ] Set OTEL resource attrs: `service.name`, `deployment.environment`, `git.commit`, `git.branch`
    - Topics:
      - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
      - [ ] [Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
  - [ ] Export traces via Alloy OTLP to Tempo
    - Topics:
      - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
      - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
      - [ ] [Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
- [ ] Correlate signals:
  - Topics:
    - [ ] [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)
    - [ ] [Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)
    - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
    - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
  - [ ] Include `trace_id` in logs (Loki) and enable trace exemplars on latency metrics
    - Topics:
      - [ ] [Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)
      - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
      - [ ] [Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides)
  - [ ] Grafana Explore: pivot metrics ↔ logs ↔ traces for a single request
    - Topics:
      - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
      - [ ] [Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
- [ ] Add git commit and branch to metrics and logs labels
  - Topics:
    - [ ] [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)
    - [ ] [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)
- [ ] Add basic alerting:
  - Topics:
    - [ ] [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)
    - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
    - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
    - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)
  - [ ] p95 latency per endpoint (Prometheus)
    - Topics:
      - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
      - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
      - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)
      - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
  - [ ] Error rate (Prometheus) and ERROR log spike (Loki)
    - Topics:
      - [ ] [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)
      - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
      - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)

### Definition of Done for Phase 1

- The Observability — tests:
  - [ ] I can see test execution by branch/commit in Grafana and compare across branches/commits
    - Topics:
      - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
      - [ ] [Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)
  - [ ] I can see the trend of per-test duration over time, filtered by branch/commit/test file/tags
    - Topics:
      - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
      - [ ] [Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)
- The Observability — function execution time (API):
  - [ ] I can see endpoint execution time distributions (p50/p95/p99), request rate, in-flight, error rate
    - Topics:
      - [ ] [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)
      - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
      - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
  - [ ] I can compare these across branches/commits and over time
    - Topics:
      - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
      - [ ] [Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)
- The Observability — traces and correlations:
  - [ ] Tempo receives traces from the app; I can view spans for a request (including DB/external calls)
    - Topics:
      - [ ] [Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)
      - [ ] [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
  - [ ] Metrics panels show trace exemplars; logs include `trace_id` and link to traces
    - Topics:
      - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
      - [ ] [Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
  - [ ] From a metric panel I can pivot to related logs and the corresponding trace
    - Topics:
      - [ ] [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)
      - [ ] [Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)
      - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
- The Observability — alerting and operations:
  - [ ] Alert rules exist for high error rate and high p95 latency, with a working contact point
    - Topics:
      - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
      - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)
      - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
  - [ ] Acknowledge/silence flow verified in Grafana Alerting
    - Topics:
      - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
      - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)

## Phase 5: Observability with Grafana, Deep Dive

- [ ] Provisioning as code: datasources, dashboards, alerting (YAML under `observability/grafana/provisioning/`)
  - Topics:
    - [ ] [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)
    - [ ] [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)
    - [ ] [Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101)
- [ ] Recording rules and performance: Prometheus recording rules; ruler/compactor tuning
  - Topics:
    - [ ] [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)
    - [ ] [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)
    - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
- [ ] Dashboard excellence: variables, transformations, drilldowns, links, UIDs, owners, folders
  - Topics:
    - [ ] [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)
    - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
    - [ ] [Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)
    - [ ] [Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides)
- [ ] SLOs and error budgets: burn-rate alerts, SLI panels, runbooks
  - Topics:
    - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
    - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
    - [ ] [k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides)
    - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
- [ ] Incident response: notification policies, grouping, silences, basic OnCall integration (optional)
  - Topics:
    - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
    - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)
- [ ] Label cardinality and cost controls: metrics/logs label strategy, Loki/Tempo retention
  - Topics:
    - [ ] [Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)
    - [ ] [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)
    - [ ] [Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides)
- [ ] Security & RBAC: folders, teams, roles, secrets handling
  - Topics:
    - [ ] [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)
    - [ ] [Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101)
- [ ] Scaling notes (optional): Mimir/Loki/Tempo high-level architecture and limits
  - Topics:
    - [ ] [k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides)
    - [ ] [Grafana APM Migration Guide](https://learn.grafana.com/path/best-practice-guides/grafana-apm-migration-guide) (Collection of Best Practice Guides)

### Definition of Done for Phase 5

- [ ] Datasources, dashboards, and alerting are provisioned as code; no manual drift
  - Topics:
    - [ ] [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)
    - [ ] [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)
- [ ] Key dashboards follow standards: owner, UID, folder, variables, links, and on-panel runbook links
  - Topics:
    - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
    - [ ] [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)
    - [ ] [Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)
- [ ] At least one SLO with burn-rate alerts is live and documented; runbook exists and is linked
  - Topics:
    - [ ] [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)
    - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
    - [ ] [k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides)
- [ ] Critical alert noise reduced via grouping/routing/silences; test plan demonstrates expected behaviour
  - Topics:
    - [ ] [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)
    - [ ] [Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)
- [ ] Recording rules reduce dashboard query latency on hot paths without losing fidelity
  - Topics:
    - [ ] [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)
    - [ ] [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)
    - [ ] [Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides)
- [ ] Retention and label cardinality policies documented and applied (Prometheus, Loki, Tempo)
  - Topics:
    - [ ] [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)
    - [ ] [Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides)
    - [ ] [Grafana APM Migration Guide](https://learn.grafana.com/path/best-practice-guides/grafana-apm-migration-guide) (Collection of Best Practice Guides)
- [ ] Access controls (folders/teams) applied according to documented policy
  - Topics:
    - [ ] [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)
    - [ ] [Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101)


## Tabular Overview

| Phase | Task | Topics |
| --- | --- | --- |
| Phase 1 | [x] Send dev logs to Loki — logs from both app and development environment visible | [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)<br>[Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)<br>[Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides) |
| Phase 1 | [x] Send function execution timings as Prometheus metrics | [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)<br>[Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)<br>[Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 1 | [x] Optional: send test execution time metrics to Prometheus (via Pushgateway) | [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)<br>[Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)<br>[Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Add Tempo service and Grafana Tempo datasource | [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)<br>[Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Enable OTEL: instrument FastAPI/app with OpenTelemetry SDK | [Intro to Data Collection](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-collection) (Grafana Fundamentals Path)<br>[Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Set OTEL resource attrs: `service.name`, `deployment.environment`, `git.commit`, `git.branch` | [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Export traces via Alloy OTLP to Tempo | [Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Grafana Alloy Instrumentation Playbooks](https://learn.grafana.com/path/best-practice-guides/grafana-alloy-instrumentation-playbooks) (Collection of Best Practice Guides)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Correlate signals: | [Intro to Grafana & Observability](https://learn.grafana.com/path/grafana-fundamentals/intro-to-grafana-observability) (Grafana Fundamentals Path)<br>[Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)<br>[Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Include `trace_id` in logs (Loki) and enable trace exemplars on latency metrics | [Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)<br>[Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Grafana Explore: pivot metrics ↔ logs ↔ traces for a single request | [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Add git commit and branch to metrics and logs labels | [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)<br>[Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Add basic alerting: | [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)<br>[Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)<br>[Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides) |
| Phase 1 | [ ] p95 latency per endpoint (Prometheus) | [Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)<br>[Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 1 | [ ] Error rate (Prometheus) and ERROR log spike (Loki) | [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)<br>[Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] I can see test execution by branch/commit in Grafana and compare across branches/commits | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] I can see the trend of per-test duration over time, filtered by branch/commit/test file/tags | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] I can see endpoint execution time distributions (p50/p95/p99), request rate, in-flight, error rate | [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)<br>[Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] I can compare these across branches/commits and over time | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] Tempo receives traces from the app; I can view spans for a request (including DB/external calls) | [Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)<br>[Collection of Metrics, Logs, & Traces](https://learn.grafana.com/path/technical-practitioner-path/collection-of-metrics-logs-traces-module-labs) (Technical Practitioner Path 101)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] Metrics panels show trace exemplars; logs include `trace_id` and link to traces | [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] From a metric panel I can pivot to related logs and the corresponding trace | [Using Logs, Metrics, and Traces Together](https://learn.grafana.com/path/technical-practitioner-path/using-logs-metrics-and-traces-together-in-grafana) (Technical Practitioner Path 101)<br>[Hands-on-Lab: Grafana Product Exploration](https://learn.grafana.com/path/grafana-fundamentals/hands-on-lab-grafana-product-exploration) (Grafana Fundamentals Path)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 1 (DoD) | [ ] Alert rules exist for high error rate and high p95 latency, with a working contact point | [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides)<br>[Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101) |
| Phase 1 (DoD) | [ ] Acknowledge/silence flow verified in Grafana Alerting | [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides) |
| Phase 5 | [ ] Provisioning as code: datasources, dashboards, alerting (YAML under `observability/grafana/provisioning/`) | [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)<br>[Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)<br>[Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101) |
| Phase 5 | [ ] Recording rules and performance: Prometheus recording rules; ruler/compactor tuning | [Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)<br>[Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 5 | [ ] Dashboard excellence: variables, transformations, drilldowns, links, UIDs, owners, folders | [Intro to Data Visualization & Alerting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-data-visualization-alerting) (Grafana Fundamentals Path)<br>[Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)<br>[Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides)<br>[Grafana Application Observability Guide](https://learn.grafana.com/path/best-practice-guides/grafana-application-observability-guide) (Collection of Best Practice Guides) |
| Phase 5 | [ ] SLOs and error budgets: burn-rate alerts, SLI panels, runbooks | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 5 | [ ] Incident response: notification policies, grouping, silences, basic OnCall integration (optional) | [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides) |
| Phase 5 | [ ] Label cardinality and cost controls: metrics/logs label strategy, Loki/Tempo retention | [Building Efficient Queries: LogQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-logql) (Technical Practitioner Path 101)<br>[Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)<br>[Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides) |
| Phase 5 | [ ] Security & RBAC: folders, teams, roles, secrets handling | [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)<br>[Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101) |
| Phase 5 | [ ] Scaling notes (optional): Mimir/Loki/Tempo high-level architecture and limits | [k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides)<br>[Grafana APM Migration Guide](https://learn.grafana.com/path/best-practice-guides/grafana-apm-migration-guide) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Datasources, dashboards, and alerting are provisioned as code; no manual drift | [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)<br>[Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Key dashboards follow standards: owner, UID, folder, variables, links, and on-panel runbook links | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Building Effective Dashboards with the Four Golden Signals](https://learn.grafana.com/path/technical-practitioner-path/building-effective-dashboards-with-the-four-golden-signals-1) (Technical Practitioner Path 101)<br>[Dashboarding Best Practices](https://learn.grafana.com/path/best-practice-guides/dashboarding-best-practices) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] At least one SLO with burn-rate alerts is live and documented; runbook exists and is linked | [Intro to Leadership Reporting](https://learn.grafana.com/path/grafana-fundamentals/intro-to-leadership-reporting) (Grafana Fundamentals Path)<br>[Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[k6 Integration and Implementation for Kubernetes](https://learn.grafana.com/path/best-practice-guides/k6-integration-and-implementation-for-kubernetes) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Critical alert noise reduced via grouping/routing/silences; test plan demonstrates expected behaviour | [Alerting Essentials](https://learn.grafana.com/path/technical-practitioner-path/alerting-essentials) (Technical Practitioner Path 101)<br>[Alerting on High-Cardinality](https://learn.grafana.com/path/best-practice-guides/alerting-on-high-cardinality) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Recording rules reduce dashboard query latency on hot paths without losing fidelity | [Recording Rules](https://learn.grafana.com/path/technical-practitioner-path/recording-rules) (Technical Practitioner Path 101)<br>[Building Efficient Queries: PromQL](https://learn.grafana.com/path/technical-practitioner-path/building-efficient-queries-promql-1) (Technical Practitioner Path 101)<br>[Anomaly Detection in PromQL](https://learn.grafana.com/path/best-practice-guides/anomaly-detection-in-promql) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Retention and label cardinality policies documented and applied (Prometheus, Loki, Tempo) | [Loki Label Strategies](https://learn.grafana.com/path/best-practice-guides/loki-label-strategies) (Collection of Best Practice Guides)<br>[Loki Log Optimisations](https://learn.grafana.com/path/best-practice-guides/loki-log-optimizations) (Collection of Best Practice Guides)<br>[Grafana APM Migration Guide](https://learn.grafana.com/path/best-practice-guides/grafana-apm-migration-guide) (Collection of Best Practice Guides) |
| Phase 5 (DoD) | [ ] Access controls (folders/teams) applied according to documented policy | [Datasource Strategies and Best Practices](https://learn.grafana.com/path/best-practice-guides/datasource-strategies-and-best-practices) (Collection of Best Practice Guides)<br>[Trailblazer Assessment & Badge](https://learn.grafana.com/path/technical-practitioner-path/trailblazer-technical-practitioner-badge) (Technical Practitioner Path 101) |
