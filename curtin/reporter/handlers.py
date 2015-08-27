# vi: ts=4 expandtab

import abc

from .registry import DictRegistry
from .. import url_helper
from .. import log as logging


LOG = logging.getLogger(__name__)


class ReportingHandler(object):
    """Base class for report handlers.

    Implement :meth:`~publish_event` for controlling what
    the handler does with an event.
    """

    @abc.abstractmethod
    def publish_event(self, event):
        """Publish an event to the ``INFO`` log level."""

    def publish_result(self, event):
        """Publish a result event.

        This is separate from other events due to file data"""
        pass


class LogHandler(ReportingHandler):
    """Publishes events to the cloud-init log at the ``INFO`` log level."""

    def __init__(self, level="DEBUG"):
        super(LogHandler, self).__init__()
        if isinstance(level, int):
            pass
        else:
            input_level = level
            try:
                level = getattr(logging, level.upper())
            except:
                LOG.warn("invalid level '%s', using WARN", input_level)
                level = logging.WARN
        self.level = level

    def publish_event(self, event):
        """Publish an event to the ``INFO`` log level."""
        logger = logging.getLogger(
            '.'.join(['cloudinit', 'reporting', event.event_type, event.name]))
        logger.log(self.level, event.as_string())


class PrintHandler(ReportingHandler):
    """Print the event as a string."""

    def publish_event(self, event):
        print(event.as_string())

    def publish_result(self, event):
        self.publish_event(event)


class WebHookHandler(ReportingHandler):
    def __init__(self, endpoint, consumer_key=None, token_key=None,
                 token_secret=None, consumer_secret=None, timeout=None,
                 retries=None):
        super(WebHookHandler, self).__init__()

        self.oauth_helper = url_helper.OauthUrlHelper(
            consumer_key=consumer_key, token_key=token_key,
            token_secret=token_secret, consumer_secret=consumer_secret)
        self.endpoint = endpoint
        self.timeout = timeout
        self.retries = retries
        self.headers = {'Content-Type': 'application/json'}

    def publish_event(self, event):
        try:
            return self.oauth_helper.geturl(
                url=self.endpoint, data=event.as_dict(),
                headers = self.headers, retries=self.retries)
        except Exception as e:
            LOG.warn("failed posting event: %s [%s]" % (event.as_string(), e))

    def publish_result(self, event):
        """Publish the result and attached files."""
        # TODO: we need to add mime multipart posting here
        # the goal is to add general infrastructure to url_helper
        # and then to use that similar to how we use geturl above
        LOG.warn("Do not yet know how to post files.")
        self.publish_event(event)


available_handlers = DictRegistry()
available_handlers.register_item('log', LogHandler)
available_handlers.register_item('print', PrintHandler)
available_handlers.register_item('webhook', WebHookHandler)
