# Generated by ariadne-codegen on 2024-08-21 16:34

from ._testing__create_employee import TestingCreateEmployee
from ._testing__create_employee import TestingCreateEmployeeEmployeeCreate
from ._testing__create_org_unit import TestingCreateOrgUnit
from ._testing__create_org_unit import TestingCreateOrgUnitOrgUnitCreate
from ._testing__create_org_unit_it_user import TestingCreateOrgUnitItUser
from ._testing__create_org_unit_it_user import TestingCreateOrgUnitItUserItuserCreate
from ._testing__get_employee import TestingGetEmployee
from ._testing__get_employee import TestingGetEmployeeEmployees
from ._testing__get_employee import TestingGetEmployeeEmployeesObjects
from ._testing__get_employee import TestingGetEmployeeEmployeesObjectsObjects
from ._testing__get_employee import TestingGetEmployeeEmployeesObjectsObjectsAddresses
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsAddressesAddressType,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsAddressesEngagement,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsAddressesValidity,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsAddressesVisibility,
)
from ._testing__get_employee import TestingGetEmployeeEmployeesObjectsObjectsEngagements
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsEngagementsEngagementType,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsEngagementsJobFunction,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsEngagementsOrgUnit,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsEngagementsPrimary,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsEngagementsValidity,
)
from ._testing__get_employee import TestingGetEmployeeEmployeesObjectsObjectsItusers
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsItusersEngagement,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsItusersItsystem,
)
from ._testing__get_employee import (
    TestingGetEmployeeEmployeesObjectsObjectsItusersValidity,
)
from ._testing__get_employee import TestingGetEmployeeEmployeesObjectsObjectsValidity
from ._testing__get_it_system import TestingGetItSystem
from ._testing__get_it_system import TestingGetItSystemItsystems
from ._testing__get_it_system import TestingGetItSystemItsystemsObjects
from ._testing__get_org_unit_type import TestingGetOrgUnitType
from ._testing__get_org_unit_type import TestingGetOrgUnitTypeClasses
from ._testing__get_org_unit_type import TestingGetOrgUnitTypeClassesObjects
from .async_base_client import AsyncBaseClient
from .base_model import BaseModel
from .client import GraphQLClient
from .delete_address import DeleteAddress
from .delete_address import DeleteAddressAddressDelete
from .delete_engagement import DeleteEngagement
from .delete_engagement import DeleteEngagementEngagementDelete
from .delete_it_user import DeleteItUser
from .delete_it_user import DeleteItUserItuserDelete
from .enums import AuditLogModel
from .enums import FileStore
from .enums import OwnerInferencePriority
from .exceptions import GraphQLClientError
from .exceptions import GraphQLClientGraphQLError
from .exceptions import GraphQLClientGraphQLMultiError
from .exceptions import GraphQLClientHttpError
from .exceptions import GraphQlClientInvalidResponseError
from .get_classes import GetClasses
from .get_classes import GetClassesFacets
from .get_classes import GetClassesFacetsObjects
from .get_classes import GetClassesFacetsObjectsCurrent
from .get_classes import GetClassesFacetsObjectsCurrentClasses
from .get_current_employee_state import GetCurrentEmployeeState
from .get_current_employee_state import GetCurrentEmployeeStateEmployees
from .get_current_employee_state import GetCurrentEmployeeStateEmployeesObjects
from .get_current_employee_state import GetCurrentEmployeeStateEmployeesObjectsCurrent
from .get_employee_addresses import GetEmployeeAddresses
from .get_employee_addresses import GetEmployeeAddressesEmployees
from .get_employee_addresses import GetEmployeeAddressesEmployeesObjects
from .get_employee_addresses import GetEmployeeAddressesEmployeesObjectsObjects
from .get_employee_addresses import GetEmployeeAddressesEmployeesObjectsObjectsAddresses
from .get_employee_addresses import (
    GetEmployeeAddressesEmployeesObjectsObjectsAddressesAddressType,
)
from .get_employee_addresses import (
    GetEmployeeAddressesEmployeesObjectsObjectsAddressesEngagement,
)
from .get_employee_addresses import (
    GetEmployeeAddressesEmployeesObjectsObjectsAddressesPerson,
)
from .get_employee_addresses import (
    GetEmployeeAddressesEmployeesObjectsObjectsAddressesValidity,
)
from .get_employee_addresses import (
    GetEmployeeAddressesEmployeesObjectsObjectsAddressesVisibility,
)
from .get_employee_engagements import GetEmployeeEngagements
from .get_employee_engagements import GetEmployeeEngagementsEmployees
from .get_employee_engagements import GetEmployeeEngagementsEmployeesObjects
from .get_employee_engagements import GetEmployeeEngagementsEmployeesObjectsObjects
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagements,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsEngagementType,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsJobFunction,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsOrgUnit,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsPerson,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsPrimary,
)
from .get_employee_engagements import (
    GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsValidity,
)
from .get_employee_it_users import GetEmployeeItUsers
from .get_employee_it_users import GetEmployeeItUsersEmployees
from .get_employee_it_users import GetEmployeeItUsersEmployeesObjects
from .get_employee_it_users import GetEmployeeItUsersEmployeesObjectsObjects
from .get_employee_it_users import GetEmployeeItUsersEmployeesObjectsObjectsItusers
from .get_employee_it_users import (
    GetEmployeeItUsersEmployeesObjectsObjectsItusersEngagement,
)
from .get_employee_it_users import (
    GetEmployeeItUsersEmployeesObjectsObjectsItusersItsystem,
)
from .get_employee_it_users import (
    GetEmployeeItUsersEmployeesObjectsObjectsItusersPerson,
)
from .get_employee_it_users import (
    GetEmployeeItUsersEmployeesObjectsObjectsItusersValidity,
)
from .get_employee_states import GetEmployeeStates
from .get_employee_states import GetEmployeeStatesEmployees
from .get_employee_states import GetEmployeeStatesEmployeesObjects
from .get_employee_states import GetEmployeeStatesEmployeesObjectsObjects
from .get_employee_uuid_from_cpr import GetEmployeeUuidFromCpr
from .get_employee_uuid_from_cpr import GetEmployeeUuidFromCprEmployees
from .get_employee_uuid_from_cpr import GetEmployeeUuidFromCprEmployeesObjects
from .get_employee_uuid_from_user_key import GetEmployeeUuidFromUserKey
from .get_employee_uuid_from_user_key import GetEmployeeUuidFromUserKeyEngagements
from .get_employee_uuid_from_user_key import (
    GetEmployeeUuidFromUserKeyEngagementsObjects,
)
from .get_employee_uuid_from_user_key import (
    GetEmployeeUuidFromUserKeyEngagementsObjectsObjects,
)
from .get_employee_uuid_from_user_key import (
    GetEmployeeUuidFromUserKeyEngagementsObjectsObjectsPerson,
)
from .get_it_systems import GetItSystems
from .get_it_systems import GetItSystemsItsystems
from .get_it_systems import GetItSystemsItsystemsObjects
from .get_it_systems import GetItSystemsItsystemsObjectsCurrent
from .get_org_unit_validity import GetOrgUnitValidity
from .get_org_unit_validity import GetOrgUnitValidityOrgUnits
from .get_org_unit_validity import GetOrgUnitValidityOrgUnitsObjects
from .get_org_unit_validity import GetOrgUnitValidityOrgUnitsObjectsObjects
from .get_org_unit_validity import GetOrgUnitValidityOrgUnitsObjectsObjectsValidity
from .get_org_unit_with_it_system_user_key import GetOrgUnitWithItSystemUserKey
from .get_org_unit_with_it_system_user_key import GetOrgUnitWithItSystemUserKeyItusers
from .get_org_unit_with_it_system_user_key import (
    GetOrgUnitWithItSystemUserKeyItusersObjects,
)
from .get_org_unit_with_it_system_user_key import (
    GetOrgUnitWithItSystemUserKeyItusersObjectsObjects,
)
from .get_org_unit_with_it_system_user_key import (
    GetOrgUnitWithItSystemUserKeyItusersObjectsObjectsOrgUnit,
)
from .get_org_unit_with_user_key import GetOrgUnitWithUserKey
from .get_org_unit_with_user_key import GetOrgUnitWithUserKeyOrgUnits
from .get_org_unit_with_user_key import GetOrgUnitWithUserKeyOrgUnitsObjects
from .get_org_unit_with_uuid import GetOrgUnitWithUuid
from .get_org_unit_with_uuid import GetOrgUnitWithUuidOrgUnits
from .get_org_unit_with_uuid import GetOrgUnitWithUuidOrgUnitsObjects
from .input_types import AddressCreateInput
from .input_types import AddressFilter
from .input_types import AddressRegistrationFilter
from .input_types import AddressTerminateInput
from .input_types import AddressUpdateInput
from .input_types import AssociationCreateInput
from .input_types import AssociationFilter
from .input_types import AssociationRegistrationFilter
from .input_types import AssociationTerminateInput
from .input_types import AssociationUpdateInput
from .input_types import AuditLogFilter
from .input_types import ClassCreateInput
from .input_types import ClassFilter
from .input_types import ClassRegistrationFilter
from .input_types import ClassTerminateInput
from .input_types import ClassUpdateInput
from .input_types import ConfigurationFilter
from .input_types import EmployeeCreateInput
from .input_types import EmployeeFilter
from .input_types import EmployeeRegistrationFilter
from .input_types import EmployeesBoundAddressFilter
from .input_types import EmployeesBoundAssociationFilter
from .input_types import EmployeesBoundEngagementFilter
from .input_types import EmployeesBoundITUserFilter
from .input_types import EmployeesBoundLeaveFilter
from .input_types import EmployeesBoundManagerFilter
from .input_types import EmployeesBoundRoleFilter
from .input_types import EmployeeTerminateInput
from .input_types import EmployeeUpdateInput
from .input_types import EngagementCreateInput
from .input_types import EngagementFilter
from .input_types import EngagementRegistrationFilter
from .input_types import EngagementTerminateInput
from .input_types import EngagementUpdateInput
from .input_types import FacetCreateInput
from .input_types import FacetFilter
from .input_types import FacetRegistrationFilter
from .input_types import FacetsBoundClassFilter
from .input_types import FacetTerminateInput
from .input_types import FacetUpdateInput
from .input_types import FileFilter
from .input_types import HealthFilter
from .input_types import ITAssociationCreateInput
from .input_types import ITAssociationTerminateInput
from .input_types import ITAssociationUpdateInput
from .input_types import ITSystemCreateInput
from .input_types import ITSystemFilter
from .input_types import ITSystemRegistrationFilter
from .input_types import ITSystemTerminateInput
from .input_types import ITSystemUpdateInput
from .input_types import ITUserCreateInput
from .input_types import ITUserFilter
from .input_types import ITUserRegistrationFilter
from .input_types import ITUserTerminateInput
from .input_types import ITUserUpdateInput
from .input_types import KLECreateInput
from .input_types import KLEFilter
from .input_types import KLERegistrationFilter
from .input_types import KLETerminateInput
from .input_types import KLEUpdateInput
from .input_types import LeaveCreateInput
from .input_types import LeaveFilter
from .input_types import LeaveRegistrationFilter
from .input_types import LeaveTerminateInput
from .input_types import LeaveUpdateInput
from .input_types import ManagerCreateInput
from .input_types import ManagerFilter
from .input_types import ManagerRegistrationFilter
from .input_types import ManagerTerminateInput
from .input_types import ManagerUpdateInput
from .input_types import ModelsUuidsBoundRegistrationFilter
from .input_types import OrganisationCreate
from .input_types import OrganisationUnitCreateInput
from .input_types import OrganisationUnitFilter
from .input_types import OrganisationUnitRegistrationFilter
from .input_types import OrganisationUnitTerminateInput
from .input_types import OrganisationUnitUpdateInput
from .input_types import OrgUnitsboundaddressfilter
from .input_types import OrgUnitsboundassociationfilter
from .input_types import OrgUnitsboundengagementfilter
from .input_types import OrgUnitsboundituserfilter
from .input_types import OrgUnitsboundklefilter
from .input_types import OrgUnitsboundleavefilter
from .input_types import OrgUnitsboundownerfilter
from .input_types import OrgUnitsboundrelatedunitfilter
from .input_types import OrgUnitsboundrolefilter
from .input_types import OwnerCreateInput
from .input_types import OwnerFilter
from .input_types import OwnerTerminateInput
from .input_types import OwnerUpdateInput
from .input_types import ParentsBoundClassFilter
from .input_types import ParentsBoundFacetFilter
from .input_types import ParentsBoundOrganisationUnitFilter
from .input_types import RAOpenValidityInput
from .input_types import RAValidityInput
from .input_types import RegistrationFilter
from .input_types import RelatedUnitFilter
from .input_types import RelatedUnitsUpdateInput
from .input_types import RoleCreateInput
from .input_types import RoleFilter
from .input_types import RoleRegistrationFilter
from .input_types import RoleTerminateInput
from .input_types import RoleUpdateInput
from .input_types import UuidsBoundClassFilter
from .input_types import UuidsBoundEmployeeFilter
from .input_types import UuidsBoundEngagementFilter
from .input_types import UuidsBoundFacetFilter
from .input_types import UuidsBoundITSystemFilter
from .input_types import UuidsBoundITUserFilter
from .input_types import UuidsBoundLeaveFilter
from .input_types import UuidsBoundOrganisationUnitFilter
from .input_types import ValidityInput

__all__ = [
    "AddressCreateInput",
    "AddressFilter",
    "AddressRegistrationFilter",
    "AddressTerminateInput",
    "AddressUpdateInput",
    "AssociationCreateInput",
    "AssociationFilter",
    "AssociationRegistrationFilter",
    "AssociationTerminateInput",
    "AssociationUpdateInput",
    "AsyncBaseClient",
    "AuditLogFilter",
    "AuditLogModel",
    "BaseModel",
    "ClassCreateInput",
    "ClassFilter",
    "ClassRegistrationFilter",
    "ClassTerminateInput",
    "ClassUpdateInput",
    "ConfigurationFilter",
    "DeleteAddress",
    "DeleteAddressAddressDelete",
    "DeleteEngagement",
    "DeleteEngagementEngagementDelete",
    "DeleteItUser",
    "DeleteItUserItuserDelete",
    "EmployeeCreateInput",
    "EmployeeFilter",
    "EmployeeRegistrationFilter",
    "EmployeeTerminateInput",
    "EmployeeUpdateInput",
    "EmployeesBoundAddressFilter",
    "EmployeesBoundAssociationFilter",
    "EmployeesBoundEngagementFilter",
    "EmployeesBoundITUserFilter",
    "EmployeesBoundLeaveFilter",
    "EmployeesBoundManagerFilter",
    "EmployeesBoundRoleFilter",
    "EngagementCreateInput",
    "EngagementFilter",
    "EngagementRegistrationFilter",
    "EngagementTerminateInput",
    "EngagementUpdateInput",
    "FacetCreateInput",
    "FacetFilter",
    "FacetRegistrationFilter",
    "FacetTerminateInput",
    "FacetUpdateInput",
    "FacetsBoundClassFilter",
    "FileFilter",
    "FileStore",
    "GetClasses",
    "GetClassesFacets",
    "GetClassesFacetsObjects",
    "GetClassesFacetsObjectsCurrent",
    "GetClassesFacetsObjectsCurrentClasses",
    "GetCurrentEmployeeState",
    "GetCurrentEmployeeStateEmployees",
    "GetCurrentEmployeeStateEmployeesObjects",
    "GetCurrentEmployeeStateEmployeesObjectsCurrent",
    "GetEmployeeAddresses",
    "GetEmployeeAddressesEmployees",
    "GetEmployeeAddressesEmployeesObjects",
    "GetEmployeeAddressesEmployeesObjectsObjects",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddresses",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddressesAddressType",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddressesEngagement",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddressesPerson",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddressesValidity",
    "GetEmployeeAddressesEmployeesObjectsObjectsAddressesVisibility",
    "GetEmployeeEngagements",
    "GetEmployeeEngagementsEmployees",
    "GetEmployeeEngagementsEmployeesObjects",
    "GetEmployeeEngagementsEmployeesObjectsObjects",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagements",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsEngagementType",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsJobFunction",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsOrgUnit",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsPerson",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsPrimary",
    "GetEmployeeEngagementsEmployeesObjectsObjectsEngagementsValidity",
    "GetEmployeeItUsers",
    "GetEmployeeItUsersEmployees",
    "GetEmployeeItUsersEmployeesObjects",
    "GetEmployeeItUsersEmployeesObjectsObjects",
    "GetEmployeeItUsersEmployeesObjectsObjectsItusers",
    "GetEmployeeItUsersEmployeesObjectsObjectsItusersEngagement",
    "GetEmployeeItUsersEmployeesObjectsObjectsItusersItsystem",
    "GetEmployeeItUsersEmployeesObjectsObjectsItusersPerson",
    "GetEmployeeItUsersEmployeesObjectsObjectsItusersValidity",
    "GetEmployeeStates",
    "GetEmployeeStatesEmployees",
    "GetEmployeeStatesEmployeesObjects",
    "GetEmployeeStatesEmployeesObjectsObjects",
    "GetEmployeeUuidFromCpr",
    "GetEmployeeUuidFromCprEmployees",
    "GetEmployeeUuidFromCprEmployeesObjects",
    "GetEmployeeUuidFromUserKey",
    "GetEmployeeUuidFromUserKeyEngagements",
    "GetEmployeeUuidFromUserKeyEngagementsObjects",
    "GetEmployeeUuidFromUserKeyEngagementsObjectsObjects",
    "GetEmployeeUuidFromUserKeyEngagementsObjectsObjectsPerson",
    "GetItSystems",
    "GetItSystemsItsystems",
    "GetItSystemsItsystemsObjects",
    "GetItSystemsItsystemsObjectsCurrent",
    "GetOrgUnitValidity",
    "GetOrgUnitValidityOrgUnits",
    "GetOrgUnitValidityOrgUnitsObjects",
    "GetOrgUnitValidityOrgUnitsObjectsObjects",
    "GetOrgUnitValidityOrgUnitsObjectsObjectsValidity",
    "GetOrgUnitWithItSystemUserKey",
    "GetOrgUnitWithItSystemUserKeyItusers",
    "GetOrgUnitWithItSystemUserKeyItusersObjects",
    "GetOrgUnitWithItSystemUserKeyItusersObjectsObjects",
    "GetOrgUnitWithItSystemUserKeyItusersObjectsObjectsOrgUnit",
    "GetOrgUnitWithUserKey",
    "GetOrgUnitWithUserKeyOrgUnits",
    "GetOrgUnitWithUserKeyOrgUnitsObjects",
    "GetOrgUnitWithUuid",
    "GetOrgUnitWithUuidOrgUnits",
    "GetOrgUnitWithUuidOrgUnitsObjects",
    "GraphQLClient",
    "GraphQLClientError",
    "GraphQLClientGraphQLError",
    "GraphQLClientGraphQLMultiError",
    "GraphQLClientHttpError",
    "GraphQlClientInvalidResponseError",
    "HealthFilter",
    "ITAssociationCreateInput",
    "ITAssociationTerminateInput",
    "ITAssociationUpdateInput",
    "ITSystemCreateInput",
    "ITSystemFilter",
    "ITSystemRegistrationFilter",
    "ITSystemTerminateInput",
    "ITSystemUpdateInput",
    "ITUserCreateInput",
    "ITUserFilter",
    "ITUserRegistrationFilter",
    "ITUserTerminateInput",
    "ITUserUpdateInput",
    "KLECreateInput",
    "KLEFilter",
    "KLERegistrationFilter",
    "KLETerminateInput",
    "KLEUpdateInput",
    "LeaveCreateInput",
    "LeaveFilter",
    "LeaveRegistrationFilter",
    "LeaveTerminateInput",
    "LeaveUpdateInput",
    "ManagerCreateInput",
    "ManagerFilter",
    "ManagerRegistrationFilter",
    "ManagerTerminateInput",
    "ManagerUpdateInput",
    "ModelsUuidsBoundRegistrationFilter",
    "OrgUnitsboundaddressfilter",
    "OrgUnitsboundassociationfilter",
    "OrgUnitsboundengagementfilter",
    "OrgUnitsboundituserfilter",
    "OrgUnitsboundklefilter",
    "OrgUnitsboundleavefilter",
    "OrgUnitsboundownerfilter",
    "OrgUnitsboundrelatedunitfilter",
    "OrgUnitsboundrolefilter",
    "OrganisationCreate",
    "OrganisationUnitCreateInput",
    "OrganisationUnitFilter",
    "OrganisationUnitRegistrationFilter",
    "OrganisationUnitTerminateInput",
    "OrganisationUnitUpdateInput",
    "OwnerCreateInput",
    "OwnerFilter",
    "OwnerInferencePriority",
    "OwnerTerminateInput",
    "OwnerUpdateInput",
    "ParentsBoundClassFilter",
    "ParentsBoundFacetFilter",
    "ParentsBoundOrganisationUnitFilter",
    "RAOpenValidityInput",
    "RAValidityInput",
    "RegistrationFilter",
    "RelatedUnitFilter",
    "RelatedUnitsUpdateInput",
    "RoleCreateInput",
    "RoleFilter",
    "RoleRegistrationFilter",
    "RoleTerminateInput",
    "RoleUpdateInput",
    "TestingCreateEmployee",
    "TestingCreateEmployeeEmployeeCreate",
    "TestingCreateOrgUnit",
    "TestingCreateOrgUnitItUser",
    "TestingCreateOrgUnitItUserItuserCreate",
    "TestingCreateOrgUnitOrgUnitCreate",
    "TestingGetEmployee",
    "TestingGetEmployeeEmployees",
    "TestingGetEmployeeEmployeesObjects",
    "TestingGetEmployeeEmployeesObjectsObjects",
    "TestingGetEmployeeEmployeesObjectsObjectsAddresses",
    "TestingGetEmployeeEmployeesObjectsObjectsAddressesAddressType",
    "TestingGetEmployeeEmployeesObjectsObjectsAddressesEngagement",
    "TestingGetEmployeeEmployeesObjectsObjectsAddressesValidity",
    "TestingGetEmployeeEmployeesObjectsObjectsAddressesVisibility",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagements",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagementsEngagementType",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagementsJobFunction",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagementsOrgUnit",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagementsPrimary",
    "TestingGetEmployeeEmployeesObjectsObjectsEngagementsValidity",
    "TestingGetEmployeeEmployeesObjectsObjectsItusers",
    "TestingGetEmployeeEmployeesObjectsObjectsItusersEngagement",
    "TestingGetEmployeeEmployeesObjectsObjectsItusersItsystem",
    "TestingGetEmployeeEmployeesObjectsObjectsItusersValidity",
    "TestingGetEmployeeEmployeesObjectsObjectsValidity",
    "TestingGetItSystem",
    "TestingGetItSystemItsystems",
    "TestingGetItSystemItsystemsObjects",
    "TestingGetOrgUnitType",
    "TestingGetOrgUnitTypeClasses",
    "TestingGetOrgUnitTypeClassesObjects",
    "UuidsBoundClassFilter",
    "UuidsBoundEmployeeFilter",
    "UuidsBoundEngagementFilter",
    "UuidsBoundFacetFilter",
    "UuidsBoundITSystemFilter",
    "UuidsBoundITUserFilter",
    "UuidsBoundLeaveFilter",
    "UuidsBoundOrganisationUnitFilter",
    "ValidityInput",
]
