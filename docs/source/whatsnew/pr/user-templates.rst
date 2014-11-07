* Added support for configurable user-supplied `Jinja
  <http://jinja.pocoo.org/>`_ HTML templates for the notebook.  Paths to
  directories containing template files can be specified via
  ``NotebookApp.extra_template_paths``.  User-supplied template directories
  searched first by the notebook, making it possible to replace existing
  templates with your own files.

  For example, to replace the notebook's built-in ``error.html`` with your own,
  create a directory like ``/home/my_templates`` and put your override template
  at ``/home/my_templates/error.html``.  To start the notebook with your custom
  error page enabled, you would run::

      ipython notebook '--extra_template_paths=["/home/my_templates/"]'

  It's also possible to override a template while also `inheriting
  <http://jinja.pocoo.org/docs/dev/templates/#template-inheritance>`_ from that
  template, by prepending ``templates/`` to the ``{% extends %}`` target of
  your child template.  This is useful when you only want to override a
  specific block of a template.  For example, to add additional CSS to the
  built-in ``error.html``, you might create an override that looks like::

    {% extends "templates/error.html" %}

    {% block stylesheet %}
    {{super()}}
    <style type="text/css">
      /* My Awesome CSS */
    </style>
    {% endblock %}
