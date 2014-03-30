//----------------------------------------------------------------------------
//  Copyright (C) 2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// Keyboard management
//============================================================================

IPython.namespace('IPython.keyboard');

IPython.keyboard = (function (IPython) {
    "use strict";

    // Setup global keycodes and inverse keycodes.

    // See http://unixpapa.com/js/key.html for a complete description. The short of
    // it is that there are different keycode sets. Firefox uses the "Mozilla keycodes"
    // and Webkit/IE use the "IE keycodes". These keycode sets are mostly the same
    // but have minor differences.

    // These apply to Firefox, (Webkit and IE)
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
    
    var browser = IPython.utils.browser[0];
    var platform = IPython.utils.platform;
    
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
        // Put a shortcut into normalized form:
        // 1. Make lowercase
        // 2. Replace cmd by meta
        // 3. Sort '-' separated modifiers into the order alt-ctrl-meta-shift
        // 4. Normalize keys
        shortcut = shortcut.toLowerCase().replace('cmd', 'meta');
        shortcut = shortcut.replace(/-$/, '_');  // catch shortcuts using '-' key
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
        // Convert a shortcut (shift-r) to a jQuery Event object
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

    var event_to_shortcut = function (event) {
        // Convert a jQuery Event object to a shortcut (shift-r)
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

    var ShortcutManager = function (delay) {
        this._shortcuts = {};
        this._counts = {};
        this._timers = {};
        this.delay = delay || 800; // delay in milliseconds
    };

    ShortcutManager.prototype.help = function () {
        var help = [];
        for (var shortcut in this._shortcuts) {
            var help_string = this._shortcuts[shortcut]['help'];
            var help_index = this._shortcuts[shortcut]['help_index'];
            if (help_string) {
                if (platform === 'MacOS') {
                    shortcut = shortcut.replace('meta', 'cmd');
                }
                help.push({
                    shortcut: shortcut,
                    help: help_string,
                    help_index: help_index}
                );
            }
        }
        help.sort(function (a, b) {
            if (a.help_index > b.help_index)
                return 1;
            if (a.help_index < b.help_index)
                return -1;
            return 0;
        });
        return help;
    };

    ShortcutManager.prototype.clear_shortcuts = function () {
        this._shortcuts = {};
    };

    ShortcutManager.prototype.add_shortcut = function (shortcut, data, suppress_help_update) {
        if (typeof(data) === 'function') {
            data = {help: '', help_index: '', handler: data};
        }
        data.help_index = data.help_index || '';
        data.help = data.help || '';
        data.count = data.count || 1;
        if (data.help_index === '') {
            data.help_index = 'zz';
        }
        shortcut = normalize_shortcut(shortcut);
        this._counts[shortcut] = 0;
        this._shortcuts[shortcut] = data;
        if (!suppress_help_update) {
            // update the keyboard shortcuts notebook help
            $([IPython.events]).trigger('rebuild.QuickHelp');
        }
    };

    ShortcutManager.prototype.add_shortcuts = function (data) {
        for (var shortcut in data) {
            this.add_shortcut(shortcut, data[shortcut], true);
        }
        // update the keyboard shortcuts notebook help
        $([IPython.events]).trigger('rebuild.QuickHelp');
    };

    ShortcutManager.prototype.remove_shortcut = function (shortcut, suppress_help_update) {
        shortcut = normalize_shortcut(shortcut);
        delete this._counts[shortcut];
        delete this._shortcuts[shortcut];
        if (!suppress_help_update) {
            // update the keyboard shortcuts notebook help
            $([IPython.events]).trigger('rebuild.QuickHelp');
        }
    };

    ShortcutManager.prototype.count_handler = function (shortcut, event, data) {
        var that = this;
        var c = this._counts;
        var t = this._timers;
        var timer = null;
        if (c[shortcut] === data.count-1) {
            c[shortcut] = 0;
            var timer = t[shortcut];
            if (timer) {clearTimeout(timer); delete t[shortcut];}
            return data.handler(event);
        } else {
            c[shortcut] = c[shortcut] + 1;
            timer = setTimeout(function () {
                c[shortcut] = 0;
            }, that.delay);
            t[shortcut] = timer;
        }
        return false;
    };

    ShortcutManager.prototype.call_handler = function (event) {
        var shortcut = event_to_shortcut(event);
        var data = this._shortcuts[shortcut];
        if (data) {
            var handler = data['handler'];
            if (handler) {
                if (data.count === 1) {
                    return handler(event);
                } else if (data.count > 1) {
                    return this.count_handler(shortcut, event, data);
                }
            }
        }
        return true;
    };

    ShortcutManager.prototype.handles = function (event) {
        var shortcut = event_to_shortcut(event);
        var data = this._shortcuts[shortcut];
        return !( data === undefined || data.handler === undefined )
    }

    return {
        keycodes : keycodes,
        inv_keycodes : inv_keycodes,
        ShortcutManager : ShortcutManager,
        normalize_key : normalize_key,
        normalize_shortcut : normalize_shortcut,
        shortcut_to_event : shortcut_to_event,
        event_to_shortcut : event_to_shortcut
    };

}(IPython));
