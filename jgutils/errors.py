import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations import Integration
from sentry_sdk.scope import add_global_event_processor

SENTRY_INTEGRATION = os.getenv('SENTRY_INTEGRATION')


class ExpectedError(Exception):
    """Exception to be raised when expected error occurs
    """
    pass


class CustomSentryIntegration(Integration):
    """Custom sentry integration to add custom data and tags to sentry events
    - NOTE: use through jgutils.logger module
        - `data` shows up under "Additional Data" in sentry - use for more detailed info
        - `tags` shows up on the top bar, use for simple data like `user_id` - things that could be filtered on

    Examples
    --------
    >>> from jgutils.logger import get_log
    >>> log = get_log(__name__)
    >>> log.set_sentry_data('user', dict(name='username', id=123)))
    >>> log.set_sentry_tag('test_tag', 'whatever')
    """
    identifier = SENTRY_INTEGRATION
    MAX_STRING_LEN = 1000

    def __init__(self):
        self._data = {}
        self._tags = {}

    def _check_object_len(self, value: Any) -> Any:  # noqa: ANN401
        """Sentry clips string data to max 1000 chars
        sql queries eg can be longer, so just check and split into a list of strings if necessary
        """
        # NOTE this doesn't work, sentry still filters the full list, but this gives a tiny bit more info
        max_len = self.MAX_STRING_LEN
        if isinstance(value, str) and len(value) > max_len:
            value = [value[i:i + max_len]
                     for i in range(0, len(value), max_len)]

        return value

    def add_custom_data(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Add custom data to sentry event"""
        self._data[key] = self._check_object_len(value)

    def add_custom_tag(self, key: str, value: Any) -> None:  # noqa: ANN401
        """Add custom tag to sentry event"""
        self._tags[key] = value

    def _attach_custom_data_to_event(self, event: dict) -> None:
        """Update event with custom data and tags

        Parameters
        ----------
        event : dict
            Sentry event
        """
        data = event.setdefault('extra', {}).setdefault(self.identifier, {})
        data.update(self._data)

        tags = event.setdefault('tags', {})
        tags.update(self._tags)

    @staticmethod
    def setup_once():
        """Called one time to set event_processor as global event processor"""

        @add_global_event_processor
        def event_processor(event: dict, hint: dict | None = None) -> dict:
            integration = sentry_sdk.Hub.current.get_integration(
                SENTRY_INTEGRATION)

            if integration is not None:
                integration._attach_custom_data_to_event(event)

            return event
