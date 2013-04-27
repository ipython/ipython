c = get_config()

c.ConverterTemplate.template_file='rst'

c.NbconvertApp.fileext='rst'
c.ExtractFigureTransformer.enabled=True

c.GlobalConfigurable.display_data_priority      =['svg', 'png', 'latex',  'jpg', 'jpeg','text']
c.ExtractFigureTransformer.display_data_priority=['svg', 'png', 'latex',  'jpg', 'jpeg','text']
c.ConverterTemplate.display_data_priority=       ['svg', 'png', 'latex',  'jpg', 'jpeg','text']


