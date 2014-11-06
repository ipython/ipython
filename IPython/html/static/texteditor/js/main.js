// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/utils',
    'base/js/page',
    'contents',
    'codemirror/lib/codemirror',
    'codemirror/mode/meta',
    'custom/custom',
], function(
    $, 
    utils,
    page,
    contents,
    CodeMirror
    ){
    page = new page.Page();

    var base_url = utils.get_body_data('baseUrl');
    contents = new contents.Contents({base_url: base_url});

    var file_path = utils.get_body_data('filePath');
    var ix = file_path.lastIndexOf("/");
    var dir_path, basename;
    if (ix == -1) {
        dir_path = '';
        basename = file_path;
    } else {
        dir_path = file_path.substring(0, ix);
        basename = file_path.substring(ix);
    }
    contents.load(dir_path, basename, {
        success: function(model) {
            page.show();
            if (model.type === "file" && model.format === "text") {
                console.log(modeinfo);
                var cm = CodeMirror($('#texteditor-container')[0], {
                    value: model.content,
                });
                
                // Find and load the highlighting mode
                var modeinfo = CodeMirror.findModeByMIME(model.mimetype);
                if (modeinfo) {
                    utils.requireCodeMirrorMode(modeinfo.mode, function() {
                        cm.setOption('mode', modeinfo.mode);
                    });
                }
                
                // Attach to document for debugging
                document.cm_instance = cm;
            } else {
                $('#texteditor-container').append(
                    $('<p/>').text(dir_path + " is not a text file")
                );
            }
        }
    });
});
