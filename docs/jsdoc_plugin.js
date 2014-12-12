exports.handlers = {
    newDoclet: function(e) {
        // e.doclet will refer to the newly created doclet
        // you can read and modify properties of that doclet if you wish
        if (typeof e.doclet.name === 'string') {
            if (e.doclet.name[0] == '_') {
                console.log('Private method "' + e.doclet.longname + '" not documented.');
                e.doclet.memberof = '<anonymous>';
            }
        }
    }
};