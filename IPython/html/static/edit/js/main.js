// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'base/js/namespace',
    'base/js/utils',
    'base/js/page',
    'base/js/events',
    'contents',
    'services/config',
    'edit/js/editor',
    'edit/js/menubar',
    'edit/js/notificationarea',
    'custom/custom',
], function(
    IPython,
    utils,
    page,
    events,
    contents,
    configmod,
    editmod,
    menubar,
    notificationarea
    ){
    page = new page.Page();

    var base_url = utils.get_body_data('baseUrl');
    var file_path = utils.get_body_data('filePath');
    contents = new contents.Contents({base_url: base_url});
    var config = new configmod.ConfigSection('edit', {base_url: base_url});
    config.load();
    
    var editor = new editmod.Editor('#texteditor-container', {
        base_url: base_url,
        events: events,
        contents: contents,
        file_path: file_path,
        config: config,
    });
    
    // Make it available for debugging
    IPython.editor = editor;
    
    var menus = new menubar.MenuBar('#menubar', {
        base_url: base_url,
        editor: editor,
        events: events,
    });
    
    var notification_area = new notificationarea.EditorNotificationArea(
        '#notification_area', {
        events: events,
    });
    notification_area.init_notification_widgets();

    config.loaded.then(function() {
        if (config.data.load_extensions) {
            var nbextension_paths = Object.getOwnPropertyNames(
                                        config.data.load_extensions);
            IPython.load_extensions.apply(this, nbextension_paths);
        }
    });
    editor.load();
    page.show();

    window.onbeforeunload = function () {
        if (!editor.codemirror.isClean(editor.generation)) {
            return "Unsaved changes will be lost. Close anyway?";
        }
    };

});
