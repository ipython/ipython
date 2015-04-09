// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.
/**
 *
 *
 * @module keyboard
 * @namespace keyboard
 * @class ShortcutManager
 */

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils',
    'underscore',
], function(IPython, $, utils, _) {
    "use strict";


    /**
     * Setup global keycodes and inverse keycodes.
     * 
     * See http://unixpapa.com/js/key.html for a complete description. The short of
     * it is that there are different keycode sets. Firefox uses the "Mozilla keycodes"
     * and Webkit/IE use the "IE keycodes". These keycode sets are mostly the same
     * but have minor differences.
     **/

     // These apply to Firefox, (Webkit and IE)
     // This does work **only** on US keyboard.
    var _keycodes = {
        'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71, 'h': 72, 'i': 73,
        'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79, 'p': 80, 'q': 81, 'r': 82,
        's': 83, 't': 84, 'u': 85, 'v': 86, 'w': 87, 'x': 88, 'y': 89, 'z': 90,
        '1 !': 49, '2 @': 50, '3 #': 51, '4 $': 52, '5 %': 53, '6 ^': 54,
        '7 &': 55, '8 *': 56, '9 (': 57, '0 )': 48, 
        '[ {': 219, '] }': 221, '` ~': 192,  ', <': 188, '. >': 190, '/ ?': 191,
        '\\ |': 220, '\' "': 222,
        'numpad0': 96, 'numpad1': 97, 'numpad2': 98, 'numpad3': 99, 'numpad4': 100,
        'numpad5': 101, 'numpad6': 102, 'numpad7': 103, 'numpad8': 104, 'numpad9': 105,
        'multiply': 106, 'add': 107, 'subtract': 109, 'decimal': 110, 'divide': 111,
        'f1': 112, 'f2': 113, 'f3': 114, 'f4': 115, 'f5': 116, 'f6': 117, 'f7': 118,
        'f8': 119, 'f9': 120, 'f11': 122, 'f12': 123, 'f13': 124, 'f14': 125, 'f15': 126,
        'backspace': 8, 'tab': 9, 'enter': 13, 'shift': 16, 'ctrl': 17, 'alt': 18,
        'meta': 91, 'capslock': 20, 'esc': 27, 'space': 32, 'pageup': 33, 'pagedown': 34,
        'end': 35, 'home': 36, 'left': 37, 'up': 38, 'right': 39, 'down': 40,
        'insert': 45, 'delete': 46, 'numlock': 144,
    };
    
    // These apply to Firefox and Opera
    var _mozilla_keycodes = {
        '; :': 59, '= +': 61, '- _': 173, 'meta': 224
    };
    
    // This apply to Webkit and IE
    var _ie_keycodes = {
        '; :': 186, '= +': 187, '- _': 189
    };
    
    var browser = utils.browser[0];
    var platform = utils.platform;
    
    if (browser === 'Firefox' || browser === 'Opera' || browser === 'Netscape') {
        $.extend(_keycodes, _mozilla_keycodes);
    } else if (browser === 'Safari' || browser === 'Chrome' || browser === 'MSIE') {
        $.extend(_keycodes, _ie_keycodes);
    }

    var keycodes = {};
    var inv_keycodes = {};
    for (var name in _keycodes) {
        var names = name.split(' ');
        if (names.length === 1) {
            var n = names[0];
            keycodes[n] = _keycodes[n];
            inv_keycodes[_keycodes[n]] = n;
        } else {
            var primary = names[0];
            var secondary = names[1];
            keycodes[primary] = _keycodes[name];
            keycodes[secondary] = _keycodes[name];
            inv_keycodes[_keycodes[name]] = primary;
        }
    }

    var normalize_key = function (key) {
        return inv_keycodes[keycodes[key]];
    };

    var normalize_shortcut = function (shortcut) {
        /**
         * @function _normalize_shortcut
         * @private
         * return a dict containing the normalized shortcut and the number of time it should be pressed:
         *
         * Put a shortcut into normalized form:
         * 1. Make lowercase
         * 2. Replace cmd by meta
         * 3. Sort '-' separated modifiers into the order alt-ctrl-meta-shift
         * 4. Normalize keys
         **/
        if (platform === 'MacOS') {
            shortcut = shortcut.toLowerCase().replace('cmdtrl-', 'cmd-');
        } else {
            shortcut = shortcut.toLowerCase().replace('cmdtrl-', 'ctrl-');
        }

        shortcut = shortcut.toLowerCase().replace('cmd', 'meta');
        shortcut = shortcut.replace(/-$/, '_');  // catch shortcuts using '-' key
        shortcut = shortcut.replace(/,$/, 'comma');  // catch shortcuts using '-' key
        if(shortcut.indexOf(',') !== -1){
            var sht = shortcut.split(',');
            sht = _.map(sht, normalize_shortcut);
            return shortcut;
        }
        shortcut = shortcut.replace(/comma/g, ',');  // catch shortcuts using '-' key
        var values = shortcut.split("-");
        if (values.length === 1) {
            return normalize_key(values[0]);
        } else {
            var modifiers = values.slice(0,-1);
            var key = normalize_key(values[values.length-1]);
            modifiers.sort();
            return modifiers.join('-') + '-' + key;
        }
    };

    var shortcut_to_event = function (shortcut, type) {
        /**
         * Convert a shortcut (shift-r) to a jQuery Event object
         **/
        type = type || 'keydown';
        shortcut = normalize_shortcut(shortcut);
        shortcut = shortcut.replace(/-$/, '_');  // catch shortcuts using '-' key
        var values = shortcut.split("-");
        var modifiers = values.slice(0,-1);
        var key = values[values.length-1];
        var opts = {which: keycodes[key]};
        if (modifiers.indexOf('alt') !== -1) {opts.altKey = true;}
        if (modifiers.indexOf('ctrl') !== -1) {opts.ctrlKey = true;}
        if (modifiers.indexOf('meta') !== -1) {opts.metaKey = true;}
        if (modifiers.indexOf('shift') !== -1) {opts.shiftKey = true;}
        return $.Event(type, opts);
    };

    var only_modifier_event = function(event){
        /**
         * Return `true` if the event only contains modifiers keys.
         * false otherwise
         **/
        var key = inv_keycodes[event.which];
        return ((event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) && 
         (key === 'alt'|| key === 'ctrl'|| key === 'meta'|| key === 'shift'));

    };

    var event_to_shortcut = function (event) {
        /**
         * Convert a jQuery Event object to a normalized shortcut string (shift-r)
         **/
        var shortcut = '';
        var key = inv_keycodes[event.which];
        if (event.altKey && key !== 'alt') {shortcut += 'alt-';}
        if (event.ctrlKey && key !== 'ctrl') {shortcut += 'ctrl-';}
        if (event.metaKey && key !== 'meta') {shortcut += 'meta-';}
        if (event.shiftKey && key !== 'shift') {shortcut += 'shift-';}
        shortcut += key;
        return shortcut;
    };

    // Shortcut manager class

    var ShortcutManager = function (delay, events, actions, env) {
        /**
         * A class to deal with keyboard event and shortcut
         *
         * @class ShortcutManager
         * @constructor
         */
        this._shortcuts = {};
        this.delay = delay || 800; // delay in milliseconds
        this.events = events;
        this.actions = actions;
        this.actions.extend_env(env);
        this._queue = [];
        this._cleartimeout = null;
        Object.seal(this);
    };

    ShortcutManager.prototype.clearsoon = function(){
        /**
         * Clear the pending shortcut soon, and cancel previous clearing
         * that might be registered.
         **/ 
         var that = this;
         clearTimeout(this._cleartimeout);
         this._cleartimeout = setTimeout(function(){that.clearqueue();}, this.delay);
    };


    ShortcutManager.prototype.clearqueue = function(){
        /**
         * clear the pending shortcut sequence now. 
         **/
        this._queue = [];
        clearTimeout(this._cleartimeout);
    };


    var flatten_shorttree = function(tree){
        /**
         * Flatten a tree of shortcut sequences. 
         * use full to iterate over all the key/values of available shortcuts.
         **/
        var  dct = {};
        for(var key in tree){
            var value = tree[key];
            if(typeof(value) === 'string'){
                dct[key] = value;
            } else {
                var ftree=flatten_shorttree(value);
                for(var subkey in ftree){
                    dct[key+','+subkey] = ftree[subkey];
                }
            } 
        }
        return dct;
    };

    ShortcutManager.prototype.help = function () {
        var help = [];
        var ftree = flatten_shorttree(this._shortcuts);
        for (var shortcut in ftree) {
            var action = this.actions.get(ftree[shortcut]);
            var help_string = action.help||'== no help ==';
            var help_index = action.help_index;
            if (help_string) {
                var shortstring = (action.shortstring||shortcut);
                help.push({
                    shortcut: shortstring,
                    help: help_string,
                    help_index: help_index}
                );
            }
        }
        help.sort(function (a, b) {
            if (a.help_index === b.help_index) {
                return 0;
            }
            if (a.help_index === undefined || a.help_index > b.help_index){
                return 1;
            }
            return -1;
        });
        return help;
    };

    ShortcutManager.prototype.clear_shortcuts = function () {
        this._shortcuts = {};
    };

    ShortcutManager.prototype.get_shortcut = function (shortcut){
        /**
         * return a node of the shortcut tree which an action name (string) if leaf,
         * and an object with `object.subtree===true`
         **/
        if(typeof(shortcut) === 'string'){
            shortcut = shortcut.split(',');
        }
        
        return this._get_leaf(shortcut, this._shortcuts);
    };


    ShortcutManager.prototype._get_leaf = function(shortcut_array, tree){
        /**
         * @private
         * find a leaf/node in a subtree of the keyboard shortcut
         *
         **/
        if(shortcut_array.length === 1){
            return tree[shortcut_array[0]];
        } else if(  typeof(tree[shortcut_array[0]]) !== 'string'){
            return this._get_leaf(shortcut_array.slice(1), tree[shortcut_array[0]]);
        }
        return null;
    };

    ShortcutManager.prototype.set_shortcut = function( shortcut, action_name){
        if( typeof(action_name) !== 'string'){ throw('action is not a string', action_name);}
        if( typeof(shortcut) === 'string'){
            shortcut = shortcut.split(',');
        }
        return this._set_leaf(shortcut, action_name, this._shortcuts);
    };

    ShortcutManager.prototype._is_leaf = function(shortcut_array, tree){
        if(shortcut_array.length === 1){
           return(typeof(tree[shortcut_array[0]]) === 'string');
        } else {
            var subtree = tree[shortcut_array[0]];
            return this._is_leaf(shortcut_array.slice(1), subtree );
        }
    };

    ShortcutManager.prototype._remove_leaf = function(shortcut_array, tree, allow_node){
        if(shortcut_array.length === 1){
            var current_node = tree[shortcut_array[0]];
            if(typeof(current_node) === 'string'){
                delete tree[shortcut_array[0]];
            } else {
                throw('try to delete non-leaf');
            }
        } else {
            this._remove_leaf(shortcut_array.slice(1),  tree[shortcut_array[0]], allow_node);
            if(_.keys(tree[shortcut_array[0]]).length === 0){
                delete tree[shortcut_array[0]];
            }
        }
    };

    ShortcutManager.prototype._set_leaf = function(shortcut_array, action_name, tree){
        var current_node = tree[shortcut_array[0]];
        if(shortcut_array.length === 1){
            if(current_node !== undefined && typeof(current_node) !== 'string'){
                console.warn('[warning], you are overriting a long shortcut with a shorter one');
            }
            tree[shortcut_array[0]] = action_name;
            return true;
        } else {
            if(typeof(current_node) === 'string'){
                console.warn('you are trying to set a shortcut that will be shadowed'+
                             'by a more specific one. Aborting for :', action_name, 'the follwing '+
                             'will take precedence', current_node);
                return false;
            } else {
                tree[shortcut_array[0]] = tree[shortcut_array[0]]||{};
            }
            this._set_leaf(shortcut_array.slice(1), action_name, tree[shortcut_array[0]]);
            return true;
        }
    };

    ShortcutManager.prototype.add_shortcut = function (shortcut, data, suppress_help_update) {
        /**
         * Add a action to be handled by shortcut manager. 
         * 
         * - `shortcut` should be a `Shortcut Sequence` of the for `Ctrl-Alt-C,Meta-X`...
         * - `data` could be an `action name`, an `action` or a `function`.
         *   if a `function` is passed it will be converted to an anonymous `action`. 
         *
         **/
        var action_name = this.actions.get_name(data);
        if (! action_name){
            throw('does nto know how to deal with ', data);
        }
        
        shortcut = normalize_shortcut(shortcut);
        this.set_shortcut(shortcut, action_name);

        if (!suppress_help_update) {
            // update the keyboard shortcuts notebook help
            this.events.trigger('rebuild.QuickHelp');
        }
    };

    ShortcutManager.prototype.add_shortcuts = function (data) {
        /**
         * Convenient methods to call `add_shortcut(key, value)` on several items
         * 
         *  data : Dict of the form {key:value, ...}
         **/
        for (var shortcut in data) {
            this.add_shortcut(shortcut, data[shortcut], true);
        }
        // update the keyboard shortcuts notebook help
        this.events.trigger('rebuild.QuickHelp');
    };

    ShortcutManager.prototype.remove_shortcut = function (shortcut, suppress_help_update) {
        /**
         * Remove the binding of shortcut `sortcut` with its action.
         * throw an error if trying to remove a non-exiting shortcut
         **/
        shortcut = normalize_shortcut(shortcut);
        if( typeof(shortcut) === 'string'){
            shortcut = shortcut.split(',');
        }
        this._remove_leaf(shortcut, this._shortcuts);
        if (!suppress_help_update) {
            // update the keyboard shortcuts notebook help
            this.events.trigger('rebuild.QuickHelp');
        }
    };



    ShortcutManager.prototype.call_handler = function (event) {
        /**
         * Call the corresponding shortcut handler for a keyboard event
         * @method call_handler
         * @return {Boolean} `true|false`, `false` if no handler was found, otherwise the  value return by the handler. 
         * @param event {event}
         *
         * given an event, call the corresponding shortcut. 
         * return false is event wan handled, true otherwise 
         * in any case returning false stop event propagation
         **/


        this.clearsoon();
        if(only_modifier_event(event)){
            return true;
        }
        var shortcut = event_to_shortcut(event);
        this._queue.push(shortcut);
        var action_name = this.get_shortcut(this._queue);

        if (typeof(action_name) === 'undefined'|| action_name === null){
            this.clearqueue();
            return true;
        }
        
        if (this.actions.exists(action_name)) {
            event.preventDefault();
            this.clearqueue();
            return this.actions.call(action_name, event);
        }

        return false;
    };


    ShortcutManager.prototype.handles = function (event) {
        var shortcut = event_to_shortcut(event);
        var action_name = this.get_shortcut(this._queue.concat(shortcut));
        return (typeof(action_name) !== 'undefined');
    };

    var keyboard = {
        keycodes : keycodes,
        inv_keycodes : inv_keycodes,
        ShortcutManager : ShortcutManager,
        normalize_key : normalize_key,
        normalize_shortcut : normalize_shortcut,
        shortcut_to_event : shortcut_to_event,
        event_to_shortcut : event_to_shortcut,
    };

    // For backwards compatibility.
    IPython.keyboard = keyboard;

    return keyboard;
});
