/***

MochiKit.Selector 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito and others.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Selector');
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
    if (typeof(MochiKit.Base) === 'undefined' ||
        typeof(MochiKit.DOM) === 'undefined' ||
        typeof(MochiKit.Iter) === 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Selector depends on MochiKit.Base, MochiKit.DOM and MochiKit.Iter!";
}

if (typeof(MochiKit.Selector) == 'undefined') {
    MochiKit.Selector = {};
}

MochiKit.Selector.NAME = "MochiKit.Selector";

MochiKit.Selector.VERSION = "1.4";

MochiKit.Selector.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};

MochiKit.Selector.toString = function () {
    return this.__repr__();
};

MochiKit.Selector.EXPORT = [
    "Selector",
    "findChildElements",
    "findDocElements",
    "$$"
];

MochiKit.Selector.EXPORT_OK = [
];

MochiKit.Selector.Selector = function (expression) {
    this.params = {classNames: [], pseudoClassNames: []};
    this.expression = expression.toString().replace(/(^\s+|\s+$)/g, '');
    this.parseExpression();
    this.compileMatcher();
};

MochiKit.Selector.Selector.prototype = {
    /***

    Selector class: convenient object to make CSS selections.

    ***/
    __class__: MochiKit.Selector.Selector,

    /** @id MochiKit.Selector.Selector.prototype.parseExpression */
    parseExpression: function () {
        function abort(message) {
            throw 'Parse error in selector: ' + message;
        }

        if (this.expression == '')  {
            abort('empty expression');
        }

        var repr = MochiKit.Base.repr;
        var params = this.params;
        var expr = this.expression;
        var match, modifier, clause, rest;
        while (match = expr.match(/^(.*)\[([a-z0-9_:-]+?)(?:([~\|!^$*]?=)(?:"([^"]*)"|([^\]\s]*)))?\]$/i)) {
            params.attributes = params.attributes || [];
            params.attributes.push({name: match[2], operator: match[3], value: match[4] || match[5] || ''});
            expr = match[1];
        }

        if (expr == '*') {
            return this.params.wildcard = true;
        }

        while (match = expr.match(/^([^a-z0-9_-])?([a-z0-9_-]+(?:\([^)]*\))?)(.*)/i)) {
            modifier = match[1];
            clause = match[2];
            rest = match[3];
            switch (modifier) {
                case '#':
                    params.id = clause;
                    break;
                case '.':
                    params.classNames.push(clause);
                    break;
                case ':':
                    params.pseudoClassNames.push(clause);
                    break;
                case '':
                case undefined:
                    params.tagName = clause.toUpperCase();
                    break;
                default:
                    abort(repr(expr));
            }
            expr = rest;
        }

        if (expr.length > 0) {
            abort(repr(expr));
        }
    },

    /** @id MochiKit.Selector.Selector.prototype.buildMatchExpression */
    buildMatchExpression: function () {
        var repr = MochiKit.Base.repr;
        var params = this.params;
        var conditions = [];
        var clause, i;

        function childElements(element) {
            return "MochiKit.Base.filter(function (node) { return node.nodeType == 1; }, " + element + ".childNodes)";
        }

        if (params.wildcard) {
            conditions.push('true');
        }
        if (clause = params.id) {
            conditions.push('element.id == ' + repr(clause));
        }
        if (clause = params.tagName) {
            conditions.push('element.tagName.toUpperCase() == ' + repr(clause));
        }
        if ((clause = params.classNames).length > 0) {
            for (i = 0; i < clause.length; i++) {
                conditions.push('MochiKit.DOM.hasElementClass(element, ' + repr(clause[i]) + ')');
            }
        }
        if ((clause = params.pseudoClassNames).length > 0) {
            for (i = 0; i < clause.length; i++) {
                var match = clause[i].match(/^([^(]+)(?:\((.*)\))?$/);
                var pseudoClass = match[1];
                var pseudoClassArgument = match[2];
                switch (pseudoClass) {
                    case 'root':
                        conditions.push('element.nodeType == 9 || element === element.ownerDocument.documentElement'); break;
                    case 'nth-child':
                    case 'nth-last-child':
                    case 'nth-of-type':
                    case 'nth-last-of-type':
                        match = pseudoClassArgument.match(/^((?:(\d+)n\+)?(\d+)|odd|even)$/);
                        if (!match) {
                            throw "Invalid argument to pseudo element nth-child: " + pseudoClassArgument;
                        }
                        var a, b;
                        if (match[0] == 'odd') {
                            a = 2;
                            b = 1;
                        } else if (match[0] == 'even') {
                            a = 2;
                            b = 0;
                        } else {
                            a = match[2] && parseInt(match) || null;
                            b = parseInt(match[3]);
                        }
                        conditions.push('this.nthChild(element,' + a + ',' + b
                                        + ',' + !!pseudoClass.match('^nth-last')    // Reverse
                                        + ',' + !!pseudoClass.match('of-type$')     // Restrict to same tagName
                                        + ')');
                        break;
                    case 'first-child':
                        conditions.push('this.nthChild(element, null, 1)');
                        break;
                    case 'last-child':
                        conditions.push('this.nthChild(element, null, 1, true)');
                        break;
                    case 'first-of-type':
                        conditions.push('this.nthChild(element, null, 1, false, true)');
                        break;
                    case 'last-of-type':
                        conditions.push('this.nthChild(element, null, 1, true, true)');
                        break;
                    case 'only-child':
                        conditions.push(childElements('element.parentNode') + '.length == 1');
                        break;
                    case 'only-of-type':
                        conditions.push('MochiKit.Base.filter(function (node) { return node.tagName == element.tagName; }, ' + childElements('element.parentNode') + ').length == 1');
                        break;
                    case 'empty':
                        conditions.push('element.childNodes.length == 0');
                        break;
                    case 'enabled':
                        conditions.push('(this.isUIElement(element) && element.disabled === false)');
                        break;
                    case 'disabled':
                        conditions.push('(this.isUIElement(element) && element.disabled === true)');
                        break;
                    case 'checked':
                        conditions.push('(this.isUIElement(element) && element.checked === true)');
                        break;
                    case 'not':
                        var subselector = new MochiKit.Selector.Selector(pseudoClassArgument);
                        conditions.push('!( ' + subselector.buildMatchExpression() + ')')
                        break;
                }
            }
        }
        if (clause = params.attributes) {
            MochiKit.Base.map(function (attribute) {
                var value = 'MochiKit.DOM.getNodeAttribute(element, ' + repr(attribute.name) + ')';
                var splitValueBy = function (delimiter) {
                    return value + '.split(' + repr(delimiter) + ')';
                }

                switch (attribute.operator) {
                    case '=':
                        conditions.push(value + ' == ' + repr(attribute.value));
                        break;
                    case '~=':
                        conditions.push(value + ' && MochiKit.Base.findValue(' + splitValueBy(' ') + ', ' + repr(attribute.value) + ') > -1');
                        break;
                    case '^=':
                        conditions.push(value + '.substring(0, ' + attribute.value.length + ') == ' + repr(attribute.value));
                        break;
                    case '$=':
                        conditions.push(value + '.substring(' + value + '.length - ' + attribute.value.length + ') == ' + repr(attribute.value));
                        break;
                    case '*=':
                        conditions.push(value + '.match(' + repr(attribute.value) + ')');
                        break;
                    case '|=':
                        conditions.push(
                            value + ' && ' + splitValueBy('-') + '[0].toUpperCase() == ' + repr(attribute.value.toUpperCase())
                        );
                        break;
                    case '!=':
                        conditions.push(value + ' != ' + repr(attribute.value));
                        break;
                    case '':
                    case undefined:
                        conditions.push(value + ' != null');
                        break;
                    default:
                        throw 'Unknown operator ' + attribute.operator + ' in selector';
                }
            }, clause);
        }

        return conditions.join(' && ');
    },

    /** @id MochiKit.Selector.Selector.prototype.compileMatcher */
    compileMatcher: function () {
        this.match = new Function('element', 'if (!element.tagName) return false; \
                return ' + this.buildMatchExpression());
    },

    /** @id MochiKit.Selector.Selector.prototype.nthChild */
    nthChild: function (element, a, b, reverse, sametag){
        var siblings = MochiKit.Base.filter(function (node) {
            return node.nodeType == 1;
        }, element.parentNode.childNodes);
        if (sametag) {
            siblings = MochiKit.Base.filter(function (node) {
                return node.tagName == element.tagName;
            }, siblings);
        }
        if (reverse) {
            siblings = MochiKit.Iter.reversed(siblings);
        }
        if (a) {
            var actualIndex = MochiKit.Base.findIdentical(siblings, element);
            return ((actualIndex + 1 - b) / a) % 1 == 0;
        } else {
            return b == MochiKit.Base.findIdentical(siblings, element) + 1;
        }
    },

    /** @id MochiKit.Selector.Selector.prototype.isUIElement */
    isUIElement: function (element) {
        return MochiKit.Base.findValue(['input', 'button', 'select', 'option', 'textarea', 'object'],
                element.tagName.toLowerCase()) > -1;
    },

    /** @id MochiKit.Selector.Selector.prototype.findElements */
    findElements: function (scope, axis) {
        var element;

        if (axis == undefined) {
            axis = "";
        }

        function inScope(element, scope) {
            if (axis == "") {
                return MochiKit.DOM.isChildNode(element, scope);
            } else if (axis == ">") {
                return element.parentNode == scope;
            } else if (axis == "+") {
                return element == nextSiblingElement(scope);
            } else if (axis == "~") {
                var sibling = scope;
                while (sibling = nextSiblingElement(sibling)) {
                    if (element == sibling) {
                        return true;
                    }
                }
                return false;
            } else {
                throw "Invalid axis: " + axis;
            }
        }

        if (element = MochiKit.DOM.getElement(this.params.id)) {
            if (this.match(element)) {
                if (!scope || inScope(element, scope)) {
                    return [element];
                }
            }
        }

        function nextSiblingElement(node) {
            node = node.nextSibling;
            while (node && node.nodeType != 1) {
                node = node.nextSibling;
            }
            return node;
        }

        if (axis == "") {
            scope = (scope || MochiKit.DOM.currentDocument()).getElementsByTagName(this.params.tagName || '*');
        } else if (axis == ">") {
            if (!scope) {
                throw "> combinator not allowed without preceeding expression";
            }
            scope = MochiKit.Base.filter(function (node) {
                return node.nodeType == 1;
            }, scope.childNodes);
        } else if (axis == "+") {
            if (!scope) {
                throw "+ combinator not allowed without preceeding expression";
            }
            scope = nextSiblingElement(scope) && [nextSiblingElement(scope)];
        } else if (axis == "~") {
            if (!scope) {
                throw "~ combinator not allowed without preceeding expression";
            }
            var newscope = [];
            while (nextSiblingElement(scope)) {
                scope = nextSiblingElement(scope);
                newscope.push(scope);
            }
            scope = newscope;
        }

        if (!scope) {
            return [];
        }

        var results = MochiKit.Base.filter(MochiKit.Base.bind(function (scopeElt) {
            return this.match(scopeElt);
        }, this), scope);

        return results;
    },

    /** @id MochiKit.Selector.Selector.prototype.repr */
    repr: function () {
        return 'Selector(' + this.expression + ')';
    },

    toString: MochiKit.Base.forwardCall("repr")
};

MochiKit.Base.update(MochiKit.Selector, {

    /** @id MochiKit.Selector.findChildElements */
    findChildElements: function (element, expressions) {
        return MochiKit.Base.flattenArray(MochiKit.Base.map(function (expression) {
            var nextScope = "";
            return MochiKit.Iter.reduce(function (results, expr) {
                if (match = expr.match(/^[>+~]$/)) {
                    nextScope = match[0];
                    return results;
                } else {
                    var selector = new MochiKit.Selector.Selector(expr);
                    var elements = MochiKit.Iter.reduce(function (elements, result) {
                        return MochiKit.Base.extend(elements, selector.findElements(result || element, nextScope));
                    }, results, []);
                    nextScope = "";
                    return elements;
                }
            }, expression.replace(/(^\s+|\s+$)/g, '').split(/\s+/), [null]);
        }, expressions));
    },

    findDocElements: function () {
        return MochiKit.Selector.findChildElements(MochiKit.DOM.currentDocument(), arguments);
    },

    __new__: function () {
        var m = MochiKit.Base;

        this.$$ = this.findDocElements;

        this.EXPORT_TAGS = {
            ":common": this.EXPORT,
            ":all": m.concat(this.EXPORT, this.EXPORT_OK)
        };

        m.nameFunctions(this);
    }
});

MochiKit.Selector.__new__();

MochiKit.Base._exportSymbols(this, MochiKit.Selector);

