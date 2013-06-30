{%- extends 'python.tpl' -%}

{#% block any_cell %}
==============================
=======start {{cell.type}}=========
{{ super() }}
======= end {{cell.type}} =========
=============================={% endblock any_cell %#}



{% block markdowncell %}---- Start MD ----{{ super() }}
---- End MD ----
{% endblock markdowncell %}

{% block codecell %}---- Start Code ----{{ super() }}
---- End Code ----
{% endblock codecell %}

{% block headingcell scoped %}---- Start heading ----{{ super() }}
---- End heading ----
{% endblock headingcell %}

{% block rawcell scoped %}---- Start Raw ----
{{ super() }}
---- End Raw ----{% endblock rawcell %}

{% block unknowncell scoped %}
unknown type  {{cell.type}}
{% endblock unknowncell %}

