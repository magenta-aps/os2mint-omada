# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import itertools
import unittest
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from typing import ClassVar
from typing import Optional
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
    return model.copy(update=dict(uuid=None, user_key=None))


@pytest.fixture(autouse=True)
def frozen_datetime() -> Iterator[datetime]:
    with freeze_time("2021-11-12 13:14:15") as frozen_datetime:
        yield frozen_datetime()


@dataclass
class TestUser:
    name: str

    mo_uuid: UUID = field(default_factory=uuid4)
    mo_addresses: dict[str, list[Address]] = field(default_factory=dict)
    mo_it_system_binding: Optional[ITSystemBinding] = None
    mo_engagement = True
    omada_it_user: Optional[OmadaITUser] = None

    address_classes: ClassVar[dict[str, UUID]] = {
        "EmailEmployee": uuid4(),
        "PhoneEmployee": uuid4(),
        "MobilePhoneEmployee": uuid4(),
        "InstitutionPhoneEmployee": uuid4(),
        "UnrelatedAddressEmployee": uuid4(),
    }

    @property
    def ad_guid(self) -> UUID:
        return uuid5(self.mo_uuid, "C_OBJECTGUID_I_AD")

    @property
    def service_number(self) -> str:
        return f"#{self.name}"

    def get_mo_it_system_binding(
        self,
        from_date: Union[date, str] = date(1991, 2, 3),
        to_date: Optional[Union[date, str]] = None,
    ) -> ITSystemBinding:
        return ITSystemBinding(
            uuid=uuid5(self.mo_uuid, "ITSystemBinding"),
            user_key=str(self.ad_guid),
            itsystem=ITSystemRef(uuid=IT_SYSTEM_UUID),
            person=PersonRef(uuid=self.mo_uuid),
            validity=Validity(from_date=from_date, to_date=to_date),
        )

    def get_omada_it_user(self, **kwargs: str) -> OmadaITUser:
        return OmadaITUser(
            service_number=self.service_number,
            ad_guid=self.ad_guid,
            login=kwargs.get("C_LOGIN", ""),
            email=kwargs.get("EMAIL", ""),
            phone_direct=kwargs.get("C_DIREKTE_TLF", ""),
            phone_cell=kwargs.get("CELLPHONE", ""),
            phone_institution=kwargs.get("C_INST_PHONE", ""),
        )

    def get_mo_addresses(
        self,
        from_date: Union[date, str] = date(1991, 2, 3),
        to_date: Optional[Union[date, str]] = None,
        **kwargs: list[str],
    ) -> dict[str, list[Address]]:
        return {
            user_key: [
                Address(
                    uuid=uuid5(self.mo_uuid, f"Address-{user_key}"),
                    address_type=AddressType(uuid=self.address_classes[user_key]),
                    value=value,
                    person=PersonRef(uuid=self.mo_uuid),
                    validity=Validity(from_date=from_date, to_date=to_date),
                )
                for value in values
            ]
            for user_key, values in kwargs.items()
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
    user = TestUser(name="Carol Create")
    user.omada_it_user = user.get_omada_it_user(
        EMAIL="carol@example.org",
        C_DIREKTE_TLF="12345678",
    )
    user.mo_addresses = user.get_mo_addresses(
        UnrelatedAddressEmployee=["Can't touch this!", "or this!"],
    )
    return user


@pytest.fixture
def dave_delete() -> TestUser:
    # Exists only in MO => should delete
    user = TestUser(name="Dave Delete")
    user.mo_it_system_binding = user.get_mo_it_system_binding()
    user.mo_addresses = user.get_mo_addresses(
        PhoneEmployee=["delete"],
        InstitutionPhoneEmployee=["me", "please"],
        UnrelatedAddressEmployee=["but not me", "or me"],
    )
    return user


@pytest.fixture
def eve_exist() -> TestUser:
    # Exists in both with up-to-date date data => should do nothing
    user = TestUser(name="Eve Exist")
    user.mo_it_system_binding = user.get_mo_it_system_binding()
    user.omada_it_user = user.get_omada_it_user(
        EMAIL="eve@example.org",
        CELLPHONE="00000001",
    )
    user.mo_addresses = user.get_mo_addresses(
        EmailEmployee=["eve@example.org"],
        MobilePhoneEmployee=["00000001"],
        UnrelatedAddressEmployee=["whatever", "dude"],
    )
    return user


@pytest.fixture
def erin_exist() -> TestUser:
    # Exists in both, but no MO engagement => should do nothing
    user = TestUser(name="Erin Exist")
    user.mo_engagement = False
    user.omada_it_user = user.get_omada_it_user(
        EMAIL="erin@example.org",
    )
    user.mo_addresses = user.get_mo_addresses(
        EmailEmployee=["erin@example.org"],
    )
    return user


@pytest.fixture
def oscar_update() -> TestUser:
    # Exists in both, but outdated in MO => should update MO
    user = TestUser(name="Oscar Update")
    user.mo_it_system_binding = user.get_mo_it_system_binding()
    user.omada_it_user = user.get_omada_it_user(
        EMAIL="oscar@example.org",
        CELLPHONE="11223344",
        C_DIREKTE_TLF="66778899",
    )
    user.mo_addresses = user.get_mo_addresses(
        EmailEmployee=["WRONG-OSCAR@example.org", "EXTRA-OSCAR@example.org"],
        MobilePhoneEmployee=["11223344", "11111111111"],
        InstitutionPhoneEmployee=["55555555"],
        UnrelatedAddressEmployee=["Can't touch this!"],
    )

    return user


@pytest.fixture
def test_users(
    carol_create: TestUser,
    dave_delete: TestUser,
    erin_exist: TestUser,
    eve_exist: TestUser,
    oscar_update: TestUser,
) -> tuple[TestUser, ...]:
    return carol_create, dave_delete, erin_exist, eve_exist, oscar_update


@pytest.fixture
def mo_it_bindings(
    test_users: tuple[TestUser, ...], it_system_uuid: UUID
) -> dict[UUID, ITSystemBinding]:
    """
    Returns: Dictionary mapping binding person UUIDs into MO ITSystemBinding objects.
    """
    return {
        user.mo_it_system_binding.person.uuid: user.mo_it_system_binding
        for user in test_users
        if user.mo_it_system_binding is not None
    }


@pytest.fixture
def omada_it_users(test_users: tuple[TestUser, ...]) -> list[OmadaITUser]:
    """
    Returns: Dictionary mapping ' service numbers to Omada IT user objects.
    """
    return [user.omada_it_user for user in test_users if user.omada_it_user is not None]


@pytest.fixture
def mo_user_addresses(
    test_users: tuple[TestUser, ...]
) -> dict[UUID, dict[str, list[Address]]]:
    """
    Returns: Dictionary mapping person UUIDs to a dictionary of lists of their MO
     adresses, indexed by its user key.
    """
    return {user.mo_uuid: user.mo_addresses for user in test_users if user.mo_addresses}


@pytest.fixture
def mo_engagements(test_users: tuple[TestUser, ...]) -> list[dict]:
    """
    Returns: List of MO engagement dicts.
    """
    return [
        {
            "user_key": u.service_number,
            "person": {"uuid": str(u.mo_uuid)},
        }
        for u in test_users
        if u.mo_engagement
    ]


@pytest.fixture
def address_classes() -> dict[str, UUID]:
    """
    Returns: Dictionary mapping address class user keys into their UUIDs.
    """
    return TestUser.address_classes


def test_get_updated_mo_objects(
    test_users: tuple[TestUser, ...],
    carol_create: TestUser,
    dave_delete: TestUser,
    erin_exist: TestUser,
    eve_exist: TestUser,
    oscar_update: TestUser,
    mo_it_bindings: dict[UUID, ITSystemBinding],
    omada_it_users: list[OmadaITUser],
    mo_user_addresses: dict[UUID, dict[str, list[Address]]],
    mo_engagements: list[dict],
    it_system_uuid: UUID,
    address_classes: dict[str, UUID],
) -> None:
    with patch("os2mint_omada.sync._updated_mo_objects") as update_mock:
        updated_objects = sync.get_updated_mo_objects(
            mo_it_bindings=mo_it_bindings,
            omada_it_users=omada_it_users,
            mo_user_addresses=mo_user_addresses,
            mo_engagements=mo_engagements,
            address_class_uuids=address_classes,
            it_system_uuid=it_system_uuid,
        )
        list(updated_objects)  # force execution of lazy 'yield from'

    expected_call_users = [
        carol_create.sync_user,
        dave_delete.sync_user,
        eve_exist.sync_user,
        oscar_update.sync_user,
    ]
    actual_call_users = [c.kwargs["user"] for c in update_mock.call_args_list]
    unittest.TestCase().assertCountEqual(actual_call_users, expected_call_users)


def test_update_carol_create(
    frozen_datetime: datetime,
    carol_create: TestUser,
    it_system_uuid: UUID,
    address_classes: dict[str, UUID],
) -> None:
    # Exists only in Omada => should create
    actual_binding, actual_address_1, actual_address_2 = sync._updated_mo_objects(
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
        EmailEmployee=["carol@example.org"],
        PhoneEmployee=["12345678"],
        from_date=frozen_datetime.date(),
    )
    actual = [without_uuid(actual_address_1), without_uuid(actual_address_2)]
    expected = [
        without_uuid(a)
        for a in itertools.chain.from_iterable(expected_addresses.values())
    ]
    assert actual == expected


def test_update_dave_delete(
    frozen_datetime: datetime,
    dave_delete: TestUser,
    it_system_uuid: UUID,
    address_classes: dict[str, UUID],
) -> None:
    # Exists only in MO => should delete
    (
        actual_binding,
        actual_address_1,
        actual_address_2,
        actual_address_3,
    ) = sync._updated_mo_objects(
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
    assert isinstance(actual_address_3, Address)
    expected_addresses = dave_delete.get_mo_addresses(
        PhoneEmployee=["delete"],
        InstitutionPhoneEmployee=["me", "please"],
        to_date=frozen_datetime.date(),
    )
    assert [
        [actual_address_2],
        [actual_address_3, actual_address_1],
    ] == list(expected_addresses.values())


def test_update_eve_exist(
    frozen_datetime: datetime,
    eve_exist: TestUser,
    it_system_uuid: UUID,
    address_classes: dict[str, UUID],
) -> None:
    # Exists in both with up-to-date date => should do nothing
    updated_objects = sync._updated_mo_objects(
        user=eve_exist.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert list(updated_objects) == []


def test_update_oscar_update(
    frozen_datetime: datetime,
    oscar_update: TestUser,
    it_system_uuid: UUID,
    address_classes: dict[str, UUID],
) -> None:
    (
        actual_address_1,
        actual_address_2,
        actual_address_3,
        actual_address_4,
        actual_address_5,
    ) = sync._updated_mo_objects(
        user=oscar_update.sync_user,
        it_system_uuid=it_system_uuid,
        address_class_uuids=address_classes,
    )
    assert isinstance(actual_address_1, Address)
    assert isinstance(actual_address_2, Address)
    assert isinstance(actual_address_3, Address)
    assert isinstance(actual_address_4, Address)
    assert isinstance(actual_address_5, Address)

    expected_create = oscar_update.get_mo_addresses(
        PhoneEmployee=["66778899"],
        from_date=frozen_datetime.date(),
    )
    # Strip UUIDs as they are (very) unlikely to be equal on create
    assert [without_uuid(actual_address_4)] == [
        without_uuid(a) for a in itertools.chain.from_iterable(expected_create.values())
    ]

    expected_update = oscar_update.get_mo_addresses(
        EmailEmployee=["oscar@example.org"],
        from_date=frozen_datetime.date(),
    )
    assert [[actual_address_3]] == list(expected_update.values())

    expected_delete = oscar_update.get_mo_addresses(
        EmailEmployee=["EXTRA-OSCAR@example.org"],
        MobilePhoneEmployee=["11111111111"],
        InstitutionPhoneEmployee=["55555555"],
        to_date=frozen_datetime.date(),
    )
    assert [
        [actual_address_1],
        [actual_address_2],
        [actual_address_5],
    ] == list(expected_delete.values())
