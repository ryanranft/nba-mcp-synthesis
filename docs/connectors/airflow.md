# Apache Airflow Integration

## Overview
Airflow connector provides workflow orchestration for automated NBA data pipelines and analytics jobs.

## Configuration

### Environment Variables
```bash
AIRFLOW_HOME=/path/to/airflow
AIRFLOW_DATABASE_URL=postgresql://user:pass@localhost:5432/airflow
AIRFLOW_EXECUTOR=LocalExecutor
AIRFLOW_WEBSERVER_PORT=8080
```

## Usage

### Creating a DAG
```python
from airflow import DAG
from mcp_server.airflow_connector import NBADataPipeline

with DAG('nba_daily_stats', schedule_interval='0 0 * * *') as dag:
    pipeline = NBADataPipeline()
    
    fetch_stats = pipeline.create_fetch_task('fetch_stats')
    process_stats = pipeline.create_process_task('process_stats')
    load_stats = pipeline.create_load_task('load_stats')
    
    fetch_stats >> process_stats >> load_stats
```

### Running a Pipeline
```bash
airflow dags trigger nba_daily_stats
```

## Testing
Run tests with:
```bash
pytest tests/test_airflow_connector.py
```

## Features
- Scheduled data collection
- ETL pipeline orchestration
- Retry logic and error handling
- Monitoring and alerting
- Parallel task execution
- Dependency management

## DAG Examples
- Daily player stats collection
- Weekly team performance analysis
- Monthly data quality checks
- Real-time game updates

## Dependencies
- apache-airflow>=2.7.0
- apache-airflow-providers-postgres>=5.7.0
- celery>=5.3.0 (for distributed execution)

## Setup
1. Initialize Airflow database: `airflow db init`
2. Create admin user: `airflow users create`
3. Start webserver: `airflow webserver`
4. Start scheduler: `airflow scheduler`

