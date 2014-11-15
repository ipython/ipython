// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

require([
    'jquery',
    'base/js/namespace',
    'base/js/utils',
    'base/js/page',
    'base/js/events',
    'contents',
    'texteditor/js/editor',
    'texteditor/js/menubar',
    'texteditor/js/notificationarea',
    'custom/custom',
], function(
    $,
    IPython,
    utils,
    page,
    events,
    contents,
    editor,
    menubar,
    notificationarea
    ){
    page = new page.Page();

    var base_url = utils.get_body_data('baseUrl');
    var file_path = utils.get_body_data('filePath');
    contents = new contents.Contents({base_url: base_url});
    
    var editor = new editor.Editor('#texteditor-container', {
        base_url: base_url,
        events: events,
        contents: contents,
        file_path: file_path,
    });
    
    // Make it available for debugging
    IPython.editor = editor;
    
    var menus = new menubar.MenuBar('#menubar', {
        base_url: base_url,
        editor: editor,
    });
    
    var notification_area = new notificationarea.EditorNotificationArea(
        '#notification_area', {
        events: events,
    });
    notification_area.init_notification_widgets();

    editor.load();
    page.show();
});
