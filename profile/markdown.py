c = get_config()

c.ConverterTemplate.template_file='markdown'

c.NbconvertApp.fileext='md'

c.GlobalConfigurable.display_data_priority=['svg', 'png', 'latex',  'jpg', 'jpeg','text']

c.ExtractFigureTransformer.enabled=True


