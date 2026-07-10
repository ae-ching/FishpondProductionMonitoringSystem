"""
Toast Notification Utilities for Django

This module provides utility functions to easily add toast notifications
to Django views using the messages framework.

Usage in views:
    from arich_app.utils.toast import toast_success, toast_error
    
    toast_success(request, "Fishpond added successfully!")
    toast_error(request, "An error occurred while updating the fishpond.")
"""

from django.contrib import messages


def toast_success(request, message, title=None):
    """
    Display a success toast notification.
    
    Args:
        request: The Django request object
        message: The message text to display
        title: Optional custom title (defaults to "Success")
    """
    messages.success(request, message, extra_tags='success', fail_silently=True)


def toast_error(request, message, title=None):
    """
    Display an error toast notification.
    
    Args:
        request: The Django request object
        message: The message text to display
        title: Optional custom title (defaults to "Error")
    """
    messages.error(request, message, extra_tags='error', fail_silently=True)


def toast_warning(request, message, title=None):
    """
    Display a warning toast notification.
    
    Args:
        request: The Django request object
        message: The message text to display
        title: Optional custom title (defaults to "Warning")
    """
    messages.warning(request, message, extra_tags='warning', fail_silently=True)


def toast_info(request, message, title=None):
    """
    Display an info toast notification.
    
    Args:
        request: The Django request object
        message: The message text to display
        title: Optional custom title (defaults to "Info")
    """
    messages.info(request, message, extra_tags='info', fail_silently=True)


def add_toast_message(request, message_text, message_type='info', title=None):
    """
    Generic function to add a toast notification.
    
    Args:
        request: The Django request object
        message_text: The message text to display
        message_type: The type of message ('success', 'error', 'warning', 'info')
        title: Optional custom title
    """
    if message_type == 'success':
        messages.success(request, message_text, extra_tags='success', fail_silently=True)
    elif message_type == 'error':
        messages.error(request, message_text, extra_tags='error', fail_silently=True)
    elif message_type == 'warning':
        messages.warning(request, message_text, extra_tags='warning', fail_silently=True)
    else:
        messages.info(request, message_text, extra_tags='info', fail_silently=True)
