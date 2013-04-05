c = get_config()

load_subconfig('base_html.py')

c.ConverterTemplate.template_file='reveal'
c.NbconvertApp.fileext='reveal.html'

