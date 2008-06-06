/***

MochiKit.Signal 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2006 Jonathan Gardner, Beau Hartshorne, Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Signal');
    dojo.require('MochiKit.Base');
    dojo.require('MochiKit.DOM');
    dojo.require('MochiKit.Style');
}
if (typeof(JSAN) != 'undefined') {
    JSAN.use('MochiKit.Base', []);
    JSAN.use('MochiKit.DOM', []);
    JSAN.use('MochiKit.Style', []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined') {
        throw '';
    }
} catch (e) {
    throw 'MochiKit.Signal depends on MochiKit.Base!';
}

try {
    if (typeof(MochiKit.DOM) == 'undefined') {
        throw '';
    }
} catch (e) {
    throw 'MochiKit.Signal depends on MochiKit.DOM!';
}

try {
    if (typeof(MochiKit.Style) == 'undefined') {
        throw '';
    }
} catch (e) {
    throw 'MochiKit.Signal depends on MochiKit.Style!';
}

if (typeof(MochiKit.Signal) == 'undefined') {
    MochiKit.Signal = {};
}

MochiKit.Signal.NAME = 'MochiKit.Signal';
MochiKit.Signal.VERSION = '1.4';

MochiKit.Signal._observers = [];

/** @id MochiKit.Signal.Event */
MochiKit.Signal.Event = function (src, e) {
    this._event = e || window.event;
    this._src = src;
};

MochiKit.Base.update(MochiKit.Signal.Event.prototype, {

    __repr__: function () {
        var repr = MochiKit.Base.repr;
        var str = '{event(): ' + repr(this.event()) +
            ', src(): ' + repr(this.src()) +
            ', type(): ' + repr(this.type()) +
            ', target(): ' + repr(this.target());

        if (this.type() &&
            this.type().indexOf('key') === 0 ||
            this.type().indexOf('mouse') === 0 ||
            this.type().indexOf('click') != -1 ||
            this.type() == 'contextmenu') {
            str += ', modifier(): ' + '{alt: ' + repr(this.modifier().alt) +
            ', ctrl: ' + repr(this.modifier().ctrl) +
            ', meta: ' + repr(this.modifier().meta) +
            ', shift: ' + repr(this.modifier().shift) +
            ', any: ' + repr(this.modifier().any) + '}';
        }

        if (this.type() && this.type().indexOf('key') === 0) {
            str += ', key(): {code: ' + repr(this.key().code) +
                ', string: ' + repr(this.key().string) + '}';
        }

        if (this.type() && (
            this.type().indexOf('mouse') === 0 ||
            this.type().indexOf('click') != -1 ||
            this.type() == 'contextmenu')) {

            str += ', mouse(): {page: ' + repr(this.mouse().page) +
                ', client: ' + repr(this.mouse().client);

            if (this.type() != 'mousemove') {
                str += ', button: {left: ' + repr(this.mouse().button.left) +
                    ', middle: ' + repr(this.mouse().button.middle) +
                    ', right: ' + repr(this.mouse().button.right) + '}}';
            } else {
                str += '}';
            }
        }
        if (this.type() == 'mouseover' || this.type() == 'mouseout') {
            str += ', relatedTarget(): ' + repr(this.relatedTarget());
        }
        str += '}';
        return str;
    },

     /** @id MochiKit.Signal.Event.prototype.toString */
    toString: function () {
        return this.__repr__();
    },

    /** @id MochiKit.Signal.Event.prototype.src */
    src: function () {
        return this._src;
    },

    /** @id MochiKit.Signal.Event.prototype.event  */
    event: function () {
        return this._event;
    },

    /** @id MochiKit.Signal.Event.prototype.type */
    type: function () {
        return this._event.type || undefined;
    },

    /** @id MochiKit.Signal.Event.prototype.target */
    target: function () {
        return this._event.target || this._event.srcElement;
    },

    _relatedTarget: null,
    /** @id MochiKit.Signal.Event.prototype.relatedTarget */
    relatedTarget: function () {
        if (this._relatedTarget !== null) {
            return this._relatedTarget;
        }

        var elem = null;
        if (this.type() == 'mouseover') {
            elem = (this._event.relatedTarget ||
                this._event.fromElement);
        } else if (this.type() == 'mouseout') {
            elem = (this._event.relatedTarget ||
                this._event.toElement);
        }
        if (elem !== null) {
            this._relatedTarget = elem;
            return elem;
        }

        return undefined;
    },

    _modifier: null,
    /** @id MochiKit.Signal.Event.prototype.modifier */
    modifier: function () {
        if (this._modifier !== null) {
            return this._modifier;
        }
        var m = {};
        m.alt = this._event.altKey;
        m.ctrl = this._event.ctrlKey;
        m.meta = this._event.metaKey || false; // IE and Opera punt here
        m.shift = this._event.shiftKey;
        m.any = m.alt || m.ctrl || m.shift || m.meta;
        this._modifier = m;
        return m;
    },

    _key: null,
    /** @id MochiKit.Signal.Event.prototype.key */
    key: function () {
        if (this._key !== null) {
            return this._key;
        }
        var k = {};
        if (this.type() && this.type().indexOf('key') === 0) {

            /*

                If you're looking for a special key, look for it in keydown or
                keyup, but never keypress. If you're looking for a Unicode
                chracter, look for it with keypress, but never keyup or
                keydown.

                Notes:

                FF key event behavior:
                key     event   charCode    keyCode
                DOWN    ku,kd   0           40
                DOWN    kp      0           40
                ESC     ku,kd   0           27
                ESC     kp      0           27
                a       ku,kd   0           65
                a       kp      97          0
                shift+a ku,kd   0           65
                shift+a kp      65          0
                1       ku,kd   0           49
                1       kp      49          0
                shift+1 ku,kd   0           0
                shift+1 kp      33          0

                IE key event behavior:
                (IE doesn't fire keypress events for special keys.)
                key     event   keyCode
                DOWN    ku,kd   40
                DOWN    kp      undefined
                ESC     ku,kd   27
                ESC     kp      27
                a       ku,kd   65
                a       kp      97
                shift+a ku,kd   65
                shift+a kp      65
                1       ku,kd   49
                1       kp      49
                shift+1 ku,kd   49
                shift+1 kp      33

                Safari key event behavior:
                (Safari sets charCode and keyCode to something crazy for
                special keys.)
                key     event   charCode    keyCode
                DOWN    ku,kd   63233       40
                DOWN    kp      63233       63233
                ESC     ku,kd   27          27
                ESC     kp      27          27
                a       ku,kd   97          65
                a       kp      97          97
                shift+a ku,kd   65          65
                shift+a kp      65          65
                1       ku,kd   49          49
                1       kp      49          49
                shift+1 ku,kd   33          49
                shift+1 kp      33          33

            */

            /* look for special keys here */
            if (this.type() == 'keydown' || this.type() == 'keyup') {
                k.code = this._event.keyCode;
                k.string = (MochiKit.Signal._specialKeys[k.code] ||
                    'KEY_UNKNOWN');
                this._key = k;
                return k;

            /* look for characters here */
            } else if (this.type() == 'keypress') {

                /*

                    Special key behavior:

                    IE: does not fire keypress events for special keys
                    FF: sets charCode to 0, and sets the correct keyCode
                    Safari: sets keyCode and charCode to something stupid

                */

                k.code = 0;
                k.string = '';

                if (typeof(this._event.charCode) != 'undefined' &&
                    this._event.charCode !== 0 &&
                    !MochiKit.Signal._specialMacKeys[this._event.charCode]) {
                    k.code = this._event.charCode;
                    k.string = String.fromCharCode(k.code);
                } else if (this._event.keyCode &&
                    typeof(this._event.charCode) == 'undefined') { // IE
                    k.code = this._event.keyCode;
                    k.string = String.fromCharCode(k.code);
                }

                this._key = k;
                return k;
            }
        }
        return undefined;
    },

    _mouse: null,
    /** @id MochiKit.Signal.Event.prototype.mouse */
    mouse: function () {
        if (this._mouse !== null) {
            return this._mouse;
        }

        var m = {};
        var e = this._event;

        if (this.type() && (
            this.type().indexOf('mouse') === 0 ||
            this.type().indexOf('click') != -1 ||
            this.type() == 'contextmenu')) {

            m.client = new MochiKit.Style.Coordinates(0, 0);
            if (e.clientX || e.clientY) {
                m.client.x = (!e.clientX || e.clientX < 0) ? 0 : e.clientX;
                m.client.y = (!e.clientY || e.clientY < 0) ? 0 : e.clientY;
            }

            m.page = new MochiKit.Style.Coordinates(0, 0);
            if (e.pageX || e.pageY) {
                m.page.x = (!e.pageX || e.pageX < 0) ? 0 : e.pageX;
                m.page.y = (!e.pageY || e.pageY < 0) ? 0 : e.pageY;
            } else {
                /*

                    The IE shortcut can be off by two. We fix it. See:
                    http://msdn.microsoft.com/workshop/author/dhtml/reference/methods/getboundingclientrect.asp

                    This is similar to the method used in
                    MochiKit.Style.getElementPosition().

                */
                var de = MochiKit.DOM._document.documentElement;
                var b = MochiKit.DOM._document.body;

                m.page.x = e.clientX +
                    (de.scrollLeft || b.scrollLeft) -
                    (de.clientLeft || 0);

                m.page.y = e.clientY +
                    (de.scrollTop || b.scrollTop) -
                    (de.clientTop || 0);

            }
            if (this.type() != 'mousemove') {
                m.button = {};
                m.button.left = false;
                m.button.right = false;
                m.button.middle = false;

                /* we could check e.button, but which is more consistent */
                if (e.which) {
                    m.button.left = (e.which == 1);
                    m.button.middle = (e.which == 2);
                    m.button.right = (e.which == 3);

                    /*

                        Mac browsers and right click:

                            - Safari doesn't fire any click events on a right
                              click:
                              http://bugs.webkit.org/show_bug.cgi?id=6595

                            - Firefox fires the event, and sets ctrlKey = true

                            - Opera fires the event, and sets metaKey = true

                        oncontextmenu is fired on right clicks between
                        browsers and across platforms.

                    */

                } else {
                    m.button.left = !!(e.button & 1);
                    m.button.right = !!(e.button & 2);
                    m.button.middle = !!(e.button & 4);
                }
            }
            this._mouse = m;
            return m;
        }
        return undefined;
    },

    /** @id MochiKit.Signal.Event.prototype.stop */
    stop: function () {
        this.stopPropagation();
        this.preventDefault();
    },

    /** @id MochiKit.Signal.Event.prototype.stopPropagation */
    stopPropagation: function () {
        if (this._event.stopPropagation) {
            this._event.stopPropagation();
        } else {
            this._event.cancelBubble = true;
        }
    },

    /** @id MochiKit.Signal.Event.prototype.preventDefault */
    preventDefault: function () {
        if (this._event.preventDefault) {
            this._event.preventDefault();
        } else if (this._confirmUnload === null) {
            this._event.returnValue = false;
        }
    },

    _confirmUnload: null,

    /** @id MochiKit.Signal.Event.prototype.confirmUnload */
    confirmUnload: function (msg) {
        if (this.type() == 'beforeunload') {
            this._confirmUnload = msg;
            this._event.returnValue = msg;
        }
    }
});

/* Safari sets keyCode to these special values onkeypress. */
MochiKit.Signal._specialMacKeys = {
    3: 'KEY_ENTER',
    63289: 'KEY_NUM_PAD_CLEAR',
    63276: 'KEY_PAGE_UP',
    63277: 'KEY_PAGE_DOWN',
    63275: 'KEY_END',
    63273: 'KEY_HOME',
    63234: 'KEY_ARROW_LEFT',
    63232: 'KEY_ARROW_UP',
    63235: 'KEY_ARROW_RIGHT',
    63233: 'KEY_ARROW_DOWN',
    63302: 'KEY_INSERT',
    63272: 'KEY_DELETE'
};

/* for KEY_F1 - KEY_F12 */
(function () {
    var _specialMacKeys = MochiKit.Signal._specialMacKeys;
    for (i = 63236; i <= 63242; i++) {
        // no F0
        _specialMacKeys[i] = 'KEY_F' + (i - 63236 + 1);
    }
})();

/* Standard keyboard key codes. */
MochiKit.Signal._specialKeys = {
    8: 'KEY_BACKSPACE',
    9: 'KEY_TAB',
    12: 'KEY_NUM_PAD_CLEAR', // weird, for Safari and Mac FF only
    13: 'KEY_ENTER',
    16: 'KEY_SHIFT',
    17: 'KEY_CTRL',
    18: 'KEY_ALT',
    19: 'KEY_PAUSE',
    20: 'KEY_CAPS_LOCK',
    27: 'KEY_ESCAPE',
    32: 'KEY_SPACEBAR',
    33: 'KEY_PAGE_UP',
    34: 'KEY_PAGE_DOWN',
    35: 'KEY_END',
    36: 'KEY_HOME',
    37: 'KEY_ARROW_LEFT',
    38: 'KEY_ARROW_UP',
    39: 'KEY_ARROW_RIGHT',
    40: 'KEY_ARROW_DOWN',
    44: 'KEY_PRINT_SCREEN',
    45: 'KEY_INSERT',
    46: 'KEY_DELETE',
    59: 'KEY_SEMICOLON', // weird, for Safari and IE only
    91: 'KEY_WINDOWS_LEFT',
    92: 'KEY_WINDOWS_RIGHT',
    93: 'KEY_SELECT',
    106: 'KEY_NUM_PAD_ASTERISK',
    107: 'KEY_NUM_PAD_PLUS_SIGN',
    109: 'KEY_NUM_PAD_HYPHEN-MINUS',
    110: 'KEY_NUM_PAD_FULL_STOP',
    111: 'KEY_NUM_PAD_SOLIDUS',
    144: 'KEY_NUM_LOCK',
    145: 'KEY_SCROLL_LOCK',
    186: 'KEY_SEMICOLON',
    187: 'KEY_EQUALS_SIGN',
    188: 'KEY_COMMA',
    189: 'KEY_HYPHEN-MINUS',
    190: 'KEY_FULL_STOP',
    191: 'KEY_SOLIDUS',
    192: 'KEY_GRAVE_ACCENT',
    219: 'KEY_LEFT_SQUARE_BRACKET',
    220: 'KEY_REVERSE_SOLIDUS',
    221: 'KEY_RIGHT_SQUARE_BRACKET',
    222: 'KEY_APOSTROPHE'
    // undefined: 'KEY_UNKNOWN'
};

(function () {
    /* for KEY_0 - KEY_9 */
    var _specialKeys = MochiKit.Signal._specialKeys;
    for (var i = 48; i <= 57; i++) {
        _specialKeys[i] = 'KEY_' + (i - 48);
    }

    /* for KEY_A - KEY_Z */
    for (i = 65; i <= 90; i++) {
        _specialKeys[i] = 'KEY_' + String.fromCharCode(i);
    }

    /* for KEY_NUM_PAD_0 - KEY_NUM_PAD_9 */
    for (i = 96; i <= 105; i++) {
        _specialKeys[i] = 'KEY_NUM_PAD_' + (i - 96);
    }

    /* for KEY_F1 - KEY_F12 */
    for (i = 112; i <= 123; i++) {
        // no F0
        _specialKeys[i] = 'KEY_F' + (i - 112 + 1);
    }
})();

/* Internal object to keep track of created signals. */
MochiKit.Signal.Ident = function (ident) {
    this.source = ident.source;
    this.signal = ident.signal;
    this.listener = ident.listener;
    this.isDOM = ident.isDOM;
    this.objOrFunc = ident.objOrFunc;
    this.funcOrStr = ident.funcOrStr;
    this.connected = ident.connected;
};

MochiKit.Signal.Ident.prototype = {};

MochiKit.Base.update(MochiKit.Signal, {

    __repr__: function () {
        return '[' + this.NAME + ' ' + this.VERSION + ']';
    },

    toString: function () {
        return this.__repr__();
    },

    _unloadCache: function () {
        var self = MochiKit.Signal;
        var observers = self._observers;

        for (var i = 0; i < observers.length; i++) {
            if (observers[i].signal !== 'onload' && observers[i].signal !== 'onunload') {
                self._disconnect(observers[i]);
            }
        }
    },

    _listener: function (src, sig, func, obj, isDOM) {
        var self = MochiKit.Signal;
        var E = self.Event;
        if (!isDOM) {
            /* We don't want to re-bind already bound methods */
            if (typeof(func.im_self) == 'undefined') {
                return MochiKit.Base.bind(func, obj);
            } else {
                return func;
            }
        }
        obj = obj || src;
        if (typeof(func) == "string") {
            if (sig === 'onload' || sig === 'onunload') {
                return function (nativeEvent) {
                    obj[func].apply(obj, [new E(src, nativeEvent)]);
                    
                    var ident = new MochiKit.Signal.Ident({
                        source: src, signal: sig, objOrFunc: obj, funcOrStr: func});
                    
                    MochiKit.Signal._disconnect(ident);
                };
            } else {
                return function (nativeEvent) {
                    obj[func].apply(obj, [new E(src, nativeEvent)]);
                };
            }
        } else {
            if (sig === 'onload' || sig === 'onunload') {
                return function (nativeEvent) {
                    func.apply(obj, [new E(src, nativeEvent)]);
                    
                    var ident = new MochiKit.Signal.Ident({
                        source: src, signal: sig, objOrFunc: func});
                    
                    MochiKit.Signal._disconnect(ident);
                };
            } else {
                return function (nativeEvent) {
                    func.apply(obj, [new E(src, nativeEvent)]);
                };
            }
        }
    },

    _browserAlreadyHasMouseEnterAndLeave: function () {
        return /MSIE/.test(navigator.userAgent);
    },

    _mouseEnterListener: function (src, sig, func, obj) {
        var E = MochiKit.Signal.Event;
        return function (nativeEvent) {
            var e = new E(src, nativeEvent);
            try {
                e.relatedTarget().nodeName;
            } catch (err) {
                /* probably hit a permission denied error; possibly one of
                 * firefox's screwy anonymous DIVs inside an input element.
                 * Allow this event to propogate up.
                 */
                return;
            }
            e.stop();
            if (MochiKit.DOM.isChildNode(e.relatedTarget(), src)) {
                /* We've moved between our node and a child. Ignore. */
                return;
            }
            e.type = function () { return sig; };
            if (typeof(func) == "string") {
                return obj[func].apply(obj, [e]);
            } else {
                return func.apply(obj, [e]);
            }
        };
    },

    _getDestPair: function (objOrFunc, funcOrStr) {
        var obj = null;
        var func = null;
        if (typeof(funcOrStr) != 'undefined') {
            obj = objOrFunc;
            func = funcOrStr;
            if (typeof(funcOrStr) == 'string') {
                if (typeof(objOrFunc[funcOrStr]) != "function") {
                    throw new Error("'funcOrStr' must be a function on 'objOrFunc'");
                }
            } else if (typeof(funcOrStr) != 'function') {
                throw new Error("'funcOrStr' must be a function or string");
            }
        } else if (typeof(objOrFunc) != "function") {
            throw new Error("'objOrFunc' must be a function if 'funcOrStr' is not given");
        } else {
            func = objOrFunc;
        }
        return [obj, func];
    },

    /** @id MochiKit.Signal.connect */
    connect: function (src, sig, objOrFunc/* optional */, funcOrStr) {
        src = MochiKit.DOM.getElement(src);
        var self = MochiKit.Signal;

        if (typeof(sig) != 'string') {
            throw new Error("'sig' must be a string");
        }

        var destPair = self._getDestPair(objOrFunc, funcOrStr);
        var obj = destPair[0];
        var func = destPair[1];
        if (typeof(obj) == 'undefined' || obj === null) {
            obj = src;
        }

        var isDOM = !!(src.addEventListener || src.attachEvent);
        if (isDOM && (sig === "onmouseenter" || sig === "onmouseleave")
                  && !self._browserAlreadyHasMouseEnterAndLeave()) {
            var listener = self._mouseEnterListener(src, sig.substr(2), func, obj);
            if (sig === "onmouseenter") {
                sig = "onmouseover";
            } else {
                sig = "onmouseout";
            }
        } else {
            var listener = self._listener(src, sig, func, obj, isDOM);
        }

        if (src.addEventListener) {
            src.addEventListener(sig.substr(2), listener, false);
        } else if (src.attachEvent) {
            src.attachEvent(sig, listener); // useCapture unsupported
        }

        var ident = new MochiKit.Signal.Ident({
            source: src, 
            signal: sig, 
            listener: listener, 
            isDOM: isDOM, 
            objOrFunc: objOrFunc, 
            funcOrStr: funcOrStr, 
            connected: true
        });
        self._observers.push(ident);

        if (!isDOM && typeof(src.__connect__) == 'function') {
            var args = MochiKit.Base.extend([ident], arguments, 1);
            src.__connect__.apply(src, args);
        }

        return ident;
    },

    _disconnect: function (ident) {
        // already disconnected
        if (!ident.connected) {
            return;
        }
        ident.connected = false;
        // check isDOM
        if (!ident.isDOM) {
            return;
        }
        var src = ident.source;
        var sig = ident.signal;
        var listener = ident.listener;

        if (src.removeEventListener) {
            src.removeEventListener(sig.substr(2), listener, false);
        } else if (src.detachEvent) {
            src.detachEvent(sig, listener); // useCapture unsupported
        } else {
            throw new Error("'src' must be a DOM element");
        }
    },

     /** @id MochiKit.Signal.disconnect */
    disconnect: function (ident) {
        var self = MochiKit.Signal;
        var observers = self._observers;
        var m = MochiKit.Base;
        if (arguments.length > 1) {
            // compatibility API
            var src = MochiKit.DOM.getElement(arguments[0]);
            var sig = arguments[1];
            var obj = arguments[2];
            var func = arguments[3];
            for (var i = observers.length - 1; i >= 0; i--) {
                var o = observers[i];
                if (o.source === src && o.signal === sig && o.objOrFunc === obj && o.funcOrStr === func) {
                    self._disconnect(o);
                    if (!self._lock) {
                        observers.splice(i, 1);
                    } else {
                        self._dirty = true;
                    }
                    return true;
                }
            }
        } else {
            var idx = m.findIdentical(observers, ident);
            if (idx >= 0) {
                self._disconnect(ident);
                if (!self._lock) {
                    observers.splice(idx, 1);
                } else {
                    self._dirty = true;
                }
                return true;
            }
        }
        return false;
    },

    /** @id MochiKit.Signal.disconnectAllTo */
    disconnectAllTo: function (objOrFunc, /* optional */funcOrStr) {
        var self = MochiKit.Signal;
        var observers = self._observers;
        var disconnect = self._disconnect;
        var locked = self._lock;
        var dirty = self._dirty;
        if (typeof(funcOrStr) === 'undefined') {
            funcOrStr = null;
        }
        for (var i = observers.length - 1; i >= 0; i--) {
            var ident = observers[i];
            if (ident.objOrFunc === objOrFunc &&
                    (funcOrStr === null || ident.funcOrStr === funcOrStr)) {
                disconnect(ident);
                if (locked) {
                    dirty = true;
                } else {
                    observers.splice(i, 1);
                }
            }
        }
        self._dirty = dirty;
    },

    /** @id MochiKit.Signal.disconnectAll */
    disconnectAll: function (src/* optional */, sig) {
        src = MochiKit.DOM.getElement(src);
        var m = MochiKit.Base;
        var signals = m.flattenArguments(m.extend(null, arguments, 1));
        var self = MochiKit.Signal;
        var disconnect = self._disconnect;
        var observers = self._observers;
        var i, ident;
        var locked = self._lock;
        var dirty = self._dirty;
        if (signals.length === 0) {
            // disconnect all
            for (i = observers.length - 1; i >= 0; i--) {
                ident = observers[i];
                if (ident.source === src) {
                    disconnect(ident);
                    if (!locked) {
                        observers.splice(i, 1);
                    } else {
                        dirty = true;
                    }
                }
            }
        } else {
            var sigs = {};
            for (i = 0; i < signals.length; i++) {
                sigs[signals[i]] = true;
            }
            for (i = observers.length - 1; i >= 0; i--) {
                ident = observers[i];
                if (ident.source === src && ident.signal in sigs) {
                    disconnect(ident);
                    if (!locked) {
                        observers.splice(i, 1);
                    } else {
                        dirty = true;
                    }
                }
            }
        }
        self._dirty = dirty;
    },

    /** @id MochiKit.Signal.signal */
    signal: function (src, sig) {
        var self = MochiKit.Signal;
        var observers = self._observers;
        src = MochiKit.DOM.getElement(src);
        var args = MochiKit.Base.extend(null, arguments, 2);
        var errors = [];
        self._lock = true;
        for (var i = 0; i < observers.length; i++) {
            var ident = observers[i];
            if (ident.source === src && ident.signal === sig &&
                    ident.connected) {
                try {
                    ident.listener.apply(src, args);
                } catch (e) {
                    errors.push(e);
                }
            }
        }
        self._lock = false;
        if (self._dirty) {
            self._dirty = false;
            for (var i = observers.length - 1; i >= 0; i--) {
                if (!observers[i].connected) {
                    observers.splice(i, 1);
                }
            }
        }
        if (errors.length == 1) {
            throw errors[0];
        } else if (errors.length > 1) {
            var e = new Error("Multiple errors thrown in handling 'sig', see errors property");
            e.errors = errors;
            throw e;
        }
    }

});

MochiKit.Signal.EXPORT_OK = [];

MochiKit.Signal.EXPORT = [
    'connect',
    'disconnect',
    'signal',
    'disconnectAll',
    'disconnectAllTo'
];

MochiKit.Signal.__new__ = function (win) {
    var m = MochiKit.Base;
    this._document = document;
    this._window = win;
    this._lock = false;
    this._dirty = false;

    try {
        this.connect(window, 'onunload', this._unloadCache);
    } catch (e) {
        // pass: might not be a browser
    }

    this.EXPORT_TAGS = {
        ':common': this.EXPORT,
        ':all': m.concat(this.EXPORT, this.EXPORT_OK)
    };

    m.nameFunctions(this);
};

MochiKit.Signal.__new__(this);

//
// XXX: Internet Explorer blows
//
if (MochiKit.__export__) {
    connect = MochiKit.Signal.connect;
    disconnect = MochiKit.Signal.disconnect;
    disconnectAll = MochiKit.Signal.disconnectAll;
    signal = MochiKit.Signal.signal;
}

MochiKit.Base._exportSymbols(this, MochiKit.Signal);
