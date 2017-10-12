{% extends "tmpl_base.py" %}

{% block class_body %}

    def _write(self, bulk):
        """Write a bulk."""
        raise NotImplementedError()

{% endblock %}
