// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.
require([
    'jquery',
    'base/js/dialog',
    'underscore',
    'base/js/namespace'
], function ($, dialog, _, IPython) {
    'use strict';
    $('#notebook_about').click(function () {
        // use underscore template to auto html escape
        var text = 'You are using IPython notebook.<br/><br/>';
        text = text + 'The version of the notebook server is ';
        text = text + _.template('<b><%- version %></b>')({ version: sys_info.ipython_version });
        if (sys_info.commit_hash) {
            text = text + _.template('-<%- hash %>')({ hash: sys_info.commit_hash });
        }
        text = text + _.template(' and is running on:<br/><pre>Python <%- pyver %></pre>')({ pyver: sys_info.sys_version });
        var kinfo = $('<div/>').attr('id', '#about-kinfo').text('Waiting for kernel to be available...');
        var body = $('<div/>');
        body.append($('<h4/>').text('Server Information:'));
        body.append($('<p/>').html(text));
        body.append($('<h4/>').text('Current Kernel Information:'));
        body.append(kinfo);
        dialog.modal({
            title: 'About IPython Notebook',
            body: body,
            buttons: { 'OK': {} }
        });
        try {
            IPython.notebook.session.kernel.kernel_info(function (data) {
                kinfo.html($('<pre/>').text(data.content.banner));
            });
        } catch (e) {
            kinfo.html($('<p/>').text('unable to contact kernel'));
        }
    });
});
