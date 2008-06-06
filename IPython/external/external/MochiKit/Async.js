/***

MochiKit.Async 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide("MochiKit.Async");
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
    throw "MochiKit.Async depends on MochiKit.Base!";
}

if (typeof(MochiKit.Async) == 'undefined') {
    MochiKit.Async = {};
}

MochiKit.Async.NAME = "MochiKit.Async";
MochiKit.Async.VERSION = "1.4";
MochiKit.Async.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};
MochiKit.Async.toString = function () {
    return this.__repr__();
};

/** @id MochiKit.Async.Deferred */
MochiKit.Async.Deferred = function (/* optional */ canceller) {
    this.chain = [];
    this.id = this._nextId();
    this.fired = -1;
    this.paused = 0;
    this.results = [null, null];
    this.canceller = canceller;
    this.silentlyCancelled = false;
    this.chained = false;
};

MochiKit.Async.Deferred.prototype = {
    /** @id MochiKit.Async.Deferred.prototype.repr */
    repr: function () {
        var state;
        if (this.fired == -1) {
            state = 'unfired';
        } else if (this.fired === 0) {
            state = 'success';
        } else {
            state = 'error';
        }
        return 'Deferred(' + this.id + ', ' + state + ')';
    },

    toString: MochiKit.Base.forwardCall("repr"),

    _nextId: MochiKit.Base.counter(),

    /** @id MochiKit.Async.Deferred.prototype.cancel */
    cancel: function () {
        var self = MochiKit.Async;
        if (this.fired == -1) {
            if (this.canceller) {
                this.canceller(this);
            } else {
                this.silentlyCancelled = true;
            }
            if (this.fired == -1) {
                this.errback(new self.CancelledError(this));
            }
        } else if ((this.fired === 0) && (this.results[0] instanceof self.Deferred)) {
            this.results[0].cancel();
        }
    },

    _resback: function (res) {
        /***

        The primitive that means either callback or errback

        ***/
        this.fired = ((res instanceof Error) ? 1 : 0);
        this.results[this.fired] = res;
        this._fire();
    },

    _check: function () {
        if (this.fired != -1) {
            if (!this.silentlyCancelled) {
                throw new MochiKit.Async.AlreadyCalledError(this);
            }
            this.silentlyCancelled = false;
            return;
        }
    },

    /** @id MochiKit.Async.Deferred.prototype.callback */
    callback: function (res) {
        this._check();
        if (res instanceof MochiKit.Async.Deferred) {
            throw new Error("Deferred instances can only be chained if they are the result of a callback");
        }
        this._resback(res);
    },

    /** @id MochiKit.Async.Deferred.prototype.errback */
    errback: function (res) {
        this._check();
        var self = MochiKit.Async;
        if (res instanceof self.Deferred) {
            throw new Error("Deferred instances can only be chained if they are the result of a callback");
        }
        if (!(res instanceof Error)) {
            res = new self.GenericError(res);
        }
        this._resback(res);
    },

    /** @id MochiKit.Async.Deferred.prototype.addBoth */
    addBoth: function (fn) {
        if (arguments.length > 1) {
            fn = MochiKit.Base.partial.apply(null, arguments);
        }
        return this.addCallbacks(fn, fn);
    },

    /** @id MochiKit.Async.Deferred.prototype.addCallback */
    addCallback: function (fn) {
        if (arguments.length > 1) {
            fn = MochiKit.Base.partial.apply(null, arguments);
        }
        return this.addCallbacks(fn, null);
    },

    /** @id MochiKit.Async.Deferred.prototype.addErrback */
    addErrback: function (fn) {
        if (arguments.length > 1) {
            fn = MochiKit.Base.partial.apply(null, arguments);
        }
        return this.addCallbacks(null, fn);
    },

    /** @id MochiKit.Async.Deferred.prototype.addCallbacks */
    addCallbacks: function (cb, eb) {
        if (this.chained) {
            throw new Error("Chained Deferreds can not be re-used");
        }
        this.chain.push([cb, eb]);
        if (this.fired >= 0) {
            this._fire();
        }
        return this;
    },

    _fire: function () {
        /***

        Used internally to exhaust the callback sequence when a result
        is available.

        ***/
        var chain = this.chain;
        var fired = this.fired;
        var res = this.results[fired];
        var self = this;
        var cb = null;
        while (chain.length > 0 && this.paused === 0) {
            // Array
            var pair = chain.shift();
            var f = pair[fired];
            if (f === null) {
                continue;
            }
            try {
                res = f(res);
                fired = ((res instanceof Error) ? 1 : 0);
                if (res instanceof MochiKit.Async.Deferred) {
                    cb = function (res) {
                        self._resback(res);
                        self.paused--;
                        if ((self.paused === 0) && (self.fired >= 0)) {
                            self._fire();
                        }
                    };
                    this.paused++;
                }
            } catch (err) {
                fired = 1;
                if (!(err instanceof Error)) {
                    err = new MochiKit.Async.GenericError(err);
                }
                res = err;
            }
        }
        this.fired = fired;
        this.results[fired] = res;
        if (cb && this.paused) {
            // this is for "tail recursion" in case the dependent deferred
            // is already fired
            res.addBoth(cb);
            res.chained = true;
        }
    }
};

MochiKit.Base.update(MochiKit.Async, {
    /** @id MochiKit.Async.evalJSONRequest */
    evalJSONRequest: function (req) {
        return MochiKit.Base.evalJSON(req.responseText);
    },

    /** @id MochiKit.Async.succeed */
    succeed: function (/* optional */result) {
        var d = new MochiKit.Async.Deferred();
        d.callback.apply(d, arguments);
        return d;
    },

    /** @id MochiKit.Async.fail */
    fail: function (/* optional */result) {
        var d = new MochiKit.Async.Deferred();
        d.errback.apply(d, arguments);
        return d;
    },

    /** @id MochiKit.Async.getXMLHttpRequest */
    getXMLHttpRequest: function () {
        var self = arguments.callee;
        if (!self.XMLHttpRequest) {
            var tryThese = [
                function () { return new XMLHttpRequest(); },
                function () { return new ActiveXObject('Msxml2.XMLHTTP'); },
                function () { return new ActiveXObject('Microsoft.XMLHTTP'); },
                function () { return new ActiveXObject('Msxml2.XMLHTTP.4.0'); },
                function () {
                    throw new MochiKit.Async.BrowserComplianceError("Browser does not support XMLHttpRequest");
                }
            ];
            for (var i = 0; i < tryThese.length; i++) {
                var func = tryThese[i];
                try {
                    self.XMLHttpRequest = func;
                    return func();
                } catch (e) {
                    // pass
                }
            }
        }
        return self.XMLHttpRequest();
    },

    _xhr_onreadystatechange: function (d) {
        // MochiKit.Logging.logDebug('this.readyState', this.readyState);
        var m = MochiKit.Base;
        if (this.readyState == 4) {
            // IE SUCKS
            try {
                this.onreadystatechange = null;
            } catch (e) {
                try {
                    this.onreadystatechange = m.noop;
                } catch (e) {
                }
            }
            var status = null;
            try {
                status = this.status;
                if (!status && m.isNotEmpty(this.responseText)) {
                    // 0 or undefined seems to mean cached or local
                    status = 304;
                }
            } catch (e) {
                // pass
                // MochiKit.Logging.logDebug('error getting status?', repr(items(e)));
            }
            // 200 is OK, 201 is CREATED, 204 is NO CONTENT
            // 304 is NOT MODIFIED, 1223 is apparently a bug in IE
            if (status == 200 || status == 201 || status == 204 ||
                    status == 304 || status == 1223) {
                d.callback(this);
            } else {
                var err = new MochiKit.Async.XMLHttpRequestError(this, "Request failed");
                if (err.number) {
                    // XXX: This seems to happen on page change
                    d.errback(err);
                } else {
                    // XXX: this seems to happen when the server is unreachable
                    d.errback(err);
                }
            }
        }
    },

    _xhr_canceller: function (req) {
        // IE SUCKS
        try {
            req.onreadystatechange = null;
        } catch (e) {
            try {
                req.onreadystatechange = MochiKit.Base.noop;
            } catch (e) {
            }
        }
        req.abort();
    },


    /** @id MochiKit.Async.sendXMLHttpRequest */
    sendXMLHttpRequest: function (req, /* optional */ sendContent) {
        if (typeof(sendContent) == "undefined" || sendContent === null) {
            sendContent = "";
        }

        var m = MochiKit.Base;
        var self = MochiKit.Async;
        var d = new self.Deferred(m.partial(self._xhr_canceller, req));

        try {
            req.onreadystatechange = m.bind(self._xhr_onreadystatechange,
                req, d);
            req.send(sendContent);
        } catch (e) {
            try {
                req.onreadystatechange = null;
            } catch (ignore) {
                // pass
            }
            d.errback(e);
        }

        return d;

    },

    /** @id MochiKit.Async.doXHR */
    doXHR: function (url, opts) {
        /*
            Work around a Firefox bug by dealing with XHR during
            the next event loop iteration. Maybe it's this one:
            https://bugzilla.mozilla.org/show_bug.cgi?id=249843
        */
        var self = MochiKit.Async;
        return self.callLater(0, self._doXHR, url, opts);
    },

    _doXHR: function (url, opts) {
        var m = MochiKit.Base;
        opts = m.update({
            method: 'GET',
            sendContent: ''
            /*
            queryString: undefined,
            username: undefined,
            password: undefined,
            headers: undefined,
            mimeType: undefined
            */
        }, opts);
        var self = MochiKit.Async;
        var req = self.getXMLHttpRequest();
        if (opts.queryString) {
            var qs = m.queryString(opts.queryString);
            if (qs) {
                url += "?" + qs;
            }
        }
        // Safari will send undefined:undefined, so we have to check.
        // We can't use apply, since the function is native.
        if ('username' in opts) {
            req.open(opts.method, url, true, opts.username, opts.password);
        } else {
            req.open(opts.method, url, true);
        }
        if (req.overrideMimeType && opts.mimeType) {
            req.overrideMimeType(opts.mimeType);
        }
        req.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        if (opts.headers) {
            var headers = opts.headers;
            if (!m.isArrayLike(headers)) {
                headers = m.items(headers);
            }
            for (var i = 0; i < headers.length; i++) {
                var header = headers[i];
                var name = header[0];
                var value = header[1];
                req.setRequestHeader(name, value);
            }
        }
        return self.sendXMLHttpRequest(req, opts.sendContent);
    },

    _buildURL: function (url/*, ...*/) {
        if (arguments.length > 1) {
            var m = MochiKit.Base;
            var qs = m.queryString.apply(null, m.extend(null, arguments, 1));
            if (qs) {
                return url + "?" + qs;
            }
        }
        return url;
    },

    /** @id MochiKit.Async.doSimpleXMLHttpRequest */
    doSimpleXMLHttpRequest: function (url/*, ...*/) {
        var self = MochiKit.Async;
        url = self._buildURL.apply(self, arguments);
        return self.doXHR(url);
    },

    /** @id MochiKit.Async.loadJSONDoc */
    loadJSONDoc: function (url/*, ...*/) {
        var self = MochiKit.Async;
        url = self._buildURL.apply(self, arguments);
        var d = self.doXHR(url, {
            'mimeType': 'text/plain',
            'headers': [['Accept', 'application/json']]
        });
        d = d.addCallback(self.evalJSONRequest);
        return d;
    },

    /** @id MochiKit.Async.wait */
    wait: function (seconds, /* optional */value) {
        var d = new MochiKit.Async.Deferred();
        var m = MochiKit.Base;
        if (typeof(value) != 'undefined') {
            d.addCallback(function () { return value; });
        }
        var timeout = setTimeout(
            m.bind("callback", d),
            Math.floor(seconds * 1000));
        d.canceller = function () {
            try {
                clearTimeout(timeout);
            } catch (e) {
                // pass
            }
        };
        return d;
    },

    /** @id MochiKit.Async.callLater */
    callLater: function (seconds, func) {
        var m = MochiKit.Base;
        var pfunc = m.partial.apply(m, m.extend(null, arguments, 1));
        return MochiKit.Async.wait(seconds).addCallback(
            function (res) { return pfunc(); }
        );
    }
});


/** @id MochiKit.Async.DeferredLock */
MochiKit.Async.DeferredLock = function () {
    this.waiting = [];
    this.locked = false;
    this.id = this._nextId();
};

MochiKit.Async.DeferredLock.prototype = {
    __class__: MochiKit.Async.DeferredLock,
    /** @id MochiKit.Async.DeferredLock.prototype.acquire */
    acquire: function () {
        var d = new MochiKit.Async.Deferred();
        if (this.locked) {
            this.waiting.push(d);
        } else {
            this.locked = true;
            d.callback(this);
        }
        return d;
    },
    /** @id MochiKit.Async.DeferredLock.prototype.release */
    release: function () {
        if (!this.locked) {
            throw TypeError("Tried to release an unlocked DeferredLock");
        }
        this.locked = false;
        if (this.waiting.length > 0) {
            this.locked = true;
            this.waiting.shift().callback(this);
        }
    },
    _nextId: MochiKit.Base.counter(),
    repr: function () {
        var state;
        if (this.locked) {
            state = 'locked, ' + this.waiting.length + ' waiting';
        } else {
            state = 'unlocked';
        }
        return 'DeferredLock(' + this.id + ', ' + state + ')';
    },
    toString: MochiKit.Base.forwardCall("repr")

};

/** @id MochiKit.Async.DeferredList */
MochiKit.Async.DeferredList = function (list, /* optional */fireOnOneCallback, fireOnOneErrback, consumeErrors, canceller) {

    // call parent constructor
    MochiKit.Async.Deferred.apply(this, [canceller]);

    this.list = list;
    var resultList = [];
    this.resultList = resultList;

    this.finishedCount = 0;
    this.fireOnOneCallback = fireOnOneCallback;
    this.fireOnOneErrback = fireOnOneErrback;
    this.consumeErrors = consumeErrors;

    var cb = MochiKit.Base.bind(this._cbDeferred, this);
    for (var i = 0; i < list.length; i++) {
        var d = list[i];
        resultList.push(undefined);
        d.addCallback(cb, i, true);
        d.addErrback(cb, i, false);
    }

    if (list.length === 0 && !fireOnOneCallback) {
        this.callback(this.resultList);
    }

};

MochiKit.Async.DeferredList.prototype = new MochiKit.Async.Deferred();

MochiKit.Async.DeferredList.prototype._cbDeferred = function (index, succeeded, result) {
    this.resultList[index] = [succeeded, result];
    this.finishedCount += 1;
    if (this.fired == -1) {
        if (succeeded && this.fireOnOneCallback) {
            this.callback([index, result]);
        } else if (!succeeded && this.fireOnOneErrback) {
            this.errback(result);
        } else if (this.finishedCount == this.list.length) {
            this.callback(this.resultList);
        }
    }
    if (!succeeded && this.consumeErrors) {
        result = null;
    }
    return result;
};

/** @id MochiKit.Async.gatherResults */
MochiKit.Async.gatherResults = function (deferredList) {
    var d = new MochiKit.Async.DeferredList(deferredList, false, true, false);
    d.addCallback(function (results) {
        var ret = [];
        for (var i = 0; i < results.length; i++) {
            ret.push(results[i][1]);
        }
        return ret;
    });
    return d;
};

/** @id MochiKit.Async.maybeDeferred */
MochiKit.Async.maybeDeferred = function (func) {
    var self = MochiKit.Async;
    var result;
    try {
        var r = func.apply(null, MochiKit.Base.extend([], arguments, 1));
        if (r instanceof self.Deferred) {
            result = r;
        } else if (r instanceof Error) {
            result = self.fail(r);
        } else {
            result = self.succeed(r);
        }
    } catch (e) {
        result = self.fail(e);
    }
    return result;
};


MochiKit.Async.EXPORT = [
    "AlreadyCalledError",
    "CancelledError",
    "BrowserComplianceError",
    "GenericError",
    "XMLHttpRequestError",
    "Deferred",
    "succeed",
    "fail",
    "getXMLHttpRequest",
    "doSimpleXMLHttpRequest",
    "loadJSONDoc",
    "wait",
    "callLater",
    "sendXMLHttpRequest",
    "DeferredLock",
    "DeferredList",
    "gatherResults",
    "maybeDeferred",
    "doXHR"
];

MochiKit.Async.EXPORT_OK = [
    "evalJSONRequest"
];

MochiKit.Async.__new__ = function () {
    var m = MochiKit.Base;
    var ne = m.partial(m._newNamedError, this);

    ne("AlreadyCalledError",
        /** @id MochiKit.Async.AlreadyCalledError */
        function (deferred) {
            /***

            Raised by the Deferred if callback or errback happens
            after it was already fired.

            ***/
            this.deferred = deferred;
        }
    );

    ne("CancelledError",
        /** @id MochiKit.Async.CancelledError */
        function (deferred) {
            /***

            Raised by the Deferred cancellation mechanism.

            ***/
            this.deferred = deferred;
        }
    );

    ne("BrowserComplianceError",
        /** @id MochiKit.Async.BrowserComplianceError */
        function (msg) {
            /***

            Raised when the JavaScript runtime is not capable of performing
            the given function.  Technically, this should really never be
            raised because a non-conforming JavaScript runtime probably
            isn't going to support exceptions in the first place.

            ***/
            this.message = msg;
        }
    );

    ne("GenericError",
        /** @id MochiKit.Async.GenericError */
        function (msg) {
            this.message = msg;
        }
    );

    ne("XMLHttpRequestError",
        /** @id MochiKit.Async.XMLHttpRequestError */
        function (req, msg) {
            /***

            Raised when an XMLHttpRequest does not complete for any reason.

            ***/
            this.req = req;
            this.message = msg;
            try {
                // Strange but true that this can raise in some cases.
                this.number = req.status;
            } catch (e) {
                // pass
            }
        }
    );


    this.EXPORT_TAGS = {
        ":common": this.EXPORT,
        ":all": m.concat(this.EXPORT, this.EXPORT_OK)
    };

    m.nameFunctions(this);

};

MochiKit.Async.__new__();

MochiKit.Base._exportSymbols(this, MochiKit.Async);
