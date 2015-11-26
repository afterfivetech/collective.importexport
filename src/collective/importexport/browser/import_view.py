# -*- coding: utf-8 -*-
from plone.dexterity.utils import iterSchemataForType
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from collective.importexport import _
from plone import api
from plone.namedfile.field import NamedFile
from plone.z3cform.layout import wrap_form
# from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.interface import Interface, directlyProvides
from zope import schema

# from zope import schema

import csv

# TODO(ivanteoh): convert to import config option (csv_col, obj_field)
matching_fields = (
    ("Filename", "filename"),
    ("Title", "title"),
    ("Summary", "description"),
    ("IAID", "iaid"),
    ("Citable Reference", "citable")
)


def _get_prop(prop, item, default=None):
    """Get value from prop as key in dictionary item."""
    ret = default
    if prop in item:
        ret = safe_unicode(item[prop])
    return ret


def dexterity_import(container, file_resource):
    """Import to dexterity-types from file to container."""
    count = 0
    reader = csv.DictReader(file_resource)

    # cat = getToolByName(container, 'portal_catalog')
    # container_path = '/'.join(container.getPhysicalPath())

    # TODO(ivanteoh): Make sure container is either folder or SiteRoot

    import_list = []
    # Find all the fields value
    for row in reader:
        fields = {}
        for csv_col, obj_field in matching_fields:
            field_value = _get_prop(csv_col, row)
            fields[obj_field] = field_value
        import_list.append(fields)
        count += 1

    # TODO(ivanteoh): Save the objects in this container

    return {'count': count}



def fields_list(context):
    terms = []

    # need to look up all the possible fields we can set on all the content
    # types we might update in the given folder
    found = {}

    for fti in context.contenttypescanaddhere():
        portal_type = fti.getId()
        schemas = iterSchemataForType(portal_type)
        for schema in schemas:
            for field in schema:
                if field not in found:
                    found[field] = 1
                    terms.append(SimpleVocabulary.createTerm(field, field, field))


    #for term in ['Slovenia', 'Spain', 'Portugal', 'France']:
    #    terms.append(SimpleVocabulary.createTerm(term, term, term))
    return SimpleVocabulary(terms)
directlyProvides(fields_list, IContextSourceBinder)

def headers_list(context):
    """ use the last upload header info from the last uploaded file
    """


    terms = []
    #for term in ['Slovenia', 'Spain', 'Portugal', 'France']:
    #    terms.append(SimpleVocabulary.createTerm(term, term, term))
    return SimpleVocabulary(terms)
directlyProvides(headers_list, IContextSourceBinder)


class IImportSchema(Interface):
    """Import settings."""

    header_mapping = schema.Dict(
        title=_(u'Header Mapping'),
        description=_(u"Any matching headers in your CSV will be mapped to "
                      u"these fields"),
        key_type=schema.Choice(source=headers_list, title=u"header"),
        value_type=schema.Choice(source=fields_list, title=u"field"),
        #default={'table th td': 'width height'},
        missing_value={},
        required=False)

    import_file = NamedFile(
        title=_("import_field_file_title",  # nopep8
                default=u"Import File"),
        description=_("import_field_file_description",  # nopep8
                      default=u"In CSV format."),
        required=True)





class ImportForm(form.Form):
    """Import data to dexterity-types."""

    fields = field.Fields(IImportSchema)
    ignoreContext = True

    label = _("import_form_label",  # nopep8
              default=u"Import")
    description = _("import_form_description",  # nopep8
                    default=u"Import data to dexterity-types objects.")

    def save_data(self, data):
        # TODO(ivanteoh): save date using Annotation Adapter
        pass

    def updateWidgets(self):



        super(ImportForm, self).updateWidgets()

    @button.buttonAndHandler(_("import_button_save", default=u"Save"))  # nopep8
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            return False

        self.save_data(data)

        api.portal.show_message(
            message=_("import_message_save",  # nopep8
                default=u"Import settings saved."),
            request=self.request,
            type="info")
        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_("import_button_save_import",  # nopep8
                               default=u"Save and Import"))
    def handleSaveImport(self, action):
        data, errors = self.extractData()
        if errors:
            return False

        self.save_data(data)

        data, errors = self.extractData()
        if errors:
            return False

        import_file = data["import_file"]

        if import_file:

            # File upload is not saved in settings
            file_resource = import_file.data
            file_name = import_file.filename

            import_metadata = dexterity_import(
                self.context,
                file_resource=file_resource
            )

            count = import_metadata['count']

            api.portal.show_message(
                message=_("import_message_csv_info",  # nopep8
                    default=u"${num} items imported from ${filename}",
                    mapping={'num': count, 'filename': file_name}),
                request=self.request,
                type="info")

        else:
            api.portal.show_message(
                message=_("import_message_csv_error",  # nopep8
                    default=u"Please provide a csv file."),
                request=self.request,
                type="error")

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(u'Cancel')
    def handleCancel(self, action):
        api.portal.show_message(
            message=_("import_message_cancel",  # nopep8
                default="Import canceled."),
            request=self.request,
            type="info")
        self.request.response.redirect(self.context.absolute_url())

ImportView = wrap_form(ImportForm)
