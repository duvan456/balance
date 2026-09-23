# Django Task API

A small Django REST Framework API for managing tasks.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/tasks/`.

## Frontend React

The React dashboard lives in `frontend/` and consumes the API through Vite's
development proxy. Start Django first, then in a second terminal run:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dashboard includes task CRUD plus read-only
views for the first 100 income and expense records from the warehouse.

## Fabric Data Warehouse

The read-only endpoints below use the corporate identity through the installed
`ODBC Driver 18 for SQL Server`:

- `GET /api/ingresos/` reads the first 100 rows from `dbo.Ingreso`
- `GET /api/gastos/` reads the first 100 rows from `dbo.Gasto`

The default Fabric configuration is already set for the `Financiera` warehouse.
It can be overridden with these environment variables before starting Django:

```powershell
$env:FABRIC_WAREHOUSE_SERVER = "gh5sughwadpurfndk6z762tuuq-fvbqi3ipc7nuxhuw4ucuzeepkm.datawarehouse.fabric.microsoft.com"
$env:FABRIC_WAREHOUSE_DATABASE = "Financiera"
$env:FABRIC_WAREHOUSE_ODBC_DRIVER = "ODBC Driver 18 for SQL Server"
$env:FABRIC_WAREHOUSE_AUTHENTICATION = "ActiveDirectoryInteractive"
```

For the managed Entra account used locally, `ActiveDirectoryInteractive` opens
the Microsoft sign-in flow and supports MFA. Federated Windows accounts can use
`ActiveDirectoryIntegrated` instead. The machine must have network/VPN access
to Fabric and the account must have permission to read both tables. The API does
not expose any endpoint that inserts, updates, or deletes warehouse data.

## Endpoints

- `GET /api/tasks/` lists tasks
- `POST /api/tasks/` creates a task
- `GET /api/tasks/<id>/` retrieves a task
- `PATCH /api/tasks/<id>/` updates a task
- `DELETE /api/tasks/<id>/` deletes a task

Example request:

```json
{
  "title": "Prepare report",
  "description": "Review the monthly metrics",
  "status": "todo"
}
```

Run tests with:

```powershell
python manage.py test
```

## Admin

- `GET /admin/` panel de administracion

usuario: admin
contrasenia: admin