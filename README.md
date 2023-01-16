# Python Connect Request Offline Criteria

[![Test](https://github.com/othercodes/python-connect-request-offline-criteria/actions/workflows/test.yml/badge.svg)](https://github.com/othercodes/python-connect-request-offline-criteria/actions/workflows/test.yml)

Provides simple, flexible and extensible way to match offline Connect requests.

## What is the offline mode?

Some use cases requires specific operations in the connector side without calling the vendor system. Good examples are
migration operations or normalization process.

## Installation

The easiest way to install the Connect Request Offline Criteria library is to get the latest version from PyPI:

```bash
# using poetry
poetry add rndi-connect-request-offline-criteria
# using pip
pip install rndi-connect-request-offline-criteria
```

## The Contracts

This package provides the following contracts or interfaces:

```python
class OfflineChecker(ABC):
    @abstractmethod
    def is_offline_enabled(self, request: Union[dict, Request]) -> bool:
        """
        Evaluates if the given request is in offline mode or not.

        :param request: Union[dict, Request] The Connect request object.
        :return: bool True if the request is in offline mode, False otherwise.
        """
```

The `OfflineChecker` exposes one single method `is_offline_enabled` that accepts the request dictionary and
returns `True` if the given request match the conditions to be considered as offline, `False` otherwise. All the given
rules must match in order to consider a request as offline.

Each condition or rule must have the following signature:

```python
Rule = Callable[[dict], bool]
```

For example, we can create a rule that will match all the requests in inquiring status as offline:

```python
def match_request_type(request: dict) -> bool:
    return Request(request).type() == 'inquiring'
```

## The Adapters

This package comes with an adapter and some simple rules, check the example below:

```python
from rndi.connect.request_offline_criteria.adapters import OfflineCriteria
from rndi.connect.request_offline_criteria.rules import (
    match_request_type,
    match_offline_asset_parameter,
)

offline = OfflineCriteria([
    match_request_type,  # match the requests with type cancel and suspend.
    match_offline_asset_parameter,  # match the request with value "True" in param "offline_mode". 
])

# True if both filters match, False otherwise
if offline.is_offline_enabled(request):
    print("is offline model")
else:
    print("is online model")
```

Alternatively, you can use the `OfflineCriteria` adapter as a business middleware to wrap business transactions:

```python
from rndi.connect.request_offline_criteria.adapters import OfflineCriteria
from rndi.connect.request_offline_criteria.rules import match_request_type, match_offline_asset_parameter
from rndi.connect.business_transactions.adapters import prepare
from rndi.connect.business_transaction_middleware.middleware import make_middleware_callstack

# get the business transaction
transaction = prepare(CreateCustomer())

# instantiate the OfflineCriteria.
offline = OfflineCriteria([
    match_request_type,  # match the requests with type cancel and suspend.
    match_offline_asset_parameter,  # match the request with value "True" in param "offline_mode". 
])

# make the middleware callstack
transaction = make_middleware_callstack([offline], transaction)

# execute the transaction normally, if the given request match the offline rules the request will be automatically 
# skipped without executing the actual transaction code. 
response = transaction(request)
```

Additionally, you can trigger custom code on matching offline, by passing the `on_match` argument to
the `OfflineCriteria`
class on instantiation, for example, you can use the `DefaultOnMatchTransaction` class that comes with the package:

```python
from rndi.connect.request_offline_criteria.adapters import OfflineCriteria, DefaultOnMatchTransaction
from rndi.connect.request_offline_criteria.rules import match_request_type, match_offline_asset_parameter

# instantiate the OfflineCriteria.
offline = OfflineCriteria([
    match_request_type,  # match the requests with type cancel and suspend.
    match_offline_asset_parameter,  # match the request with value "True" in param "offline_mode". 
], DefaultOnMatchTransaction("TL-662-440-096", client, logger))
```

By default, the `DefaultOnMatchTransaction` class will:

* Log the message: `"The subscription {id} is in offline mode."`.
* Approve the request with the configured activation template.
* Finish the transaction with `BackgroundResponse.done()`.

Or simply use a callable that receives the request dictionary and returns a valid `BackgroundResponse`:

```python
from connect.eaas.core.responses import BackgroundResponse
from rndi.connect.request_offline_criteria.adapters import OfflineCriteria
from rndi.connect.request_offline_criteria.rules import match_request_type, match_offline_asset_parameter


def custom_offline_on_match(request: dict) -> BackgroundResponse:
    # do something custom here.
    return BackgroundResponse.done()


offline = OfflineCriteria([
    match_request_type,
    match_offline_asset_parameter,
], custom_offline_on_match)
```
