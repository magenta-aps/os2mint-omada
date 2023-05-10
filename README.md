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

The API can be viewed from the host through http://localhost:9000/.

After the initial import of Omada users, it can be useful to force-synchronise
information for already-existing MO users. This is done by executing the
following:
```commandline
curl -X POST http://localhost/sync/mo
```
The call returns immediately, but processing can take upwards of 12 hours to
complete. Alternatively, a subset of MO users can be synchronised as follows:
```commandline
curl -X POST http://localhost/sync/mo -H 'Content-Type: application/json' --data '["3fa85f64-5717-4562-b3fc-2c963f66afa6"]'
```

**NOTE** that MO organisation units are not watched for changes, so manual Omada
users, which should be inserted into a non-existent organisation unit will not
be synchronised automatically when (and if) this organisation unit is created in
MO. To force-synchronise Omada users for the newly created organisation unit,
the `/sync/omada` endpoint can be used.


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
