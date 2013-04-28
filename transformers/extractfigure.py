 

class ExtractFigureTransformer(ActivatableTransformer):


    extra_ext_map =  Dict({},
            config=True,
            help="""extra map to override extension based on type.
            Usefull for latex where svg will be converted to pdf before inclusion
            """
            )

    key_format_map =  Dict({},
            config=True,
            )

    figname_format_map =  Dict({},
            config=True,
            )


    #to do change this to .format {} syntax
    default_key_tpl = Unicode('_fig_{count:02d}.{ext}', config=True)

    def _get_ext(self, ext):
        if ext in self.extra_ext_map :
            return self.extra_ext_map[ext]
        return ext

    def _new_figure(self, data, fmt, count):
        """Create a new figure file in the given format.

        """
        tplf = self.figname_format_map.get(fmt, self.default_key_tpl)
        tplk = self.key_format_map.get(fmt, self.default_key_tpl)

        # option to pass the hash as data ?
        figname = tplf.format(count=count, ext=self._get_ext(fmt))
        key     = tplk.format(count=count, ext=self._get_ext(fmt))

        # Binary files are base64-encoded, SVG is already XML
        binary = False
        if fmt in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')
            binary = True

        return figname, key, data, binary


    def cell_transform(self, cell, other, count):
        if other.get('figures', None) is None :
            other['figures'] = {'text':{},'binary':{}}
        for out in cell.get('outputs', []):
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    figname, key, data, binary = self._new_figure(out[out_type], out_type, count)
                    out['key_'+out_type] = figname
                    if binary :
                        other['figures']['binary'][key] = data
                    else :
                        other['figures']['text'][key] = data
                    count = count+1
        return cell, other

