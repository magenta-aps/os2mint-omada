# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import unittest
from dataclasses import dataclass
from dataclasses import field
from dataclasses import InitVar
from datetime import date
from datetime import datetime
from typing import ClassVar
from typing import Dict
from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import Union
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4
from uuid import uuid5

import pytest
from freezegun import freeze_time
from ramodels.mo import MOBase
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Validity
from ramodels.mo.details import Address
from ramodels.mo.details import ITSystemBinding

from os2mint_omada import sync
from os2mint_omada.omada import OmadaITUser
from tests.conftest import IT_SYSTEM_UUID


def without_uuid(model: MOBase) -> MOBase:
    """
    Strip MO Model UUID attribute to help comparison.
    """
    return model.copy(update=dict(uuid=None))


@pytest.fixture(autouse=True)
def frozen_datetime() -> Iterator[datetime]:
    with freeze_time("2021-11-12 13:14:15") as frozen_datetime:
        yield frozen_datetime()


@dataclass
class TestUser:
    name: str

    mo_uuid: UUID = field(default_factory=uuid4)
    mo_addresses: Dict[str, Address] = field(default_factory=dict)
    mo_it_system_binding: Optional[ITSystemBinding] = None
    omada_it_user: Optional[OmadaITUser] = None

    # Init vars
    create_mo_it_system_binding: InitVar[bool] = False
    omada_it_user_fields: InitVar[Optional[Dict[str, str]]] = None
    mo_address_fields: InitVar[Optional[Dict[str, str]]] = None

    address_classes: ClassVar[Dict[str, UUID]] = {
        "EmailEmployee": uuid4(),
        "PhoneEmployee": uuid4(),
        "MobilePhoneEmployee": uuid4(),
        "InstitutionPhoneEmployee": uuid4(),
    }

    def __post_init__(
        self,
        create_mo_it_system_binding: bool,
        omada_it_user_fields: Optional[Dict[str, str]],
        mo_address_fields: Optional[Dict[str, str]],
    ) -> None:
        if create_mo_it_system_binding:
            self.mo_it_system_binding = self.get_mo_it_system_binding()
        if omada_it_user_fields is not None:
            self.omada_it_user = self.get_omada_it_user(omada_it_user_fields)
        if mo_address_fields is not None:
            self.mo_addresses = self.get_mo_addresses(mo_address_fields)

    @property
    def c_objectguid_i_ad(self) -> UUID:
        return uuid5(self.mo_uuid, "C_OBJECTGUID_I_AD")

    def get_mo_it_system_binding(
        self,
        from_date: Union[date, str] = date(1991, 2, 3),
        to_date: Optional[Union[date, str]] = None,
    ) -> ITSystemBinding:
        return ITSystemBinding(
            uuid=uuid5(self.mo_uuid, "ITSystemBinding"),
            user_key=str(self.c_objectguid_i_ad),
            itsystem=ITSystemRef(uuid=IT_SYSTEM_UUID),
            person=PersonRef(uuid=self.mo_uuid),
            validity=Validity(
                from_date=from_date,
                to_date=to_date,
            ),
        )

    def get_omada_it_user(self, omada_it_user_fields: Dict[str, str]) -> OmadaITUser:
        return OmadaITUser(
            C_TJENESTENR=f"#{self.name}",
            C_OBJECTGUID_I_AD=self.c_objectguid_i_ad,
            C_LOGIN=omada_it_user_fields.get("C_LOGIN", ""),
            EMAIL=omada_it_user_fields.get("EMAIL", ""),
            C_DIREKTE_TLF=omada_it_user_fields.get("C_DIREKTE_TLF", ""),
            CELLPHONE=omada_it_user_fields.get("CELLPHONE", ""),
            C_INST_PHONE=omada_it_user_fields.get("C_INST_PHONE", ""),
        )

    def get_mo_addresses(
        self,
        mo_address_fields: Dict[str, str],
        from_date: Union[date, str] = date(1991, 2, 3),
        to_date: Optional[Union[date, str]] = None,
    ) -> Dict[str, Address]:
        return {
            user_key: Address(
                uuid=uuid5(self.mo_uuid, f"Address-{user_key}"),
                address_type=AddressType(uuid=self.address_classes[user_key]),
                value=value,
                person=PersonRef(uuid=self.mo_uuid),
                validity=Validity(
                    from_date=from_date,
                    to_date=to_date,
                ),
            )
            for user_key, value in mo_address_fields.items()
        }

    @property
    def sync_user(self) -> sync.User:
        return sync.User(
            omada_it_user=self.omada_it_user,
            mo_it_system_binding=self.mo_it_system_binding,
            mo_addresses=self.mo_addresses,
            mo_person_uuid=self.mo_uuid,
        )


@pytest.fixture
def carol_create() -> TestUser:
    # Exists only in Omada => should create
    return TestUser(
        name="Carol Create",
        create_mo_it_system_binding=False,
        omada_it_user_fields={
            "EMAIL": "carol@example.org",
            "C_DIREKTE_TLF": "+45 12 34 56 78",
        },
        mo_address_fields=None,
    )


@pytest.fixture
def dave_delete() -> TestUser:
    # Exists only in MO => should delete
    return TestUser(
        name="Dave Delete",
        create_mo_it_system_binding=True,
        omada_it_user_fields=None,
        mo_address_fields={
            "PhoneEmployee": "delete",
            "InstitutionPhoneEmployee": "me",
        },
    )


@pytest.fixture
def eve_exist() -> TestUser:
    # Exists in both with up-to-date date => should do nothing
    return TestUser(
        name="Eve Exist",
        create_mo_it_system_binding=True,
        omada_it_user_fields={
            "EMAIL": "eve@example.org",
            "CELLPHONE": "+45 00 00 00 01",
        },
        mo_address_fields={
            "EmailEmployee": "eve@example.org",
            "MobilePhoneEmployee": "+45 00 00 00 01",
        },
    )


@pytest.fixture
def erin_exist() -> TestUser:
    # Exists in both with no relevance to Omada => should do nothing
    return TestUser(
        name="Erin Exist",
        create_mo_it_system_binding=False,
        omada_it_user_fields=None,
        mo_address_fields=None,
    )


@pytest.fixture
def oscar_update() -> TestUser:
    # Exists in both, but outdated in MO => should update MO
    return TestUser(
        name="Oscar Update",
        create_mo_it_system_binding=True,
        omada_it_user_fields={
            "EMAIL": "oscar@example.org",
            "CELLPHONE": "+45 11 22 33 44",
            "C_DIREKTE_TLF": "+45 66 77 88 99",
        },
        mo_address_fields={
            "EmailEmployee": "WRONG-OSCAR@example.org",
            "MobilePhoneEmployee": "+45 11 22 33 44",
            "InstitutionPhoneEmployee": "+45 55 55 55 55",
        },
    )


@pytest.fixture
def test_users(
    carol_create: TestUser,
    dave_delete: TestUser,
    erin_exist: TestUser,
    eve_exist: TestUser,
    oscar_update: TestUser,
) -> Tuple[TestUser, ...]:
    return carol_create, dave_delete, erin_exist, eve_exist, oscar_update


@pytest.fixture
def mo_it_bindings(
    test_users: Tuple[TestUser, ...], it_system_uuid: UUID
) -> Dict[UUID, ITSystemBinding]:
    """
    Returns: Dictionary mapping binding person UUIDs into MO ITSystemBinding objects.
    """
    return {
        user.mo_it_system_binding.person.uuid: user.mo_it_system_binding
        for user in test_users
        if user.mo_it_system_binding is not None
    }


@pytest.fixture
def omada_it_users(test_users: Tuple[TestUser, ...]) -> Dict[str, OmadaITUser]:
    """
    Returns: Dictionary mapping 'TJENESTENR' service numbers to Omada IT user objects.
    """
    return {
        user.omada_it_user.C_TJENESTENR: user.omada_it_user
        for user in test_users
        if user.omada_it_user is not None
    }


@pytest.fixture
def mo_user_addresses(
    test_users: Tuple[TestUser, ...]
) -> Dict[UUID, Dict[str, Address]]:
    """
    Returns: Dictionary mapping user person UUIDs to a dictionary of MO Addresses
             indexed by user_key.
    """
    return {
        user.mo_uuid: {
            address_user_key: address
            for address_user_key, address in user.mo_addresses.items()
        }
        for user in test_users
        if user.mo_addresses
    }


@pytest.fixture
def service_number_to_person(test_users: Tuple[TestUser, ...]) -> Dict[str, UUID]:
    """
    Returns: Dictionary mapping Omada 'TJENESTENR' to MO person UUIDs.
    """
    return {
        user.omada_it_user.C_TJENESTENR: user.mo_uuid
        for user in test_users
        if user.omada_it_user is not None
    }


@pytest.fixture
def address_classes() -> Dict[str, UUID]:
    """
    Returns: Dictionary mapping address class user keys into their UUIDs.
    """
    return TestUser.address_classes


def test_get_updated_mo_objects(
    test_users: Tuple[TestUser, ...],
    carol_create: TestUser,
    dave_delete: TestUser,
    erin_exist: TestUser,
    eve_exist: TestUser,
    oscar_update: TestUser,
    mo_it_bindings: Dict[UUID, ITSystemBinding],
    omada_it_users: Dict[str, OmadaITUser],
    mo_user_addresses: Dict[UUID, Dict[str, Address]],
    service_number_to_person: Dict[str, UUID],
    it_system_uuid: UUID,
    address_classes: Dict[str, UUID],
) -> None:
    with patch("os2mint_omada.sync.update") as update_mock:
        updated_objects = sync.get_updated_mo_objects(
            mo_it_bindings=mo_it_bindings,
            omada_it_users=omada_it_users,
            mo_user_addresses=mo_user_addresses,
            service_number_to_person=service_number_to_person,
            address_classes=address_classes,
            it_system_uuid=it_system_uuid,
        )
        list(updated_objects)  # force execution of lazy 'yield from update(...)'

    expected_call_users = [
        carol_create.sync_user,
        dave_delete.sync_user,
        eve_exist.sync_user,
        oscar_update.sync_user,
    ]
    actual_call_users = [ca.kwargs["user"] for ca in update_mock.call_args_list]
    unittest.TestCase().assertCountEqual(actual_call_users, expected_call_users)


def test_update_carol_create(
    frozen_datetime: datetime,
    carol_create: TestUser,
    it_system_uuid: UUID,
    address_classes: Dict[str, UUID],
) -> None:
    # Exists only in Omada => should create
    actual_binding, actual_address_1, actual_address_2 = sync.update(
        user=carol_create.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert isinstance(actual_binding, ITSystemBinding)
    expected_binding = carol_create.get_mo_it_system_binding(
        from_date=frozen_datetime.date()
    )
    # Strip UUIDs as they are (very) unlikely to be equal on create
    assert without_uuid(actual_binding) == without_uuid(expected_binding)

    assert isinstance(actual_address_1, Address)
    assert isinstance(actual_address_2, Address)
    expected_addresses = carol_create.get_mo_addresses(
        mo_address_fields={
            "EmailEmployee": "carol@example.org",
            "PhoneEmployee": "+45 12 34 56 78",
        },
        from_date=frozen_datetime.date(),
    )

    actual = [without_uuid(actual_address_1), without_uuid(actual_address_2)]
    expected = [without_uuid(a) for a in expected_addresses.values()]
    assert actual == expected


def test_update_dave_delete(
    frozen_datetime: datetime,
    dave_delete: TestUser,
    it_system_uuid: UUID,
    address_classes: Dict[str, UUID],
) -> None:
    # Exists only in MO => should delete
    actual_binding, actual_address_1, actual_address_2 = sync.update(
        user=dave_delete.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert isinstance(actual_binding, ITSystemBinding)
    expected_binding = dave_delete.get_mo_it_system_binding(
        to_date=frozen_datetime.date()
    )
    assert actual_binding == expected_binding

    assert isinstance(actual_address_1, Address)
    assert isinstance(actual_address_2, Address)
    expected_addresses = dave_delete.get_mo_addresses(
        mo_address_fields={
            "PhoneEmployee": "delete",
            "InstitutionPhoneEmployee": "me",
        },
        to_date=frozen_datetime.date(),
    )
    assert [actual_address_1, actual_address_2] == list(expected_addresses.values())


def test_update_eve_exist(
    frozen_datetime: datetime,
    eve_exist: TestUser,
    it_system_uuid: UUID,
    address_classes: Dict[str, UUID],
) -> None:
    # Exists in both with up-to-date date => should do nothing
    updated_objects = sync.update(
        user=eve_exist.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert list(updated_objects) == []


def test_update_oscar_update(
    frozen_datetime: datetime,
    oscar_update: TestUser,
    it_system_uuid: UUID,
    address_classes: Dict[str, UUID],
) -> None:
    actual_address_1, actual_address_2, actual_address_3 = sync.update(
        user=oscar_update.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert isinstance(actual_address_1, Address)
    assert isinstance(actual_address_2, Address)
    assert isinstance(actual_address_3, Address)

    expected_update = oscar_update.get_mo_addresses(
        mo_address_fields={
            "EmailEmployee": "oscar@example.org",
        },
        from_date=frozen_datetime.date(),
    )["EmailEmployee"]
    assert actual_address_1 == expected_update

    expected_create = oscar_update.get_mo_addresses(
        mo_address_fields={
            "PhoneEmployee": "+45 66 77 88 99",
        },
        from_date=frozen_datetime.date(),
    )["PhoneEmployee"]
    # Strip UUIDs as they are (very) unlikely to be equal on create
    assert without_uuid(actual_address_2) == without_uuid(expected_create)

    expected_delete = oscar_update.get_mo_addresses(
        mo_address_fields={
            "InstitutionPhoneEmployee": "+45 55 55 55 55",
        },
        to_date=frozen_datetime.date(),
    )["InstitutionPhoneEmployee"]
    assert actual_address_3 == expected_delete
