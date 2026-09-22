# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import re

from os2mint_omada.omada.models import OmadaEventSubject
from os2mint_omada.omada.models import OmadaUser
from os2mint_omada.sync.models import CPR_INCL_FICTIVE_REGEX


def build_omada_subject(omada_user: OmadaUser, cpr_key: str) -> OmadaEventSubject:
    """Build the Omada event subject for a user.

    The CPR-number is read from the customer-specific field named by cpr_key,
    normalised (dashes stripped), and omitted if missing or invalid.
    """
    cpr = getattr(omada_user, cpr_key, None)
    cpr = cpr.replace("-", "") if isinstance(cpr, str) else None
    if not (cpr and re.match(CPR_INCL_FICTIVE_REGEX, cpr)):
        cpr = None
    return OmadaEventSubject(id=omada_user.id, cpr=cpr)
