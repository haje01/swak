"""Test {{type_names|join(', ')}} plugin{%if type_names|length > 1%}s{%endif%} of {{class_name}}."""

from swak import stdplugins as stp

{% if prefixes|length == 1 %}from .{{prefixes[0]}}_{{file_name}} import {{class_name}}
{% else %}{% for pr in prefixes %}from .{{prefixes[0]}}_{{file_name}} import {{class_name}} as {{pr}}_{{class_name}}
{% endfor %}{% endif %}

def test_{{class_name|lower}}_basic(router):
    """Test basic features of {{class_name}}."""
    pass
