## API

The API prefix is configured by `API_PREFIX` (it is `/api` in `.env.example`).
The paths below include that prefix.

### `GET /api/departments/all`

Returns all departments as an `items` array. Each item contains an `id` and
`name`. Use a department's `id` when calling the database-backed aggregation
endpoint.

### `POST /api/expenses/aggregated/file`

Aggregates expense amounts directly from an uploaded CSV, without reading from
or writing to the database. Submit a `multipart/form-data` request with:

- `upload_file`: the CSV file (for example, `expenses.csv`)
- `department_name`: department name to aggregate
- `year` (optional): year to filter by
- `month` (optional): three-letter month such as `Jan` or `Dec`
- `quarter` (optional): quarter number from `1` to `4`

Only one of `month` or `quarter` can be provided. If neither is provided, all
months are included.

### `POST /api/expenses/import-file`

Imports a CSV into the internal PostgreSQL database. Submit the file as
`upload_file` in a `multipart/form-data` request. The CSV must contain
`Department`, `Expense Type`, `Year`, and all twelve month columns (`Jan`
through `Dec`), separated by semicolons.

Existing departments and expense types are reused, so importing the same file
does not create duplicate department or expense-type records. Expense rows are
inserted again on every import; expenses have no uniqueness constraint to
prevent duplicates. A successful import returns `201 Created`.

### `POST /api/expenses/aggregated`

Aggregates expenses already stored in the database. Submit parameters as
`multipart/form-data`:

- `department_id`: department ID (required; see `GET /api/departments/all`)
- `year` (optional): year to filter by
- `month` (optional): month number from `1` to `12`
- `quarter` (optional): quarter number from `1` to `4`

Only one of `month` or `quarter` can be provided. If neither is provided, all
months are included. The response contains the aggregated `total`.

## Run the project

Docker Compose is all you need to run the application. Copy the example
environment file, then start the services from the project root:

```sh
cp .env.example .env
docker compose up --build
```

When the API container starts, it automatically applies pending Alembic
migrations before starting the application.

## Tests

Install the development dependencies and run the tests from the project root:

```sh
uv sync --group dev
uv run pytest
```

Tests use an in-memory SQLite database, so PostgreSQL and Docker do not need to
be running.
