"""Django app configuration for django-cloudevents.

This module defines the Django app configuration for the django-cloudevents
library. It registers the app with Django's app registry and provides the
namespace for the package.

The app provides:
- CloudEvent webhook handling views
- Event processor infrastructure
- Django signals for CloudEvent lifecycle events

For more information about configuring Django apps, see:
https://docs.djangoproject.com/en/stable/ref/applications/
"""

from django.apps import AppConfig


class DjangoCloudEventsConfig(AppConfig):
    """Configuration for the django-cloudevents Django app.

    This class configures the django-cloudevents application within the
    Django project. It sets the app name and can be extended to add
    custom initialization logic if needed.

    Attributes:
        name: The dotted path to the application package.

    Example:
        In settings.py::

            INSTALLED_APPS = [
                ...
                'django_cloudevents',
                ...
            ]

    Note:
        This configuration class is automatically discovered by Django
        when the app is listed in ``INSTALLED_APPS``.
    """

    name = "django_cloudevents"
