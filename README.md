# User Management API — E2E Test Suite

E2E test suite for the User Management API, covering all endpoints
and both `dev`/`prod` environments as documented in
`sdet_challenge_api.yml`.

## Project structure

```
client/            HTTP client wrapper around the API
tests/              Test suite (pytest)
  conftest.py       Shared fixtures (client, unique data, cleanup)
  test_list_users.py
  test_get_user.py
  test_create_user.py
  test_update_user.py
  test_delete_user.py
  test_cross_cutting.py
.github/workflows/  CI pipeline (dev + prod stages, run in parallel)
BUGS.md             Bugs found vs. spec, with reproduction steps
```

## Running locally

1. Start the application:
   ```
   docker run -p 3000:3000 ghcr.io/danielsilva-loanpro/sdet-interview-challenge:latest
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the suite against `dev` (default):
   ```
   pytest
   ```
   Against `prod`:
   ```
   API_ENV=prod pytest
   ```
4. Generate an HTML report:
   ```
   pytest --html=report.html --self-contained-html
   ```

## Environment variables

| Variable     | Default                 | Purpose                          |
| ------------ | ------------------------ | --------------------------------- |
| `BASE_URL`   | `http://localhost:3000`  | Base URL of the running app       |
| `API_ENV`    | `dev`                    | Environment prefix (`dev`/`prod`) |
| `AUTH_TOKEN` | `mysecrettoken`          | Token for auth-protected routes   |

## CI

`.github/workflows/tests.yml` runs two independent jobs, `test-dev`
and `test-prod`, in parallel. Each spins up the app container, waits
for readiness, runs the suite against its environment, and uploads
the HTML report as a build artifact — even if tests fail, so failures
in one environment never block or hide results from the other.

## Bugs found

See [`BUGS.md`](./BUGS.md) for the list of behaviors that don't match
the spec, each backed by a failing (or documenting) test in the
suite.
