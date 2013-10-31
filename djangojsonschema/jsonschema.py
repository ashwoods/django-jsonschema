import inspect

from django.forms import widgets, fields
from collections import OrderedDict


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

    def get_base_json_schema(self, form):
        """Contructs a base json_schema from a form"""

        base_json_schema = {
            'title': pretty_name(form.__class__.__name__),
            'description': form.__doc__ or '',
            'type': 'object',
            'properties': OrderedDict(),
        }
        return base_json_schema

    def convert_form(self, form, instance=None, exclude_fields=[]):
        """Converts a django form to a json schema"""

        json_schema = self.get_base_json_schema(form)
        form_fields = self.get_form_fields(form)
        model = form._meta.model

        for name, field in form_fields:
            if not name in exclude_fields:
                properties = self.get_base_properties(name, field, model)
                field_properties = self.get_field_properties(field)
                properties.update(field_properties)
                json_schema['properties'][name] = properties
        return json_schema

    def get_base_properties(self, name, field, model):
        """Adds base properties to the field"""

        title = pretty_name(name)
        description = field.help_text
        readonly = field.widget.attrs.get('readonly', False)
        required = field.required
        bound_field = model._meta.get_field_by_name(name)[0]

        base_properties = dict(
            title=title,
            description=description,
            readonly=readonly,
            required=required)

        if bound_field.has_default():
            if callable(bound_field.default):
                default = bound_field.default()
            else:
                default = bound_field.default
            base_properties.update(default=default)

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

    def get_field_properties(self, field):
        """Converts a django form field to a set of properties"""

        field_properties = dict()

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
