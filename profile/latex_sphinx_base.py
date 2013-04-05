c = get_config()

# Inherit
load_subconfig('latex_base.py')

# Overrides
c.ConverterTemplate.template_file='latex_sphinx_base'
c.NbconvertApp.write = True

# Set sphinx transformer options.
c.SphinxTransformer.enabled = True

