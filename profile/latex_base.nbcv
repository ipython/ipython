c = get_config()

c.ConverterTemplate.template_file='latex_base'
c.ConverterTemplate.tex_environement=True


c.NbconvertApp.fileext='tex'

c.GlobalConfigurable.display_data_priority      =['latex', 'svg', 'png', 'jpg', 'jpeg' , 'text']
# do not extract text
c.ExtractFigureTransformer.display_data_priority=['latex', 'svg', 'png', 'jpg', 'jpeg']


c.ExtractFigureTransformer.extra_ext_map={'svg':'pdf'}
c.ExtractFigureTransformer.enabled=True

# Enable latex transformer (make markdown2latex work with math $.)
c.LatexTransformer.enabled=True
