<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# OS2mint: Omada
OS2mo integration for [Omada](https://omadaidentity.com/).


## Prerequisites
The integration requires MO to be initialised with a number of facet classes.
Users are encouraged to do so by applying [init.config.yml] using
[os2mo-init](https://git.magenta.dk/rammearkitektur/os2mo-init). The default
`docker-compose.yml` does so automatically.

## Persistence
Omada's API is not event-driven. Instead, the entire Omada view is read
periodically and cached to a local file on disk. For this reason, the `/data`
path should be mounted into the container and persisted. It is our goal to
implement persistence using a backing service in the future.


## Usage
```
docker-compose up -d
```
Configuration is done through environment variables. Available options can be
seen in [os2mint_omada/config.py]. Complex variables such as dict or lists can
be given as JSON strings, as specified by Pydantic's settings parser.

After the initial import of Omada users, it can be useful to force-synchronise
information for already-existing MO users. This can be done through OS2mo's
`refresh` GraphQL mutators.

**NOTE** that MO organisation units are not watched for changes, so manual Omada
users, which should be inserted into a non-existent organisation unit will not
be synchronised automatically when (and if) this organisation unit is created in
MO. To force-synchronise Omada users for the newly created organisation unit,
the `/sync/omada` endpoint can be used.

### HTTP API
The following command is useful to force-synchronise all users from the Omada
API:
```
curl -X POST 'http://localhost:8000/sync/omada'
```
or a subset of users:
```
curl -X POST --get 'http://localhost:8000/sync/omada' --data-urlencode "omada_filter=EMAIL eq 'foo@example.com'"
```

The following can be used to retrieve a list of users from the Omada API:
```
curl --get 'http://localhost:8000/get-users' --data-urlencode "omada_filter=EMAIL eq 'foo@example.com'"
```

A common error is users in the Omada view which do not have one of the required
fields in the model, e.g. CPR-number. Empty fields are (often) represented by
an empty string in the Omada view, so these users can be found using:
```
curl --get 'http://localhost:8000/get-users' --data-urlencode "omada_filter=C_CPRNUMBER eq ''"
```
The field `C_CPRNUMBER` is customer-specific; see `sync/*/models.py`.


## Versioning
This project uses [Semantic Versioning](https://semver.org/) with the following
strategy:
- MAJOR: Incompatible API changes.
- MINOR: Backwards-compatible updates and functionality.
- PATCH: Backwards-compatible bug fixes.


## Authors
Magenta ApS <https://magenta.dk>


## License
- This project: [MPL-2.0](LICENSES/MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing. All licenses can be found in the [LICENSES folder](LICENSES/) of the project.
