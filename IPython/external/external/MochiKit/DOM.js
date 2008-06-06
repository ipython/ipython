/***

MochiKit.DOM 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide("MochiKit.DOM");
    dojo.require("MochiKit.Base");
}
if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Base", []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.DOM depends on MochiKit.Base!";
}

if (typeof(MochiKit.DOM) == 'undefined') {
    MochiKit.DOM = {};
}

MochiKit.DOM.NAME = "MochiKit.DOM";
MochiKit.DOM.VERSION = "1.4";
MochiKit.DOM.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};
MochiKit.DOM.toString = function () {
    return this.__repr__();
};

MochiKit.DOM.EXPORT = [
    "removeEmptyTextNodes",
    "formContents",
    "currentWindow",
    "currentDocument",
    "withWindow",
    "withDocument",
    "registerDOMConverter",
    "coerceToDOM",
    "createDOM",
    "createDOMFunc",
    "isChildNode",
    "getNodeAttribute",
    "removeNodeAttribute",
    "setNodeAttribute",
    "updateNodeAttributes",
    "appendChildNodes",
    "insertSiblingNodesAfter",
    "insertSiblingNodesBefore",
    "replaceChildNodes",
    "removeElement",
    "swapDOM",
    "BUTTON",
    "TT",
    "PRE",
    "H1",
    "H2",
    "H3",
    "BR",
    "CANVAS",
    "HR",
    "LABEL",
    "TEXTAREA",
    "FORM",
    "STRONG",
    "SELECT",
    "OPTION",
    "OPTGROUP",
    "LEGEND",
    "FIELDSET",
    "P",
    "UL",
    "OL",
    "LI",
    "TD",
    "TR",
    "THEAD",
    "TBODY",
    "TFOOT",
    "TABLE",
    "TH",
    "INPUT",
    "SPAN",
    "A",
    "DIV",
    "IMG",
    "getElement",
    "$",
    "getElementsByTagAndClassName",
    "addToCallStack",
    "addLoadEvent",
    "focusOnLoad",
    "setElementClass",
    "toggleElementClass",
    "addElementClass",
    "removeElementClass",
    "swapElementClass",
    "hasElementClass",
    "escapeHTML",
    "toHTML",
    "emitHTML",
    "scrapeText",
    "isParent",
    "getFirstParentByTagAndClassName",
    "makeClipping",
    "undoClipping",
    "makePositioned",
    "undoPositioned",
    "getFirstElementByTagAndClassName"
];

MochiKit.DOM.EXPORT_OK = [
    "domConverters"
];

MochiKit.DOM.DEPRECATED = [
    ['computedStyle', 'MochiKit.Style.getStyle', '1.4'],
    /** @id MochiKit.DOM.elementDimensions  */
    ['elementDimensions', 'MochiKit.Style.getElementDimensions', '1.4'],
    /** @id MochiKit.DOM.elementPosition  */
    ['elementPosition', 'MochiKit.Style.getElementPosition', '1.4'],
    ['hideElement', 'MochiKit.Style.hideElement', '1.4'],
    /** @id MochiKit.DOM.setElementDimensions */
    ['setElementDimensions', 'MochiKit.Style.setElementDimensions', '1.4'],
    /** @id MochiKit.DOM.setElementPosition */
    ['setElementPosition', 'MochiKit.Style.setElementPosition', '1.4'],
    ['setDisplayForElement', 'MochiKit.Style.setDisplayForElement', '1.4'],
    /** @id MochiKit.DOM.setOpacity */
    ['setOpacity', 'MochiKit.Style.setOpacity', '1.4'],
    ['showElement', 'MochiKit.Style.showElement', '1.4'],
    /** @id MochiKit.DOM.Coordinates */
    ['Coordinates', 'MochiKit.Style.Coordinates', '1.4'], // FIXME: broken
    /** @id MochiKit.DOM.Dimensions */
    ['Dimensions', 'MochiKit.Style.Dimensions', '1.4'] // FIXME: broken
];

/** @id MochiKit.DOM.getViewportDimensions */
MochiKit.DOM.getViewportDimensions = new Function('' +
    'if (!MochiKit["Style"]) {' +
    '    throw new Error("This function has been deprecated and depends on MochiKit.Style.");' +
    '}' +
    'return MochiKit.Style.getViewportDimensions.apply(this, arguments);');

MochiKit.Base.update(MochiKit.DOM, {

    /** @id MochiKit.DOM.currentWindow */
    currentWindow: function () {
        return MochiKit.DOM._window;
    },

    /** @id MochiKit.DOM.currentDocument */
    currentDocument: function () {
        return MochiKit.DOM._document;
    },

    /** @id MochiKit.DOM.withWindow */
    withWindow: function (win, func) {
        var self = MochiKit.DOM;
        var oldDoc = self._document;
        var oldWin = self._window;
        var rval;
        try {
            self._window = win;
            self._document = win.document;
            rval = func();
        } catch (e) {
            self._window = oldWin;
            self._document = oldDoc;
            throw e;
        }
        self._window = oldWin;
        self._document = oldDoc;
        return rval;
    },

    /** @id MochiKit.DOM.formContents  */
    formContents: function (elem/* = document.body */) {
        var names = [];
        var values = [];
        var m = MochiKit.Base;
        var self = MochiKit.DOM;
        if (typeof(elem) == "undefined" || elem === null) {
            elem = self._document.body;
        } else {
            elem = self.getElement(elem);
        }
        m.nodeWalk(elem, function (elem) {
            var name = elem.name;
            if (m.isNotEmpty(name)) {
                var tagName = elem.tagName.toUpperCase();
                if (tagName === "INPUT"
                    && (elem.type == "radio" || elem.type == "checkbox")
                    && !elem.checked
                ) {
                    return null;
                }
                if (tagName === "SELECT") {
                    if (elem.type == "select-one") {
                        if (elem.selectedIndex >= 0) {
                            var opt = elem.options[elem.selectedIndex];
                            var v = opt.value;
                            if (!v) {
                                var h = opt.outerHTML;
                                // internet explorer sure does suck.
                                if (h && !h.match(/^[^>]+\svalue\s*=/i)) {
                                    v = opt.text;
                                }
                            }
                            names.push(name);
                            values.push(v);
                            return null;
                        }
                        // no form elements?
                        names.push(name);
                        values.push("");
                        return null;
                    } else {
                        var opts = elem.options;
                        if (!opts.length) {
                            names.push(name);
                            values.push("");
                            return null;
                        }
                        for (var i = 0; i < opts.length; i++) {
                            var opt = opts[i];
                            if (!opt.selected) {
                                continue;
                            }
                            var v = opt.value;
                            if (!v) {
                                var h = opt.outerHTML;
                                // internet explorer sure does suck.
                                if (h && !h.match(/^[^>]+\svalue\s*=/i)) {
                                    v = opt.text;
                                }
                            }
                            names.push(name);
                            values.push(v);
                        }
                        return null;
                    }
                }
                if (tagName === "FORM" || tagName === "P" || tagName === "SPAN"
                    || tagName === "DIV"
                ) {
                    return elem.childNodes;
                }
                names.push(name);
                values.push(elem.value || '');
                return null;
            }
            return elem.childNodes;
        });
        return [names, values];
    },

    /** @id MochiKit.DOM.withDocument */
    withDocument: function (doc, func) {
        var self = MochiKit.DOM;
        var oldDoc = self._document;
        var rval;
        try {
            self._document = doc;
            rval = func();
        } catch (e) {
            self._document = oldDoc;
            throw e;
        }
        self._document = oldDoc;
        return rval;
    },

    /** @id MochiKit.DOM.registerDOMConverter */
    registerDOMConverter: function (name, check, wrap, /* optional */override) {
        MochiKit.DOM.domConverters.register(name, check, wrap, override);
    },

    /** @id MochiKit.DOM.coerceToDOM */
    coerceToDOM: function (node, ctx) {
        var m = MochiKit.Base;
        var im = MochiKit.Iter;
        var self = MochiKit.DOM;
        if (im) {
            var iter = im.iter;
            var repeat = im.repeat;
            var map = m.map;
        }
        var domConverters = self.domConverters;
        var coerceToDOM = arguments.callee;
        var NotFound = m.NotFound;
        while (true) {
            if (typeof(node) == 'undefined' || node === null) {
                return null;
            }
            // this is a safari childNodes object, avoiding crashes w/ attr
            // lookup
            if (typeof(node) == "function" &&
                    typeof(node.length) == "number" &&
                    !(node instanceof Function)) {
                node = im.list(node);
            }
            if (typeof(node.nodeType) != 'undefined' && node.nodeType > 0) {
                return node;
            }
            if (typeof(node) == 'number' || typeof(node) == 'boolean') {
                node = node.toString();
                // FALL THROUGH
            }
            if (typeof(node) == 'string') {
                return self._document.createTextNode(node);
            }
            if (typeof(node.__dom__) == 'function') {
                node = node.__dom__(ctx);
                continue;
            }
            if (typeof(node.dom) == 'function') {
                node = node.dom(ctx);
                continue;
            }
            if (typeof(node) == 'function') {
                node = node.apply(ctx, [ctx]);
                continue;
            }

            if (im) {
                // iterable
                var iterNodes = null;
                try {
                    iterNodes = iter(node);
                } catch (e) {
                    // pass
                }
                if (iterNodes) {
                    return map(coerceToDOM, iterNodes, repeat(ctx));
                }
            }

            // adapter
            try {
                node = domConverters.match(node, ctx);
                continue;
            } catch (e) {
                if (e != NotFound) {
                    throw e;
                }
            }

            // fallback
            return self._document.createTextNode(node.toString());
        }
        // mozilla warnings aren't too bright
        return undefined;
    },

    /** @id MochiKit.DOM.isChildNode */
    isChildNode: function (node, maybeparent) {
        var self = MochiKit.DOM;
        if (typeof(node) == "string") {
            node = self.getElement(node);
        }
        if (typeof(maybeparent) == "string") {
            maybeparent = self.getElement(maybeparent);
        }
        if (typeof(node) == 'undefined' || node === null || node === self._document) {
            return false;
        }
        do {
            if (node === maybeparent) {
                return true;
            }
            var tagName = node.tagName;
            node = node.parentNode;
            if (!tagName) {
                break;
            }
            tagName = tagName.toUpperCase();
        } while (tagName != "BODY" && tagName != "HTML");
        return false;
    },

    /** @id MochiKit.DOM.setNodeAttribute */
    setNodeAttribute: function (node, attr, value) {
        var o = {};
        o[attr] = value;
        try {
            return MochiKit.DOM.updateNodeAttributes(node, o);
        } catch (e) {
            // pass
        }
        return null;
    },

    /** @id MochiKit.DOM.getNodeAttribute */
    getNodeAttribute: function (node, attr) {
        var self = MochiKit.DOM;
        var rename = self.attributeArray.renames[attr];
        node = self.getElement(node);
        try {
            if (rename) {
                return node[rename];
            }
            return node.getAttribute(attr);
        } catch (e) {
            // pass
        }
        return null;
    },

    /** @id MochiKit.DOM.removeNodeAttribute */
    removeNodeAttribute: function (node, attr) {
        var self = MochiKit.DOM;
        var rename = self.attributeArray.renames[attr];
        node = self.getElement(node);
        try {
            if (rename) {
                return node[rename];
            }
            return node.removeAttribute(attr);
        } catch (e) {
            // pass
        }
        return null;
    },

    /** @id MochiKit.DOM.updateNodeAttributes */
    updateNodeAttributes: function (node, attrs) {
        var elem = node;
        var self = MochiKit.DOM;
        if (typeof(node) == 'string') {
            elem = self.getElement(node);
        }
        if (attrs) {
            var updatetree = MochiKit.Base.updatetree;
            if (self.attributeArray.compliant) {
                // not IE, good.
                for (var k in attrs) {
                    var v = attrs[k];
                    if (typeof(v) == 'object' && typeof(elem[k]) == 'object') {
                        if (k == "style" && MochiKit.Style) {
                            MochiKit.Style.setStyle(elem, v);
                        } else {
                            updatetree(elem[k], v);
                        }
                    } else if (k.substring(0, 2) == "on") {
                        if (typeof(v) == "string") {
                            v = new Function(v);
                        }
                        elem[k] = v;
                    } else {
                        elem.setAttribute(k, v);
                    }
                }
            } else {
                // IE is insane in the membrane
                var renames = self.attributeArray.renames;
                for (var k in attrs) {
                    v = attrs[k];
                    var renamed = renames[k];
                    if (k == "style" && typeof(v) == "string") {
                        elem.style.cssText = v;
                    } else if (typeof(renamed) == "string") {
                        elem[renamed] = v;
                    } else if (typeof(elem[k]) == 'object'
                            && typeof(v) == 'object') {
                        if (k == "style" && MochiKit.Style) {
                            MochiKit.Style.setStyle(elem, v);
                        } else {
                            updatetree(elem[k], v);
                        }
                    } else if (k.substring(0, 2) == "on") {
                        if (typeof(v) == "string") {
                            v = new Function(v);
                        }
                        elem[k] = v;
                    } else {
                        elem.setAttribute(k, v);
                    }
                }
            }
        }
        return elem;
    },

    /** @id MochiKit.DOM.appendChildNodes */
    appendChildNodes: function (node/*, nodes...*/) {
        var elem = node;
        var self = MochiKit.DOM;
        if (typeof(node) == 'string') {
            elem = self.getElement(node);
        }
        var nodeStack = [
            self.coerceToDOM(
                MochiKit.Base.extend(null, arguments, 1),
                elem
            )
        ];
        var concat = MochiKit.Base.concat;
        while (nodeStack.length) {
            var n = nodeStack.shift();
            if (typeof(n) == 'undefined' || n === null) {
                // pass
            } else if (typeof(n.nodeType) == 'number') {
                elem.appendChild(n);
            } else {
                nodeStack = concat(n, nodeStack);
            }
        }
        return elem;
    },


    /** @id MochiKit.DOM.insertSiblingNodesBefore */
    insertSiblingNodesBefore: function (node/*, nodes...*/) {
        var elem = node;
        var self = MochiKit.DOM;
        if (typeof(node) == 'string') {
            elem = self.getElement(node);
        }
        var nodeStack = [
            self.coerceToDOM(
                MochiKit.Base.extend(null, arguments, 1),
                elem
            )
        ];
        var parentnode = elem.parentNode;
        var concat = MochiKit.Base.concat;
        while (nodeStack.length) {
            var n = nodeStack.shift();
            if (typeof(n) == 'undefined' || n === null) {
                // pass
            } else if (typeof(n.nodeType) == 'number') {
                parentnode.insertBefore(n, elem);
            } else {
                nodeStack = concat(n, nodeStack);
            }
        }
        return parentnode;
    },

    /** @id MochiKit.DOM.insertSiblingNodesAfter */
    insertSiblingNodesAfter: function (node/*, nodes...*/) {
        var elem = node;
        var self = MochiKit.DOM;

        if (typeof(node) == 'string') {
            elem = self.getElement(node);
        }
        var nodeStack = [
            self.coerceToDOM(
                MochiKit.Base.extend(null, arguments, 1),
                elem
            )
        ];

        if (elem.nextSibling) {
            return self.insertSiblingNodesBefore(elem.nextSibling, nodeStack);
        }
        else {
            return self.appendChildNodes(elem.parentNode, nodeStack);
        }
    },

    /** @id MochiKit.DOM.replaceChildNodes */
    replaceChildNodes: function (node/*, nodes...*/) {
        var elem = node;
        var self = MochiKit.DOM;
        if (typeof(node) == 'string') {
            elem = self.getElement(node);
            arguments[0] = elem;
        }
        var child;
        while ((child = elem.firstChild)) {
            elem.removeChild(child);
        }
        if (arguments.length < 2) {
            return elem;
        } else {
            return self.appendChildNodes.apply(this, arguments);
        }
    },

    /** @id MochiKit.DOM.createDOM */
    createDOM: function (name, attrs/*, nodes... */) {
        var elem;
        var self = MochiKit.DOM;
        var m = MochiKit.Base;
        if (typeof(attrs) == "string" || typeof(attrs) == "number") {
            var args = m.extend([name, null], arguments, 1);
            return arguments.callee.apply(this, args);
        }
        if (typeof(name) == 'string') {
            // Internet Explorer is dumb
            var xhtml = self._xhtml;
            if (attrs && !self.attributeArray.compliant) {
                // http://msdn.microsoft.com/workshop/author/dhtml/reference/properties/name_2.asp
                var contents = "";
                if ('name' in attrs) {
                    contents += ' name="' + self.escapeHTML(attrs.name) + '"';
                }
                if (name == 'input' && 'type' in attrs) {
                    contents += ' type="' + self.escapeHTML(attrs.type) + '"';
                }
                if (contents) {
                    name = "<" + name + contents + ">";
                    xhtml = false;
                }
            }
            var d = self._document;
            if (xhtml && d === document) {
                elem = d.createElementNS("http://www.w3.org/1999/xhtml", name);
            } else {
                elem = d.createElement(name);
            }
        } else {
            elem = name;
        }
        if (attrs) {
            self.updateNodeAttributes(elem, attrs);
        }
        if (arguments.length <= 2) {
            return elem;
        } else {
            var args = m.extend([elem], arguments, 2);
            return self.appendChildNodes.apply(this, args);
        }
    },

    /** @id MochiKit.DOM.createDOMFunc */
    createDOMFunc: function (/* tag, attrs, *nodes */) {
        var m = MochiKit.Base;
        return m.partial.apply(
            this,
            m.extend([MochiKit.DOM.createDOM], arguments)
        );
    },

    /** @id MochiKit.DOM.removeElement */
    removeElement: function (elem) {
        var e = MochiKit.DOM.getElement(elem);
        e.parentNode.removeChild(e);
        return e;
    },

    /** @id MochiKit.DOM.swapDOM */
    swapDOM: function (dest, src) {
        var self = MochiKit.DOM;
        dest = self.getElement(dest);
        var parent = dest.parentNode;
        if (src) {
            src = self.getElement(src);
            parent.replaceChild(src, dest);
        } else {
            parent.removeChild(dest);
        }
        return src;
    },

    /** @id MochiKit.DOM.getElement */
    getElement: function (id) {
        var self = MochiKit.DOM;
        if (arguments.length == 1) {
            return ((typeof(id) == "string") ?
                self._document.getElementById(id) : id);
        } else {
            return MochiKit.Base.map(self.getElement, arguments);
        }
    },

    /** @id MochiKit.DOM.getElementsByTagAndClassName */
    getElementsByTagAndClassName: function (tagName, className,
            /* optional */parent) {
        var self = MochiKit.DOM;
        if (typeof(tagName) == 'undefined' || tagName === null) {
            tagName = '*';
        }
        if (typeof(parent) == 'undefined' || parent === null) {
            parent = self._document;
        }
        parent = self.getElement(parent);
        var children = (parent.getElementsByTagName(tagName)
            || self._document.all);
        if (typeof(className) == 'undefined' || className === null) {
            return MochiKit.Base.extend(null, children);
        }

        var elements = [];
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            var cls = child.className;
            if (!cls) {
                continue;
            }
            var classNames = cls.split(' ');
            for (var j = 0; j < classNames.length; j++) {
                if (classNames[j] == className) {
                    elements.push(child);
                    break;
                }
            }
        }

        return elements;
    },

    _newCallStack: function (path, once) {
        var rval = function () {
            var callStack = arguments.callee.callStack;
            for (var i = 0; i < callStack.length; i++) {
                if (callStack[i].apply(this, arguments) === false) {
                    break;
                }
            }
            if (once) {
                try {
                    this[path] = null;
                } catch (e) {
                    // pass
                }
            }
        };
        rval.callStack = [];
        return rval;
    },

    /** @id MochiKit.DOM.addToCallStack */
    addToCallStack: function (target, path, func, once) {
        var self = MochiKit.DOM;
        var existing = target[path];
        var regfunc = existing;
        if (!(typeof(existing) == 'function'
                && typeof(existing.callStack) == "object"
                && existing.callStack !== null)) {
            regfunc = self._newCallStack(path, once);
            if (typeof(existing) == 'function') {
                regfunc.callStack.push(existing);
            }
            target[path] = regfunc;
        }
        regfunc.callStack.push(func);
    },

    /** @id MochiKit.DOM.addLoadEvent */
    addLoadEvent: function (func) {
        var self = MochiKit.DOM;
        self.addToCallStack(self._window, "onload", func, true);

    },

    /** @id MochiKit.DOM.focusOnLoad */
    focusOnLoad: function (element) {
        var self = MochiKit.DOM;
        self.addLoadEvent(function () {
            element = self.getElement(element);
            if (element) {
                element.focus();
            }
        });
    },

    /** @id MochiKit.DOM.setElementClass */
    setElementClass: function (element, className) {
        var self = MochiKit.DOM;
        var obj = self.getElement(element);
        if (self.attributeArray.compliant) {
            obj.setAttribute("class", className);
        } else {
            obj.setAttribute("className", className);
        }
    },

    /** @id MochiKit.DOM.toggleElementClass */
    toggleElementClass: function (className/*, element... */) {
        var self = MochiKit.DOM;
        for (var i = 1; i < arguments.length; i++) {
            var obj = self.getElement(arguments[i]);
            if (!self.addElementClass(obj, className)) {
                self.removeElementClass(obj, className);
            }
        }
    },

    /** @id MochiKit.DOM.addElementClass */
    addElementClass: function (element, className) {
        var self = MochiKit.DOM;
        var obj = self.getElement(element);
        var cls = obj.className;
        // trivial case, no className yet
        if (cls == undefined || cls.length === 0) {
            self.setElementClass(obj, className);
            return true;
        }
        // the other trivial case, already set as the only class
        if (cls == className) {
            return false;
        }
        var classes = cls.split(" ");
        for (var i = 0; i < classes.length; i++) {
            // already present
            if (classes[i] == className) {
                return false;
            }
        }
        // append class
        self.setElementClass(obj, cls + " " + className);
        return true;
    },

    /** @id MochiKit.DOM.removeElementClass */
    removeElementClass: function (element, className) {
        var self = MochiKit.DOM;
        var obj = self.getElement(element);
        var cls = obj.className;
        // trivial case, no className yet
        if (cls == undefined || cls.length === 0) {
            return false;
        }
        // other trivial case, set only to className
        if (cls == className) {
            self.setElementClass(obj, "");
            return true;
        }
        var classes = cls.split(" ");
        for (var i = 0; i < classes.length; i++) {
            // already present
            if (classes[i] == className) {
                // only check sane case where the class is used once
                classes.splice(i, 1);
                self.setElementClass(obj, classes.join(" "));
                return true;
            }
        }
        // not found
        return false;
    },

    /** @id MochiKit.DOM.swapElementClass */
    swapElementClass: function (element, fromClass, toClass) {
        var obj = MochiKit.DOM.getElement(element);
        var res = MochiKit.DOM.removeElementClass(obj, fromClass);
        if (res) {
            MochiKit.DOM.addElementClass(obj, toClass);
        }
        return res;
    },

    /** @id MochiKit.DOM.hasElementClass */
    hasElementClass: function (element, className/*...*/) {
        var obj = MochiKit.DOM.getElement(element);
        var cls = obj.className;
        if (!cls) {
            return false;
        }
        var classes = cls.split(" ");
        for (var i = 1; i < arguments.length; i++) {
            var good = false;
            for (var j = 0; j < classes.length; j++) {
                if (classes[j] == arguments[i]) {
                    good = true;
                    break;
                }
            }
            if (!good) {
                return false;
            }
        }
        return true;
    },

    /** @id MochiKit.DOM.escapeHTML */
    escapeHTML: function (s) {
        return s.replace(/&/g, "&amp;"
            ).replace(/"/g, "&quot;"
            ).replace(/</g, "&lt;"
            ).replace(/>/g, "&gt;");
    },

    /** @id MochiKit.DOM.toHTML */
    toHTML: function (dom) {
        return MochiKit.DOM.emitHTML(dom).join("");
    },

    /** @id MochiKit.DOM.emitHTML */
    emitHTML: function (dom, /* optional */lst) {
        if (typeof(lst) == 'undefined' || lst === null) {
            lst = [];
        }
        // queue is the call stack, we're doing this non-recursively
        var queue = [dom];
        var self = MochiKit.DOM;
        var escapeHTML = self.escapeHTML;
        var attributeArray = self.attributeArray;
        while (queue.length) {
            dom = queue.pop();
            if (typeof(dom) == 'string') {
                lst.push(dom);
            } else if (dom.nodeType == 1) {
                // we're not using higher order stuff here
                // because safari has heisenbugs.. argh.
                //
                // I think it might have something to do with
                // garbage collection and function calls.
                lst.push('<' + dom.tagName.toLowerCase());
                var attributes = [];
                var domAttr = attributeArray(dom);
                for (var i = 0; i < domAttr.length; i++) {
                    var a = domAttr[i];
                    attributes.push([
                        " ",
                        a.name,
                        '="',
                        escapeHTML(a.value),
                        '"'
                    ]);
                }
                attributes.sort();
                for (i = 0; i < attributes.length; i++) {
                    var attrs = attributes[i];
                    for (var j = 0; j < attrs.length; j++) {
                        lst.push(attrs[j]);
                    }
                }
                if (dom.hasChildNodes()) {
                    lst.push(">");
                    // queue is the FILO call stack, so we put the close tag
                    // on first
                    queue.push("</" + dom.tagName.toLowerCase() + ">");
                    var cnodes = dom.childNodes;
                    for (i = cnodes.length - 1; i >= 0; i--) {
                        queue.push(cnodes[i]);
                    }
                } else {
                    lst.push('/>');
                }
            } else if (dom.nodeType == 3) {
                lst.push(escapeHTML(dom.nodeValue));
            }
        }
        return lst;
    },

    /** @id MochiKit.DOM.scrapeText */
    scrapeText: function (node, /* optional */asArray) {
        var rval = [];
        (function (node) {
            var cn = node.childNodes;
            if (cn) {
                for (var i = 0; i < cn.length; i++) {
                    arguments.callee.call(this, cn[i]);
                }
            }
            var nodeValue = node.nodeValue;
            if (typeof(nodeValue) == 'string') {
                rval.push(nodeValue);
            }
        })(MochiKit.DOM.getElement(node));
        if (asArray) {
            return rval;
        } else {
            return rval.join("");
        }
    },

    /** @id MochiKit.DOM.removeEmptyTextNodes */
    removeEmptyTextNodes: function (element) {
        element = MochiKit.DOM.getElement(element);
        for (var i = 0; i < element.childNodes.length; i++) {
            var node = element.childNodes[i];
            if (node.nodeType == 3 && !/\S/.test(node.nodeValue)) {
                node.parentNode.removeChild(node);
            }
        }
    },

    /** @id MochiKit.DOM.makeClipping */
    makeClipping: function (element) {
        element = MochiKit.DOM.getElement(element);
        var oldOverflow = element.style.overflow;
        if ((MochiKit.Style.getStyle(element, 'overflow') || 'visible') != 'hidden') {
            element.style.overflow = 'hidden';
        }
        return oldOverflow;
    },

    /** @id MochiKit.DOM.undoClipping */
    undoClipping: function (element, overflow) {
        element = MochiKit.DOM.getElement(element);
        if (!overflow) {
            return;
        }
        element.style.overflow = overflow;
    },

    /** @id MochiKit.DOM.makePositioned */
    makePositioned: function (element) {
        element = MochiKit.DOM.getElement(element);
        var pos = MochiKit.Style.getStyle(element, 'position');
        if (pos == 'static' || !pos) {
            element.style.position = 'relative';
            // Opera returns the offset relative to the positioning context,
            // when an element is position relative but top and left have
            // not been defined
            if (/Opera/.test(navigator.userAgent)) {
                element.style.top = 0;
                element.style.left = 0;
            }
        }
    },

    /** @id MochiKit.DOM.undoPositioned */
    undoPositioned: function (element) {
        element = MochiKit.DOM.getElement(element);
        if (element.style.position == 'relative') {
            element.style.position = element.style.top = element.style.left = element.style.bottom = element.style.right = '';
        }
    },

    /** @id MochiKit.DOM.getFirstElementByTagAndClassName */
    getFirstElementByTagAndClassName: function (tagName, className,
            /* optional */parent) {
        var self = MochiKit.DOM;
        if (typeof(tagName) == 'undefined' || tagName === null) {
            tagName = '*';
        }
        if (typeof(parent) == 'undefined' || parent === null) {
            parent = self._document;
        }
        parent = self.getElement(parent);
        var children = (parent.getElementsByTagName(tagName)
            || self._document.all);
        if (typeof(className) == 'undefined' || className === null) {
            return children[0];
        }

        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            var classNames = child.className.split(' ');
            for (var j = 0; j < classNames.length; j++) {
                if (classNames[j] == className) {
                    return child;
                }
            }
        }
    },

    /** @id MochiKit.DOM.getFirstParentByTagAndClassName */
    getFirstParentByTagAndClassName: function (elem, tagName, className) {
        var self = MochiKit.DOM;
        elem = self.getElement(elem);
        if (typeof(tagName) == 'undefined' || tagName === null) {
            tagName = '*';
        } else {
            tagName = tagName.toUpperCase();
        }
        if (typeof(className) == 'undefined' || className === null) {
            className = null;
        }

        var classList = '';
        var curTagName = '';
        while (elem && elem.tagName) {
            elem = elem.parentNode;
            if (tagName == '*' && className === null) {
                return elem;
            }
            classList = elem.className.split(' ');
            curTagName = elem.tagName.toUpperCase();
            if (className === null && tagName == curTagName) {
                return elem;
            } else if (className !== null) {
                for (var i = 0; i < classList.length; i++) {
                    if (tagName == '*' && classList[i] == className) {
                        return elem;
                    } else if (tagName == curTagName && classList[i] == className) {
                        return elem;
                    }
                }
            }
        }
        return elem;
    },

    /** @id MochiKit.DOM.isParent */
    isParent: function (child, element) {
        if (!child.parentNode || child == element) {
            return false;
        }

        if (child.parentNode == element) {
            return true;
        }

        return MochiKit.DOM.isParent(child.parentNode, element);
    },

    __new__: function (win) {

        var m = MochiKit.Base;
        if (typeof(document) != "undefined") {
            this._document = document;
            var kXULNSURI = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul";
            this._xhtml = (document.documentElement &&
                document.createElementNS &&
                document.documentElement.namespaceURI === kXULNSURI);
        } else if (MochiKit.MockDOM) {
            this._document = MochiKit.MockDOM.document;
        }
        this._window = win;

        this.domConverters = new m.AdapterRegistry();

        var __tmpElement = this._document.createElement("span");
        var attributeArray;
        if (__tmpElement && __tmpElement.attributes &&
                __tmpElement.attributes.length > 0) {
            // for braindead browsers (IE) that insert extra junk
            var filter = m.filter;
            attributeArray = function (node) {
                return filter(attributeArray.ignoreAttrFilter, node.attributes);
            };
            attributeArray.ignoreAttr = {};
            var attrs = __tmpElement.attributes;
            var ignoreAttr = attributeArray.ignoreAttr;
            for (var i = 0; i < attrs.length; i++) {
                var a = attrs[i];
                ignoreAttr[a.name] = a.value;
            }
            attributeArray.ignoreAttrFilter = function (a) {
                return (attributeArray.ignoreAttr[a.name] != a.value);
            };
            attributeArray.compliant = false;
            attributeArray.renames = {
                "class": "className",
                "checked": "defaultChecked",
                "usemap": "useMap",
                "for": "htmlFor",
                "readonly": "readOnly",
                "colspan": "colSpan",
                "bgcolor": "bgColor",
                "cellspacing": "cellSpacing",
                "cellpadding": "cellPadding"
            };
        } else {
            attributeArray = function (node) {
                /***

                    Return an array of attributes for a given node,
                    filtering out attributes that don't belong for
                    that are inserted by "Certain Browsers".

                ***/
                return node.attributes;
            };
            attributeArray.compliant = true;
            attributeArray.renames = {};
        }
        this.attributeArray = attributeArray;

        // FIXME: this really belongs in Base, and could probably be cleaner
        var _deprecated = function(fromModule, arr) {
            var modules = arr[1].split('.');
            var str = '';
            var obj = {};

            str += 'if (!MochiKit.' + modules[1] + ') { throw new Error("';
            str += 'This function has been deprecated and depends on MochiKit.';
            str += modules[1] + '.");}';
            str += 'return MochiKit.' + modules[1] + '.' + arr[0];
            str += '.apply(this, arguments);';

            obj[modules[2]] = new Function(str);
            MochiKit.Base.update(MochiKit[fromModule], obj);
        }
        for (var i; i < MochiKit.DOM.DEPRECATED.length; i++) {
            _deprecated('DOM', MochiKit.DOM.DEPRECATED[i]);
        }

        // shorthand for createDOM syntax
        var createDOMFunc = this.createDOMFunc;
        /** @id MochiKit.DOM.UL */
        this.UL = createDOMFunc("ul");
        /** @id MochiKit.DOM.OL */
        this.OL = createDOMFunc("ol");
        /** @id MochiKit.DOM.LI */
        this.LI = createDOMFunc("li");
        /** @id MochiKit.DOM.TD */
        this.TD = createDOMFunc("td");
        /** @id MochiKit.DOM.TR */
        this.TR = createDOMFunc("tr");
        /** @id MochiKit.DOM.TBODY */
        this.TBODY = createDOMFunc("tbody");
        /** @id MochiKit.DOM.THEAD */
        this.THEAD = createDOMFunc("thead");
        /** @id MochiKit.DOM.TFOOT */
        this.TFOOT = createDOMFunc("tfoot");
        /** @id MochiKit.DOM.TABLE */
        this.TABLE = createDOMFunc("table");
        /** @id MochiKit.DOM.TH */
        this.TH = createDOMFunc("th");
        /** @id MochiKit.DOM.INPUT */
        this.INPUT = createDOMFunc("input");
        /** @id MochiKit.DOM.SPAN */
        this.SPAN = createDOMFunc("span");
        /** @id MochiKit.DOM.A */
        this.A = createDOMFunc("a");
        /** @id MochiKit.DOM.DIV */
        this.DIV = createDOMFunc("div");
        /** @id MochiKit.DOM.IMG */
        this.IMG = createDOMFunc("img");
        /** @id MochiKit.DOM.BUTTON */
        this.BUTTON = createDOMFunc("button");
        /** @id MochiKit.DOM.TT */
        this.TT = createDOMFunc("tt");
        /** @id MochiKit.DOM.PRE */
        this.PRE = createDOMFunc("pre");
        /** @id MochiKit.DOM.H1 */
        this.H1 = createDOMFunc("h1");
        /** @id MochiKit.DOM.H2 */
        this.H2 = createDOMFunc("h2");
        /** @id MochiKit.DOM.H3 */
        this.H3 = createDOMFunc("h3");
        /** @id MochiKit.DOM.BR */
        this.BR = createDOMFunc("br");
        /** @id MochiKit.DOM.HR */
        this.HR = createDOMFunc("hr");
        /** @id MochiKit.DOM.LABEL */
        this.LABEL = createDOMFunc("label");
        /** @id MochiKit.DOM.TEXTAREA */
        this.TEXTAREA = createDOMFunc("textarea");
        /** @id MochiKit.DOM.FORM */
        this.FORM = createDOMFunc("form");
        /** @id MochiKit.DOM.P */
        this.P = createDOMFunc("p");
        /** @id MochiKit.DOM.SELECT */
        this.SELECT = createDOMFunc("select");
        /** @id MochiKit.DOM.OPTION */
        this.OPTION = createDOMFunc("option");
        /** @id MochiKit.DOM.OPTGROUP */
        this.OPTGROUP = createDOMFunc("optgroup");
        /** @id MochiKit.DOM.LEGEND */
        this.LEGEND = createDOMFunc("legend");
        /** @id MochiKit.DOM.FIELDSET */
        this.FIELDSET = createDOMFunc("fieldset");
        /** @id MochiKit.DOM.STRONG */
        this.STRONG = createDOMFunc("strong");
        /** @id MochiKit.DOM.CANVAS */
        this.CANVAS = createDOMFunc("canvas");

        /** @id MochiKit.DOM.$ */
        this.$ = this.getElement;

        this.EXPORT_TAGS = {
            ":common": this.EXPORT,
            ":all": m.concat(this.EXPORT, this.EXPORT_OK)
        };

        m.nameFunctions(this);

    }
});


MochiKit.DOM.__new__(((typeof(window) == "undefined") ? this : window));

//
// XXX: Internet Explorer blows
//
if (MochiKit.__export__) {
    withWindow = MochiKit.DOM.withWindow;
    withDocument = MochiKit.DOM.withDocument;
}

MochiKit.Base._exportSymbols(this, MochiKit.DOM);
