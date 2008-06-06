/***

MochiKit.Iter 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Iter');
    dojo.require('MochiKit.Base');
}

if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Base", []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Iter depends on MochiKit.Base!";
}

if (typeof(MochiKit.Iter) == 'undefined') {
    MochiKit.Iter = {};
}

MochiKit.Iter.NAME = "MochiKit.Iter";
MochiKit.Iter.VERSION = "1.4";
MochiKit.Base.update(MochiKit.Iter, {
    __repr__: function () {
        return "[" + this.NAME + " " + this.VERSION + "]";
    },
    toString: function () {
        return this.__repr__();
    },

    /** @id MochiKit.Iter.registerIteratorFactory  */
    registerIteratorFactory: function (name, check, iterfactory, /* optional */ override) {
        MochiKit.Iter.iteratorRegistry.register(name, check, iterfactory, override);
    },

    /** @id MochiKit.Iter.iter */
    iter: function (iterable, /* optional */ sentinel) {
        var self = MochiKit.Iter;
        if (arguments.length == 2) {
            return self.takewhile(
                function (a) { return a != sentinel; },
                iterable
            );
        }
        if (typeof(iterable.next) == 'function') {
            return iterable;
        } else if (typeof(iterable.iter) == 'function') {
            return iterable.iter();
        /*
        }  else if (typeof(iterable.__iterator__) == 'function') {
            //
            // XXX: We can't support JavaScript 1.7 __iterator__ directly
            //      because of Object.prototype.__iterator__
            //
            return iterable.__iterator__();
        */
        }

        try {
            return self.iteratorRegistry.match(iterable);
        } catch (e) {
            var m = MochiKit.Base;
            if (e == m.NotFound) {
                e = new TypeError(typeof(iterable) + ": " + m.repr(iterable) + " is not iterable");
            }
            throw e;
        }
    },

    /** @id MochiKit.Iter.count */
    count: function (n) {
        if (!n) {
            n = 0;
        }
        var m = MochiKit.Base;
        return {
            repr: function () { return "count(" + n + ")"; },
            toString: m.forwardCall("repr"),
            next: m.counter(n)
        };
    },

    /** @id MochiKit.Iter.cycle */
    cycle: function (p) {
        var self = MochiKit.Iter;
        var m = MochiKit.Base;
        var lst = [];
        var iterator = self.iter(p);
        return {
            repr: function () { return "cycle(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                try {
                    var rval = iterator.next();
                    lst.push(rval);
                    return rval;
                } catch (e) {
                    if (e != self.StopIteration) {
                        throw e;
                    }
                    if (lst.length === 0) {
                        this.next = function () {
                            throw self.StopIteration;
                        };
                    } else {
                        var i = -1;
                        this.next = function () {
                            i = (i + 1) % lst.length;
                            return lst[i];
                        };
                    }
                    return this.next();
                }
            }
        };
    },

    /** @id MochiKit.Iter.repeat */
    repeat: function (elem, /* optional */n) {
        var m = MochiKit.Base;
        if (typeof(n) == 'undefined') {
            return {
                repr: function () {
                    return "repeat(" + m.repr(elem) + ")";
                },
                toString: m.forwardCall("repr"),
                next: function () {
                    return elem;
                }
            };
        }
        return {
            repr: function () {
                return "repeat(" + m.repr(elem) + ", " + n + ")";
            },
            toString: m.forwardCall("repr"),
            next: function () {
                if (n <= 0) {
                    throw MochiKit.Iter.StopIteration;
                }
                n -= 1;
                return elem;
            }
        };
    },

    /** @id MochiKit.Iter.next */
    next: function (iterator) {
        return iterator.next();
    },

    /** @id MochiKit.Iter.izip */
    izip: function (p, q/*, ...*/) {
        var m = MochiKit.Base;
        var self = MochiKit.Iter;
        var next = self.next;
        var iterables = m.map(self.iter, arguments);
        return {
            repr: function () { return "izip(...)"; },
            toString: m.forwardCall("repr"),
            next: function () { return m.map(next, iterables); }
        };
    },

    /** @id MochiKit.Iter.ifilter */
    ifilter: function (pred, seq) {
        var m = MochiKit.Base;
        seq = MochiKit.Iter.iter(seq);
        if (pred === null) {
            pred = m.operator.truth;
        }
        return {
            repr: function () { return "ifilter(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                while (true) {
                    var rval = seq.next();
                    if (pred(rval)) {
                        return rval;
                    }
                }
                // mozilla warnings aren't too bright
                return undefined;
            }
        };
    },

    /** @id MochiKit.Iter.ifilterfalse */
    ifilterfalse: function (pred, seq) {
        var m = MochiKit.Base;
        seq = MochiKit.Iter.iter(seq);
        if (pred === null) {
            pred = m.operator.truth;
        }
        return {
            repr: function () { return "ifilterfalse(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                while (true) {
                    var rval = seq.next();
                    if (!pred(rval)) {
                        return rval;
                    }
                }
                // mozilla warnings aren't too bright
                return undefined;
            }
        };
    },

    /** @id MochiKit.Iter.islice */
    islice: function (seq/*, [start,] stop[, step] */) {
        var self = MochiKit.Iter;
        var m = MochiKit.Base;
        seq = self.iter(seq);
        var start = 0;
        var stop = 0;
        var step = 1;
        var i = -1;
        if (arguments.length == 2) {
            stop = arguments[1];
        } else if (arguments.length == 3) {
            start = arguments[1];
            stop = arguments[2];
        } else {
            start = arguments[1];
            stop = arguments[2];
            step = arguments[3];
        }
        return {
            repr: function () {
                return "islice(" + ["...", start, stop, step].join(", ") + ")";
            },
            toString: m.forwardCall("repr"),
            next: function () {
                var rval;
                while (i < start) {
                    rval = seq.next();
                    i++;
                }
                if (start >= stop) {
                    throw self.StopIteration;
                }
                start += step;
                return rval;
            }
        };
    },

    /** @id MochiKit.Iter.imap */
    imap: function (fun, p, q/*, ...*/) {
        var m = MochiKit.Base;
        var self = MochiKit.Iter;
        var iterables = m.map(self.iter, m.extend(null, arguments, 1));
        var map = m.map;
        var next = self.next;
        return {
            repr: function () { return "imap(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                return fun.apply(this, map(next, iterables));
            }
        };
    },

    /** @id MochiKit.Iter.applymap */
    applymap: function (fun, seq, self) {
        seq = MochiKit.Iter.iter(seq);
        var m = MochiKit.Base;
        return {
            repr: function () { return "applymap(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                return fun.apply(self, seq.next());
            }
        };
    },

    /** @id MochiKit.Iter.chain */
    chain: function (p, q/*, ...*/) {
        // dumb fast path
        var self = MochiKit.Iter;
        var m = MochiKit.Base;
        if (arguments.length == 1) {
            return self.iter(arguments[0]);
        }
        var argiter = m.map(self.iter, arguments);
        return {
            repr: function () { return "chain(...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                while (argiter.length > 1) {
                    try {
                        return argiter[0].next();
                    } catch (e) {
                        if (e != self.StopIteration) {
                            throw e;
                        }
                        argiter.shift();
                    }
                }
                if (argiter.length == 1) {
                    // optimize last element
                    var arg = argiter.shift();
                    this.next = m.bind("next", arg);
                    return this.next();
                }
                throw self.StopIteration;
            }
        };
    },

    /** @id MochiKit.Iter.takewhile */
    takewhile: function (pred, seq) {
        var self = MochiKit.Iter;
        seq = self.iter(seq);
        return {
            repr: function () { return "takewhile(...)"; },
            toString: MochiKit.Base.forwardCall("repr"),
            next: function () {
                var rval = seq.next();
                if (!pred(rval)) {
                    this.next = function () {
                        throw self.StopIteration;
                    };
                    this.next();
                }
                return rval;
            }
        };
    },

    /** @id MochiKit.Iter.dropwhile */
    dropwhile: function (pred, seq) {
        seq = MochiKit.Iter.iter(seq);
        var m = MochiKit.Base;
        var bind = m.bind;
        return {
            "repr": function () { return "dropwhile(...)"; },
            "toString": m.forwardCall("repr"),
            "next": function () {
                while (true) {
                    var rval = seq.next();
                    if (!pred(rval)) {
                        break;
                    }
                }
                this.next = bind("next", seq);
                return rval;
            }
        };
    },

    _tee: function (ident, sync, iterable) {
        sync.pos[ident] = -1;
        var m = MochiKit.Base;
        var listMin = m.listMin;
        return {
            repr: function () { return "tee(" + ident + ", ...)"; },
            toString: m.forwardCall("repr"),
            next: function () {
                var rval;
                var i = sync.pos[ident];

                if (i == sync.max) {
                    rval = iterable.next();
                    sync.deque.push(rval);
                    sync.max += 1;
                    sync.pos[ident] += 1;
                } else {
                    rval = sync.deque[i - sync.min];
                    sync.pos[ident] += 1;
                    if (i == sync.min && listMin(sync.pos) != sync.min) {
                        sync.min += 1;
                        sync.deque.shift();
                    }
                }
                return rval;
            }
        };
    },

    /** @id MochiKit.Iter.tee */
    tee: function (iterable, n/* = 2 */) {
        var rval = [];
        var sync = {
            "pos": [],
            "deque": [],
            "max": -1,
            "min": -1
        };
        if (arguments.length == 1 || typeof(n) == "undefined" || n === null) {
            n = 2;
        }
        var self = MochiKit.Iter;
        iterable = self.iter(iterable);
        var _tee = self._tee;
        for (var i = 0; i < n; i++) {
            rval.push(_tee(i, sync, iterable));
        }
        return rval;
    },

    /** @id MochiKit.Iter.list */
    list: function (iterable) {
        // Fast-path for Array and Array-like
        var rval;
        if (iterable instanceof Array) {
            return iterable.slice();
        } 
        // this is necessary to avoid a Safari crash
        if (typeof(iterable) == "function" &&
                !(iterable instanceof Function) &&
                typeof(iterable.length) == 'number') {
            rval = [];
            for (var i = 0; i < iterable.length; i++) {
                rval.push(iterable[i]);
            }
            return rval;
        }

        var self = MochiKit.Iter;
        iterable = self.iter(iterable);
        var rval = [];
        try {
            while (true) {
                rval.push(iterable.next());
            }
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
            return rval;
        }
        // mozilla warnings aren't too bright
        return undefined;
    },


    /** @id MochiKit.Iter.reduce */
    reduce: function (fn, iterable, /* optional */initial) {
        var i = 0;
        var x = initial;
        var self = MochiKit.Iter;
        iterable = self.iter(iterable);
        if (arguments.length < 3) {
            try {
                x = iterable.next();
            } catch (e) {
                if (e == self.StopIteration) {
                    e = new TypeError("reduce() of empty sequence with no initial value");
                }
                throw e;
            }
            i++;
        }
        try {
            while (true) {
                x = fn(x, iterable.next());
            }
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
        }
        return x;
    },

    /** @id MochiKit.Iter.range */
    range: function (/* [start,] stop[, step] */) {
        var start = 0;
        var stop = 0;
        var step = 1;
        if (arguments.length == 1) {
            stop = arguments[0];
        } else if (arguments.length == 2) {
            start = arguments[0];
            stop = arguments[1];
        } else if (arguments.length == 3) {
            start = arguments[0];
            stop = arguments[1];
            step = arguments[2];
        } else {
            throw new TypeError("range() takes 1, 2, or 3 arguments!");
        }
        if (step === 0) {
            throw new TypeError("range() step must not be 0");
        }
        return {
            next: function () {
                if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {
                    throw MochiKit.Iter.StopIteration;
                }
                var rval = start;
                start += step;
                return rval;
            },
            repr: function () {
                return "range(" + [start, stop, step].join(", ") + ")";
            },
            toString: MochiKit.Base.forwardCall("repr")
        };
    },

    /** @id MochiKit.Iter.sum */
    sum: function (iterable, start/* = 0 */) {
        if (typeof(start) == "undefined" || start === null) {
            start = 0;
        }
        var x = start;
        var self = MochiKit.Iter;
        iterable = self.iter(iterable);
        try {
            while (true) {
                x += iterable.next();
            }
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
        }
        return x;
    },

    /** @id MochiKit.Iter.exhaust */
    exhaust: function (iterable) {
        var self = MochiKit.Iter;
        iterable = self.iter(iterable);
        try {
            while (true) {
                iterable.next();
            }
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
        }
    },

    /** @id MochiKit.Iter.forEach */
    forEach: function (iterable, func, /* optional */self) {
        var m = MochiKit.Base;
        if (arguments.length > 2) {
            func = m.bind(func, self);
        }
        // fast path for array
        if (m.isArrayLike(iterable)) {
            try {
                for (var i = 0; i < iterable.length; i++) {
                    func(iterable[i]);
                }
            } catch (e) {
                if (e != MochiKit.Iter.StopIteration) {
                    throw e;
                }
            }
        } else {
            self = MochiKit.Iter;
            self.exhaust(self.imap(func, iterable));
        }
    },

    /** @id MochiKit.Iter.every */
    every: function (iterable, func) {
        var self = MochiKit.Iter;
        try {
            self.ifilterfalse(func, iterable).next();
            return false;
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
            return true;
        }
    },

    /** @id MochiKit.Iter.sorted */
    sorted: function (iterable, /* optional */cmp) {
        var rval = MochiKit.Iter.list(iterable);
        if (arguments.length == 1) {
            cmp = MochiKit.Base.compare;
        }
        rval.sort(cmp);
        return rval;
    },

    /** @id MochiKit.Iter.reversed */
    reversed: function (iterable) {
        var rval = MochiKit.Iter.list(iterable);
        rval.reverse();
        return rval;
    },

    /** @id MochiKit.Iter.some */
    some: function (iterable, func) {
        var self = MochiKit.Iter;
        try {
            self.ifilter(func, iterable).next();
            return true;
        } catch (e) {
            if (e != self.StopIteration) {
                throw e;
            }
            return false;
        }
    },

    /** @id MochiKit.Iter.iextend */
    iextend: function (lst, iterable) {
        if (MochiKit.Base.isArrayLike(iterable)) {
            // fast-path for array-like
            for (var i = 0; i < iterable.length; i++) {
                lst.push(iterable[i]);
            }
        } else {
            var self = MochiKit.Iter;
            iterable = self.iter(iterable);
            try {
                while (true) {
                    lst.push(iterable.next());
                }
            } catch (e) {
                if (e != self.StopIteration) {
                    throw e;
                }
            }
        }
        return lst;
    },

    /** @id MochiKit.Iter.groupby */
    groupby: function(iterable, /* optional */ keyfunc) {
        var m = MochiKit.Base;
        var self = MochiKit.Iter;
        if (arguments.length < 2) {
            keyfunc = m.operator.identity;
        }
        iterable = self.iter(iterable);

        // shared
        var pk = undefined;
        var k = undefined;
        var v;

        function fetch() {
            v = iterable.next();
            k = keyfunc(v);
        };

        function eat() {
            var ret = v;
            v = undefined;
            return ret;
        };

        var first = true;
        var compare = m.compare;
        return {
            repr: function () { return "groupby(...)"; },
            next: function() {
                // iterator-next

                // iterate until meet next group
                while (compare(k, pk) === 0) {
                    fetch();
                    if (first) {
                        first = false;
                        break;
                    }
                }
                pk = k;
                return [k, {
                    next: function() {
                        // subiterator-next
                        if (v == undefined) { // Is there something to eat?
                            fetch();
                        }
                        if (compare(k, pk) !== 0) {
                            throw self.StopIteration;
                        }
                        return eat();
                    }
                }];
            }
        };
    },

    /** @id MochiKit.Iter.groupby_as_array */
    groupby_as_array: function (iterable, /* optional */ keyfunc) {
        var m = MochiKit.Base;
        var self = MochiKit.Iter;
        if (arguments.length < 2) {
            keyfunc = m.operator.identity;
        }

        iterable = self.iter(iterable);
        var result = [];
        var first = true;
        var prev_key;
        var compare = m.compare;
        while (true) {
            try {
                var value = iterable.next();
                var key = keyfunc(value);
            } catch (e) {
                if (e == self.StopIteration) {
                    break;
                }
                throw e;
            }
            if (first || compare(key, prev_key) !== 0) {
                var values = [];
                result.push([key, values]);
            }
            values.push(value);
            first = false;
            prev_key = key;
        }
        return result;
    },

    /** @id MochiKit.Iter.arrayLikeIter */
    arrayLikeIter: function (iterable) {
        var i = 0;
        return {
            repr: function () { return "arrayLikeIter(...)"; },
            toString: MochiKit.Base.forwardCall("repr"),
            next: function () {
                if (i >= iterable.length) {
                    throw MochiKit.Iter.StopIteration;
                }
                return iterable[i++];
            }
        };
    },

    /** @id MochiKit.Iter.hasIterateNext */
    hasIterateNext: function (iterable) {
        return (iterable && typeof(iterable.iterateNext) == "function");
    },

    /** @id MochiKit.Iter.iterateNextIter */
    iterateNextIter: function (iterable) {
        return {
            repr: function () { return "iterateNextIter(...)"; },
            toString: MochiKit.Base.forwardCall("repr"),
            next: function () {
                var rval = iterable.iterateNext();
                if (rval === null || rval === undefined) {
                    throw MochiKit.Iter.StopIteration;
                }
                return rval;
            }
        };
    }
});


MochiKit.Iter.EXPORT_OK = [
    "iteratorRegistry",
    "arrayLikeIter",
    "hasIterateNext",
    "iterateNextIter"
];

MochiKit.Iter.EXPORT = [
    "StopIteration",
    "registerIteratorFactory",
    "iter",
    "count",
    "cycle",
    "repeat",
    "next",
    "izip",
    "ifilter",
    "ifilterfalse",
    "islice",
    "imap",
    "applymap",
    "chain",
    "takewhile",
    "dropwhile",
    "tee",
    "list",
    "reduce",
    "range",
    "sum",
    "exhaust",
    "forEach",
    "every",
    "sorted",
    "reversed",
    "some",
    "iextend",
    "groupby",
    "groupby_as_array"
];

MochiKit.Iter.__new__ = function () {
    var m = MochiKit.Base;
    // Re-use StopIteration if exists (e.g. SpiderMonkey)
    if (typeof(StopIteration) != "undefined") {
        this.StopIteration = StopIteration;
    } else {
        /** @id MochiKit.Iter.StopIteration */
        this.StopIteration = new m.NamedError("StopIteration");
    }
    this.iteratorRegistry = new m.AdapterRegistry();
    // Register the iterator factory for arrays
    this.registerIteratorFactory(
        "arrayLike",
        m.isArrayLike,
        this.arrayLikeIter
    );

    this.registerIteratorFactory(
        "iterateNext",
        this.hasIterateNext,
        this.iterateNextIter
    );

    this.EXPORT_TAGS = {
        ":common": this.EXPORT,
        ":all": m.concat(this.EXPORT, this.EXPORT_OK)
    };

    m.nameFunctions(this);

};

MochiKit.Iter.__new__();

//
// XXX: Internet Explorer blows
//
if (MochiKit.__export__) {
    reduce = MochiKit.Iter.reduce;
}

MochiKit.Base._exportSymbols(this, MochiKit.Iter);
