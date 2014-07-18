// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([], function() {
    "use strict";

    var default_config = {
        /**
         * Dictionary of object to autodetect highlight mode for code cell.
         * Item of the dictionnary should take the form :
         *
         *     key : {'reg':[list_of_regexp]}
         *
         * where `key` will be the code mirror mode name
         * and `list_of_regexp` should be a list of regext that should match
         * the first line of the cell to trigger this mode.
         *
         * if `key` is prefixed by the `magic_` prefix the codemirror `mode`
         * will be applied only at the end of the first line
         *
         * @attribute cell_magic_highlight
         * @example
         * This would trigger javascript mode
         * from the second line if first line start with `%%javascript` or `%%jsmagic`
         *
         *     cell_magic_highlight['magic_javascript'] = {'reg':[/^%%javascript/,/^%%jsmagic/]}
         * @example
         * This would trigger javascript mode
         * from the second line if first line start with `var`
         *
         *     cell_magic_highlight['javascript'] = {'reg':[/^var/]}
         */
        cell_magic_highlight : {
            'magic_javascript'    :{'reg':[/^%%javascript/]},
            'magic_perl'          :{'reg':[/^%%perl/]},
            'magic_ruby'          :{'reg':[/^%%ruby/]},
            'magic_python'        :{'reg':[/^%%python3?/]},
            'magic_shell'         :{'reg':[/^%%bash/]},
            'magic_r'             :{'reg':[/^%%R/]},
            'magic_text/x-cython' :{'reg':[/^%%cython/]},
        },

        /**
         * same as `cell_magic_highlight` but for raw cells
         * @attribute raw_cell_highlight
         */
        raw_cell_highlight : {
            'diff'         :{'reg':[/^diff/]}
        },
    };

    return {
        'default_config': default_config,
    };
});
