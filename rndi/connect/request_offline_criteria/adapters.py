#
# This file is part of the Ingram Micro CloudBlue RnD Integration Connectors SDK.
#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#
from logging import LoggerAdapter
from typing import List, Optional, Union

from connect.client import AsyncConnectClient, ConnectClient
from connect.eaas.core.responses import BackgroundResponse
from rndi.connect.api_facades.assets.mixins import WithAssetFacade
from rndi.connect.business_objects.adapters import Request
from rndi.connect.business_transactions.contracts import FnBackgroundExecution
from rndi.connect.request_offline_criteria.contracts import OfflineChecker, Rule


class OfflineCriteria(OfflineChecker):
    def __init__(self, criteria: List[Rule], on_match: Optional[FnBackgroundExecution] = None):
        self.__criteria = criteria
        self.__on_match = on_match

    def is_offline_enabled(self, request: dict) -> bool:
        if len(self.__criteria) == 0:
            return False

        for rule in self.__criteria:
            if not rule(request):
                return False

        return True

    def __call__(self, request: dict, nxt: Optional[FnBackgroundExecution] = None) -> BackgroundResponse:
        """
        Middleware implementation of the offline mode

        :param request: dict The Connect Request dict.
        :param nxt: Optional[FnTransaction] The optional next middleware (Functional Transaction).
        :return: ProcessingResponse
        """
        if not self.is_offline_enabled(request):
            return nxt(request)

        if callable(self.__on_match):
            return self.__on_match(request)
        return BackgroundResponse.skip()


class DefaultOnMatchTransaction(WithAssetFacade):
    """
    Provides out-of-the-box functionality for offline request.

    This class will:
        - Log the message: "The subscription {id} is in offline mode.".
        - Approve the request with the configured activation template.
        - Finish the transaction with BackgroundResponse.done().
    """

    def __init__(self, activation_tpl: str, client: Union[ConnectClient, AsyncConnectClient], logger: LoggerAdapter):
        self.activation_tpl = activation_tpl
        self.client = client
        self.logger = logger

    def __call__(self, request: dict) -> BackgroundResponse:
        request = Request(request)
        self.logger.info("The subscription {id} is in offline mode.".format(
            id=request.asset().id(),
        ))
        self.approve_asset_request(request, self.activation_tpl)

        return BackgroundResponse.done()
