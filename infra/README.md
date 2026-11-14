# Local services

This directory runs the services needed for a real local demonstration. It is intentionally separate from the application container so that MLflow and Airflow data survive an API rebuild.

Start the services from the repository root:

```powershell
docker compose -f infra/compose.local.yaml up --build -d
```

MLflow is available at `http://localhost:5000`. Airflow is available at `http://localhost:8080`. Airflow 3 writes the initial admin password to its startup log; retrieve it with `docker compose -f infra/compose.local.yaml logs airflow`, then copy it into your untracked `.env` file as `AIRFLOW_PASSWORD`. The username is `admin` for Airflow standalone.

Use `docker compose -f infra/compose.local.yaml down` to stop services without deleting their data. Adding `--volumes` deletes the local tracking and scheduler history and should only be used when a clean reset is intended.
