CHANGELOG
=========

3.0.0 - 2022-12-21
------------------

[#53756] Omada OIDC support

2.0.0 - 2022-12-06
------------------

[#53756] Omada OIDC support

1.10.6 - 2022-11-24
-------------------

[#53629] Use address visibility 'Public' instead of 'Internal'

1.10.5 - 2022-11-21
-------------------

[#53602] Bump graphql to v3

1.10.4 - 2022-11-08
-------------------

[#52084] Fix support for multiple Employee states

1.10.3 - 2022-11-04
-------------------

[#52084] Add support for multiple Employee states

1.10.2 - 2022-11-03
-------------------

[#52084] Fix only error

1.10.1 - 2022-11-03
-------------------

[#52084] Fix one error

1.10.0 - 2022-11-01
-------------------

[#53184] Operate on full MO history, instead of just the present

Omada already provides temporality through its 'VALIDFROM' and 'VALIDTO' fields, so all of an object's validity intervals should be synchronised; operating only on the latest/present one is insufficient.

1.9.0 - 2022-10-18
------------------

[#52084] Add feature flag to disallow modification of existing (manual) employees in MO

1.8.0 - 2022-10-18
------------------

[#52084] Revert "[#49604] Ignore failed engagements"

1.7.0 - 2022-10-13
------------------

[#52084] Allow force-synchronising a subset of MO users

1.6.8 - 2022-10-12
------------------

[#52084] More logging
[#52084] Update RAMQP to fix issue with sleep_on_error

1.6.7 - 2022-10-04
------------------

[#52332] Move sleep_on_errors util to ramqp

1.6.6 - 2022-10-04
------------------

[#52332] Chill prefetch count

1.6.5 - 2022-09-23
------------------

[#51949] Sleep on errors to avoid race-conditions
[#51949] Replace with_concurrency with RAMQP prefetch limit

1.6.4 - 2022-09-10
------------------

[#52084] Fix ModelClient.post()

1.6.3 - 2022-09-10
------------------

[#52084] Update dependencies

Fixes validation error for Engagement "none is not an allowed value for 'primary'"

1.6.2 - 2022-08-19
------------------

[#49604] Properly assume CPR numbers are unique

1.6.1 - 2022-08-18
------------------

[#51893] Allow non-string filters in Omada API calls

1.6.0 - 2022-08-18
------------------

[#51893] Add support for user visibility ("C_SYNLIG_I_OS2MO")

1.5.1 - 2022-08-17
------------------

[#51802] Add exclusivity to synchronisation handlers to avoid race conditions

1.5.0 - 2022-08-15
------------------

[#51786] Add endpoint to manually sync Omada user(s)
[#49604] Only allow KeyErrors for failed engagements
[#51786] Omada RoutingKey WILDCARD

1.4.0 - 2022-07-26
------------------

[#49604] Revert "Bump AMQP concurrency to 5"
[#49604] Ignore failed engagements

1.3.5 - 2022-07-26
------------------

[#49604] Bump AMQP concurrency to 5

1.3.4 - 2022-07-26
------------------

[#49604] Proper validity union/intersection

1.3.3 - 2022-07-25
------------------

[#49604] Clamp engagement validity range to org unit's

1.3.2 - 2022-07-22
------------------

[#49604] Proper ridiculous timeout

1.3.1 - 2022-07-22
------------------

[#49604] Ridiculous timeout until MO supports pagination/streaming

1.3.0 - 2022-07-21
------------------

[#49604] Add force-sync endpoint

1.2.1 - 2022-07-21
------------------

[#49604] Prefer parsing to ManualOmadaUser if possible

1.2.0 - 2022-07-21
------------------

[#49604] Omada 1.2

1.1.3 - 2022-07-19
------------------

[#49604] Bump ramodels for more relaxed Employee CPR checking

1.1.2 - 2022-07-18
------------------

[#49604] SERIALIZE EVERYTHING

1.1.1 - 2022-07-15
------------------

[#49604] SERIALIZE UUIDS

1.1.0 - 2022-07-15
------------------

[#49604] Fix EmployeeData parsing
[#49604] Terminate using the service API
[#51523] Temporary fix: The GraphQL API always returns an org unit when querying uuids
[#49604] Fix wrongly assuming all other users for a manual user were also manual

1.0.2 - 2022-07-14
------------------

[#49604] Fix EmployeeData parsing

1.0.1 - 2022-07-13
------------------

[#49604] Remove nested settings factory
[#49604] Fix Omada pseudo infinity
[#49604] Remove visibility

1.0.0 - 2022-07-13
------------------

[#49604] Omada AMQP

0.4.4 - 2022-02-25
------------------

[#48572] Add missing await

0.4.3 - 2022-02-25
------------------

[#48572] Increase logging

0.4.2 - 2022-02-25
------------------

[#48572] Update ModelClient

0.4.1 - 2022-01-24
------------------

[#47972] Update httpx-ntlm dependency to upstream version from PyPI

0.4.0 - 2022-01-19
------------------

[#47972] Add support for NTLM authentication

0.3.1 - 2021-12-08
------------------

[#47404] Changed uvicorn port to 8080

0.3.0 - 2021-12-07
------------------

[#47452] API lock on endpoint

0.2.1 - 2021-12-06
------------------

[#46555] Use Python 3.9

0.2.0 - 2021-12-03
------------------

[#47447] Kubernetes readiness probe

0.1.5 - 2021-12-03
------------------

[#47423] Create addresses with 'Intern' visibility

0.1.4 - 2021-12-02
------------------

[#47348] Pull data synchronously to avoid overloading MO/LoRa 🥲
[#47348] Ignore Omada users without 'C_OBJECTGUID_I_AD'
[#47348] Ignore non-MO-compliant phone numbers

0.1.3 - 2021-12-01
------------------

[#42613] Actually fix autopub

0.1.2 - 2021-12-01
------------------

[#42613] Fix autopub
