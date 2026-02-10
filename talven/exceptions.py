# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exception types raised by SearXNG modules."""

import typing as t

if t.TYPE_CHECKING:
    from lxml.etree import XPath


class TalvenException(Exception):
    """Base Talven exception."""


class TalvenParameterException(TalvenException):
    """Raised when query miss a required parameter"""

    def __init__(self, name: str, value: t.Any):
        if value == '' or value is None:
            message = f"Empty {name} parameter"
        else:
            message = f"Invalid value {value} for parameter {name}"
        super().__init__(message)
        self.message: str = message
        self.parameter_name: str = name
        self.parameter_value: t.Any = value


@t.final
class TalvenSettingsException(TalvenException):
    """Error while loading the settings"""

    def __init__(self, message: str | Exception, filename: str | None):
        super().__init__(message)
        self.message = message
        self.filename = filename


class TalvenEngineException(TalvenException):
    """Error inside an engine"""


class TalvenXPathSyntaxException(TalvenEngineException):
    """Syntax error in a XPATH"""

    def __init__(self, xpath_spec: "str | XPath", message: str):
        super().__init__(str(xpath_spec) + " " + message)
        self.message: str = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str: str = str(xpath_spec)


class TalvenEngineResponseException(TalvenEngineException):
    """Impossible to parse the result of an engine"""


class TalvenEngineAPIException(TalvenEngineResponseException):
    """The website has returned an application error"""


class TalvenEngineAccessDeniedException(TalvenEngineResponseException):
    """The website is blocking the access"""

    SUSPEND_TIME_SETTING: str = "search.suspended_times.TalvenEngineAccessDenied"
    """This settings contains the default suspended time (default 86400 sec / 1
    day)."""

    def __init__(self, suspended_time: int | None = None, message: str = 'Access denied'):
        """Generic exception to raise when an engine denies access to the results.

        :param suspended_time: How long the engine is going to be suspended in
            second. Defaults to None.
        :type suspended_time: int, None
        :param message: Internal message.  Defaults to ``Access denied``
        :type message: str
        """
        if suspended_time is None:
            suspended_time = self._get_default_suspended_time()
        self.message: str = f"{message} (suspended_time={suspended_time})"
        self.suspended_time: int = suspended_time
        super().__init__(self.message)

    def _get_default_suspended_time(self) -> int:
        from talven import get_setting  # pylint: disable=C0415

        return get_setting(self.SUSPEND_TIME_SETTING)


class TalvenEngineCaptchaException(TalvenEngineAccessDeniedException):
    """The website has returned a CAPTCHA."""

    SUSPEND_TIME_SETTING: str = "search.suspended_times.TalvenEngineCaptcha"
    """This settings contains the default suspended time (default 86400 sec / 1
    day)."""

    def __init__(self, suspended_time: int | None = None, message: str = 'CAPTCHA'):
        super().__init__(message=message, suspended_time=suspended_time)


class TalvenEngineTooManyRequestsException(TalvenEngineAccessDeniedException):
    """The website has returned a Too Many Request status code

    By default, Talven stops sending requests to this engine for 1 hour.
    """

    SUSPEND_TIME_SETTING: str = "search.suspended_times.TalvenEngineTooManyRequests"
    """This settings contains the default suspended time (default 3660 sec / 1
    hour)."""

    def __init__(self, suspended_time: int | None = None, message: str = 'Too many request'):
        super().__init__(message=message, suspended_time=suspended_time)


class TalvenEngineXPathException(TalvenEngineResponseException):
    """Error while getting the result of an XPath expression"""

    def __init__(self, xpath_spec: "str | XPath", message: str):
        super().__init__(str(xpath_spec) + " " + message)
        self.message: str = message
        # str(xpath_spec) to deal with str and XPath instance
        self.xpath_str: str = str(xpath_spec)
