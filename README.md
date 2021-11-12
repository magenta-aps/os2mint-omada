<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# OS2mint: Omada
TODO.


## Usage
```
docker-compose up -d
```
The API can then be viewed from the host through http://localhost:9000/.

The following environment variables are used:
  - `AUTH_SERVER`: Keycloak authentication server, e.g. `http://keycloak:8080/auth`.


  - `MO_URL`: OS2mo URL, e.g. `http://mo:80`.
  - `CLIENT_ID`: Client ID used to authenticate against OS2mo, e.g. `dipex`.
  - `CLIENT_SECRET`: Client secret used to authenticate against OS2mo, e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.
  - `AUTH_REALM`: Keycloak realm for OS2mo authentication, e.g. `mo`.


  - `LORA_URL`: OS2mo URL, e.g. `http://mox:80`.
  - `LORA_CLIENT_ID`: Client ID used to authenticate against LoRa, e.g. `dipex`.
  - `LORA_CLIENT_SECRET`: Client secret used to authenticate against OS2mo, e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.
  - `LORA_AUTH_REALM`: Keycloak realm for LoRa authentication, e.g. `lora`.


  - `IT_SYSTEM_UUID`: UUID of the IT system users will be inserted into, e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.
  - `IT_SYSTEM_USER_KEY`: User key of the IT system users will be inserted into, e.g. `OMADA`.
  - `IT_SYSTEM_NAME`: Name of the IT system users will be inserted into, e.g. `Omada`.


  - `ODATA_URL`: Omada OData view URL to fetch users from, e.g. `http://omada.example.org/OData/DataObjects/Identity?viewid=xxxxx`.


## Versioning
This project uses [Semantic Versioning](https://semver.org/) with the following strategy:
- MAJOR: Incompatible API changes.
- MINOR: Backwards-compatible updates and functionality.
- PATCH: Backwards-compatible bug fixes.


## Authors
Magenta ApS <https://magenta.dk>


## License
- This project: [MPL-2.0](LICENSES/MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing. All licenses can be found in the [LICENSES folder](LICENSES/) of the project.
