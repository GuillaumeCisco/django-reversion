import sys
from reversion.revisions import create_revision as create_revision_base
from reversion.views import _request_creates_revision, _set_user_from_request, create_revision


class RevisionMiddleware(object):

    """Wraps the entire request in a revision."""

    manage_manually = False

    using = None

    def __init__(self, get_response=None):
        super(RevisionMiddleware, self).__init__()
        # Support Django 1.10 middleware.
        if get_response is not None:
            self.get_response = create_revision(manage_manually=self.manage_manually, using=self.using)(get_response)

    def process_request(self, request):
        if _request_creates_revision(request):
            context = create_revision_base(manage_manually=self.manage_manually, using=self.using)
            context.__enter__()
            _set_user_from_request(request)
            if not hasattr(request, "_revision_middleware"):
                setattr(request, "_revision_middleware", {})
            request._revision_middleware[self] = context

    def _close_revision(self, request):
        if self in getattr(request, "_revision_middleware", {}):
            request._revision_middleware.pop(self).__exit__(*sys.exc_info())

    def process_response(self, request, response):
        self._close_revision(request)
        return response

    def process_exception(self, request, exception):
        self._close_revision(request)

    def __call__(self, request):
        return self.get_response(request)
