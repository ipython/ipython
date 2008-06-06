/***

MochiKit.Format 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Format');
}

if (typeof(MochiKit) == 'undefined') {
    MochiKit = {};
}

if (typeof(MochiKit.Format) == 'undefined') {
    MochiKit.Format = {};
}

MochiKit.Format.NAME = "MochiKit.Format";
MochiKit.Format.VERSION = "1.4";
MochiKit.Format.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};
MochiKit.Format.toString = function () {
    return this.__repr__();
};

MochiKit.Format._numberFormatter = function (placeholder, header, footer, locale, isPercent, precision, leadingZeros, separatorAt, trailingZeros) {
    return function (num) {
        num = parseFloat(num);
        if (typeof(num) == "undefined" || num === null || isNaN(num)) {
            return placeholder;
        }
        var curheader = header;
        var curfooter = footer;
        if (num < 0) {
            num = -num;
        } else {
            curheader = curheader.replace(/-/, "");
        }
        var me = arguments.callee;
        var fmt = MochiKit.Format.formatLocale(locale);
        if (isPercent) {
            num = num * 100.0;
            curfooter = fmt.percent + curfooter;
        }
        num = MochiKit.Format.roundToFixed(num, precision);
        var parts = num.split(/\./);
        var whole = parts[0];
        var frac = (parts.length == 1) ? "" : parts[1];
        var res = "";
        while (whole.length < leadingZeros) {
            whole = "0" + whole;
        }
        if (separatorAt) {
            while (whole.length > separatorAt) {
                var i = whole.length - separatorAt;
                //res = res + fmt.separator + whole.substring(i, whole.length);
                res = fmt.separator + whole.substring(i, whole.length) + res;
                whole = whole.substring(0, i);
            }
        }
        res = whole + res;
        if (precision > 0) {
            while (frac.length < trailingZeros) {
                frac = frac + "0";
            }
            res = res + fmt.decimal + frac;
        }
        return curheader + res + curfooter;
    };
};

/** @id MochiKit.Format.numberFormatter */
MochiKit.Format.numberFormatter = function (pattern, placeholder/* = "" */, locale/* = "default" */) {
    // http://java.sun.com/docs/books/tutorial/i18n/format/numberpattern.html
    // | 0 | leading or trailing zeros
    // | # | just the number
    // | , | separator
    // | . | decimal separator
    // | % | Multiply by 100 and format as percent
    if (typeof(placeholder) == "undefined") {
        placeholder = "";
    }
    var match = pattern.match(/((?:[0#]+,)?[0#]+)(?:\.([0#]+))?(%)?/);
    if (!match) {
        throw TypeError("Invalid pattern");
    }
    var header = pattern.substr(0, match.index);
    var footer = pattern.substr(match.index + match[0].length);
    if (header.search(/-/) == -1) {
        header = header + "-";
    }
    var whole = match[1];
    var frac = (typeof(match[2]) == "string" && match[2] != "") ? match[2] : "";
    var isPercent = (typeof(match[3]) == "string" && match[3] != "");
    var tmp = whole.split(/,/);
    var separatorAt;
    if (typeof(locale) == "undefined") {
        locale = "default";
    }
    if (tmp.length == 1) {
        separatorAt = null;
    } else {
        separatorAt = tmp[1].length;
    }
    var leadingZeros = whole.length - whole.replace(/0/g, "").length;
    var trailingZeros = frac.length - frac.replace(/0/g, "").length;
    var precision = frac.length;
    var rval = MochiKit.Format._numberFormatter(
        placeholder, header, footer, locale, isPercent, precision,
        leadingZeros, separatorAt, trailingZeros
    );
    var m = MochiKit.Base;
    if (m) {
        var fn = arguments.callee;
        var args = m.concat(arguments);
        rval.repr = function () {
            return [
                self.NAME,
                "(",
                map(m.repr, args).join(", "),
                ")"
            ].join("");
        };
    }
    return rval;
};

/** @id MochiKit.Format.formatLocale */
MochiKit.Format.formatLocale = function (locale) {
    if (typeof(locale) == "undefined" || locale === null) {
        locale = "default";
    }
    if (typeof(locale) == "string") {
        var rval = MochiKit.Format.LOCALE[locale];
        if (typeof(rval) == "string") {
            rval = arguments.callee(rval);
            MochiKit.Format.LOCALE[locale] = rval;
        }
        return rval;
    } else {
        return locale;
    }
};

/** @id MochiKit.Format.twoDigitAverage */
MochiKit.Format.twoDigitAverage = function (numerator, denominator) {
    if (denominator) {
        var res = numerator / denominator;
        if (!isNaN(res)) {
            return MochiKit.Format.twoDigitFloat(numerator / denominator);
        }
    }
    return "0";
};

/** @id MochiKit.Format.twoDigitFloat */
MochiKit.Format.twoDigitFloat = function (someFloat) {
    var sign = (someFloat < 0 ? '-' : '');
    var s = Math.floor(Math.abs(someFloat) * 100).toString();
    if (s == '0') {
        return s;
    }
    if (s.length < 3) {
        while (s.charAt(s.length - 1) == '0') {
            s = s.substring(0, s.length - 1);
        }
        return sign + '0.' + s;
    }
    var head = sign + s.substring(0, s.length - 2);
    var tail = s.substring(s.length - 2, s.length);
    if (tail == '00') {
        return head;
    } else if (tail.charAt(1) == '0') {
        return head + '.' + tail.charAt(0);
    } else {
        return head + '.' + tail;
    }
};

/** @id MochiKit.Format.lstrip */
MochiKit.Format.lstrip = function (str, /* optional */chars) {
    str = str + "";
    if (typeof(str) != "string") {
        return null;
    }
    if (!chars) {
        return str.replace(/^\s+/, "");
    } else {
        return str.replace(new RegExp("^[" + chars + "]+"), "");
    }
};

/** @id MochiKit.Format.rstrip */
MochiKit.Format.rstrip = function (str, /* optional */chars) {
    str = str + "";
    if (typeof(str) != "string") {
        return null;
    }
    if (!chars) {
        return str.replace(/\s+$/, "");
    } else {
        return str.replace(new RegExp("[" + chars + "]+$"), "");
    }
};

/** @id MochiKit.Format.strip */
MochiKit.Format.strip = function (str, /* optional */chars) {
    var self = MochiKit.Format;
    return self.rstrip(self.lstrip(str, chars), chars);
};

/** @id MochiKit.Format.truncToFixed */
MochiKit.Format.truncToFixed = function (aNumber, precision) {
    aNumber = Math.floor(aNumber * Math.pow(10, precision));
    var res = (aNumber * Math.pow(10, -precision)).toFixed(precision);
    if (res.charAt(0) == ".") {
        res = "0" + res;
    }
    return res;
};

/** @id MochiKit.Format.roundToFixed */
MochiKit.Format.roundToFixed = function (aNumber, precision) {
    return MochiKit.Format.truncToFixed(
        aNumber + 0.5 * Math.pow(10, -precision),
        precision
    );
};

/** @id MochiKit.Format.percentFormat */
MochiKit.Format.percentFormat = function (someFloat) {
    return MochiKit.Format.twoDigitFloat(100 * someFloat) + '%';
};

MochiKit.Format.EXPORT = [
    "truncToFixed",
    "roundToFixed",
    "numberFormatter",
    "formatLocale",
    "twoDigitAverage",
    "twoDigitFloat",
    "percentFormat",
    "lstrip",
    "rstrip",
    "strip"
];

MochiKit.Format.LOCALE = {
    en_US: {separator: ",", decimal: ".", percent: "%"},
    de_DE: {separator: ".", decimal: ",", percent: "%"},
    pt_BR: {separator: ".", decimal: ",", percent: "%"},
    fr_FR: {separator: " ", decimal: ",", percent: "%"},
    "default": "en_US"
};

MochiKit.Format.EXPORT_OK = [];
MochiKit.Format.EXPORT_TAGS = {
    ':all': MochiKit.Format.EXPORT,
    ':common': MochiKit.Format.EXPORT
};

MochiKit.Format.__new__ = function () {
    // MochiKit.Base.nameFunctions(this);
    var base = this.NAME + ".";
    var k, v, o;
    for (k in this.LOCALE) {
        o = this.LOCALE[k];
        if (typeof(o) == "object") {
            o.repr = function () { return this.NAME; };
            o.NAME = base + "LOCALE." + k;
        }
    }
    for (k in this) {
        o = this[k];
        if (typeof(o) == 'function' && typeof(o.NAME) == 'undefined') {
            try {
                o.NAME = base + k;
            } catch (e) {
                // pass
            }
        }
    }
};

MochiKit.Format.__new__();

if (typeof(MochiKit.Base) != "undefined") {
    MochiKit.Base._exportSymbols(this, MochiKit.Format);
} else {
    (function (globals, module) {
        if ((typeof(JSAN) == 'undefined' && typeof(dojo) == 'undefined')
            || (MochiKit.__export__ === false)) {
            var all = module.EXPORT_TAGS[":all"];
            for (var i = 0; i < all.length; i++) {
                globals[all[i]] = module[all[i]];
            }
        }
    })(this, MochiKit.Format);
}
