REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "common.utils.authentications.IsAuthenticatedAndNotBlacklisted",
    ],
    "EXCEPTION_HANDLER": "common.handlers.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.base.paginations.StandardResultsSetPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 20,
}


