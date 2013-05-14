from .base import ConfigurableTransformer

class RevealHelpTransformer(ConfigurableTransformer):

    def __call__(self, nb, other):
        for worksheet in nb.worksheets :
            for i, cell in enumerate(worksheet.cells):
                if not cell.get('metadata', None):
                    break
                cell.metadata.slide_type = cell.metadata.get('slideshow', {}).get('slide_type', None)
                if cell.metadata.slide_type is None:
                    cell.metadata.slide_type = '-'
                if cell.metadata.slide_type in ['slide']:
                    worksheet.cells[i - 1].metadata.slide_helper = 'slide_end'
                if cell.metadata.slide_type in ['subslide']:
                    worksheet.cells[i - 1].metadata.slide_helper = 'subslide_end'
        return nb, other