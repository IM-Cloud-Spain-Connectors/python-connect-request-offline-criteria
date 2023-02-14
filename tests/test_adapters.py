from unittest.mock import Mock

from connect.eaas.core.responses import ProcessingResponse
from rndi.connect.business_objects.adapters import Asset, Request
from rndi.connect.business_transaction_middleware.middleware import make_middleware_callstack
from rndi.connect.business_transactions.adapters import prepare
from rndi.connect.business_transactions.contracts import BackgroundTransaction
from rndi.connect.request_offline_criteria.adapters import DefaultOnMatchTransaction, OfflineCriteria
from rndi.connect.request_offline_criteria.rules import (
    composited_match_offline_asset_and_marketplace_parameter,
    match_offline_asset_parameter,
    match_offline_marketplace_parameter,
    match_request_type,
)


class CreateCustomer(BackgroundTransaction):
    def name(self) -> str:
        return 'Create Customer'

    def should_execute(self, request: dict) -> bool:
        return True

    def execute(self, request: dict) -> ProcessingResponse:
        assert request
        return ProcessingResponse.done()

    def compensate(self, request: dict, e: Exception) -> ProcessingResponse:
        return ProcessingResponse.done()


def test_offline_criteria_should_not_match_request_due_to_no_rules():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending') \
        .raw()

    offline = OfflineCriteria([])

    assert not offline.is_offline_enabled(request)


def test_offline_criteria_should_not_match_request():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('approved') \
        .raw()

    def match_request_is_pending(request: dict) -> bool:
        return request.get('status', 'pending') == 'pending'

    offline = OfflineCriteria([match_request_is_pending])

    assert not offline.is_offline_enabled(request)


def test_offline_criteria_should_match_request():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending') \
        .raw()

    def match_request_is_pending(request: dict) -> bool:
        return request.get('status', 'pending') == 'pending'

    offline = OfflineCriteria([match_request_is_pending])

    assert offline.is_offline_enabled(request)


def test_offline_criteria_should_match_request_and_execute_arbitrary_code_as_middleware():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending') \
        .raw()

    def match_request_is_pending(request: dict) -> bool:
        return request.get('status', 'pending') == 'pending'

    def on_match_assertion(request: dict) -> ProcessingResponse:
        assert request
        return ProcessingResponse.done()

    offline = OfflineCriteria([match_request_is_pending], on_match_assertion)
    transaction = prepare(CreateCustomer())
    transaction = make_middleware_callstack([offline], transaction)

    transaction(request)


def test_offline_criteria_should_match_request_and_not_execute_arbitrary_code_as_middleware():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending') \
        .raw()

    def match_request_is_pending(request: dict) -> bool:
        return request.get('status', 'pending') == 'pending'

    offline = OfflineCriteria([match_request_is_pending])
    transaction = prepare(CreateCustomer())
    transaction = make_middleware_callstack([offline], transaction)

    assert transaction(request).status == 'skip'


def test_offline_criteria_should_not_match_request_as_middleware():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('approved') \
        .raw()

    def match_request_is_pending(request: dict) -> bool:
        return request.get('status', 'pending') == 'pending'

    offline = OfflineCriteria([match_request_is_pending])
    transaction = prepare(CreateCustomer())
    transaction = make_middleware_callstack([offline], transaction)

    transaction(request)


def test_rule_match_request_type_should_match_request_correctly():
    request = Request()

    request.with_type('purchase')
    assert not match_request_type(request.raw())

    request.with_type('cancel')
    assert match_request_type(request.raw())

    request.with_type('suspend')
    assert match_request_type(request.raw())


def test_rule_match_offline_asset_parameter_should_match_request_correctly_from_asset():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending')

    assert not match_offline_asset_parameter(request.raw())

    asset = Asset() \
        .with_id('AS-0000-0000-0001') \
        .with_param('offline_mode', 'AS-0000-0000-0001', '', 'ordering')

    request.with_asset(asset)

    assert match_offline_asset_parameter(request.raw())


def test_rule_match_offline_asset_parameter_should_match_request_correctly_from_request():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending') \
        .with_param('offline_mode', 'AS-0000-0000-0001', '', 'ordering')

    assert not match_offline_asset_parameter(request.raw())

    asset = Asset() \
        .with_id('AS-0000-0000-0001')

    request.with_asset(asset)

    assert match_offline_asset_parameter(request.raw())


def test_rule_match_offline_marketplace_parameter_should_match_request_correctly():
    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('purchase') \
        .with_status('pending')

    asset = Asset() \
        .with_id('AS-0000-0000-0001')

    request.with_asset(asset)

    assert not match_offline_marketplace_parameter(request.raw())

    asset.with_configuration_param('offline_mode_list', [])
    request.with_asset(asset)

    assert not match_offline_marketplace_parameter(request.raw())

    asset.with_configuration_param('offline_mode_list', ['AS-0000-0000-0001'])
    request.with_asset(asset)

    assert match_offline_marketplace_parameter(request.raw())


def test_composited_match_offline_asset_and_marketplace_parameter_should_match_request_correctly():
    asset = Asset() \
        .with_id('AS-0000-0000-0001') \
        .with_configuration_param('offline_mode_list', ['AS-0000-0000-0001']) \
        .with_param('offline_mode', 'AS-0000-0000-0002', '', 'ordering')

    request = Request() \
        .with_id('PR-0000-0000-0001') \
        .with_type('cancel') \
        .with_status('pending') \
        .with_param('PARAM_CUSTOMER_ID', 'eda1b4f1-a3a8-4a87-bd3f-ad71f6c2e93e') \
        .with_param('offline_mode', 'AS-0000-0000-0002', '', 'ordering') \
        .with_asset(asset)

    assert composited_match_offline_asset_and_marketplace_parameter(request.raw())


def test_default_on_match_transaction_should_approve_given_request_successfully(sync_client_factory, response_factory):
    subscription_id = 'AS-8027-7606-7082'

    asset = Asset()
    asset.with_id(subscription_id)
    asset.with_status('active')

    request = Request()
    request.with_id('PR-8027-7606-7082-001')
    request.with_type('purchase')
    request.with_status('approved')
    request.with_asset(asset)

    activation_tpl = 'TL-662-440-096'

    def __logger_info(message: str):
        assert message == f"The subscription {subscription_id} is in offline mode."

    logger = Mock()
    logger.info = __logger_info

    client = sync_client_factory([
        response_factory(value=request.raw(), status=200),
    ])

    default_on_match = DefaultOnMatchTransaction(
        activation_tpl,
        client,
        logger,
    )

    asset = request.asset()
    asset.with_status('processing')

    request = Request()
    request.with_id('PR-8027-7606-7082-001')
    request.with_type('purchase')
    request.with_status('pending')
    request.with_asset(asset)

    response = default_on_match(request.raw())

    assert response.status == 'success'
