/***

MochiKit.MockDOM 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(MochiKit) == "undefined") {
    MochiKit = {};
}

if (typeof(MochiKit.MockDOM) == "undefined") {
    MochiKit.MockDOM = {};
}

MochiKit.MockDOM.NAME = "MochiKit.MockDOM";
MochiKit.MockDOM.VERSION = "1.4";

MochiKit.MockDOM.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};

/** @id MochiKit.MockDOM.toString */
MochiKit.MockDOM.toString = function () {
    return this.__repr__();
};

/** @id MochiKit.MockDOM.createDocument */
MochiKit.MockDOM.createDocument = function () {
    var doc = new MochiKit.MockDOM.MockElement("DOCUMENT");
    doc.body = doc.createElement("BODY");
    doc.appendChild(doc.body);
    return doc;
};

/** @id MochiKit.MockDOM.MockElement */
MochiKit.MockDOM.MockElement = function (name, data, ownerDocument) {
    this.tagName = this.nodeName = name.toUpperCase();
    this.ownerDocument = ownerDocument || null;
    if (name == "DOCUMENT") {
        this.nodeType = 9;
        this.childNodes = [];
    } else if (typeof(data) == "string") {
        this.nodeValue = data;
        this.nodeType = 3;
    } else {
        this.nodeType = 1;
        this.childNodes = [];
    }
    if (name.substring(0, 1) == "<") {
        var nameattr = name.substring(
            name.indexOf('"') + 1, name.lastIndexOf('"'));
        name = name.substring(1, name.indexOf(" "));
        this.tagName = this.nodeName = name.toUpperCase();
        this.setAttribute("name", nameattr);
    }
};

MochiKit.MockDOM.MockElement.prototype = {
    /** @id MochiKit.MockDOM.MockElement.prototype.createElement */
    createElement: function (tagName) {
        return new MochiKit.MockDOM.MockElement(tagName, null, this.nodeType == 9 ? this : this.ownerDocument);
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.createTextNode */
    createTextNode: function (text) {
        return new MochiKit.MockDOM.MockElement("text", text, this.nodeType == 9 ? this : this.ownerDocument);
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.setAttribute */
    setAttribute: function (name, value) {
        this[name] = value;
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.getAttribute */
    getAttribute: function (name) {
        return this[name];
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.appendChild */
    appendChild: function (child) {
        this.childNodes.push(child);
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.toString */
    toString: function () {
        return "MockElement(" + this.tagName + ")";
    },
    /** @id MochiKit.MockDOM.MockElement.prototype.getElementsByTagName */
    getElementsByTagName: function (tagName) {
        var foundElements = [];
        MochiKit.Base.nodeWalk(this, function(node){
            if (tagName == '*' || tagName == node.tagName) {
                foundElements.push(node);
                return node.childNodes;
            }
        });
        return foundElements;
    }
};

    /** @id MochiKit.MockDOM.EXPORT_OK */
MochiKit.MockDOM.EXPORT_OK = [
    "mockElement",
    "createDocument"
];

    /** @id MochiKit.MockDOM.EXPORT */
MochiKit.MockDOM.EXPORT = [
    "document"
];

MochiKit.MockDOM.__new__ = function () {
    this.document = this.createDocument();
};

MochiKit.MockDOM.__new__();
