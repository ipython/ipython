// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/utils',
    'base/js/page',
    'base/js/events',
    'contents',
    'codemirror/lib/codemirror',
    'texteditor/js/menubar',
    'codemirror/mode/meta',
    'custom/custom',
], function(
    $,
    utils,
    page,
    events,
    contents,
    CodeMirror,
    menubar
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
        basename = file_path.substring(ix+1);
    }
    contents.load(dir_path, basename, {
        success: function(model) {
            page.show();
            if (model.type === "file" && model.format === "text") {
                console.log(modeinfo);
                var cm = CodeMirror($('#texteditor-container')[0], {
                    value: model.content,
                });
                
                var menus = new menubar.MenuBar('#menubar', {
                    base_url: base_url,
                    codemirror: cm,
                    contents: contents,
                    events: events,
                    file_path: file_path
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
