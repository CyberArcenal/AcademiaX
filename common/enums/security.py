# common/enums/security.py
from django.db import models

class SecurityEventType(models.TextChoices):
    LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'Login Success'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
    LOGOUT = 'LOGOUT', 'Logout'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Change'
    PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
    TWO_FACTOR_ENABLED = 'TWO_FACTOR_ENABLED', '2FA Enabled'
    TWO_FACTOR_DISABLED = 'TWO_FACTOR_DISABLED', '2FA Disabled'
    TWO_FACTOR_VERIFIED = 'TWO_FACTOR_VERIFIED', '2FA Verified'
    DEVICE_ADDED = 'DEVICE_ADDED', 'New Device Added'
    DEVICE_REMOVED = 'DEVICE_REMOVED', 'Device Removed'
    PROFILE_UPDATE = 'PROFILE_UPDATE', 'Profile Updated'
    ROLE_CHANGE = 'ROLE_CHANGE', 'Role Changed'
    ACCOUNT_LOCKED = 'ACCOUNT_LOCKED', 'Account Locked'
    ACCOUNT_UNLOCKED = 'ACCOUNT_UNLOCKED', 'Account Unlocked'