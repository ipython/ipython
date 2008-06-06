/***

MochiKit.Visual 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito and others.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Visual');
    dojo.require('MochiKit.Base');
    dojo.require('MochiKit.DOM');
    dojo.require('MochiKit.Style');
    dojo.require('MochiKit.Color');
    dojo.require('MochiKit.Position');
}

if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Base", []);
    JSAN.use("MochiKit.DOM", []);
    JSAN.use("MochiKit.Style", []);
    JSAN.use("MochiKit.Color", []);
    JSAN.use("MochiKit.Position", []);
}

try {
    if (typeof(MochiKit.Base) === 'undefined' ||
        typeof(MochiKit.DOM) === 'undefined' ||
        typeof(MochiKit.Style) === 'undefined' ||
        typeof(MochiKit.Position) === 'undefined' ||
        typeof(MochiKit.Color) === 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Visual depends on MochiKit.Base, MochiKit.DOM, MochiKit.Style, MochiKit.Position and MochiKit.Color!";
}

if (typeof(MochiKit.Visual) == "undefined") {
    MochiKit.Visual = {};
}

MochiKit.Visual.NAME = "MochiKit.Visual";
MochiKit.Visual.VERSION = "1.4";

MochiKit.Visual.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};

MochiKit.Visual.toString = function () {
    return this.__repr__();
};

MochiKit.Visual._RoundCorners = function (e, options) {
    e = MochiKit.DOM.getElement(e);
    this._setOptions(options);
    if (this.options.__unstable__wrapElement) {
        e = this._doWrap(e);
    }

    var color = this.options.color;
    var C = MochiKit.Color.Color;
    if (this.options.color === "fromElement") {
        color = C.fromBackground(e);
    } else if (!(color instanceof C)) {
        color = C.fromString(color);
    }
    this.isTransparent = (color.asRGB().a <= 0);

    var bgColor = this.options.bgColor;
    if (this.options.bgColor === "fromParent") {
        bgColor = C.fromBackground(e.offsetParent);
    } else if (!(bgColor instanceof C)) {
        bgColor = C.fromString(bgColor);
    }

    this._roundCornersImpl(e, color, bgColor);
};

MochiKit.Visual._RoundCorners.prototype = {
    _doWrap: function (e) {
        var parent = e.parentNode;
        var doc = MochiKit.DOM.currentDocument();
        if (typeof(doc.defaultView) === "undefined"
            || doc.defaultView === null) {
            return e;
        }
        var style = doc.defaultView.getComputedStyle(e, null);
        if (typeof(style) === "undefined" || style === null) {
            return e;
        }
        var wrapper = MochiKit.DOM.DIV({"style": {
            display: "block",
            // convert padding to margin
            marginTop: style.getPropertyValue("padding-top"),
            marginRight: style.getPropertyValue("padding-right"),
            marginBottom: style.getPropertyValue("padding-bottom"),
            marginLeft: style.getPropertyValue("padding-left"),
            // remove padding so the rounding looks right
            padding: "0px"
            /*
            paddingRight: "0px",
            paddingLeft: "0px"
            */
        }});
        wrapper.innerHTML = e.innerHTML;
        e.innerHTML = "";
        e.appendChild(wrapper);
        return e;
    },

    _roundCornersImpl: function (e, color, bgColor) {
        if (this.options.border) {
            this._renderBorder(e, bgColor);
        }
        if (this._isTopRounded()) {
            this._roundTopCorners(e, color, bgColor);
        }
        if (this._isBottomRounded()) {
            this._roundBottomCorners(e, color, bgColor);
        }
    },

    _renderBorder: function (el, bgColor) {
        var borderValue = "1px solid " + this._borderColor(bgColor);
        var borderL = "border-left: "  + borderValue;
        var borderR = "border-right: " + borderValue;
        var style = "style='" + borderL + ";" + borderR +  "'";
        el.innerHTML = "<div " + style + ">" + el.innerHTML + "</div>";
    },

    _roundTopCorners: function (el, color, bgColor) {
        var corner = this._createCorner(bgColor);
        for (var i = 0; i < this.options.numSlices; i++) {
            corner.appendChild(
                this._createCornerSlice(color, bgColor, i, "top")
            );
        }
        el.style.paddingTop = 0;
        el.insertBefore(corner, el.firstChild);
    },

    _roundBottomCorners: function (el, color, bgColor) {
        var corner = this._createCorner(bgColor);
        for (var i = (this.options.numSlices - 1); i >= 0; i--) {
            corner.appendChild(
                this._createCornerSlice(color, bgColor, i, "bottom")
            );
        }
        el.style.paddingBottom = 0;
        el.appendChild(corner);
    },

    _createCorner: function (bgColor) {
        var dom = MochiKit.DOM;
        return dom.DIV({style: {backgroundColor: bgColor.toString()}});
    },

    _createCornerSlice: function (color, bgColor, n, position) {
        var slice = MochiKit.DOM.SPAN();

        var inStyle = slice.style;
        inStyle.backgroundColor = color.toString();
        inStyle.display = "block";
        inStyle.height = "1px";
        inStyle.overflow = "hidden";
        inStyle.fontSize = "1px";

        var borderColor = this._borderColor(color, bgColor);
        if (this.options.border && n === 0) {
            inStyle.borderTopStyle = "solid";
            inStyle.borderTopWidth = "1px";
            inStyle.borderLeftWidth = "0px";
            inStyle.borderRightWidth = "0px";
            inStyle.borderBottomWidth = "0px";
            // assumes css compliant box model
            inStyle.height = "0px";
            inStyle.borderColor = borderColor.toString();
        } else if (borderColor) {
            inStyle.borderColor = borderColor.toString();
            inStyle.borderStyle = "solid";
            inStyle.borderWidth = "0px 1px";
        }

        if (!this.options.compact && (n == (this.options.numSlices - 1))) {
            inStyle.height = "2px";
        }

        this._setMargin(slice, n, position);
        this._setBorder(slice, n, position);

        return slice;
    },

    _setOptions: function (options) {
        this.options = {
            corners: "all",
            color: "fromElement",
            bgColor: "fromParent",
            blend: true,
            border: false,
            compact: false,
            __unstable__wrapElement: false
        };
        MochiKit.Base.update(this.options, options);

        this.options.numSlices = (this.options.compact ? 2 : 4);
    },

    _whichSideTop: function () {
        var corners = this.options.corners;
        if (this._hasString(corners, "all", "top")) {
            return "";
        }

        var has_tl = (corners.indexOf("tl") != -1);
        var has_tr = (corners.indexOf("tr") != -1);
        if (has_tl && has_tr) {
            return "";
        }
        if (has_tl) {
            return "left";
        }
        if (has_tr) {
            return "right";
        }
        return "";
    },

    _whichSideBottom: function () {
        var corners = this.options.corners;
        if (this._hasString(corners, "all", "bottom")) {
            return "";
        }

        var has_bl = (corners.indexOf('bl') != -1);
        var has_br = (corners.indexOf('br') != -1);
        if (has_bl && has_br) {
            return "";
        }
        if (has_bl) {
            return "left";
        }
        if (has_br) {
            return "right";
        }
        return "";
    },

    _borderColor: function (color, bgColor) {
        if (color == "transparent") {
            return bgColor;
        } else if (this.options.border) {
            return this.options.border;
        } else if (this.options.blend) {
            return bgColor.blendedColor(color);
        }
        return "";
    },


    _setMargin: function (el, n, corners) {
        var marginSize = this._marginSize(n) + "px";
        var whichSide = (
            corners == "top" ? this._whichSideTop() : this._whichSideBottom()
        );
        var style = el.style;

        if (whichSide == "left") {
            style.marginLeft = marginSize;
            style.marginRight = "0px";
        } else if (whichSide == "right") {
            style.marginRight = marginSize;
            style.marginLeft = "0px";
        } else {
            style.marginLeft = marginSize;
            style.marginRight = marginSize;
        }
    },

    _setBorder: function (el, n, corners) {
        var borderSize = this._borderSize(n) + "px";
        var whichSide = (
            corners == "top" ? this._whichSideTop() : this._whichSideBottom()
        );

        var style = el.style;
        if (whichSide == "left") {
            style.borderLeftWidth = borderSize;
            style.borderRightWidth = "0px";
        } else if (whichSide == "right") {
            style.borderRightWidth = borderSize;
            style.borderLeftWidth = "0px";
        } else {
            style.borderLeftWidth = borderSize;
            style.borderRightWidth = borderSize;
        }
    },

    _marginSize: function (n) {
        if (this.isTransparent) {
            return 0;
        }

        var o = this.options;
        if (o.compact && o.blend) {
            var smBlendedMarginSizes = [1, 0];
            return smBlendedMarginSizes[n];
        } else if (o.compact) {
            var compactMarginSizes = [2, 1];
            return compactMarginSizes[n];
        } else if (o.blend) {
            var blendedMarginSizes = [3, 2, 1, 0];
            return blendedMarginSizes[n];
        } else {
            var marginSizes = [5, 3, 2, 1];
            return marginSizes[n];
        }
    },

    _borderSize: function (n) {
        var o = this.options;
        var borderSizes;
        if (o.compact && (o.blend || this.isTransparent)) {
            return 1;
        } else if (o.compact) {
            borderSizes = [1, 0];
        } else if (o.blend) {
            borderSizes = [2, 1, 1, 1];
        } else if (o.border) {
            borderSizes = [0, 2, 0, 0];
        } else if (this.isTransparent) {
            borderSizes = [5, 3, 2, 1];
        } else {
            return 0;
        }
        return borderSizes[n];
    },

    _hasString: function (str) {
        for (var i = 1; i< arguments.length; i++) {
            if (str.indexOf(arguments[i]) != -1) {
                return true;
            }
        }
        return false;
    },

    _isTopRounded: function () {
        return this._hasString(this.options.corners,
            "all", "top", "tl", "tr"
        );
    },

    _isBottomRounded: function () {
        return this._hasString(this.options.corners,
            "all", "bottom", "bl", "br"
        );
    },

    _hasSingleTextChild: function (el) {
        return (el.childNodes.length == 1 && el.childNodes[0].nodeType == 3);
    }
};

/** @id MochiKit.Visual.roundElement */
MochiKit.Visual.roundElement = function (e, options) {
    new MochiKit.Visual._RoundCorners(e, options);
};

/** @id MochiKit.Visual.roundClass */
MochiKit.Visual.roundClass = function (tagName, className, options) {
    var elements = MochiKit.DOM.getElementsByTagAndClassName(
        tagName, className
    );
    for (var i = 0; i < elements.length; i++) {
        MochiKit.Visual.roundElement(elements[i], options);
    }
};

/** @id MochiKit.Visual.tagifyText */
MochiKit.Visual.tagifyText = function (element, /* optional */tagifyStyle) {
    /***

    Change a node text to character in tags.

    @param tagifyStyle: the style to apply to character nodes, default to
    'position: relative'.

    ***/
    tagifyStyle = tagifyStyle || 'position:relative';
    if (/MSIE/.test(navigator.userAgent)) {
        tagifyStyle += ';zoom:1';
    }
    element = MochiKit.DOM.getElement(element);
    var ma = MochiKit.Base.map;
    ma(function (child) {
        if (child.nodeType == 3) {
            ma(function (character) {
                element.insertBefore(
                    MochiKit.DOM.SPAN({style: tagifyStyle},
                        character == ' ' ? String.fromCharCode(160) : character), child);
            }, child.nodeValue.split(''));
            MochiKit.DOM.removeElement(child);
        }
    }, element.childNodes);
};

/** @id MochiKit.Visual.forceRerendering */
MochiKit.Visual.forceRerendering = function (element) {
    try {
        element = MochiKit.DOM.getElement(element);
        var n = document.createTextNode(' ');
        element.appendChild(n);
        element.removeChild(n);
    } catch(e) {
    }
};

/** @id MochiKit.Visual.multiple */
MochiKit.Visual.multiple = function (elements, effect, /* optional */options) {
    /***

    Launch the same effect subsequently on given elements.

    ***/
    options = MochiKit.Base.update({
        speed: 0.1, delay: 0.0
    }, options);
    var masterDelay = options.delay;
    var index = 0;
    MochiKit.Base.map(function (innerelement) {
        options.delay = index * options.speed + masterDelay;
        new effect(innerelement, options);
        index += 1;
    }, elements);
};

MochiKit.Visual.PAIRS = {
    'slide': ['slideDown', 'slideUp'],
    'blind': ['blindDown', 'blindUp'],
    'appear': ['appear', 'fade'],
    'size': ['grow', 'shrink']
};

/** @id MochiKit.Visual.toggle */
MochiKit.Visual.toggle = function (element, /* optional */effect, /* optional */options) {
    /***

    Toggle an item between two state depending of its visibility, making
    a effect between these states. Default  effect is 'appear', can be
    'slide' or 'blind'.

    ***/
    element = MochiKit.DOM.getElement(element);
    effect = (effect || 'appear').toLowerCase();
    options = MochiKit.Base.update({
        queue: {position: 'end', scope: (element.id || 'global'), limit: 1}
    }, options);
    var v = MochiKit.Visual;
    v[MochiKit.Style.getStyle(element, 'display') != 'none' ?
      v.PAIRS[effect][1] : v.PAIRS[effect][0]](element, options);
};

/***

Transitions: define functions calculating variations depending of a position.

***/

MochiKit.Visual.Transitions = {};

/** @id MochiKit.Visual.Transitions.linear */
MochiKit.Visual.Transitions.linear = function (pos) {
    return pos;
};

/** @id MochiKit.Visual.Transitions.sinoidal */
MochiKit.Visual.Transitions.sinoidal = function (pos) {
    return (-Math.cos(pos*Math.PI)/2) + 0.5;
};

/** @id MochiKit.Visual.Transitions.reverse */
MochiKit.Visual.Transitions.reverse = function (pos) {
    return 1 - pos;
};

/** @id MochiKit.Visual.Transitions.flicker */
MochiKit.Visual.Transitions.flicker = function (pos) {
    return ((-Math.cos(pos*Math.PI)/4) + 0.75) + Math.random()/4;
};

/** @id MochiKit.Visual.Transitions.wobble */
MochiKit.Visual.Transitions.wobble = function (pos) {
    return (-Math.cos(pos*Math.PI*(9*pos))/2) + 0.5;
};

/** @id MochiKit.Visual.Transitions.pulse */
MochiKit.Visual.Transitions.pulse = function (pos, pulses) {
    if (!pulses) {
        return (Math.floor(pos*10) % 2 === 0 ?
            (pos*10 - Math.floor(pos*10)) : 1 - (pos*10 - Math.floor(pos*10)));
    }
    return (Math.round((pos % (1/pulses)) * pulses) == 0 ?
            ((pos * pulses * 2) - Math.floor(pos * pulses * 2)) :
        1 - ((pos * pulses * 2) - Math.floor(pos * pulses * 2)));
};

/** @id MochiKit.Visual.Transitions.none */
MochiKit.Visual.Transitions.none = function (pos) {
    return 0;
};

/** @id MochiKit.Visual.Transitions.full */
MochiKit.Visual.Transitions.full = function (pos) {
    return 1;
};

/***

Core effects

***/

MochiKit.Visual.ScopedQueue = function () {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls();
    }
    this.__init__();
};

MochiKit.Base.update(MochiKit.Visual.ScopedQueue.prototype, {
    __init__: function () {
        this.effects = [];
        this.interval = null;
    },

    /** @id MochiKit.Visual.ScopedQueue.prototype.add */
    add: function (effect) {
        var timestamp = new Date().getTime();

        var position = (typeof(effect.options.queue) == 'string') ?
            effect.options.queue : effect.options.queue.position;

        var ma = MochiKit.Base.map;
        switch (position) {
            case 'front':
                // move unstarted effects after this effect
                ma(function (e) {
                    if (e.state == 'idle') {
                        e.startOn += effect.finishOn;
                        e.finishOn += effect.finishOn;
                    }
                }, this.effects);
                break;
            case 'end':
                var finish;
                // start effect after last queued effect has finished
                ma(function (e) {
                    var i = e.finishOn;
                    if (i >= (finish || i)) {
                        finish = i;
                    }
                }, this.effects);
                timestamp = finish || timestamp;
                break;
            case 'break':
                ma(function (e) {
                    e.finalize();
                }, this.effects);
                break;
        }

        effect.startOn += timestamp;
        effect.finishOn += timestamp;
        if (!effect.options.queue.limit ||
            this.effects.length < effect.options.queue.limit) {
            this.effects.push(effect);
        }

        if (!this.interval) {
            this.interval = this.startLoop(MochiKit.Base.bind(this.loop, this),
                                        40);
        }
    },

    /** @id MochiKit.Visual.ScopedQueue.prototype.startLoop */
    startLoop: function (func, interval) {
        return setInterval(func, interval);
    },

    /** @id MochiKit.Visual.ScopedQueue.prototype.remove */
    remove: function (effect) {
        this.effects = MochiKit.Base.filter(function (e) {
            return e != effect;
        }, this.effects);
        if (!this.effects.length) {
            this.stopLoop(this.interval);
            this.interval = null;
        }
    },

    /** @id MochiKit.Visual.ScopedQueue.prototype.stopLoop */
    stopLoop: function (interval) {
        clearInterval(interval);
    },

    /** @id MochiKit.Visual.ScopedQueue.prototype.loop */
    loop: function () {
        var timePos = new Date().getTime();
        MochiKit.Base.map(function (effect) {
            effect.loop(timePos);
        }, this.effects);
    }
});

MochiKit.Visual.Queues = {
    instances: {},

    get: function (queueName) {
        if (typeof(queueName) != 'string') {
            return queueName;
        }

        if (!this.instances[queueName]) {
            this.instances[queueName] = new MochiKit.Visual.ScopedQueue();
        }
        return this.instances[queueName];
    }
};

MochiKit.Visual.Queue = MochiKit.Visual.Queues.get('global');

MochiKit.Visual.DefaultOptions = {
    transition: MochiKit.Visual.Transitions.sinoidal,
    duration: 1.0,  // seconds
    fps: 25.0,  // max. 25fps due to MochiKit.Visual.Queue implementation
    sync: false,  // true for combining
    from: 0.0,
    to: 1.0,
    delay: 0.0,
    queue: 'parallel'
};

MochiKit.Visual.Base = function () {};

MochiKit.Visual.Base.prototype = {
    /***

    Basic class for all Effects. Define a looping mechanism called for each step
    of an effect. Don't instantiate it, only subclass it.

    ***/

    __class__ : MochiKit.Visual.Base,

    /** @id MochiKit.Visual.Base.prototype.start */
    start: function (options) {
        var v = MochiKit.Visual;
        this.options = MochiKit.Base.setdefault(options,
                                                v.DefaultOptions);
        this.currentFrame = 0;
        this.state = 'idle';
        this.startOn = this.options.delay*1000;
        this.finishOn = this.startOn + (this.options.duration*1000);
        this.event('beforeStart');
        if (!this.options.sync) {
            v.Queues.get(typeof(this.options.queue) == 'string' ?
                'global' : this.options.queue.scope).add(this);
        }
    },

    /** @id MochiKit.Visual.Base.prototype.loop */
    loop: function (timePos) {
        if (timePos >= this.startOn) {
            if (timePos >= this.finishOn) {
                return this.finalize();
            }
            var pos = (timePos - this.startOn) / (this.finishOn - this.startOn);
            var frame =
                Math.round(pos * this.options.fps * this.options.duration);
            if (frame > this.currentFrame) {
                this.render(pos);
                this.currentFrame = frame;
            }
        }
    },

    /** @id MochiKit.Visual.Base.prototype.render */
    render: function (pos) {
        if (this.state == 'idle') {
            this.state = 'running';
            this.event('beforeSetup');
            this.setup();
            this.event('afterSetup');
        }
        if (this.state == 'running') {
            if (this.options.transition) {
                pos = this.options.transition(pos);
            }
            pos *= (this.options.to - this.options.from);
            pos += this.options.from;
            this.event('beforeUpdate');
            this.update(pos);
            this.event('afterUpdate');
        }
    },

    /** @id MochiKit.Visual.Base.prototype.cancel */
    cancel: function () {
        if (!this.options.sync) {
            MochiKit.Visual.Queues.get(typeof(this.options.queue) == 'string' ?
                'global' : this.options.queue.scope).remove(this);
        }
        this.state = 'finished';
    },

    /** @id MochiKit.Visual.Base.prototype.finalize */
    finalize: function () {
        this.render(1.0);
        this.cancel();
        this.event('beforeFinish');
        this.finish();
        this.event('afterFinish');
    },

    setup: function () {
    },

    finish: function () {
    },

    update: function (position) {
    },

    /** @id MochiKit.Visual.Base.prototype.event */
    event: function (eventName) {
        if (this.options[eventName + 'Internal']) {
            this.options[eventName + 'Internal'](this);
        }
        if (this.options[eventName]) {
            this.options[eventName](this);
        }
    },

    /** @id MochiKit.Visual.Base.prototype.repr */
    repr: function () {
        return '[' + this.__class__.NAME + ', options:' +
               MochiKit.Base.repr(this.options) + ']';
    }
};

    /** @id MochiKit.Visual.Parallel */
MochiKit.Visual.Parallel = function (effects, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(effects, options);
    }

    this.__init__(effects, options);
};

MochiKit.Visual.Parallel.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Parallel.prototype, {
    /***

    Run multiple effects at the same time.

    ***/

    __class__ : MochiKit.Visual.Parallel,

    __init__: function (effects, options) {
        this.effects = effects || [];
        this.start(options);
    },

    /** @id MochiKit.Visual.Parallel.prototype.update */
    update: function (position) {
        MochiKit.Base.map(function (effect) {
            effect.render(position);
        }, this.effects);
    },

    /** @id MochiKit.Visual.Parallel.prototype.finish */
    finish: function () {
        MochiKit.Base.map(function (effect) {
            effect.finalize();
        }, this.effects);
    }
});

/** @id MochiKit.Visual.Opacity */
MochiKit.Visual.Opacity = function (element, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, options);
    }
    this.__init__(element, options);
};

MochiKit.Visual.Opacity.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Opacity.prototype, {
    /***

    Change the opacity of an element.

    @param options: 'from' and 'to' change the starting and ending opacities.
    Must be between 0.0 and 1.0. Default to current opacity and 1.0.

    ***/

    __class__ : MochiKit.Visual.Opacity,

    __init__: function (element, /* optional */options) {
        var b = MochiKit.Base;
        var s = MochiKit.Style;
        this.element = MochiKit.DOM.getElement(element);
        // make this work on IE on elements without 'layout'
        if (this.element.currentStyle &&
            (!this.element.currentStyle.hasLayout)) {
            s.setStyle(this.element, {zoom: 1});
        }
        options = b.update({
            from: s.getStyle(this.element, 'opacity') || 0.0,
            to: 1.0
        }, options);
        this.start(options);
    },

    /** @id MochiKit.Visual.Opacity.prototype.update */
    update: function (position) {
        MochiKit.Style.setStyle(this.element, {'opacity': position});
    }
});

/**  @id MochiKit.Visual.Move.prototype */
MochiKit.Visual.Move = function (element, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, options);
    }
    this.__init__(element, options);
};

MochiKit.Visual.Move.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Move.prototype, {
    /***

    Move an element between its current position to a defined position

    @param options: 'x' and 'y' for final positions, default to 0, 0.

    ***/

    __class__ : MochiKit.Visual.Move,

    __init__: function (element, /* optional */options) {
        this.element = MochiKit.DOM.getElement(element);
        options = MochiKit.Base.update({
            x: 0,
            y: 0,
            mode: 'relative'
        }, options);
        this.start(options);
    },

    /** @id MochiKit.Visual.Move.prototype.setup */
    setup: function () {
        // Bug in Opera: Opera returns the 'real' position of a static element
        // or relative element that does not have top/left explicitly set.
        // ==> Always set top and left for position relative elements in your
        // stylesheets (to 0 if you do not need them)
        MochiKit.DOM.makePositioned(this.element);

        var s = this.element.style;
        var originalVisibility = s.visibility;
        var originalDisplay = s.display;
        if (originalDisplay == 'none') {
            s.visibility = 'hidden';
            s.display = '';
        }

        this.originalLeft = parseFloat(MochiKit.Style.getStyle(this.element, 'left') || '0');
        this.originalTop = parseFloat(MochiKit.Style.getStyle(this.element, 'top') || '0');

        if (this.options.mode == 'absolute') {
            // absolute movement, so we need to calc deltaX and deltaY
            this.options.x -= this.originalLeft;
            this.options.y -= this.originalTop;
        }
        if (originalDisplay == 'none') {
            s.visibility = originalVisibility;
            s.display = originalDisplay;
        }
    },

    /** @id MochiKit.Visual.Move.prototype.update */
    update: function (position) {
        MochiKit.Style.setStyle(this.element, {
            left: Math.round(this.options.x * position + this.originalLeft) + 'px',
            top: Math.round(this.options.y * position + this.originalTop) + 'px'
        });
    }
});

/** @id MochiKit.Visual.Scale */
MochiKit.Visual.Scale = function (element, percent, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, percent, options);
    }
    this.__init__(element, percent, options);
};

MochiKit.Visual.Scale.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Scale.prototype, {
    /***

    Change the size of an element.

    @param percent: final_size = percent*original_size

    @param options: several options changing scale behaviour

    ***/

    __class__ : MochiKit.Visual.Scale,

    __init__: function (element, percent, /* optional */options) {
        this.element = MochiKit.DOM.getElement(element);
        options = MochiKit.Base.update({
            scaleX: true,
            scaleY: true,
            scaleContent: true,
            scaleFromCenter: false,
            scaleMode: 'box',  // 'box' or 'contents' or {} with provided values
            scaleFrom: 100.0,
            scaleTo: percent
        }, options);
        this.start(options);
    },

    /** @id MochiKit.Visual.Scale.prototype.setup */
    setup: function () {
        this.restoreAfterFinish = this.options.restoreAfterFinish || false;
        this.elementPositioning = MochiKit.Style.getStyle(this.element,
                                                        'position');

        var ma = MochiKit.Base.map;
        var b = MochiKit.Base.bind;
        this.originalStyle = {};
        ma(b(function (k) {
                this.originalStyle[k] = this.element.style[k];
            }, this), ['top', 'left', 'width', 'height', 'fontSize']);

        this.originalTop = this.element.offsetTop;
        this.originalLeft = this.element.offsetLeft;

        var fontSize = MochiKit.Style.getStyle(this.element,
                                             'font-size') || '100%';
        ma(b(function (fontSizeType) {
            if (fontSize.indexOf(fontSizeType) > 0) {
                this.fontSize = parseFloat(fontSize);
                this.fontSizeType = fontSizeType;
            }
        }, this), ['em', 'px', '%']);

        this.factor = (this.options.scaleTo - this.options.scaleFrom)/100;

        if (/^content/.test(this.options.scaleMode)) {
            this.dims = [this.element.scrollHeight, this.element.scrollWidth];
        } else if (this.options.scaleMode == 'box') {
            this.dims = [this.element.offsetHeight, this.element.offsetWidth];
        } else {
            this.dims = [this.options.scaleMode.originalHeight,
                         this.options.scaleMode.originalWidth];
        }
    },

    /** @id MochiKit.Visual.Scale.prototype.update */
    update: function (position) {
        var currentScale = (this.options.scaleFrom/100.0) +
                           (this.factor * position);
        if (this.options.scaleContent && this.fontSize) {
            MochiKit.Style.setStyle(this.element, {
                fontSize: this.fontSize * currentScale + this.fontSizeType
            });
        }
        this.setDimensions(this.dims[0] * currentScale,
                           this.dims[1] * currentScale);
    },

    /** @id MochiKit.Visual.Scale.prototype.finish */
    finish: function () {
        if (this.restoreAfterFinish) {
            MochiKit.Style.setStyle(this.element, this.originalStyle);
        }
    },

    /** @id MochiKit.Visual.Scale.prototype.setDimensions */
    setDimensions: function (height, width) {
        var d = {};
        var r = Math.round;
        if (/MSIE/.test(navigator.userAgent)) {
            r = Math.ceil;
        }
        if (this.options.scaleX) {
            d.width = r(width) + 'px';
        }
        if (this.options.scaleY) {
            d.height = r(height) + 'px';
        }
        if (this.options.scaleFromCenter) {
            var topd = (height - this.dims[0])/2;
            var leftd = (width - this.dims[1])/2;
            if (this.elementPositioning == 'absolute') {
                if (this.options.scaleY) {
                    d.top = this.originalTop - topd + 'px';
                }
                if (this.options.scaleX) {
                    d.left = this.originalLeft - leftd + 'px';
                }
            } else {
                if (this.options.scaleY) {
                    d.top = -topd + 'px';
                }
                if (this.options.scaleX) {
                    d.left = -leftd + 'px';
                }
            }
        }
        MochiKit.Style.setStyle(this.element, d);
    }
});

/** @id MochiKit.Visual.Highlight */
MochiKit.Visual.Highlight = function (element, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, options);
    }
    this.__init__(element, options);
};

MochiKit.Visual.Highlight.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Highlight.prototype, {
    /***

    Highlight an item of the page.

    @param options: 'startcolor' for choosing highlighting color, default
    to '#ffff99'.

    ***/

    __class__ : MochiKit.Visual.Highlight,

    __init__: function (element, /* optional */options) {
        this.element = MochiKit.DOM.getElement(element);
        options = MochiKit.Base.update({
            startcolor: '#ffff99'
        }, options);
        this.start(options);
    },

    /** @id MochiKit.Visual.Highlight.prototype.setup */
    setup: function () {
        var b = MochiKit.Base;
        var s = MochiKit.Style;
        // Prevent executing on elements not in the layout flow
        if (s.getStyle(this.element, 'display') == 'none') {
            this.cancel();
            return;
        }
        // Disable background image during the effect
        this.oldStyle = {
            backgroundImage: s.getStyle(this.element, 'background-image')
        };
        s.setStyle(this.element, {
            backgroundImage: 'none'
        });

        if (!this.options.endcolor) {
            this.options.endcolor =
                MochiKit.Color.Color.fromBackground(this.element).toHexString();
        }
        if (b.isUndefinedOrNull(this.options.restorecolor)) {
            this.options.restorecolor = s.getStyle(this.element,
                                                   'background-color');
        }
        // init color calculations
        this._base = b.map(b.bind(function (i) {
            return parseInt(
                this.options.startcolor.slice(i*2 + 1, i*2 + 3), 16);
        }, this), [0, 1, 2]);
        this._delta = b.map(b.bind(function (i) {
            return parseInt(this.options.endcolor.slice(i*2 + 1, i*2 + 3), 16)
                - this._base[i];
        }, this), [0, 1, 2]);
    },

    /** @id MochiKit.Visual.Highlight.prototype.update */
    update: function (position) {
        var m = '#';
        MochiKit.Base.map(MochiKit.Base.bind(function (i) {
            m += MochiKit.Color.toColorPart(Math.round(this._base[i] +
                                            this._delta[i]*position));
        }, this), [0, 1, 2]);
        MochiKit.Style.setStyle(this.element, {
            backgroundColor: m
        });
    },

    /** @id MochiKit.Visual.Highlight.prototype.finish */
    finish: function () {
        MochiKit.Style.setStyle(this.element,
            MochiKit.Base.update(this.oldStyle, {
                backgroundColor: this.options.restorecolor
        }));
    }
});

/** @id MochiKit.Visual.ScrollTo */
MochiKit.Visual.ScrollTo = function (element, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, options);
    }
    this.__init__(element, options);
};

MochiKit.Visual.ScrollTo.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.ScrollTo.prototype, {
    /***

    Scroll to an element in the page.

    ***/

    __class__ : MochiKit.Visual.ScrollTo,

    __init__: function (element, /* optional */options) {
        this.element = MochiKit.DOM.getElement(element);
        this.start(options);
    },

    /** @id MochiKit.Visual.ScrollTo.prototype.setup */
    setup: function () {
        var p = MochiKit.Position;
        p.prepare();
        var offsets = p.cumulativeOffset(this.element);
        if (this.options.offset) {
            offsets.y += this.options.offset;
        }
        var max;
        if (window.innerHeight) {
            max = window.innerHeight - window.height;
        } else if (document.documentElement &&
                   document.documentElement.clientHeight) {
            max = document.documentElement.clientHeight -
                  document.body.scrollHeight;
        } else if (document.body) {
            max = document.body.clientHeight - document.body.scrollHeight;
        }
        this.scrollStart = p.windowOffset.y;
        this.delta = (offsets.y > max ? max : offsets.y) - this.scrollStart;
    },

    /** @id MochiKit.Visual.ScrollTo.prototype.update */
    update: function (position) {
        var p = MochiKit.Position;
        p.prepare();
        window.scrollTo(p.windowOffset.x, this.scrollStart + (position * this.delta));
    }
});

MochiKit.Visual.CSS_LENGTH = /^(([\+\-]?[0-9\.]+)(em|ex|px|in|cm|mm|pt|pc|\%))|0$/;

MochiKit.Visual.Morph = function (element, options) {
    var cls = arguments.callee;
    if (!(this instanceof cls)) {
        return new cls(element, options);
    }
    this.__init__(element, options);
};

MochiKit.Visual.Morph.prototype = new MochiKit.Visual.Base();

MochiKit.Base.update(MochiKit.Visual.Morph.prototype, {
    /***

    Morph effect: make a transformation from current style to the given style,
    automatically making a transition between the two.

    ***/

    __class__ : MochiKit.Visual.Morph,

    __init__: function (element, /* optional */options) {
        this.element = MochiKit.DOM.getElement(element);
        this.start(options);
    },

    /** @id MochiKit.Visual.Morph.prototype.setup */
    setup: function () {
        var b = MochiKit.Base;
        var style = this.options.style;
        this.styleStart = {};
        this.styleEnd = {};
        this.units = {};
        var value, unit;
        for (var s in style) {
            value = style[s];
            s = b.camelize(s);
            if (MochiKit.Visual.CSS_LENGTH.test(value)) {
                var components = value.match(/^([\+\-]?[0-9\.]+)(.*)$/);
                value = parseFloat(components[1]);
                unit = (components.length == 3) ? components[2] : null;
                this.styleEnd[s] = value;
                this.units[s] = unit;
                value = MochiKit.Style.getStyle(this.element, s);
                components = value.match(/^([\+\-]?[0-9\.]+)(.*)$/);
                value = parseFloat(components[1]);
                this.styleStart[s] = value;
            } else {
                var c = MochiKit.Color.Color;
                value = c.fromString(value);
                if (value) {
                    this.units[s] = "color";
                    this.styleEnd[s] = value.toHexString();
                    value = MochiKit.Style.getStyle(this.element, s);
                    this.styleStart[s] = c.fromString(value).toHexString();

                    this.styleStart[s] = b.map(b.bind(function (i) {
                        return parseInt(
                            this.styleStart[s].slice(i*2 + 1, i*2 + 3), 16);
                    }, this), [0, 1, 2]);
                    this.styleEnd[s] = b.map(b.bind(function (i) {
                        return parseInt(
                            this.styleEnd[s].slice(i*2 + 1, i*2 + 3), 16);
                    }, this), [0, 1, 2]);
                }
            }
        }
    },

    /** @id MochiKit.Visual.Morph.prototype.update */
    update: function (position) {
        var value;
        for (var s in this.styleStart) {
            if (this.units[s] == "color") {
                var m = '#';
                var start = this.styleStart[s];
                var end = this.styleEnd[s];
                MochiKit.Base.map(MochiKit.Base.bind(function (i) {
                    m += MochiKit.Color.toColorPart(Math.round(start[i] +
                                                    (end[i] - start[i])*position));
                }, this), [0, 1, 2]);
                this.element.style[s] = m;
            } else {
                value = this.styleStart[s] + Math.round((this.styleEnd[s] - this.styleStart[s]) * position * 1000) / 1000 + this.units[s];
                this.element.style[s] = value;
            }
        }
    }
});

/***

Combination effects.

***/

/** @id MochiKit.Visual.fade */
MochiKit.Visual.fade = function (element, /* optional */ options) {
    /***

    Fade a given element: change its opacity and hide it in the end.

    @param options: 'to' and 'from' to change opacity.

    ***/
    var s = MochiKit.Style;
    var oldOpacity = s.getStyle(element, 'opacity');
    options = MochiKit.Base.update({
        from: s.getStyle(element, 'opacity') || 1.0,
        to: 0.0,
        afterFinishInternal: function (effect) {
            if (effect.options.to !== 0) {
                return;
            }
            s.hideElement(effect.element);
            s.setStyle(effect.element, {'opacity': oldOpacity});
        }
    }, options);
    return new MochiKit.Visual.Opacity(element, options);
};

/** @id MochiKit.Visual.appear */
MochiKit.Visual.appear = function (element, /* optional */ options) {
    /***

    Make an element appear.

    @param options: 'to' and 'from' to change opacity.

    ***/
    var s = MochiKit.Style;
    var v = MochiKit.Visual;
    options = MochiKit.Base.update({
        from: (s.getStyle(element, 'display') == 'none' ? 0.0 :
               s.getStyle(element, 'opacity') || 0.0),
        to: 1.0,
        // force Safari to render floated elements properly
        afterFinishInternal: function (effect) {
            v.forceRerendering(effect.element);
        },
        beforeSetupInternal: function (effect) {
            s.setStyle(effect.element, {'opacity': effect.options.from});
            s.showElement(effect.element);
        }
    }, options);
    return new v.Opacity(element, options);
};

/** @id MochiKit.Visual.puff */
MochiKit.Visual.puff = function (element, /* optional */ options) {
    /***

    'Puff' an element: grow it to double size, fading it and make it hidden.

    ***/
    var s = MochiKit.Style;
    var v = MochiKit.Visual;
    element = MochiKit.DOM.getElement(element);
    var oldStyle = {
        position: s.getStyle(element, 'position'),
        top: element.style.top,
        left: element.style.left,
        width: element.style.width,
        height: element.style.height,
        opacity: s.getStyle(element, 'opacity')
    };
    options = MochiKit.Base.update({
        beforeSetupInternal: function (effect) {
            MochiKit.Position.absolutize(effect.effects[0].element);
        },
        afterFinishInternal: function (effect) {
            s.hideElement(effect.effects[0].element);
            s.setStyle(effect.effects[0].element, oldStyle);
        },
        scaleContent: true,
        scaleFromCenter: true
    }, options);
    return new v.Parallel(
        [new v.Scale(element, 200,
            {sync: true, scaleFromCenter: options.scaleFromCenter,
             scaleContent: options.scaleContent, restoreAfterFinish: true}),
         new v.Opacity(element, {sync: true, to: 0.0 })],
        options);
};

/** @id MochiKit.Visual.blindUp */
MochiKit.Visual.blindUp = function (element, /* optional */ options) {
    /***

    Blind an element up: change its vertical size to 0.

    ***/
    var d = MochiKit.DOM;
    element = d.getElement(element);
    var elemClip = d.makeClipping(element);
    options = MochiKit.Base.update({
        scaleContent: false,
        scaleX: false,
        restoreAfterFinish: true,
        afterFinishInternal: function (effect) {
            MochiKit.Style.hideElement(effect.element);
            d.undoClipping(effect.element, elemClip);
        }
    }, options);

    return new MochiKit.Visual.Scale(element, 0, options);
};

/** @id MochiKit.Visual.blindDown */
MochiKit.Visual.blindDown = function (element, /* optional */ options) {
    /***

    Blind an element down: restore its vertical size.

    ***/
    var d = MochiKit.DOM;
    var s = MochiKit.Style;
    element = d.getElement(element);
    var elementDimensions = s.getElementDimensions(element);
    var elemClip;
    options = MochiKit.Base.update({
        scaleContent: false,
        scaleX: false,
        scaleFrom: 0,
        scaleMode: {originalHeight: elementDimensions.h,
                    originalWidth: elementDimensions.w},
        restoreAfterFinish: true,
        afterSetupInternal: function (effect) {
            elemClip = d.makeClipping(effect.element);
            s.setStyle(effect.element, {height: '0px'});
            s.showElement(effect.element);
        },
        afterFinishInternal: function (effect) {
            d.undoClipping(effect.element, elemClip);
        }
    }, options);
    return new MochiKit.Visual.Scale(element, 100, options);
};

/** @id MochiKit.Visual.switchOff */
MochiKit.Visual.switchOff = function (element, /* optional */ options) {
    /***

    Apply a switch-off-like effect.

    ***/
    var d = MochiKit.DOM;
    element = d.getElement(element);
    var oldOpacity = MochiKit.Style.getStyle(element, 'opacity');
    var elemClip;
    options = MochiKit.Base.update({
        duration: 0.3,
        scaleFromCenter: true,
        scaleX: false,
        scaleContent: false,
        restoreAfterFinish: true,
        beforeSetupInternal: function (effect) {
            d.makePositioned(effect.element);
            elemClip = d.makeClipping(effect.element);
        },
        afterFinishInternal: function (effect) {
            MochiKit.Style.hideElement(effect.element);
            d.undoClipping(effect.element, elemClip);
            d.undoPositioned(effect.element);
            MochiKit.Style.setStyle(effect.element, {'opacity': oldOpacity});
        }
    }, options);
    var v = MochiKit.Visual;
    return new v.appear(element, {
        duration: 0.4,
        from: 0,
        transition: v.Transitions.flicker,
        afterFinishInternal: function (effect) {
            new v.Scale(effect.element, 1, options);
        }
    });
};

/** @id MochiKit.Visual.dropOut */
MochiKit.Visual.dropOut = function (element, /* optional */ options) {
    /***

    Make an element fall and disappear.

    ***/
    var d = MochiKit.DOM;
    var s = MochiKit.Style;
    element = d.getElement(element);
    var oldStyle = {
        top: s.getStyle(element, 'top'),
        left: s.getStyle(element, 'left'),
        opacity: s.getStyle(element, 'opacity')
    };

    options = MochiKit.Base.update({
        duration: 0.5,
        distance: 100,
        beforeSetupInternal: function (effect) {
            d.makePositioned(effect.effects[0].element);
        },
        afterFinishInternal: function (effect) {
            s.hideElement(effect.effects[0].element);
            d.undoPositioned(effect.effects[0].element);
            s.setStyle(effect.effects[0].element, oldStyle);
        }
    }, options);
    var v = MochiKit.Visual;
    return new v.Parallel(
        [new v.Move(element, {x: 0, y: options.distance, sync: true}),
         new v.Opacity(element, {sync: true, to: 0.0})],
        options);
};

/** @id MochiKit.Visual.shake */
MochiKit.Visual.shake = function (element, /* optional */ options) {
    /***

    Move an element from left to right several times.

    ***/
    var d = MochiKit.DOM;
    var v = MochiKit.Visual;
    var s = MochiKit.Style;
    element = d.getElement(element);
    options = MochiKit.Base.update({
        x: -20,
        y: 0,
        duration: 0.05,
        afterFinishInternal: function (effect) {
            d.undoPositioned(effect.element);
            s.setStyle(effect.element, oldStyle);
        }
    }, options);
    var oldStyle = {
        top: s.getStyle(element, 'top'),
        left: s.getStyle(element, 'left') };
        return new v.Move(element,
          {x: 20, y: 0, duration: 0.05, afterFinishInternal: function (effect) {
        new v.Move(effect.element,
          {x: -40, y: 0, duration: 0.1, afterFinishInternal: function (effect) {
        new v.Move(effect.element,
           {x: 40, y: 0, duration: 0.1, afterFinishInternal: function (effect) {
        new v.Move(effect.element,
          {x: -40, y: 0, duration: 0.1, afterFinishInternal: function (effect) {
        new v.Move(effect.element,
           {x: 40, y: 0, duration: 0.1, afterFinishInternal: function (effect) {
        new v.Move(effect.element, options
        ) }}) }}) }}) }}) }});
};

/** @id MochiKit.Visual.slideDown */
MochiKit.Visual.slideDown = function (element, /* optional */ options) {
    /***

    Slide an element down.
    It needs to have the content of the element wrapped in a container
    element with fixed height.

    ***/
    var d = MochiKit.DOM;
    var b = MochiKit.Base;
    var s = MochiKit.Style;
    element = d.getElement(element);
    if (!element.firstChild) {
        throw "MochiKit.Visual.slideDown must be used on a element with a child";
    }
    d.removeEmptyTextNodes(element);
    var oldInnerBottom = s.getStyle(element.firstChild, 'bottom') || 0;
    var elementDimensions = s.getElementDimensions(element);
    var elemClip;
    options = b.update({
        scaleContent: false,
        scaleX: false,
        scaleFrom: 0,
        scaleMode: {originalHeight: elementDimensions.h,
                    originalWidth: elementDimensions.w},
        restoreAfterFinish: true,
        afterSetupInternal: function (effect) {
            d.makePositioned(effect.element);
            d.makePositioned(effect.element.firstChild);
            if (/Opera/.test(navigator.userAgent)) {
                s.setStyle(effect.element, {top: ''});
            }
            elemClip = d.makeClipping(effect.element);
            s.setStyle(effect.element, {height: '0px'});
            s.showElement(effect.element);
        },
        afterUpdateInternal: function (effect) {
            s.setStyle(effect.element.firstChild,
               {bottom: (effect.dims[0] - effect.element.clientHeight) + 'px'});
        },
        afterFinishInternal: function (effect) {
            d.undoClipping(effect.element, elemClip);
            // IE will crash if child is undoPositioned first
            if (/MSIE/.test(navigator.userAgent)) {
                d.undoPositioned(effect.element);
                d.undoPositioned(effect.element.firstChild);
            } else {
                d.undoPositioned(effect.element.firstChild);
                d.undoPositioned(effect.element);
            }
            s.setStyle(effect.element.firstChild,
                                  {bottom: oldInnerBottom});
        }
    }, options);

    return new MochiKit.Visual.Scale(element, 100, options);
};

/** @id MochiKit.Visual.slideUp */
MochiKit.Visual.slideUp = function (element, /* optional */ options) {
    /***

    Slide an element up.
    It needs to have the content of the element wrapped in a container
    element with fixed height.

    ***/
    var d = MochiKit.DOM;
    var b = MochiKit.Base;
    var s = MochiKit.Style;
    element = d.getElement(element);
    if (!element.firstChild) {
        throw "MochiKit.Visual.slideUp must be used on a element with a child";
    }
    d.removeEmptyTextNodes(element);
    var oldInnerBottom = s.getStyle(element.firstChild, 'bottom');
    var elemClip;
    options = b.update({
        scaleContent: false,
        scaleX: false,
        scaleMode: 'box',
        scaleFrom: 100,
        restoreAfterFinish: true,
        beforeStartInternal: function (effect) {
            d.makePositioned(effect.element);
            d.makePositioned(effect.element.firstChild);
            if (/Opera/.test(navigator.userAgent)) {
                s.setStyle(effect.element, {top: ''});
            }
            elemClip = d.makeClipping(effect.element);
            s.showElement(effect.element);
        },
        afterUpdateInternal: function (effect) {
            s.setStyle(effect.element.firstChild,
            {bottom: (effect.dims[0] - effect.element.clientHeight) + 'px'});
        },
        afterFinishInternal: function (effect) {
            s.hideElement(effect.element);
            d.undoClipping(effect.element, elemClip);
            d.undoPositioned(effect.element.firstChild);
            d.undoPositioned(effect.element);
            s.setStyle(effect.element.firstChild, {bottom: oldInnerBottom});
        }
    }, options);
    return new MochiKit.Visual.Scale(element, 0, options);
};

// Bug in opera makes the TD containing this element expand for a instance
// after finish
/** @id MochiKit.Visual.squish */
MochiKit.Visual.squish = function (element, /* optional */ options) {
    /***

    Reduce an element and make it disappear.

    ***/
    var d = MochiKit.DOM;
    var b = MochiKit.Base;
    var elemClip;
    options = b.update({
        restoreAfterFinish: true,
        beforeSetupInternal: function (effect) {
            elemClip = d.makeClipping(effect.element);
        },
        afterFinishInternal: function (effect) {
            MochiKit.Style.hideElement(effect.element);
            d.undoClipping(effect.element, elemClip);
        }
    }, options);

    return new MochiKit.Visual.Scale(element, /Opera/.test(navigator.userAgent) ? 1 : 0, options);
};

/** @id MochiKit.Visual.grow */
MochiKit.Visual.grow = function (element, /* optional */ options) {
    /***

    Grow an element to its original size. Make it zero-sized before
    if necessary.

    ***/
    var d = MochiKit.DOM;
    var v = MochiKit.Visual;
    var s = MochiKit.Style;
    element = d.getElement(element);
    options = MochiKit.Base.update({
        direction: 'center',
        moveTransition: v.Transitions.sinoidal,
        scaleTransition: v.Transitions.sinoidal,
        opacityTransition: v.Transitions.full,
        scaleContent: true,
        scaleFromCenter: false
    }, options);
    var oldStyle = {
        top: element.style.top,
        left: element.style.left,
        height: element.style.height,
        width: element.style.width,
        opacity: s.getStyle(element, 'opacity')
    };

    var dims = s.getElementDimensions(element);
    var initialMoveX, initialMoveY;
    var moveX, moveY;

    switch (options.direction) {
        case 'top-left':
            initialMoveX = initialMoveY = moveX = moveY = 0;
            break;
        case 'top-right':
            initialMoveX = dims.w;
            initialMoveY = moveY = 0;
            moveX = -dims.w;
            break;
        case 'bottom-left':
            initialMoveX = moveX = 0;
            initialMoveY = dims.h;
            moveY = -dims.h;
            break;
        case 'bottom-right':
            initialMoveX = dims.w;
            initialMoveY = dims.h;
            moveX = -dims.w;
            moveY = -dims.h;
            break;
        case 'center':
            initialMoveX = dims.w / 2;
            initialMoveY = dims.h / 2;
            moveX = -dims.w / 2;
            moveY = -dims.h / 2;
            break;
    }

    var optionsParallel = MochiKit.Base.update({
        beforeSetupInternal: function (effect) {
            s.setStyle(effect.effects[0].element, {height: '0px'});
            s.showElement(effect.effects[0].element);
        },
        afterFinishInternal: function (effect) {
            d.undoClipping(effect.effects[0].element);
            d.undoPositioned(effect.effects[0].element);
            s.setStyle(effect.effects[0].element, oldStyle);
        }
    }, options);

    return new v.Move(element, {
        x: initialMoveX,
        y: initialMoveY,
        duration: 0.01,
        beforeSetupInternal: function (effect) {
            s.hideElement(effect.element);
            d.makeClipping(effect.element);
            d.makePositioned(effect.element);
        },
        afterFinishInternal: function (effect) {
            new v.Parallel(
                [new v.Opacity(effect.element, {
                    sync: true, to: 1.0, from: 0.0,
                    transition: options.opacityTransition
                 }),
                 new v.Move(effect.element, {
                     x: moveX, y: moveY, sync: true,
                     transition: options.moveTransition
                 }),
                 new v.Scale(effect.element, 100, {
                        scaleMode: {originalHeight: dims.h,
                                    originalWidth: dims.w},
                        sync: true,
                        scaleFrom: /Opera/.test(navigator.userAgent) ? 1 : 0,
                        transition: options.scaleTransition,
                        scaleContent: options.scaleContent,
                        scaleFromCenter: options.scaleFromCenter,
                        restoreAfterFinish: true
                })
                ], optionsParallel
            );
        }
    });
};

/** @id MochiKit.Visual.shrink */
MochiKit.Visual.shrink = function (element, /* optional */ options) {
    /***

    Shrink an element and make it disappear.

    ***/
    var d = MochiKit.DOM;
    var v = MochiKit.Visual;
    var s = MochiKit.Style;
    element = d.getElement(element);
    options = MochiKit.Base.update({
        direction: 'center',
        moveTransition: v.Transitions.sinoidal,
        scaleTransition: v.Transitions.sinoidal,
        opacityTransition: v.Transitions.none,
        scaleContent: true,
        scaleFromCenter: false
    }, options);
    var oldStyle = {
        top: element.style.top,
        left: element.style.left,
        height: element.style.height,
        width: element.style.width,
        opacity: s.getStyle(element, 'opacity')
    };

    var dims = s.getElementDimensions(element);
    var moveX, moveY;

    switch (options.direction) {
        case 'top-left':
            moveX = moveY = 0;
            break;
        case 'top-right':
            moveX = dims.w;
            moveY = 0;
            break;
        case 'bottom-left':
            moveX = 0;
            moveY = dims.h;
            break;
        case 'bottom-right':
            moveX = dims.w;
            moveY = dims.h;
            break;
        case 'center':
            moveX = dims.w / 2;
            moveY = dims.h / 2;
            break;
    }
    var elemClip;

    var optionsParallel = MochiKit.Base.update({
        beforeStartInternal: function (effect) {
            elemClip = d.makePositioned(effect.effects[0].element);
            d.makeClipping(effect.effects[0].element);
        },
        afterFinishInternal: function (effect) {
            s.hideElement(effect.effects[0].element);
            d.undoClipping(effect.effects[0].element, elemClip);
            d.undoPositioned(effect.effects[0].element);
            s.setStyle(effect.effects[0].element, oldStyle);
        }
    }, options);

    return new v.Parallel(
        [new v.Opacity(element, {
            sync: true, to: 0.0, from: 1.0,
            transition: options.opacityTransition
         }),
         new v.Scale(element, /Opera/.test(navigator.userAgent) ? 1 : 0, {
             sync: true, transition: options.scaleTransition,
             scaleContent: options.scaleContent,
             scaleFromCenter: options.scaleFromCenter,
             restoreAfterFinish: true
         }),
         new v.Move(element, {
             x: moveX, y: moveY, sync: true, transition: options.moveTransition
         })
        ], optionsParallel
    );
};

/** @id MochiKit.Visual.pulsate */
MochiKit.Visual.pulsate = function (element, /* optional */ options) {
    /***

    Pulse an element between appear/fade.

    ***/
    var d = MochiKit.DOM;
    var v = MochiKit.Visual;
    var b = MochiKit.Base;
    var oldOpacity = MochiKit.Style.getStyle(element, 'opacity');
    options = b.update({
        duration: 3.0,
        from: 0,
        afterFinishInternal: function (effect) {
            MochiKit.Style.setStyle(effect.element, {'opacity': oldOpacity});
        }
    }, options);
    var transition = options.transition || v.Transitions.sinoidal;
    var reverser = b.bind(function (pos) {
        return transition(1 - v.Transitions.pulse(pos, options.pulses));
    }, transition);
    b.bind(reverser, transition);
    return new v.Opacity(element, b.update({
        transition: reverser}, options));
};

/** @id MochiKit.Visual.fold */
MochiKit.Visual.fold = function (element, /* optional */ options) {
    /***

    Fold an element, first vertically, then horizontally.

    ***/
    var d = MochiKit.DOM;
    var v = MochiKit.Visual;
    var s = MochiKit.Style;
    element = d.getElement(element);
    var oldStyle = {
        top: element.style.top,
        left: element.style.left,
        width: element.style.width,
        height: element.style.height
    };
    var elemClip = d.makeClipping(element);
    options = MochiKit.Base.update({
        scaleContent: false,
        scaleX: false,
        afterFinishInternal: function (effect) {
            new v.Scale(element, 1, {
                scaleContent: false,
                scaleY: false,
                afterFinishInternal: function (effect) {
                    s.hideElement(effect.element);
                    d.undoClipping(effect.element, elemClip);
                    s.setStyle(effect.element, oldStyle);
                }
            });
        }
    }, options);
    return new v.Scale(element, 5, options);
};


// Compatibility with MochiKit 1.0
MochiKit.Visual.Color = MochiKit.Color.Color;
MochiKit.Visual.getElementsComputedStyle = MochiKit.DOM.computedStyle;

/* end of Rico adaptation */

MochiKit.Visual.__new__ = function () {
    var m = MochiKit.Base;

    m.nameFunctions(this);

    this.EXPORT_TAGS = {
        ":common": this.EXPORT,
        ":all": m.concat(this.EXPORT, this.EXPORT_OK)
    };

};

MochiKit.Visual.EXPORT = [
    "roundElement",
    "roundClass",
    "tagifyText",
    "multiple",
    "toggle",
    "Parallel",
    "Opacity",
    "Move",
    "Scale",
    "Highlight",
    "ScrollTo",
    "Morph",
    "fade",
    "appear",
    "puff",
    "blindUp",
    "blindDown",
    "switchOff",
    "dropOut",
    "shake",
    "slideDown",
    "slideUp",
    "squish",
    "grow",
    "shrink",
    "pulsate",
    "fold"
];

MochiKit.Visual.EXPORT_OK = [
    "Base",
    "PAIRS"
];

MochiKit.Visual.__new__();

MochiKit.Base._exportSymbols(this, MochiKit.Visual);
