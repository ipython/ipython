/***
Copyright (c) 2005 Thomas Fuchs (http://script.aculo.us, http://mir.aculo.us)
    Mochi-ized By Thomas Herve (_firstname_@nimail.org)

See scriptaculous.js for full license.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Sortable');
    dojo.require('MochiKit.Base');
    dojo.require('MochiKit.DOM');
    dojo.require('MochiKit.Iter');
}

if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Base", []);
    JSAN.use("MochiKit.DOM", []);
    JSAN.use("MochiKit.Iter", []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined' ||
        typeof(MochiKit.DOM) == 'undefined' ||
        typeof(MochiKit.Iter) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.DragAndDrop depends on MochiKit.Base, MochiKit.DOM and MochiKit.Iter!";
}

if (typeof(MochiKit.Sortable) == 'undefined') {
    MochiKit.Sortable = {};
}

MochiKit.Sortable.NAME = 'MochiKit.Sortable';
MochiKit.Sortable.VERSION = '1.4';

MochiKit.Sortable.__repr__ = function () {
    return '[' + this.NAME + ' ' + this.VERSION + ']';
};

MochiKit.Sortable.toString = function () {
    return this.__repr__();
};

MochiKit.Sortable.EXPORT = [
];

MochiKit.Sortable.EXPORT_OK = [
];

MochiKit.Base.update(MochiKit.Sortable, {
    /***

    Manage sortables. Mainly use the create function to add a sortable.

    ***/
    sortables: {},

    _findRootElement: function (element) {
        while (element.tagName.toUpperCase() != "BODY") {
            if (element.id && MochiKit.Sortable.sortables[element.id]) {
                return element;
            }
            element = element.parentNode;
        }
    },

    /** @id MochiKit.Sortable.options */
    options: function (element) {
        element = MochiKit.Sortable._findRootElement(MochiKit.DOM.getElement(element));
        if (!element) {
            return;
        }
        return MochiKit.Sortable.sortables[element.id];
    },

    /** @id MochiKit.Sortable.destroy */
    destroy: function (element){
        var s = MochiKit.Sortable.options(element);
        var b = MochiKit.Base;
        var d = MochiKit.DragAndDrop;

        if (s) {
            MochiKit.Signal.disconnect(s.startHandle);
            MochiKit.Signal.disconnect(s.endHandle);
            b.map(function (dr) {
                d.Droppables.remove(dr);
            }, s.droppables);
            b.map(function (dr) {
                dr.destroy();
            }, s.draggables);

            delete MochiKit.Sortable.sortables[s.element.id];
        }
    },

    /** @id MochiKit.Sortable.create */
    create: function (element, options) {
        element = MochiKit.DOM.getElement(element);
        var self = MochiKit.Sortable;

        /** @id MochiKit.Sortable.options */
        options = MochiKit.Base.update({

            /** @id MochiKit.Sortable.element */
            element: element,

            /** @id MochiKit.Sortable.tag */
            tag: 'li',  // assumes li children, override with tag: 'tagname'

            /** @id MochiKit.Sortable.dropOnEmpty */
            dropOnEmpty: false,

            /** @id MochiKit.Sortable.tree */
            tree: false,

            /** @id MochiKit.Sortable.treeTag */
            treeTag: 'ul',

            /** @id MochiKit.Sortable.overlap */
            overlap: 'vertical',  // one of 'vertical', 'horizontal'

            /** @id MochiKit.Sortable.constraint */
            constraint: 'vertical',  // one of 'vertical', 'horizontal', false
            // also takes array of elements (or ids); or false

            /** @id MochiKit.Sortable.containment */
            containment: [element],

            /** @id MochiKit.Sortable.handle */
            handle: false,  // or a CSS class

            /** @id MochiKit.Sortable.only */
            only: false,

            /** @id MochiKit.Sortable.hoverclass */
            hoverclass: null,

            /** @id MochiKit.Sortable.ghosting */
            ghosting: false,

            /** @id MochiKit.Sortable.scroll */
            scroll: false,

            /** @id MochiKit.Sortable.scrollSensitivity */
            scrollSensitivity: 20,

            /** @id MochiKit.Sortable.scrollSpeed */
            scrollSpeed: 15,

            /** @id MochiKit.Sortable.format */
            format: /^[^_]*_(.*)$/,

            /** @id MochiKit.Sortable.onChange */
            onChange: MochiKit.Base.noop,

            /** @id MochiKit.Sortable.onUpdate */
            onUpdate: MochiKit.Base.noop,

            /** @id MochiKit.Sortable.accept */
            accept: null
        }, options);

        // clear any old sortable with same element
        self.destroy(element);

        // build options for the draggables
        var options_for_draggable = {
            revert: true,
            ghosting: options.ghosting,
            scroll: options.scroll,
            scrollSensitivity: options.scrollSensitivity,
            scrollSpeed: options.scrollSpeed,
            constraint: options.constraint,
            handle: options.handle
        };

        if (options.starteffect) {
            options_for_draggable.starteffect = options.starteffect;
        }

        if (options.reverteffect) {
            options_for_draggable.reverteffect = options.reverteffect;
        } else if (options.ghosting) {
            options_for_draggable.reverteffect = function (innerelement) {
                innerelement.style.top = 0;
                innerelement.style.left = 0;
            };
        }

        if (options.endeffect) {
            options_for_draggable.endeffect = options.endeffect;
        }

        if (options.zindex) {
            options_for_draggable.zindex = options.zindex;
        }

        // build options for the droppables
        var options_for_droppable = {
            overlap: options.overlap,
            containment: options.containment,
            hoverclass: options.hoverclass,
            onhover: self.onHover,
            tree: options.tree,
            accept: options.accept
        }

        var options_for_tree = {
            onhover: self.onEmptyHover,
            overlap: options.overlap,
            containment: options.containment,
            hoverclass: options.hoverclass,
            accept: options.accept
        }

        // fix for gecko engine
        MochiKit.DOM.removeEmptyTextNodes(element);

        options.draggables = [];
        options.droppables = [];

        // drop on empty handling
        if (options.dropOnEmpty || options.tree) {
            new MochiKit.DragAndDrop.Droppable(element, options_for_tree);
            options.droppables.push(element);
        }
        MochiKit.Base.map(function (e) {
            // handles are per-draggable
            var handle = options.handle ?
                MochiKit.DOM.getFirstElementByTagAndClassName(null,
                    options.handle, e) : e;
            options.draggables.push(
                new MochiKit.DragAndDrop.Draggable(e,
                    MochiKit.Base.update(options_for_draggable,
                                         {handle: handle})));
            new MochiKit.DragAndDrop.Droppable(e, options_for_droppable);
            if (options.tree) {
                e.treeNode = element;
            }
            options.droppables.push(e);
        }, (self.findElements(element, options) || []));

        if (options.tree) {
            MochiKit.Base.map(function (e) {
                new MochiKit.DragAndDrop.Droppable(e, options_for_tree);
                e.treeNode = element;
                options.droppables.push(e);
            }, (self.findTreeElements(element, options) || []));
        }

        // keep reference
        self.sortables[element.id] = options;

        options.lastValue = self.serialize(element);
        options.startHandle = MochiKit.Signal.connect(MochiKit.DragAndDrop.Draggables, 'start',
                                MochiKit.Base.partial(self.onStart, element));
        options.endHandle = MochiKit.Signal.connect(MochiKit.DragAndDrop.Draggables, 'end',
                                MochiKit.Base.partial(self.onEnd, element));
    },

    /** @id MochiKit.Sortable.onStart */
    onStart: function (element, draggable) {
        var self = MochiKit.Sortable;
        var options = self.options(element);
        options.lastValue = self.serialize(options.element);
    },

    /** @id MochiKit.Sortable.onEnd */
    onEnd: function (element, draggable) {
        var self = MochiKit.Sortable;
        self.unmark();
        var options = self.options(element);
        if (options.lastValue != self.serialize(options.element)) {
            options.onUpdate(options.element);
        }
    },

    // return all suitable-for-sortable elements in a guaranteed order

    /** @id MochiKit.Sortable.findElements */
    findElements: function (element, options) {
        return MochiKit.Sortable.findChildren(
            element, options.only, options.tree ? true : false, options.tag);
    },

    /** @id MochiKit.Sortable.findTreeElements */
    findTreeElements: function (element, options) {
        return MochiKit.Sortable.findChildren(
            element, options.only, options.tree ? true : false, options.treeTag);
    },

    /** @id MochiKit.Sortable.findChildren */
    findChildren: function (element, only, recursive, tagName) {
        if (!element.hasChildNodes()) {
            return null;
        }
        tagName = tagName.toUpperCase();
        if (only) {
            only = MochiKit.Base.flattenArray([only]);
        }
        var elements = [];
        MochiKit.Base.map(function (e) {
            if (e.tagName &&
                e.tagName.toUpperCase() == tagName &&
               (!only ||
                MochiKit.Iter.some(only, function (c) {
                    return MochiKit.DOM.hasElementClass(e, c);
                }))) {
                elements.push(e);
            }
            if (recursive) {
                var grandchildren = MochiKit.Sortable.findChildren(e, only, recursive, tagName);
                if (grandchildren && grandchildren.length > 0) {
                    elements = elements.concat(grandchildren);
                }
            }
        }, element.childNodes);
        return elements;
    },

    /** @id MochiKit.Sortable.onHover */
    onHover: function (element, dropon, overlap) {
        if (MochiKit.DOM.isParent(dropon, element)) {
            return;
        }
        var self = MochiKit.Sortable;

        if (overlap > .33 && overlap < .66 && self.options(dropon).tree) {
            return;
        } else if (overlap > 0.5) {
            self.mark(dropon, 'before');
            if (dropon.previousSibling != element) {
                var oldParentNode = element.parentNode;
                element.style.visibility = 'hidden';  // fix gecko rendering
                dropon.parentNode.insertBefore(element, dropon);
                if (dropon.parentNode != oldParentNode) {
                    self.options(oldParentNode).onChange(element);
                }
                self.options(dropon.parentNode).onChange(element);
            }
        } else {
            self.mark(dropon, 'after');
            var nextElement = dropon.nextSibling || null;
            if (nextElement != element) {
                var oldParentNode = element.parentNode;
                element.style.visibility = 'hidden';  // fix gecko rendering
                dropon.parentNode.insertBefore(element, nextElement);
                if (dropon.parentNode != oldParentNode) {
                    self.options(oldParentNode).onChange(element);
                }
                self.options(dropon.parentNode).onChange(element);
            }
        }
    },

    _offsetSize: function (element, type) {
        if (type == 'vertical' || type == 'height') {
            return element.offsetHeight;
        } else {
            return element.offsetWidth;
        }
    },

    /** @id MochiKit.Sortable.onEmptyHover */
    onEmptyHover: function (element, dropon, overlap) {
        var oldParentNode = element.parentNode;
        var self = MochiKit.Sortable;
        var droponOptions = self.options(dropon);

        if (!MochiKit.DOM.isParent(dropon, element)) {
            var index;

            var children = self.findElements(dropon, {tag: droponOptions.tag,
                                                      only: droponOptions.only});
            var child = null;

            if (children) {
                var offset = self._offsetSize(dropon, droponOptions.overlap) * (1.0 - overlap);

                for (index = 0; index < children.length; index += 1) {
                    if (offset - self._offsetSize(children[index], droponOptions.overlap) >= 0) {
                        offset -= self._offsetSize(children[index], droponOptions.overlap);
                    } else if (offset - (self._offsetSize (children[index], droponOptions.overlap) / 2) >= 0) {
                        child = index + 1 < children.length ? children[index + 1] : null;
                        break;
                    } else {
                        child = children[index];
                        break;
                    }
                }
            }

            dropon.insertBefore(element, child);

            self.options(oldParentNode).onChange(element);
            droponOptions.onChange(element);
        }
    },

    /** @id MochiKit.Sortable.unmark */
    unmark: function () {
        var m = MochiKit.Sortable._marker;
        if (m) {
            MochiKit.Style.hideElement(m);
        }
    },

    /** @id MochiKit.Sortable.mark */
    mark: function (dropon, position) {
        // mark on ghosting only
        var d = MochiKit.DOM;
        var self = MochiKit.Sortable;
        var sortable = self.options(dropon.parentNode);
        if (sortable && !sortable.ghosting) {
            return;
        }

        if (!self._marker) {
            self._marker = d.getElement('dropmarker') ||
                        document.createElement('DIV');
            MochiKit.Style.hideElement(self._marker);
            d.addElementClass(self._marker, 'dropmarker');
            self._marker.style.position = 'absolute';
            document.getElementsByTagName('body').item(0).appendChild(self._marker);
        }
        var offsets = MochiKit.Position.cumulativeOffset(dropon);
        self._marker.style.left = offsets.x + 'px';
        self._marker.style.top = offsets.y + 'px';

        if (position == 'after') {
            if (sortable.overlap == 'horizontal') {
                self._marker.style.left = (offsets.x + dropon.clientWidth) + 'px';
            } else {
                self._marker.style.top = (offsets.y + dropon.clientHeight) + 'px';
            }
        }
        MochiKit.Style.showElement(self._marker);
    },

    _tree: function (element, options, parent) {
        var self = MochiKit.Sortable;
        var children = self.findElements(element, options) || [];

        for (var i = 0; i < children.length; ++i) {
            var match = children[i].id.match(options.format);

            if (!match) {
                continue;
            }

            var child = {
                id: encodeURIComponent(match ? match[1] : null),
                element: element,
                parent: parent,
                children: [],
                position: parent.children.length,
                container: self._findChildrenElement(children[i], options.treeTag.toUpperCase())
            }

            /* Get the element containing the children and recurse over it */
            if (child.container) {
                self._tree(child.container, options, child)
            }

            parent.children.push (child);
        }

        return parent;
    },

    /* Finds the first element of the given tag type within a parent element.
       Used for finding the first LI[ST] within a L[IST]I[TEM].*/
    _findChildrenElement: function (element, containerTag) {
        if (element && element.hasChildNodes) {
            containerTag = containerTag.toUpperCase();
            for (var i = 0; i < element.childNodes.length; ++i) {
                if (element.childNodes[i].tagName.toUpperCase() == containerTag) {
                    return element.childNodes[i];
                }
            }
        }
        return null;
    },

    /** @id MochiKit.Sortable.tree */
    tree: function (element, options) {
        element = MochiKit.DOM.getElement(element);
        var sortableOptions = MochiKit.Sortable.options(element);
        options = MochiKit.Base.update({
            tag: sortableOptions.tag,
            treeTag: sortableOptions.treeTag,
            only: sortableOptions.only,
            name: element.id,
            format: sortableOptions.format
        }, options || {});

        var root = {
            id: null,
            parent: null,
            children: new Array,
            container: element,
            position: 0
        }

        return MochiKit.Sortable._tree(element, options, root);
    },

    /**
     * Specifies the sequence for the Sortable.
     * @param {Node} element    Element to use as the Sortable.
     * @param {Object} newSequence    New sequence to use.
     * @param {Object} options    Options to use fro the Sortable.
     */
    setSequence: function (element, newSequence, options) {
        var self = MochiKit.Sortable;
        var b = MochiKit.Base;
        element = MochiKit.DOM.getElement(element);
        options = b.update(self.options(element), options || {});

        var nodeMap = {};
        b.map(function (n) {
            var m = n.id.match(options.format);
            if (m) {
                nodeMap[m[1]] = [n, n.parentNode];
            }
            n.parentNode.removeChild(n);
        }, self.findElements(element, options));

        b.map(function (ident) {
            var n = nodeMap[ident];
            if (n) {
                n[1].appendChild(n[0]);
                delete nodeMap[ident];
            }
        }, newSequence);
    },

    /* Construct a [i] index for a particular node */
    _constructIndex: function (node) {
        var index = '';
        do {
            if (node.id) {
                index = '[' + node.position + ']' + index;
            }
        } while ((node = node.parent) != null);
        return index;
    },

    /** @id MochiKit.Sortable.sequence */
    sequence: function (element, options) {
        element = MochiKit.DOM.getElement(element);
        var self = MochiKit.Sortable;
        var options = MochiKit.Base.update(self.options(element), options || {});

        return MochiKit.Base.map(function (item) {
            return item.id.match(options.format) ? item.id.match(options.format)[1] : '';
        }, MochiKit.DOM.getElement(self.findElements(element, options) || []));
    },

    /**
     * Serializes the content of a Sortable. Useful to send this content through a XMLHTTPRequest.
     * These options override the Sortable options for the serialization only.
     * @param {Node} element    Element to serialize.
     * @param {Object} options    Serialization options.
     */
    serialize: function (element, options) {
        element = MochiKit.DOM.getElement(element);
        var self = MochiKit.Sortable;
        options = MochiKit.Base.update(self.options(element), options || {});
        var name = encodeURIComponent(options.name || element.id);

        if (options.tree) {
            return MochiKit.Base.flattenArray(MochiKit.Base.map(function (item) {
                return [name + self._constructIndex(item) + "[id]=" +
                encodeURIComponent(item.id)].concat(item.children.map(arguments.callee));
            }, self.tree(element, options).children)).join('&');
        } else {
            return MochiKit.Base.map(function (item) {
                return name + "[]=" + encodeURIComponent(item);
            }, self.sequence(element, options)).join('&');
        }
    }
});

// trunk compatibility
MochiKit.Sortable.Sortable = MochiKit.Sortable;
