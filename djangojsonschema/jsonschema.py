import inspect

from django.forms import widgets, fields


def pretty_name(name):
    """Converts 'first_name' to 'First name'"""
    if not name:
        return u''
    return name.replace('_', ' ').capitalize()


class DjangoFormToJSONSchema(object):

    input_type_map = {
        'text': 'string',
    }

    def get_form_fields(self, form):
        """ base_fields when given a class,
            fields for when given an instance
        """
        is_class = inspect.isclass(form)
        if is_class:
            form_fields = form.base_fields.iteritems()
        else:
            form_fields = form.fields.iteritems()
        return form_fields

    def populate_schema_defaults_from_instance(self, json_schema, instance):
        """ Populate the json_schema with default
            values if an instance is given """
        for name, properties in json_schema.get('properties').items():
            if hasattr(instance, name):
                value = getattr(instance, name)
                json_schema['properties'][name]['default'] = unicode(value)
        return json_schema

    def convert_form(self, form, json_schema=None, instance=None):
        if json_schema is None:

            json_schema = {
                'title': pretty_name(form.__class__.__name__),
                'description': form.__doc__ or '',
                'type': 'object',
                'properties': {},
            }

        form_fields = self.get_form_fields(form)

        for name, field in form_fields:
            field_data = self.convert_formfield(name, field, json_schema)
            json_schema['properties'][name] = field_data

        if instance:
            """ Populate the default values if an instance is given """
            self.populate_schema_defaults_from_instance(
                json_schema, instance)

        return json_schema

    def convert_formfield(self, name, field, json_schema):
        #TODO detect bound field
        widget = field.widget
        target_def = {
            'title': pretty_name(name),
            'description': field.help_text,
            'readonly': widget.attrs.get('readonly', False),
            'required': field.required,
            'default': field.initial or ''}

        #TODO JSONSchemaField; include subschema and ref the type
        if isinstance(field, fields.URLField):
            target_def['type'] = 'string'
            target_def['format'] = 'url'
        elif isinstance(field, fields.FileField):
            target_def['type'] = 'string'
            target_def['format'] = 'uri'
        elif isinstance(field, fields.DateField):
            target_def['type'] = 'string'
            target_def['format'] = 'date'
        elif isinstance(field, fields.DateTimeField):
            target_def['type'] = 'string'
            target_def['format'] = 'datetime'
        elif isinstance(field, (fields.DecimalField, fields.FloatField)):
            target_def['type'] = 'number'
        elif isinstance(field, fields.IntegerField):
            target_def['type'] = 'integer'
        elif isinstance(field, fields.EmailField):
            target_def['type'] = 'string'
            target_def['format'] = 'email'
        elif isinstance(field, fields.NullBooleanField):
            target_def['type'] = 'boolean'
        elif isinstance(widget, widgets.CheckboxInput):
            target_def['type'] = 'boolean'
        elif isinstance(widget, widgets.Select):
            target_def['type'] = 'string'
            if hasattr(widget, 'allow_multiple_selected'):
                if widget.allow_multiple_selected:
                    target_def['type'] = 'array'
            target_def['enum'] = [choice[0] for choice in field.choices]
        elif isinstance(widget, widgets.Input):
            translated_type = self.input_type_map.get(
                widget.input_type, 'string')
            target_def['type'] = translated_type
        else:
            target_def['type'] = 'string'
        return target_def
