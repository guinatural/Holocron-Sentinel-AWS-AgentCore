# Holocron Sentinel

Holocron Sentinel is a Python API and a set of AWS security scanners. The local
test suite uses stubs and does not contact AWS. Actual scans require AWS
credentials and permissions; report generation requires access to Amazon
Bedrock.

**Project status:** experimental and not production-ready. Authentication,
authorization, tenant isolation, secure session encryption, deployment
hardening, and live AWS behavior have not been established by the local test
suite.

## Requirements

- Python 3.12 or newer
- AWS credentials and permissions only when running real scans
- Bedrock model access only when generating reports with the live service

## Run locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m uvicorn app.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is
at `/docs`. Starting the server does not itself run a scan. The audit and scan
endpoints call AWS services when requested.

## Test offline

The suite replaces boto3 clients with local mocks; tests must not use real AWS
credentials, network access, or deploy resources.

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pytest tests/
py -3.12 -m ruff check app tests
py -3.12 -m black --check app tests
```

The latest full local run with Python 3.12 and the pinned dependencies passed
57 tests with 54% total coverage. These are measured results, not a coverage
target; coverage is reported by pytest according to `pytest.ini`.

## API flow

- `POST /api/v1/audit` starts an audit and returns its job ID.
- `GET /api/v1/audit/{job_id}?tenant_id={tenant_id}` reads the saved job.
- `GET /api/v1/summary/{tenant_id}` summarizes completed jobs for that tenant.
- `POST /api/v1/scanners/scan` runs one scanner.
- `GET /api/v1/scanners` lists scanner names.
- `GET /api/v1/scanners/status?tenant_id={tenant_id}` checks scanner clients.

Audit job records are stored locally under a tenant-scoped hashed file name.
Without `SESSION_KEY`, the process uses a temporary process-local key: data is
readable across requests in the same process but is not durable across a
restart. The current XOR transformation is not secure encryption. This storage
must not be used for sensitive or production data.

## Known limitations

- `tenant_id` is supplied by the caller; there is no authentication or
  authorization establishing that a caller may access that tenant.
- Tenant-scoped file paths do not constitute a proven security boundary.
- Session data is not protected by production-grade authenticated encryption.
- The tests verify mocked AWS request/response behavior, not permissions,
  service availability, model access, costs, or behavior in a real AWS account.
- Deployment, scaling, operational monitoring, and production readiness have
  not been validated.
