// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
], function(IPython, $, utils) {
    // TODO: remove IPython dependency here 
    "use strict";

    // monkey patch CM to be able to syntax highlight cell magics
    // bug reported upstream,
    // see https://github.com/marijnh/CodeMirror2/issues/670
    if(CodeMirror.getMode(1,'text/plain').indent === undefined ){
        CodeMirror.modes.null = function() {
            return {token: function(stream) {stream.skipToEnd();},indent : function(){return 0;}};
        };
    }

    CodeMirror.patchedGetMode = function(config, mode){
            var cmmode = CodeMirror.getMode(config, mode);
            if(cmmode.indent === null) {
                console.log('patch mode "' , mode, '" on the fly');
                cmmode.indent = function(){return 0;};
            }
            return cmmode;
        };
    // end monkey patching CodeMirror

    var Cell = function (options) {
        // Constructor
        //
        // The Base `Cell` class from which to inherit.
        //
        // Parameters:
        //  options: dictionary
        //      Dictionary of keyword arguments.
        //          events: $(Events) instance 
        //          config: dictionary
        //          keyboard_manager: KeyboardManager instance 
        options = options || {};
        this.keyboard_manager = options.keyboard_manager;
        this.events = options.events;
        var config = this.mergeopt(Cell, options.config);
        // superclass default overwrite our default
        
        this.placeholder = config.placeholder || '';
        this.read_only = config.cm_config.readOnly;
        this.selected = false;
        this.rendered = false;
        this.mode = 'command';
        this.metadata = {};
        // load this from metadata later ?
        this.user_highlight = 'auto';
        this.cm_config = config.cm_config;
        this.cell_id = utils.uuid();
        this._options = config;

        // For JS VM engines optimization, attributes should be all set (even
        // to null) in the constructor, and if possible, if different subclass
        // have new attributes with same name, they should be created in the
        // same order. Easiest is to create and set to null in parent class.

        this.element = null;
        this.cell_type = this.cell_type || null;
        this.code_mirror = null;

        this.create_element();
        if (this.element !== null) {
            this.element.data("cell", this);
            this.bind_events();
            this.init_classes();
        }
    };

    Cell.options_default = {
        cm_config : {
            indentUnit : 4,
            readOnly: false,
            theme: "default",
            extraKeys: {
                "Cmd-Right":"goLineRight",
                "End":"goLineRight",
                "Cmd-Left":"goLineLeft"
            }
        }
    };
    
    // FIXME: Workaround CM Bug #332 (Safari segfault on drag)
    // by disabling drag/drop altogether on Safari
    // https://github.com/marijnh/CodeMirror/issues/332    
    if (utils.browser[0] == "Safari") {
        Cell.options_default.cm_config.dragDrop = false;
    }

    Cell.prototype.mergeopt = function(_class, options, overwrite){
        options = options || {};
        overwrite = overwrite || {};
        return $.extend(true, {}, _class.options_default, options, overwrite);
    };

    
     /**
     * Subclasses must implement create_element.
     * This should contain all the code to create the DOM element in notebook
     * and will be called by Base Class constructor.
     * 
     * In this base class constructor, should be
     * element of the DOM having to be common to all cell,
     * regardless of their type.
     * Subclasses should get the common element and fill them.
     * @method create_element 
     **/
    
    Cell.prototype.create_element = function () {
        var cell =  $('<div></div>').addClass('cell');
        cell.attr('tabindex','2');
        
        this.element = cell;
        
    };

    Cell.prototype.init_classes = function () {
        // Call after this.element exists to initialize the css classes
        // related to selected, rendered and mode.
        if (this.selected) {
            this.element.addClass('selected');
        } else {
            this.element.addClass('unselected');
        }
        if (this.rendered) {
            this.element.addClass('rendered');
        } else {
            this.element.addClass('unrendered');
        }
        if (this.mode === 'edit') {
            this.element.addClass('edit_mode');
        } else {
            this.element.addClass('command_mode');
        }
        

    };

    /**
     * Subclasses can implement override bind_events.
     * Be carefull to call the parent method when overwriting as it fires event.
     * this will be triggerd after create_element in constructor.
     * @method bind_events
     */
    Cell.prototype.bind_events = function () {
        var that = this;
        // We trigger events so that Cell doesn't have to depend on Notebook.
        that.element.click(function (event) {
            if (!that.selected) {
                that.events.trigger('select.Cell', {'cell':that});
            }
        });
        that.element.focusin(function (event) {
            if (!that.selected) {
                that.events.trigger('select.Cell', {'cell':that});
            }
        });
        if (this.code_mirror) {
            this.code_mirror.on("change", function(cm, change) {
                that.events.trigger("set_dirty.Notebook", {value: true});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('focus', function(cm, change) {
                that.events.trigger('edit_mode.Cell', {cell: that});
            });
        }
        if (this.code_mirror) {
            this.code_mirror.on('blur', function(cm, change) {
                that.events.trigger('command_mode.Cell', {cell: that});
            });
        }
    };
    
    /**
     * This method gets called in CodeMirror's onKeyDown/onKeyPress
     * handlers and is used to provide custom key handling.
     *
     * To have custom handling, subclasses should override this method, but still call it
     * in order to process the Edit mode keyboard shortcuts.
     *
     * @method handle_codemirror_keyevent
     * @param {CodeMirror} editor - The codemirror instance bound to the cell
     * @param {event} event - key press event which either should or should not be handled by CodeMirror
     * @return {Boolean} `true` if CodeMirror should ignore the event, `false` Otherwise
     */
    Cell.prototype.handle_codemirror_keyevent = function (editor, event) {
        var shortcuts = this.keyboard_manager.edit_shortcuts;

        // if this is an edit_shortcuts shortcut, the global keyboard/shortcut
        // manager will handle it
        if (shortcuts.handles(event)) { return true; }
        
        return false;
    };


    /**
     * Triger typsetting of math by mathjax on current cell element
     * @method typeset
     */
    Cell.prototype.typeset = function () {
        if (window.MathJax) {
            var cell_math = this.element.get(0);
            MathJax.Hub.Queue(["Typeset", MathJax.Hub, cell_math]);
        }
    };

    /**
     * handle cell level logic when a cell is selected
     * @method select
     * @return is the action being taken
     */
    Cell.prototype.select = function () {
        if (!this.selected) {
            this.element.addClass('selected');
            this.element.removeClass('unselected');
            this.selected = true;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is unselected
     * @method unselect
     * @return is the action being taken
     */
    Cell.prototype.unselect = function () {
        if (this.selected) {
            this.element.addClass('unselected');
            this.element.removeClass('selected');
            this.selected = false;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is rendered
     * @method render
     * @return is the action being taken
     */
    Cell.prototype.render = function () {
        if (!this.rendered) {
            this.element.addClass('rendered');
            this.element.removeClass('unrendered');
            this.rendered = true;
            return true;
        } else {
            return false;
        }
    };

    /**
     * handle cell level logic when a cell is unrendered
     * @method unrender
     * @return is the action being taken
     */
    Cell.prototype.unrender = function () {
        if (this.rendered) {
            this.element.addClass('unrendered');
            this.element.removeClass('rendered');
            this.rendered = false;
            return true;
        } else {
            return false;
        }
    };

    /**
     * Delegates keyboard shortcut handling to either IPython keyboard
     * manager when in command mode, or CodeMirror when in edit mode
     *
     * @method handle_keyevent
     * @param {CodeMirror} editor - The codemirror instance bound to the cell
     * @param {event} - key event to be handled
     * @return {Boolean} `true` if CodeMirror should ignore the event, `false` Otherwise
     */
    Cell.prototype.handle_keyevent = function (editor, event) {

        // console.log('CM', this.mode, event.which, event.type)

        if (this.mode === 'command') {
            return true;
        } else if (this.mode === 'edit') {
            return this.handle_codemirror_keyevent(editor, event);
        }
    };

    /**
     * @method at_top
     * @return {Boolean}
     */
    Cell.prototype.at_top = function () {
        var cm = this.code_mirror;
        var cursor = cm.getCursor();
        if (cursor.line === 0 && cursor.ch === 0) {
            return true;
        }
        return false;
    };

    /**
     * @method at_bottom
     * @return {Boolean}
     * */
    Cell.prototype.at_bottom = function () {
        var cm = this.code_mirror;
        var cursor = cm.getCursor();
        if (cursor.line === (cm.lineCount()-1) && cursor.ch === cm.getLine(cursor.line).length) {
            return true;
        }
        return false;
    };

    /**
     * enter the command mode for the cell
     * @method command_mode
     * @return is the action being taken
     */
    Cell.prototype.command_mode = function () {
        if (this.mode !== 'command') {
            this.element.addClass('command_mode');
            this.element.removeClass('edit_mode');
            this.mode = 'command';
            return true;
        } else {
            return false;
        }
    };

    /**
     * enter the edit mode for the cell
     * @method command_mode
     * @return is the action being taken
     */
    Cell.prototype.edit_mode = function () {
        if (this.mode !== 'edit') {
            this.element.addClass('edit_mode');
            this.element.removeClass('command_mode');
            this.mode = 'edit';
            return true;
        } else {
            return false;
        }
    };
    
    /**
     * Focus the cell in the DOM sense
     * @method focus_cell
     */
    Cell.prototype.focus_cell = function () {
        this.element.focus();
    };

    /**
     * Focus the editor area so a user can type
     *
     * NOTE: If codemirror is focused via a mouse click event, you don't want to
     * call this because it will cause a page jump.
     * @method focus_editor
     */
    Cell.prototype.focus_editor = function () {
        this.refresh();
        this.code_mirror.focus();
    };

    /**
     * Refresh codemirror instance
     * @method refresh
     */
    Cell.prototype.refresh = function () {
        this.code_mirror.refresh();
    };

    /**
     * should be overritten by subclass
     * @method get_text
     */
    Cell.prototype.get_text = function () {
    };

    /**
     * should be overritten by subclass
     * @method set_text
     * @param {string} text
     */
    Cell.prototype.set_text = function (text) {
    };

    /**
     * should be overritten by subclass
     * serialise cell to json.
     * @method toJSON
     **/
    Cell.prototype.toJSON = function () {
        var data = {};
        data.metadata = this.metadata;
        data.cell_type = this.cell_type;
        return data;
    };


    /**
     * should be overritten by subclass
     * @method fromJSON
     **/
    Cell.prototype.fromJSON = function (data) {
        if (data.metadata !== undefined) {
            this.metadata = data.metadata;
        }
        
        // Csstag
        
        
        if (this.metadata.hasOwnProperty('jupyter')){
            
            for (name in this.metadata.jupyter){
                
                if(typeof(this.metadata.jupyter[name]) == 'string'){
                    this.element.addClass(this.metadata.jupyter[name]);
                    
                }else if((typeof(this.metadata.jupyter[name])=='boolean')&&(this.metadata.jupyter[name] == true)){
                    this.element.addClass(name);
                    
                }else{//should never append
                    console.log('Error: bad csstag metadata, '+name+' tag is avoided ');
                }
            }
        }
        
        this.celltoolbar.rebuild();
    };


    /**
     * can the cell be split into two cells
     * @method is_splittable
     **/
    Cell.prototype.is_splittable = function () {
        return true;
    };


    /**
     * can the cell be merged with other cells
     * @method is_mergeable
     **/
    Cell.prototype.is_mergeable = function () {
        return true;
    };


    /**
     * @return {String} - the text before the cursor
     * @method get_pre_cursor
     **/
    Cell.prototype.get_pre_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var text = this.code_mirror.getRange({line:0, ch:0}, cursor);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    };


    /**
     * @return {String} - the text after the cursor
     * @method get_post_cursor
     **/
    Cell.prototype.get_post_cursor = function () {
        var cursor = this.code_mirror.getCursor();
        var last_line_num = this.code_mirror.lineCount()-1;
        var last_line_len = this.code_mirror.getLine(last_line_num).length;
        var end = {line:last_line_num, ch:last_line_len};
        var text = this.code_mirror.getRange(cursor, end);
        text = text.replace(/^\n+/, '').replace(/\n+$/, '');
        return text;
    };

    /**
     * Show/Hide CodeMirror LineNumber
     * @method show_line_numbers
     *
     * @param value {Bool}  show (true), or hide (false) the line number in CodeMirror
     **/
    Cell.prototype.show_line_numbers = function (value) {
        this.code_mirror.setOption('lineNumbers', value);
        this.code_mirror.refresh();
    };

    /**
     * Toggle  CodeMirror LineNumber
     * @method toggle_line_numbers
     **/
    Cell.prototype.toggle_line_numbers = function () {
        var val = this.code_mirror.getOption('lineNumbers');
        this.show_line_numbers(!val);
    };

    /**
     * Force codemirror highlight mode
     * @method force_highlight
     * @param {object} - CodeMirror mode
     **/
    Cell.prototype.force_highlight = function(mode) {
        this.user_highlight = mode;
        this.auto_highlight();
    };
    
    /**
     * Try to autodetect cell highlight mode, or use selected mode
     * @methods _auto_highlight
     * @private
     * @param {String|object|undefined} - CodeMirror mode | 'auto'
     **/
    Cell.prototype._auto_highlight = function (modes) {
        //Here we handle manually selected modes
        var mode;
        if( this.user_highlight !== undefined &&  this.user_highlight != 'auto' )
        {
            mode = this.user_highlight;
            CodeMirror.autoLoadMode(this.code_mirror, mode);
            this.code_mirror.setOption('mode', mode);
            return;
        }
        var current_mode = this.code_mirror.getOption('mode', mode);
        var first_line = this.code_mirror.getLine(0);
        // loop on every pairs
        for(mode in modes) {
            var regs = modes[mode].reg;
            // only one key every time but regexp can't be keys...
            for(var i=0; i<regs.length; i++) {
                // here we handle non magic_modes
                if(first_line.match(regs[i]) !== null) {
                    if(current_mode == mode){
                        return;
                    }
                    if (mode.search('magic_') !== 0) {
                        this.code_mirror.setOption('mode', mode);
                        CodeMirror.autoLoadMode(this.code_mirror, mode);
                        return;
                    }
                    var open = modes[mode].open || "%%";
                    var close = modes[mode].close || "%%end";
                    var mmode = mode;
                    mode = mmode.substr(6);
                    if(current_mode == mode){
                        return;
                    }
                    CodeMirror.autoLoadMode(this.code_mirror, mode);
                    // create on the fly a mode that swhitch between
                    // plain/text and smth else otherwise `%%` is
                    // source of some highlight issues.
                    // we use patchedGetMode to circumvent a bug in CM
                    CodeMirror.defineMode(mmode , function(config) {
                        return CodeMirror.multiplexingMode(
                        CodeMirror.patchedGetMode(config, 'text/plain'),
                            // always set someting on close
                            {open: open, close: close,
                             mode: CodeMirror.patchedGetMode(config, mode),
                             delimStyle: "delimit"
                            }
                        );
                    });
                    this.code_mirror.setOption('mode', mmode);
                    return;
                }
            }
            
            
        }
        // fallback on default
        var default_mode;
        try {
            default_mode = this._options.cm_config.mode;
        } catch(e) {
            default_mode = 'text/plain';
        }
        if( current_mode === default_mode){
            return;
        }
        this.code_mirror.setOption('mode', default_mode);
    };
    
    /**
     * Add a tag to the cell.
     * A tag consist in:
     *   - a metadata element 
     *   - a corresponding class added to the cell DOM element
     * This function is a general API, particular usecase should call it
     * @method add_tag
     * @param {String} the tag name
     * @param {String} the value associated with the tag
     * @param {String} the dedicated namespace in metadata
     * @param {String} to avoid namespace collision in html, the class_name is the tag prefixed by this string.
     */
    Cell.prototype.add_tag = function(tag, value, metadata_prefix, class_tag_prefix){
        var class_name = class_tag_prefix +'-'+ tag;
        var meta = this.metadata;
        
        if('metadata_prefix' == ''){
            console.log("Empty metadata prefix is forbidden, to avoid name collision")
        }
        else if(meta.hasOwnProperty(metadata_prefix)){
            meta[metadata_prefix][tag] = value;
            this.element.addClass(class_name);
        }
        else{
            meta[metadata_prefix] = {};
            meta[metadata_prefix][tag] = value;
            this.element.addClass(class_name);
        }
    };
    
    /**
     * Remove a tag from the cell.
     * A tag consist in:
     *   - a metadata element 
     *   - a corresponding class added to the cell DOM element
     * This function is a general API, particular usecase should call it
     * @method add_tag
     * @param {String} the tag name
     * @param {String} the value associated with the tag
     * @param {String} the dedicated namespace in metadata
     * @param {String} to avoid namespace collision in html, the class_name is the tag prefixed by this string.
     */
    Cell.prototype.remove_tag = function(tag, metadata_prefix, class_tag_prefix){
        var class_name = class_tag_prefix +'-'+ tag;
        var meta = this.metadata;
        
        if('metadata_prefix' == ''){
            console.log("Empty metadata prefix is forbidden, to avoid name collision")
        }
        else if(meta.hasOwnProperty(metadata_prefix)){  
            delete meta[metadata_prefix][tag];
            this.element.removeClass(class_name);
        }
        else{
            console.log("Warning, attempt to remove tag from unexisting metadata namespace")
        }
    };
    
    /**
     * API: The css tag
     * ================
     * 
     * 
     * These tag's class should correspond **exclusively** with css selectors.
     * The purpose, is notebook presentation without beeing invasive in the DOM but instead by 
     * adding and remove class from the **cell div**. 
     * 
     * A class called 'csstag_present' activate the css. If removed, all css should be unactivated.
     * 
     * The possible css tag are of two types:
     *  
     *  - a single modal css selector tag. It consists in css rules that are not compatible with each other. 
     *   In metadata, it is implemented by the key 'type' and the value is a string containing the name of the tag
     *   
     *  - several optional css selector tag. In metadata it should be implemented by a key which is the name tag, and a boolean value. 
     *
     * Set (add if doesn't exist) a css tag to the value.
     * If the tag name is 'type' value should be a string, else value should be boolean
     * See 'API: The css tag' for details
     *  
     * @method set_csstag
     * @param {String} the tag name
     * @param {String} the value associated with the tag
     */
    Cell.prototype.set_csstag = function(tag, value){
        // Check for incorrect API call
        // Right now the API is to have a reserved modal name 'type' for
        // the all cell and options. It could evolve in the future
        if(!( (tag == 'type' && typeof(value) == 'string') || (tag != 'type' && typeof(value)=='boolean'))){
            console.log("Error, 'type' is a reserved tag name corresponding with modal css selector tag, should not be used this way");
        }else{
            // API Here the tag prefix is set
            this.add_tag(tag, value, 'jupyter', 'jupyter');
        }
    }

    /**
     * Remove the tag from DOM and metadata. Usualy, you might 
     * set the csstag to an other value.
     *  
     * @method remove_csstag
     * @param {String} the tag name
     */

    Cell.prototype.remove_csstag = function(tag){
        this.add_tag(tag, 'jupyter', 'jupyter');
    };

    // Backwards compatibility.
    IPython.Cell = Cell;

    return {'Cell': Cell};
});