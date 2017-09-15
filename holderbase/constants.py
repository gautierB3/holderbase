class FileExtension(object):
    """ Extensions categorization."""
    #JSON = '.json'
    #XML = '.xml'
    CSV = '.csv'
    PDF = '.pdf'

    @staticmethod
    def dataset():  # define type of files to dataset
        return  FileExtension.CSV#, FileExtension.JSON, FileExtension.XML

    @staticmethod
    def report():
        return FileExtension.PDF

