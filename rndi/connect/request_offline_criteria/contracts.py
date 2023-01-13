#
# This file is part of the Ingram Micro CloudBlue RnD Integration Connectors SDK.
#
# Copyright (c) 2023 Ingram Micro. All Rights Reserved.
#
from abc import ABC, abstractmethod
from typing import Callable, Union

from rndi.connect.business_objects.adapters import Request

Rule = Callable[[dict], bool]


class OfflineChecker(ABC):
    @abstractmethod
    def is_offline_enabled(self, request: Union[dict, Request]) -> bool:
        """
        Evaluates if the given request is in offline mode or not.

        :param request: Union[dict, Request] The Connect request object.
        :return: bool True if the request is in offline mode, False otherwise.
        """
