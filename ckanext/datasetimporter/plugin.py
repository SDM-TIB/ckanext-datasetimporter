import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from .views import datasetimporter

class DatasetimporterPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'datasetimporter')

    def get_blueprint(self):
        return [datasetimporter]
