from gettext import gettext as _

from pydantic import ValidationError

from apps.shared.exception import UnauthorizedError


class ProlificInvalidApiTokenError(UnauthorizedError):
    message = _("Prolific token is invalid.")


class ProlificInvalidStudyError(UnauthorizedError):
    message = _("Invalid Prolific study id.")


class ProlificIntegrationNotConfiguredError(ValidationError):
    message = _("Prolific integration not configured.")