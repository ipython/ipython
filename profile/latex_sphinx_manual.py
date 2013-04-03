c = get_config()

#Inherit
load_subconfig('latex_sphinx_base.py')

#Overrides
c.ConverterTemplate.template_file='latex_sphinx_manual'
