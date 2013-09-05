import inspect

from django.forms import widgets, fields


def pretty_name(name):
    """Converts 'first_name' to 'First name'"""
    if not name:
        return u''
    return name.replace('_', ' ').capitalize()


class DjangoFormToJSONSchema(object):

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

    def get_base_json_schema(self, form):
        """Contructs a base json_schema from a form"""

        base_json_schema = {
            'title': pretty_name(form.__class__.__name__),
            'description': form.__doc__ or '',
            'type': 'object',
            'properties': {},
        }
        return base_json_schema

    def convert_form(self, form, instance=None):
        """Converts a django form to a json schema"""

        json_schema = self.get_base_json_schema(form)
        form_fields = self.get_form_fields(form)

        for name, field in form_fields:
            properties = self.get_base_properties(name, field)
            field_properties = self.get_field_properties(field)
            properties.update(field_properties)
            json_schema['properties'][name] = properties

        if instance:
            self.populate_schema_defaults_from_instance(
                json_schema, instance)

        return json_schema

    def get_base_properties(self, name, field, base_properties={}):
        """Adds base properties to the field"""

        title = pretty_name(name)
        description = field.help_text
        readonly = field.widget.attrs.get('readonly', False)
        required = field.required
        default = field.initial or ''

        base_properties.update(
            title=title,
            description=description,
            readonly=readonly,
            required=required,
            default=default)

        if 'maxlength' in field.widget.attrs:
            maxLength = field.widget.attrs.get('maxlength')
            base_properties.update(maxLength=maxLength)

        if 'minlength' in field.widget.attrs:
            minLength = field.widget.attrs.get('minlength')
            base_properties.update(minLength=minLength)

        if getattr(field, 'max_value', False):
            base_properties.update(maximum=field.max_value)

        if getattr(field, 'min_value', False):
            base_properties.update(minimum=field.min_value)

        if getattr(field, 'choices', False):
            if field.choices:
                choices = []
                for choice in field.choices:
                    if choice[0] is not '':
                        choices.append(choice[0])
                base_properties.update(enum=choices)

        return base_properties

    def get_field_properties(self, field, field_properties={}):
        """Converts a django form field to a set of properties"""

        if isinstance(field, fields.URLField):
            field_properties.update(type='string', format='url')

        elif isinstance(field, fields.FileField):
            field_properties.update(type='string', format='uri')

        elif isinstance(field, fields.DateField):
            # TODO: Use field.widget.format to pattern property (regex)
            field_properties.update(type='string', format='date')

        elif isinstance(field, fields.DateTimeField):
            # TODO: Use field.widget.format to pattern property (regex)
            field_properties.update(type='string', format='datetime')

        elif isinstance(field, (fields.DecimalField, fields.FloatField)):
            """
                TODO: Use field.widget.format to pattern property (regex)
                TODO: exclusiveMinimum.
                    Property value can not equal the number defined by the
                    minimum schema property.
                    boolean false
                TODO: exclusiveMaximum.
                    Property value can not equal the number defined by the
                    maximum schema property.
                    boolean false
            """
            field_properties.update(type='number')

        elif isinstance(field, fields.IntegerField):
            """
                TODO: Use field.widget.format to pattern property (regex)
                TODO: exclusiveMinimum.
                    Property value can not equal the number defined by the
                    minimum schema property.
                    boolean false
                TODO: exclusiveMaximum.
                    Property value can not equal the number defined by the
                    maximum schema property.
                    boolean false
                TODO: divisibleBy.
                    Property value must be divisible by this number.
                    integer
            """
            field_properties.update(type='integer')

        elif isinstance(field, fields.EmailField):
            # TODO: Use field.widget.format to pattern property (regex)
            field_properties.update(type='string', format='email')

        elif isinstance(field, fields.NullBooleanField):
            field_properties.update(type='boolean')

        elif isinstance(field.widget, widgets.CheckboxInput):
            field_properties.update(type='boolean')

        elif isinstance(field.widget, widgets.Select):
            field_properties.update(type='string')

            if hasattr(field.widget, 'allow_multiple_selected'):
                if field.widget.allow_multiple_selected:
                    field_properties.update(type='array')

        elif isinstance(field.widget, widgets.Input):
            # TODO: Use field.widget.format to pattern property (regex)
            field_properties.update(type='string')

        else:
            # All other cases
            field_properties.update(type='string')

        return field_properties
