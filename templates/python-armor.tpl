{%- extends 'python.tpl' -%}

{% block any_cell %}
==============================
=======start {{cell.type}}=========
{{ super() }}
======= end {{cell.type}} =========
=============================={% endblock any_cell %}

