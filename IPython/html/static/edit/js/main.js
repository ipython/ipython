// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/namespace',
    'base/js/utils',
    'base/js/page',
    'base/js/events',
    'contents',
    'services/config',
    'edit/js/editor',
    'edit/js/menubar',
    'edit/js/savewidget',
    'edit/js/notificationarea',
    'custom/custom',
], function(
    $,
    IPython,
    utils,
    page,
    events,
    contents,
    configmod,
    editmod,
    menubar,
    savewidget,
    notificationarea
    ){
    "use strict";
    page = new page.Page();

    var base_url = utils.get_body_data('baseUrl');
    var file_path = utils.get_body_data('filePath');
    var config = new configmod.ConfigSection('edit', {base_url: base_url});
    config.load();
    var common_config = new configmod.ConfigSection('common', {base_url: base_url});
    common_config.load();
    contents = new contents.Contents({
        base_url: base_url,
        common_config: common_config
    });
    
    var editor = new editmod.Editor('#texteditor-container', {
        base_url: base_url,
        events: events,
        contents: contents,
        file_path: file_path,
        config: config,
    });
    
    // Make it available for debugging
    IPython.editor = editor;
    
    var save_widget = new savewidget.SaveWidget('span#save_widget', {
        editor: editor,
        events: events,
    });
    
    var menus = new menubar.MenuBar('#menubar', {
        base_url: base_url,
        editor: editor,
        events: events,
        save_widget: save_widget,
    });
    
    var notification_area = new notificationarea.EditorNotificationArea(
        '#notification_area', {
        events: events,
    });
    editor.notification_area = notification_area;
    notification_area.init_notification_widgets();

    utils.load_extensions_from_config(config);
    utils.load_extensions_from_config(common_config);
    editor.load();
    page.show();

    window.onbeforeunload = function () {
        if (editor.save_enabled && !editor.codemirror.isClean(editor.generation)) {
            return "Unsaved changes will be lost. Close anyway?";
        }
    };

    // Make sure the codemirror editor is sized appropriatley.
    var _handle_resize = function() {
        var backdrop = $("#texteditor-backdrop");

        // account for padding on the backdrop wrapper
        var padding = backdrop.outerHeight(true) - backdrop.height();
        $('div.CodeMirror').height($("#site").height() - padding);
    };
    $(window).resize(_handle_resize);

    // On document ready, resize codemirror.
    $(document).ready(_handle_resize);
});
