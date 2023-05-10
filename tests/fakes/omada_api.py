# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import json
import re

from fastapi import FastAPI
from fastapi import Request

app = FastAPI()


@app.get("/")
async def get(request: Request) -> dict:
    with open("/odata.json") as f:
        omada_json: dict = json.load(f)
    values = omada_json["value"]
    if omada_filter := request.query_params.get("$filter"):
        key, value = re.match(r"(.+) eq '(.+)'", omada_filter).groups()
        values = [v for v in values if v[key] == value]
    return {"value": values}
