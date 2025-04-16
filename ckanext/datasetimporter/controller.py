from ckan.lib.base import BaseController, render


class DatasetImporterController(BaseController):
    def index(self):
        return render('datasetimporter/index.html')
