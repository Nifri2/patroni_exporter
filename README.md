# Prometheus Exporter for Patroni
Based on [The Patroni REST API](https://patroni.readthedocs.io/en/latest/rest_api.html)

- [Prometheus Exporter for Patroni](#prometheus-exporter-for-patroni)
  - [Exported Metrics](#exported-metrics)
  - [Installation](#installation)


## Exported Metrics

| Name  | Endpoint | Descripton |
|-------|----------|------------|
|`lag`|patroni_exporter_replica_lag|the lag of the node, if the node is a `replica`|
|`lag_mb`| patroni_exporter_replica_lag_mb |the lag of the node, if the node is a `replica`|
|`timeline`| patroni_exporter_node_timeline |
|`role`| patroni_exporter_role | the role of the node (Either `replica` or `leader`)|
|`state`| patroni_exporter_state | the state of the node (Either `running` or `stopped`)|
|`health`| patroni_exporter_health | returns `OK` only when PostgreSQL is up and running, otherwise `ERROR`|
|`liveness`| patroni_exporter_liveness | returns `OK` what only indicates that Patroni is running, otherwise `ERROR`|
|`check`| patroni_exporter_running_check | returns `running` when the exporter is working properly, otherwise uuuh.... probalby nothing because the process would be dead|

## Installation

- Install python3
- run `pip install -r requirements.txt`
- change the config to your needs
- run using `python patroni_exporter.py`
- optional: use a systemd unit to run it 