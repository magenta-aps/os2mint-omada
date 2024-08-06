# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import json
import re

from fastapi import FastAPI
from fastapi import Request


def create_app(values: list | None = None) -> FastAPI:
    """This fake Omada API is used for both manual and integration tests."""
    # During integration testing, 'values' is passed by each test to mock a certain
    # view of users. Otherwise, when running through uvicorn in docker compose, it
    # will be None, so we read the mounted json file instead.
    if values is None:
        with open("/odata.json") as f:
            omada_json: dict = json.load(f)
        values = omada_json["value"]

    app = FastAPI()

    @app.get("/")
    async def get(request: Request) -> dict:
        """Incredibly basic Omada OData implementation.

        All our queries to the Omada API are either filter-less, or contain exactly one
        filter of the format `<field> eq '<value>'` or `Id eq <value>`.
        """
        omada_filter = request.query_params.get("$filter")
        if not omada_filter:
            return {"value": values}
        match = re.match(r"(.+) eq (?:(\d+)|'(.+)')", omada_filter)
        assert match is not None
        key, int_value, str_value = match.groups()
        value: int | str
        if int_value is not None:
            value = int(int_value)
        elif str_value is not None:
            value = str_value
        else:
            raise ValueError(f"Unknown filter: {omada_filter}")
        return {"value": [v for v in values if v[key] == value]}

    return app
