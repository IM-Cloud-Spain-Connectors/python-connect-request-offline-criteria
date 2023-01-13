#
# This file is part of the Ingram Micro CloudBlue RnD Integration Connectors SDK.
#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#
from rndi.connect.business_objects.adapters import Request
from rndi.connect.business_objects.exceptions import MissingParameterError

PARAM_OFFLINE_MODE_LIST = 'offline_mode_list'
PARAM_OFFLINE_MODE = 'offline_mode'


def match_request_type(request: dict) -> bool:
    return Request(request).type() in ['cancel', 'suspend']


def match_offline_asset_parameter(request: dict) -> bool:
    """
    Evaluate if the given connect request is in offline mode based on
    the offline_mode asset ordering parameter.

    :param request: dict The Connect request dictionary.
    :return: bool
    """
    request = Request(request)

    # Ordering parameters can be found:
    #   a. in the request business object.
    #   b. in the request asset business object.

    offline_mode_list = []
    try:
        # First, try to extract the value from request parameters.
        offline_mode_list.append(request.param(PARAM_OFFLINE_MODE, 'value', ''))
    except MissingParameterError:
        pass

    try:
        # Next, try to extract the value from the request asset parameters.
        offline_mode_list.append(request.asset().param(PARAM_OFFLINE_MODE, 'value', ''))
    except MissingParameterError:
        pass

    # finally evaluate if the subscription id (asset id) is in the list.
    return request.asset().id() in offline_mode_list


def match_offline_marketplace_parameter(request: dict) -> bool:
    """
    Evaluate if the given connect request is in offline mode based on
    the offline_mode_list marketplace configuration parameter.

    :param request: dict The Connect request dictionary.
    :return: bool
    """
    request = Request(request)
    try:
        offline_mode_list = request.asset().configuration_param(
            PARAM_OFFLINE_MODE_LIST,
            'structured_value',
            [],
        )
        return request.asset().id() in offline_mode_list
    except MissingParameterError:
        return False


def composited_match_offline_asset_and_marketplace_parameter(request: dict) -> bool:
    """
    Composite rule
    :param request:
    :return:
    """
    return any([
        match_offline_marketplace_parameter(request),
        match_offline_asset_parameter(request),
    ])
