<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->
# Project: OS2mint Omada

## Context
- This is an integration for the OS2mo application (https://github.com/OS2mo)
  that runs as a separate docker-compose service.
- The integration synchronises identities from
  [Omada](https://omadaidentity.com/) into OS2mo (MO), keeping employees,
  engagements, addresses and IT-users in sync. Behaviour differs per customer
  (currently `frederikshavn` and `silkeborg`), selected via the `CUSTOMER`
  environment variable.
- It is event-driven from two sides:
  - It listens to GraphQL events from OS2mo (the new event system). Listeners
    are declared in `os2mint_omada/app.py` and the HTTP event handlers live in
    `os2mint_omada/sync/<customer>/events.py` (the `mo_router` FastAPI router).
  - Omada's API is not event-driven, so the built-in `OmadaEventGenerator`
    periodically reads the entire Omada OData view and emits events on its own
    AMQP exchange, which the `omada_router` handlers consume.

## Running Tests
- Unit tests are in `tests/`, except for sub-directories like
  `tests/integration/`, which is for integration tests.
- Integration tests are marked with `@pytest.mark.integration_test` and require
  a running MO stack.

### Bring up the MO stack
The integration tests talk to a real OS2mo instance. Clone and start it:
```
git clone https://github.com/OS2mo/os2mo
cd os2mo
docker compose up -d --build
```
This creates the external `os2mo_default` Docker network that this project's
`docker-compose.yml` attaches to.

### Run the tests
From this repository (mirrors the pattern MO integrations use):
```
docker compose up -d          # start db, run os2mo-init, start fake-omada-api and the app
docker compose stop omada     # stop the long-running app so it does not race the tests
docker compose run --rm omada pytest                       # run all tests
docker compose run --rm omada pytest tests/integration     # only integration tests
docker compose run --rm omada pytest -m "not integration_test"  # only unit tests
```
The `os2mo-init` service (a dependency of `omada`) seeds MO with the
IT-systems, facets and classes the integration expects; see `init.config.yml`.

Notes:
- The repository is mounted read-only into the container, so pytest emits a
  harmless `PytestCacheWarning` about not being able to write its cache.
- To regenerate the GraphQL client after changing `queries.graphql`, build the
  image and run `ariadne-codegen` against a writable mount (the compose service
  mounts the repo read-only, so use `docker run` directly):
  ```
  docker compose build omada
  docker run --rm -v "$(pwd):/app" -w /app os2mint-omada-omada ariadne-codegen client
  ```

## Boundaries
- If there are uncommitted changes, do not add them to commits you make. Either
  commit your changes separately, or if it isn't possible, ask me for
  permission to commit the existing changes.
