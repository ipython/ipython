/***

MochiKit.Style 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005-2006 Bob Ippolito, Beau Hartshorne.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Style');
    dojo.require('MochiKit.Base');
    dojo.require('MochiKit.DOM');
}
if (typeof(JSAN) != 'undefined') {
    JSAN.use('MochiKit.Base', []);
    JSAN.use('MochiKit.DOM', []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined') {
        throw '';
    }
} catch (e) {
    throw 'MochiKit.Style depends on MochiKit.Base!';
}

try {
    if (typeof(MochiKit.DOM) == 'undefined') {
        throw '';
    }
} catch (e) {
    throw 'MochiKit.Style depends on MochiKit.DOM!';
}


if (typeof(MochiKit.Style) == 'undefined') {
    MochiKit.Style = {};
}

MochiKit.Style.NAME = 'MochiKit.Style';
MochiKit.Style.VERSION = '1.4';
MochiKit.Style.__repr__ = function () {
    return '[' + this.NAME + ' ' + this.VERSION + ']';
};
MochiKit.Style.toString = function () {
    return this.__repr__();
};

MochiKit.Style.EXPORT_OK = [];

MochiKit.Style.EXPORT = [
    'setStyle',
    'setOpacity',
    'getStyle',
    'getElementDimensions',
    'elementDimensions', // deprecated
    'setElementDimensions',
    'getElementPosition',
    'elementPosition', // deprecated
    'setElementPosition',
    'setDisplayForElement',
    'hideElement',
    'showElement',
    'getViewportDimensions',
    'getViewportPosition',
    'Dimensions',
    'Coordinates'
];


/*

    Dimensions

*/
/** @id MochiKit.Style.Dimensions */
MochiKit.Style.Dimensions = function (w, h) {
    this.w = w;
    this.h = h;
};

MochiKit.Style.Dimensions.prototype.__repr__ = function () {
    var repr = MochiKit.Base.repr;
    return '{w: '  + repr(this.w) + ', h: ' + repr(this.h) + '}';
};

MochiKit.Style.Dimensions.prototype.toString = function () {
    return this.__repr__();
};


/*

    Coordinates

*/
/** @id MochiKit.Style.Coordinates */
MochiKit.Style.Coordinates = function (x, y) {
    this.x = x;
    this.y = y;
};

MochiKit.Style.Coordinates.prototype.__repr__ = function () {
    var repr = MochiKit.Base.repr;
    return '{x: '  + repr(this.x) + ', y: ' + repr(this.y) + '}';
};

MochiKit.Style.Coordinates.prototype.toString = function () {
    return this.__repr__();
};


MochiKit.Base.update(MochiKit.Style, {

    /** @id MochiKit.Style.getStyle */
    getStyle: function (elem, cssProperty) {
        var dom = MochiKit.DOM;
        var d = dom._document;

        elem = dom.getElement(elem);
        cssProperty = MochiKit.Base.camelize(cssProperty);

        if (!elem || elem == d) {
            return undefined;
        }
        if (cssProperty == 'opacity' && elem.filters) {
            var opacity = (MochiKit.Style.getStyle(elem, 'filter') || '').match(/alpha\(opacity=(.*)\)/);
            if (opacity && opacity[1]) {
                return parseFloat(opacity[1]) / 100;
            }
            return 1.0;
        }
        var value = elem.style ? elem.style[cssProperty] : null;
        if (!value) {
            if (d.defaultView && d.defaultView.getComputedStyle) {
                var css = d.defaultView.getComputedStyle(elem, null);
                cssProperty = cssProperty.replace(/([A-Z])/g, '-$1'
                    ).toLowerCase(); // from dojo.style.toSelectorCase
                value = css ? css.getPropertyValue(cssProperty) : null;
            } else if (elem.currentStyle) {
                value = elem.currentStyle[cssProperty];
            }
        }
        if (cssProperty == 'opacity') {
            value = parseFloat(value);
        }

        if (/Opera/.test(navigator.userAgent) && (MochiKit.Base.find(['left', 'top', 'right', 'bottom'], cssProperty) != -1)) {
            if (MochiKit.Style.getStyle(elem, 'position') == 'static') {
                value = 'auto';
            }
        }

        return value == 'auto' ? null : value;
    },

    /** @id MochiKit.Style.setStyle */
    setStyle: function (elem, style) {
        elem = MochiKit.DOM.getElement(elem);
        for (var name in style) {
            if (name == 'opacity') {
                MochiKit.Style.setOpacity(elem, style[name]);
            } else {
                elem.style[MochiKit.Base.camelize(name)] = style[name];
            }
        }
    },

    /** @id MochiKit.Style.setOpacity */
    setOpacity: function (elem, o) {
        elem = MochiKit.DOM.getElement(elem);
        var self = MochiKit.Style;
        if (o == 1) {
            var toSet = /Gecko/.test(navigator.userAgent) && !(/Konqueror|AppleWebKit|KHTML/.test(navigator.userAgent));
            elem.style["opacity"] = toSet ? 0.999999 : 1.0;
            if (/MSIE/.test(navigator.userAgent)) {
                elem.style['filter'] =
                    self.getStyle(elem, 'filter').replace(/alpha\([^\)]*\)/gi, '');
            }
        } else {
            if (o < 0.00001) {
                o = 0;
            }
            elem.style["opacity"] = o;
            if (/MSIE/.test(navigator.userAgent)) {
                elem.style['filter'] =
                    self.getStyle(elem, 'filter').replace(/alpha\([^\)]*\)/gi, '') + 'alpha(opacity=' + o * 100 + ')';
            }
        }
    },

    /*

        getElementPosition is adapted from YAHOO.util.Dom.getXY v0.9.0.
        Copyright: Copyright (c) 2006, Yahoo! Inc. All rights reserved.
        License: BSD, http://developer.yahoo.net/yui/license.txt

    */

    /** @id MochiKit.Style.getElementPosition */
    getElementPosition: function (elem, /* optional */relativeTo) {
        var self = MochiKit.Style;
        var dom = MochiKit.DOM;
        elem = dom.getElement(elem);

        if (!elem ||
            (!(elem.x && elem.y) &&
            (!elem.parentNode === null ||
            self.getStyle(elem, 'display') == 'none'))) {
            return undefined;
        }

        var c = new self.Coordinates(0, 0);
        var box = null;
        var parent = null;

        var d = MochiKit.DOM._document;
        var de = d.documentElement;
        var b = d.body;

        if (!elem.parentNode && elem.x && elem.y) {
            /* it's just a MochiKit.Style.Coordinates object */
            c.x += elem.x || 0;
            c.y += elem.y || 0;
        } else if (elem.getBoundingClientRect) { // IE shortcut
            /*

                The IE shortcut can be off by two. We fix it. See:
                http://msdn.microsoft.com/workshop/author/dhtml/reference/methods/getboundingclientrect.asp

                This is similar to the method used in
                MochiKit.Signal.Event.mouse().

            */
            box = elem.getBoundingClientRect();

            c.x += box.left +
                (de.scrollLeft || b.scrollLeft) -
                (de.clientLeft || 0);

            c.y += box.top +
                (de.scrollTop || b.scrollTop) -
                (de.clientTop || 0);

        } else if (elem.offsetParent) {
            c.x += elem.offsetLeft;
            c.y += elem.offsetTop;
            parent = elem.offsetParent;

            if (parent != elem) {
                while (parent) {
                    c.x += parent.offsetLeft;
                    c.y += parent.offsetTop;
                    parent = parent.offsetParent;
                }
            }

            /*

                Opera < 9 and old Safari (absolute) incorrectly account for
                body offsetTop and offsetLeft.

            */
            var ua = navigator.userAgent.toLowerCase();
            if ((typeof(opera) != 'undefined' &&
                parseFloat(opera.version()) < 9) ||
                (ua.indexOf('AppleWebKit') != -1 &&
                self.getStyle(elem, 'position') == 'absolute')) {

                c.x -= b.offsetLeft;
                c.y -= b.offsetTop;

            }
        }

        if (typeof(relativeTo) != 'undefined') {
            relativeTo = arguments.callee(relativeTo);
            if (relativeTo) {
                c.x -= (relativeTo.x || 0);
                c.y -= (relativeTo.y || 0);
            }
        }

        if (elem.parentNode) {
            parent = elem.parentNode;
        } else {
            parent = null;
        }

        while (parent) {
            var tagName = parent.tagName.toUpperCase();
            if (tagName === 'BODY' || tagName === 'HTML') {
                break;
            }
            var disp = self.getStyle(parent, 'display');
            // Handle strange Opera bug for some display
            if (disp != 'inline' && disp != 'table-row') {
                c.x -= parent.scrollLeft;
                c.y -= parent.scrollTop;
            }
            if (parent.parentNode) {
                parent = parent.parentNode;
            } else {
                parent = null;
            }
        }

        return c;
    },

    /** @id MochiKit.Style.setElementPosition */
    setElementPosition: function (elem, newPos/* optional */, units) {
        elem = MochiKit.DOM.getElement(elem);
        if (typeof(units) == 'undefined') {
            units = 'px';
        }
        var newStyle = {};
        var isUndefNull = MochiKit.Base.isUndefinedOrNull;
        if (!isUndefNull(newPos.x)) {
            newStyle['left'] = newPos.x + units;
        }
        if (!isUndefNull(newPos.y)) {
            newStyle['top'] = newPos.y + units;
        }
        MochiKit.DOM.updateNodeAttributes(elem, {'style': newStyle});
    },

    /** @id MochiKit.Style.getElementDimensions */
    getElementDimensions: function (elem) {
        var self = MochiKit.Style;
        var dom = MochiKit.DOM;
        if (typeof(elem.w) == 'number' || typeof(elem.h) == 'number') {
            return new self.Dimensions(elem.w || 0, elem.h || 0);
        }
        elem = dom.getElement(elem);
        if (!elem) {
            return undefined;
        }
        var disp = self.getStyle(elem, 'display');
        // display can be empty/undefined on WebKit/KHTML
        if (disp != 'none' && disp !== '' && typeof(disp) != 'undefined') {
            return new self.Dimensions(elem.offsetWidth || 0,
                elem.offsetHeight || 0);
        }
        var s = elem.style;
        var originalVisibility = s.visibility;
        var originalPosition = s.position;
        s.visibility = 'hidden';
        s.position = 'absolute';
        s.display = '';
        var originalWidth = elem.offsetWidth;
        var originalHeight = elem.offsetHeight;
        s.display = 'none';
        s.position = originalPosition;
        s.visibility = originalVisibility;
        return new self.Dimensions(originalWidth, originalHeight);
    },

    /** @id MochiKit.Style.setElementDimensions */
    setElementDimensions: function (elem, newSize/* optional */, units) {
        elem = MochiKit.DOM.getElement(elem);
        if (typeof(units) == 'undefined') {
            units = 'px';
        }
        var newStyle = {};
        var isUndefNull = MochiKit.Base.isUndefinedOrNull;
        if (!isUndefNull(newSize.w)) {
            newStyle['width'] = newSize.w + units;
        }
        if (!isUndefNull(newSize.h)) {
            newStyle['height'] = newSize.h + units;
        }
        MochiKit.DOM.updateNodeAttributes(elem, {'style': newStyle});
    },

    /** @id MochiKit.Style.setDisplayForElement */
    setDisplayForElement: function (display, element/*, ...*/) {
        var elements = MochiKit.Base.extend(null, arguments, 1);
        var getElement = MochiKit.DOM.getElement;
        for (var i = 0; i < elements.length; i++) {
            element = getElement(elements[i]);
            if (element) {
                element.style.display = display;
            }
        }
    },

    /** @id MochiKit.Style.getViewportDimensions */
    getViewportDimensions: function () {
        var d = new MochiKit.Style.Dimensions();

        var w = MochiKit.DOM._window;
        var b = MochiKit.DOM._document.body;

        if (w.innerWidth) {
            d.w = w.innerWidth;
            d.h = w.innerHeight;
        } else if (b.parentElement.clientWidth) {
            d.w = b.parentElement.clientWidth;
            d.h = b.parentElement.clientHeight;
        } else if (b && b.clientWidth) {
            d.w = b.clientWidth;
            d.h = b.clientHeight;
        }
        return d;
    },

    /** @id MochiKit.Style.getViewportPosition */
    getViewportPosition: function () {
        var c = new MochiKit.Style.Coordinates(0, 0);
        var d = MochiKit.DOM._document;
        var de = d.documentElement;
        var db = d.body;
        if (de && (de.scrollTop || de.scrollLeft)) {
            c.x = de.scrollLeft;
            c.y = de.scrollTop;
        } else if (db) {
            c.x = db.scrollLeft;
            c.y = db.scrollTop;
        }
        return c;
    },

    __new__: function () {
        var m = MochiKit.Base;

        this.elementPosition = this.getElementPosition;
        this.elementDimensions = this.getElementDimensions;

        this.hideElement = m.partial(this.setDisplayForElement, 'none');
        this.showElement = m.partial(this.setDisplayForElement, 'block');

        this.EXPORT_TAGS = {
            ':common': this.EXPORT,
            ':all': m.concat(this.EXPORT, this.EXPORT_OK)
        };

        m.nameFunctions(this);
    }
});

MochiKit.Style.__new__();
MochiKit.Base._exportSymbols(this, MochiKit.Style);
