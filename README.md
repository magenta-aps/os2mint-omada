<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# OS2mint: Omada
TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
OS2mo integration for Omada. Synchronises Omada IT users to MO through the IT system defined by the `IT_SYSTEM_USER_KEY`
environment variable.


## Prerequisites
The integration requires MO to be initialised with the IT system and address classes `EmailEmployee`, `PhoneEmployee`,
`MobilePhoneEmployee`, and `InstitutionPhoneEmployee`. Users are encouraged to do so by adding the following to their
[os2mo-init](https://git.magenta.dk/rammearkitektur/os2mo-init) configuration:
```yaml
facets:
  employee_address_type:
    EmailEmployee:
      title: "Email"
      scope: "EMAIL"
    PhoneEmployee:
      title: "Telefon"
      scope: "PHONE"
    MobilePhoneEmployee:
      title: "Mobiltelefon"
      scope: "PHONE"
    InstitutionPhoneEmployee:
      title: "Institutionstelefonnummer"
      scope: "PHONE"
  visibility:
    Intern:
      title: "Må vises internt"
      scope: "INTERNAL"

it_systems:
  omada_ad_guid: "Omada"
```
The default `docker-compose.yml` does so automatically. Additionally, the v1 API must be enabled in OS2mo by setting the environment variable `V1_API_ENABLE=true`, the "lora" realm must be enabled in Keycloak, and the DIPEX client for the LoRa realm must be enabled as well.


## Usage
```
docker-compose up -d
```
The API can then be viewed from the host through http://localhost:9000/.

The following environment variables are used:
TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
  - `MO_URL`: OS2mo URL, e.g. `http://mo:80`.
  - `CLIENT_ID`: Client ID used to authenticate against OS2mo, e.g. `dipex`.
  - `CLIENT_SECRET`: Client secret used to authenticate against OS2mo, e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.
  - `AUTH_REALM`: Keycloak realm for OS2mo authentication, e.g. `mo`.
  - `AUTH_SERVER`: Keycloak authentication server, e.g. `http://keycloak:8080/auth`.

  - `IT_SYSTEM_USER_KEY`: User key of the IT system users will be inserted into, e.g. `omada`.

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
