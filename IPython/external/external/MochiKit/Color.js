/***

MochiKit.Color 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito and others.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.Color');
    dojo.require('MochiKit.Base');
    dojo.require('MochiKit.DOM');
    dojo.require('MochiKit.Style');
}

if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Base", []);
    JSAN.use("MochiKit.DOM", []);
    JSAN.use("MochiKit.Style", []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Color depends on MochiKit.Base";
}

try {
    if (typeof(MochiKit.DOM) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Color depends on MochiKit.DOM";
}

try {
    if (typeof(MochiKit.Style) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.Color depends on MochiKit.Style";
}

if (typeof(MochiKit.Color) == "undefined") {
    MochiKit.Color = {};
}

MochiKit.Color.NAME = "MochiKit.Color";
MochiKit.Color.VERSION = "1.4";

MochiKit.Color.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};

MochiKit.Color.toString = function () {
    return this.__repr__();
};


/** @id MochiKit.Color.Color */
MochiKit.Color.Color = function (red, green, blue, alpha) {
    if (typeof(alpha) == 'undefined' || alpha === null) {
        alpha = 1.0;
    }
    this.rgb = {
        r: red,
        g: green,
        b: blue,
        a: alpha
    };
};


// Prototype methods

MochiKit.Color.Color.prototype = {

    __class__: MochiKit.Color.Color,

    /** @id MochiKit.Color.Color.prototype.colorWithAlpha */
    colorWithAlpha: function (alpha) {
        var rgb = this.rgb;
        var m = MochiKit.Color;
        return m.Color.fromRGB(rgb.r, rgb.g, rgb.b, alpha);
    },

    /** @id MochiKit.Color.Color.prototype.colorWithHue */
    colorWithHue: function (hue) {
        // get an HSL model, and set the new hue...
        var hsl = this.asHSL();
        hsl.h = hue;
        var m = MochiKit.Color;
        // convert back to RGB...
        return m.Color.fromHSL(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.colorWithSaturation */
    colorWithSaturation: function (saturation) {
        // get an HSL model, and set the new hue...
        var hsl = this.asHSL();
        hsl.s = saturation;
        var m = MochiKit.Color;
        // convert back to RGB...
        return m.Color.fromHSL(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.colorWithLightness */
    colorWithLightness: function (lightness) {
        // get an HSL model, and set the new hue...
        var hsl = this.asHSL();
        hsl.l = lightness;
        var m = MochiKit.Color;
        // convert back to RGB...
        return m.Color.fromHSL(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.darkerColorWithLevel */
    darkerColorWithLevel: function (level) {
        var hsl  = this.asHSL();
        hsl.l = Math.max(hsl.l - level, 0);
        var m = MochiKit.Color;
        return m.Color.fromHSL(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.lighterColorWithLevel */
    lighterColorWithLevel: function (level) {
        var hsl  = this.asHSL();
        hsl.l = Math.min(hsl.l + level, 1);
        var m = MochiKit.Color;
        return m.Color.fromHSL(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.blendedColor */
    blendedColor: function (other, /* optional */ fraction) {
        if (typeof(fraction) == 'undefined' || fraction === null) {
            fraction = 0.5;
        }
        var sf = 1.0 - fraction;
        var s = this.rgb;
        var d = other.rgb;
        var df = fraction;
        return MochiKit.Color.Color.fromRGB(
            (s.r * sf) + (d.r * df),
            (s.g * sf) + (d.g * df),
            (s.b * sf) + (d.b * df),
            (s.a * sf) + (d.a * df)
        );
    },

    /** @id MochiKit.Color.Color.prototype.compareRGB */
    compareRGB: function (other) {
        var a = this.asRGB();
        var b = other.asRGB();
        return MochiKit.Base.compare(
            [a.r, a.g, a.b, a.a],
            [b.r, b.g, b.b, b.a]
        );
    },

    /** @id MochiKit.Color.Color.prototype.isLight */
    isLight: function () {
        return this.asHSL().b > 0.5;
    },

    /** @id MochiKit.Color.Color.prototype.isDark */
    isDark: function () {
        return (!this.isLight());
    },

    /** @id MochiKit.Color.Color.prototype.toHSLString */
    toHSLString: function () {
        var c = this.asHSL();
        var ccc = MochiKit.Color.clampColorComponent;
        var rval = this._hslString;
        if (!rval) {
            var mid = (
                ccc(c.h, 360).toFixed(0)
                + "," + ccc(c.s, 100).toPrecision(4) + "%"
                + "," + ccc(c.l, 100).toPrecision(4) + "%"
            );
            var a = c.a;
            if (a >= 1) {
                a = 1;
                rval = "hsl(" + mid + ")";
            } else {
                if (a <= 0) {
                    a = 0;
                }
                rval = "hsla(" + mid + "," + a + ")";
            }
            this._hslString = rval;
        }
        return rval;
    },

    /** @id MochiKit.Color.Color.prototype.toRGBString */
    toRGBString: function () {
        var c = this.rgb;
        var ccc = MochiKit.Color.clampColorComponent;
        var rval = this._rgbString;
        if (!rval) {
            var mid = (
                ccc(c.r, 255).toFixed(0)
                + "," + ccc(c.g, 255).toFixed(0)
                + "," + ccc(c.b, 255).toFixed(0)
            );
            if (c.a != 1) {
                rval = "rgba(" + mid + "," + c.a + ")";
            } else {
                rval = "rgb(" + mid + ")";
            }
            this._rgbString = rval;
        }
        return rval;
    },

    /** @id MochiKit.Color.Color.prototype.asRGB */
    asRGB: function () {
        return MochiKit.Base.clone(this.rgb);
    },

    /** @id MochiKit.Color.Color.prototype.toHexString */
    toHexString: function () {
        var m = MochiKit.Color;
        var c = this.rgb;
        var ccc = MochiKit.Color.clampColorComponent;
        var rval = this._hexString;
        if (!rval) {
            rval = ("#" +
                m.toColorPart(ccc(c.r, 255)) +
                m.toColorPart(ccc(c.g, 255)) +
                m.toColorPart(ccc(c.b, 255))
            );
            this._hexString = rval;
        }
        return rval;
    },

    /** @id MochiKit.Color.Color.prototype.asHSV */
    asHSV: function () {
        var hsv = this.hsv;
        var c = this.rgb;
        if (typeof(hsv) == 'undefined' || hsv === null) {
            hsv = MochiKit.Color.rgbToHSV(this.rgb);
            this.hsv = hsv;
        }
        return MochiKit.Base.clone(hsv);
    },

    /** @id MochiKit.Color.Color.prototype.asHSL */
    asHSL: function () {
        var hsl = this.hsl;
        var c = this.rgb;
        if (typeof(hsl) == 'undefined' || hsl === null) {
            hsl = MochiKit.Color.rgbToHSL(this.rgb);
            this.hsl = hsl;
        }
        return MochiKit.Base.clone(hsl);
    },

    /** @id MochiKit.Color.Color.prototype.toString */
    toString: function () {
        return this.toRGBString();
    },

    /** @id MochiKit.Color.Color.prototype.repr */
    repr: function () {
        var c = this.rgb;
        var col = [c.r, c.g, c.b, c.a];
        return this.__class__.NAME + "(" + col.join(", ") + ")";
    }

};

// Constructor methods

MochiKit.Base.update(MochiKit.Color.Color, {
    /** @id MochiKit.Color.Color.fromRGB */
    fromRGB: function (red, green, blue, alpha) {
        // designated initializer
        var Color = MochiKit.Color.Color;
        if (arguments.length == 1) {
            var rgb = red;
            red = rgb.r;
            green = rgb.g;
            blue = rgb.b;
            if (typeof(rgb.a) == 'undefined') {
                alpha = undefined;
            } else {
                alpha = rgb.a;
            }
        }
        return new Color(red, green, blue, alpha);
    },

    /** @id MochiKit.Color.Color.fromHSL */
    fromHSL: function (hue, saturation, lightness, alpha) {
        var m = MochiKit.Color;
        return m.Color.fromRGB(m.hslToRGB.apply(m, arguments));
    },

    /** @id MochiKit.Color.Color.fromHSV */
    fromHSV: function (hue, saturation, value, alpha) {
        var m = MochiKit.Color;
        return m.Color.fromRGB(m.hsvToRGB.apply(m, arguments));
    },

    /** @id MochiKit.Color.Color.fromName */
    fromName: function (name) {
        var Color = MochiKit.Color.Color;
        // Opera 9 seems to "quote" named colors(?!)
        if (name.charAt(0) == '"') {
            name = name.substr(1, name.length - 2);
        }
        var htmlColor = Color._namedColors[name.toLowerCase()];
        if (typeof(htmlColor) == 'string') {
            return Color.fromHexString(htmlColor);
        } else if (name == "transparent") {
            return Color.transparentColor();
        }
        return null;
    },

    /** @id MochiKit.Color.Color.fromString */
    fromString: function (colorString) {
        var self = MochiKit.Color.Color;
        var three = colorString.substr(0, 3);
        if (three == "rgb") {
            return self.fromRGBString(colorString);
        } else if (three == "hsl") {
            return self.fromHSLString(colorString);
        } else if (colorString.charAt(0) == "#") {
            return self.fromHexString(colorString);
        }
        return self.fromName(colorString);
    },


    /** @id MochiKit.Color.Color.fromHexString */
    fromHexString: function (hexCode) {
        if (hexCode.charAt(0) == '#') {
            hexCode = hexCode.substring(1);
        }
        var components = [];
        var i, hex;
        if (hexCode.length == 3) {
            for (i = 0; i < 3; i++) {
                hex = hexCode.substr(i, 1);
                components.push(parseInt(hex + hex, 16) / 255.0);
            }
        } else {
            for (i = 0; i < 6; i += 2) {
                hex = hexCode.substr(i, 2);
                components.push(parseInt(hex, 16) / 255.0);
            }
        }
        var Color = MochiKit.Color.Color;
        return Color.fromRGB.apply(Color, components);
    },


    _fromColorString: function (pre, method, scales, colorCode) {
        // parses either HSL or RGB
        if (colorCode.indexOf(pre) === 0) {
            colorCode = colorCode.substring(colorCode.indexOf("(", 3) + 1, colorCode.length - 1);
        }
        var colorChunks = colorCode.split(/\s*,\s*/);
        var colorFloats = [];
        for (var i = 0; i < colorChunks.length; i++) {
            var c = colorChunks[i];
            var val;
            var three = c.substring(c.length - 3);
            if (c.charAt(c.length - 1) == '%') {
                val = 0.01 * parseFloat(c.substring(0, c.length - 1));
            } else if (three == "deg") {
                val = parseFloat(c) / 360.0;
            } else if (three == "rad") {
                val = parseFloat(c) / (Math.PI * 2);
            } else {
                val = scales[i] * parseFloat(c);
            }
            colorFloats.push(val);
        }
        return this[method].apply(this, colorFloats);
    },

    /** @id MochiKit.Color.Color.fromComputedStyle */
    fromComputedStyle: function (elem, style) {
        var d = MochiKit.DOM;
        var cls = MochiKit.Color.Color;
        for (elem = d.getElement(elem); elem; elem = elem.parentNode) {
            var actualColor = MochiKit.Style.getStyle.apply(d, arguments);
            if (!actualColor) {
                continue;
            }
            var color = cls.fromString(actualColor);
            if (!color) {
                break;
            }
            if (color.asRGB().a > 0) {
                return color;
            }
        }
        return null;
    },

    /** @id MochiKit.Color.Color.fromBackground */
    fromBackground: function (elem) {
        var cls = MochiKit.Color.Color;
        return cls.fromComputedStyle(
            elem, "backgroundColor", "background-color") || cls.whiteColor();
    },

    /** @id MochiKit.Color.Color.fromText */
    fromText: function (elem) {
        var cls = MochiKit.Color.Color;
        return cls.fromComputedStyle(
            elem, "color", "color") || cls.blackColor();
    },

    /** @id MochiKit.Color.Color.namedColors */
    namedColors: function () {
        return MochiKit.Base.clone(MochiKit.Color.Color._namedColors);
    }
});


// Module level functions

MochiKit.Base.update(MochiKit.Color, {
    /** @id MochiKit.Color.clampColorComponent */
    clampColorComponent: function (v, scale) {
        v *= scale;
        if (v < 0) {
            return 0;
        } else if (v > scale) {
            return scale;
        } else {
            return v;
        }
    },

    _hslValue: function (n1, n2, hue) {
        if (hue > 6.0) {
            hue -= 6.0;
        } else if (hue < 0.0) {
            hue += 6.0;
        }
        var val;
        if (hue < 1.0) {
            val = n1 + (n2 - n1) * hue;
        } else if (hue < 3.0) {
            val = n2;
        } else if (hue < 4.0) {
            val = n1 + (n2 - n1) * (4.0 - hue);
        } else {
            val = n1;
        }
        return val;
    },

    /** @id MochiKit.Color.hsvToRGB */
    hsvToRGB: function (hue, saturation, value, alpha) {
        if (arguments.length == 1) {
            var hsv = hue;
            hue = hsv.h;
            saturation = hsv.s;
            value = hsv.v;
            alpha = hsv.a;
        }
        var red;
        var green;
        var blue;
        if (saturation === 0) {
            red = value;
            green = value;
            blue = value;
        } else {
            var i = Math.floor(hue * 6);
            var f = (hue * 6) - i;
            var p = value * (1 - saturation);
            var q = value * (1 - (saturation * f));
            var t = value * (1 - (saturation * (1 - f)));
            switch (i) {
                case 1: red = q; green = value; blue = p; break;
                case 2: red = p; green = value; blue = t; break;
                case 3: red = p; green = q; blue = value; break;
                case 4: red = t; green = p; blue = value; break;
                case 5: red = value; green = p; blue = q; break;
                case 6: // fall through
                case 0: red = value; green = t; blue = p; break;
            }
        }
        return {
            r: red,
            g: green,
            b: blue,
            a: alpha
        };
    },

    /** @id MochiKit.Color.hslToRGB */
    hslToRGB: function (hue, saturation, lightness, alpha) {
        if (arguments.length == 1) {
            var hsl = hue;
            hue = hsl.h;
            saturation = hsl.s;
            lightness = hsl.l;
            alpha = hsl.a;
        }
        var red;
        var green;
        var blue;
        if (saturation === 0) {
            red = lightness;
            green = lightness;
            blue = lightness;
        } else {
            var m2;
            if (lightness <= 0.5) {
                m2 = lightness * (1.0 + saturation);
            } else {
                m2 = lightness + saturation - (lightness * saturation);
            }
            var m1 = (2.0 * lightness) - m2;
            var f = MochiKit.Color._hslValue;
            var h6 = hue * 6.0;
            red = f(m1, m2, h6 + 2);
            green = f(m1, m2, h6);
            blue = f(m1, m2, h6 - 2);
        }
        return {
            r: red,
            g: green,
            b: blue,
            a: alpha
        };
    },

    /** @id MochiKit.Color.rgbToHSV */
    rgbToHSV: function (red, green, blue, alpha) {
        if (arguments.length == 1) {
            var rgb = red;
            red = rgb.r;
            green = rgb.g;
            blue = rgb.b;
            alpha = rgb.a;
        }
        var max = Math.max(Math.max(red, green), blue);
        var min = Math.min(Math.min(red, green), blue);
        var hue;
        var saturation;
        var value = max;
        if (min == max) {
            hue = 0;
            saturation = 0;
        } else {
            var delta = (max - min);
            saturation = delta / max;

            if (red == max) {
                hue = (green - blue) / delta;
            } else if (green == max) {
                hue = 2 + ((blue - red) / delta);
            } else {
                hue = 4 + ((red - green) / delta);
            }
            hue /= 6;
            if (hue < 0) {
                hue += 1;
            }
            if (hue > 1) {
                hue -= 1;
            }
        }
        return {
            h: hue,
            s: saturation,
            v: value,
            a: alpha
        };
    },

    /** @id MochiKit.Color.rgbToHSL */
    rgbToHSL: function (red, green, blue, alpha) {
        if (arguments.length == 1) {
            var rgb = red;
            red = rgb.r;
            green = rgb.g;
            blue = rgb.b;
            alpha = rgb.a;
        }
        var max = Math.max(red, Math.max(green, blue));
        var min = Math.min(red, Math.min(green, blue));
        var hue;
        var saturation;
        var lightness = (max + min) / 2.0;
        var delta = max - min;
        if (delta === 0) {
            hue = 0;
            saturation = 0;
        } else {
            if (lightness <= 0.5) {
                saturation = delta / (max + min);
            } else {
                saturation = delta / (2 - max - min);
            }
            if (red == max) {
                hue = (green - blue) / delta;
            } else if (green == max) {
                hue = 2 + ((blue - red) / delta);
            } else {
                hue = 4 + ((red - green) / delta);
            }
            hue /= 6;
            if (hue < 0) {
                hue += 1;
            }
            if (hue > 1) {
                hue -= 1;
            }

        }
        return {
            h: hue,
            s: saturation,
            l: lightness,
            a: alpha
        };
    },

    /** @id MochiKit.Color.toColorPart */
    toColorPart: function (num) {
        num = Math.round(num);
        var digits = num.toString(16);
        if (num < 16) {
            return '0' + digits;
        }
        return digits;
    },

    __new__: function () {
        var m = MochiKit.Base;
        /** @id MochiKit.Color.fromRGBString */
        this.Color.fromRGBString = m.bind(
            this.Color._fromColorString, this.Color, "rgb", "fromRGB",
            [1.0/255.0, 1.0/255.0, 1.0/255.0, 1]
        );
        /** @id MochiKit.Color.fromHSLString */
        this.Color.fromHSLString = m.bind(
            this.Color._fromColorString, this.Color, "hsl", "fromHSL",
            [1.0/360.0, 0.01, 0.01, 1]
        );

        var third = 1.0 / 3.0;
        /** @id MochiKit.Color.colors */
        var colors = {
            // NSColor colors plus transparent
            /** @id MochiKit.Color.blackColor */
            black: [0, 0, 0],
            /** @id MochiKit.Color.blueColor */
            blue: [0, 0, 1],
            /** @id MochiKit.Color.brownColor */
            brown: [0.6, 0.4, 0.2],
            /** @id MochiKit.Color.cyanColor */
            cyan: [0, 1, 1],
            /** @id MochiKit.Color.darkGrayColor */
            darkGray: [third, third, third],
            /** @id MochiKit.Color.grayColor */
            gray: [0.5, 0.5, 0.5],
            /** @id MochiKit.Color.greenColor */
            green: [0, 1, 0],
            /** @id MochiKit.Color.lightGrayColor */
            lightGray: [2 * third, 2 * third, 2 * third],
            /** @id MochiKit.Color.magentaColor */
            magenta: [1, 0, 1],
            /** @id MochiKit.Color.orangeColor */
            orange: [1, 0.5, 0],
            /** @id MochiKit.Color.purpleColor */
            purple: [0.5, 0, 0.5],
            /** @id MochiKit.Color.redColor */
            red: [1, 0, 0],
            /** @id MochiKit.Color.transparentColor */
            transparent: [0, 0, 0, 0],
            /** @id MochiKit.Color.whiteColor */
            white: [1, 1, 1],
            /** @id MochiKit.Color.yellowColor */
            yellow: [1, 1, 0]
        };

        var makeColor = function (name, r, g, b, a) {
            var rval = this.fromRGB(r, g, b, a);
            this[name] = function () { return rval; };
            return rval;
        };

        for (var k in colors) {
            var name = k + "Color";
            var bindArgs = m.concat(
                [makeColor, this.Color, name],
                colors[k]
            );
            this.Color[name] = m.bind.apply(null, bindArgs);
        }

        var isColor = function () {
            for (var i = 0; i < arguments.length; i++) {
                if (!(arguments[i] instanceof Color)) {
                    return false;
                }
            }
            return true;
        };

        var compareColor = function (a, b) {
            return a.compareRGB(b);
        };

        m.nameFunctions(this);

        m.registerComparator(this.Color.NAME, isColor, compareColor);

        this.EXPORT_TAGS = {
            ":common": this.EXPORT,
            ":all": m.concat(this.EXPORT, this.EXPORT_OK)
        };

    }
});

MochiKit.Color.EXPORT = [
    "Color"
];

MochiKit.Color.EXPORT_OK = [
    "clampColorComponent",
    "rgbToHSL",
    "hslToRGB",
    "rgbToHSV",
    "hsvToRGB",
    "toColorPart"
];

MochiKit.Color.__new__();

MochiKit.Base._exportSymbols(this, MochiKit.Color);

// Full table of css3 X11 colors <http://www.w3.org/TR/css3-color/#X11COLORS>

MochiKit.Color.Color._namedColors = {
    aliceblue: "#f0f8ff",
    antiquewhite: "#faebd7",
    aqua: "#00ffff",
    aquamarine: "#7fffd4",
    azure: "#f0ffff",
    beige: "#f5f5dc",
    bisque: "#ffe4c4",
    black: "#000000",
    blanchedalmond: "#ffebcd",
    blue: "#0000ff",
    blueviolet: "#8a2be2",
    brown: "#a52a2a",
    burlywood: "#deb887",
    cadetblue: "#5f9ea0",
    chartreuse: "#7fff00",
    chocolate: "#d2691e",
    coral: "#ff7f50",
    cornflowerblue: "#6495ed",
    cornsilk: "#fff8dc",
    crimson: "#dc143c",
    cyan: "#00ffff",
    darkblue: "#00008b",
    darkcyan: "#008b8b",
    darkgoldenrod: "#b8860b",
    darkgray: "#a9a9a9",
    darkgreen: "#006400",
    darkgrey: "#a9a9a9",
    darkkhaki: "#bdb76b",
    darkmagenta: "#8b008b",
    darkolivegreen: "#556b2f",
    darkorange: "#ff8c00",
    darkorchid: "#9932cc",
    darkred: "#8b0000",
    darksalmon: "#e9967a",
    darkseagreen: "#8fbc8f",
    darkslateblue: "#483d8b",
    darkslategray: "#2f4f4f",
    darkslategrey: "#2f4f4f",
    darkturquoise: "#00ced1",
    darkviolet: "#9400d3",
    deeppink: "#ff1493",
    deepskyblue: "#00bfff",
    dimgray: "#696969",
    dimgrey: "#696969",
    dodgerblue: "#1e90ff",
    firebrick: "#b22222",
    floralwhite: "#fffaf0",
    forestgreen: "#228b22",
    fuchsia: "#ff00ff",
    gainsboro: "#dcdcdc",
    ghostwhite: "#f8f8ff",
    gold: "#ffd700",
    goldenrod: "#daa520",
    gray: "#808080",
    green: "#008000",
    greenyellow: "#adff2f",
    grey: "#808080",
    honeydew: "#f0fff0",
    hotpink: "#ff69b4",
    indianred: "#cd5c5c",
    indigo: "#4b0082",
    ivory: "#fffff0",
    khaki: "#f0e68c",
    lavender: "#e6e6fa",
    lavenderblush: "#fff0f5",
    lawngreen: "#7cfc00",
    lemonchiffon: "#fffacd",
    lightblue: "#add8e6",
    lightcoral: "#f08080",
    lightcyan: "#e0ffff",
    lightgoldenrodyellow: "#fafad2",
    lightgray: "#d3d3d3",
    lightgreen: "#90ee90",
    lightgrey: "#d3d3d3",
    lightpink: "#ffb6c1",
    lightsalmon: "#ffa07a",
    lightseagreen: "#20b2aa",
    lightskyblue: "#87cefa",
    lightslategray: "#778899",
    lightslategrey: "#778899",
    lightsteelblue: "#b0c4de",
    lightyellow: "#ffffe0",
    lime: "#00ff00",
    limegreen: "#32cd32",
    linen: "#faf0e6",
    magenta: "#ff00ff",
    maroon: "#800000",
    mediumaquamarine: "#66cdaa",
    mediumblue: "#0000cd",
    mediumorchid: "#ba55d3",
    mediumpurple: "#9370db",
    mediumseagreen: "#3cb371",
    mediumslateblue: "#7b68ee",
    mediumspringgreen: "#00fa9a",
    mediumturquoise: "#48d1cc",
    mediumvioletred: "#c71585",
    midnightblue: "#191970",
    mintcream: "#f5fffa",
    mistyrose: "#ffe4e1",
    moccasin: "#ffe4b5",
    navajowhite: "#ffdead",
    navy: "#000080",
    oldlace: "#fdf5e6",
    olive: "#808000",
    olivedrab: "#6b8e23",
    orange: "#ffa500",
    orangered: "#ff4500",
    orchid: "#da70d6",
    palegoldenrod: "#eee8aa",
    palegreen: "#98fb98",
    paleturquoise: "#afeeee",
    palevioletred: "#db7093",
    papayawhip: "#ffefd5",
    peachpuff: "#ffdab9",
    peru: "#cd853f",
    pink: "#ffc0cb",
    plum: "#dda0dd",
    powderblue: "#b0e0e6",
    purple: "#800080",
    red: "#ff0000",
    rosybrown: "#bc8f8f",
    royalblue: "#4169e1",
    saddlebrown: "#8b4513",
    salmon: "#fa8072",
    sandybrown: "#f4a460",
    seagreen: "#2e8b57",
    seashell: "#fff5ee",
    sienna: "#a0522d",
    silver: "#c0c0c0",
    skyblue: "#87ceeb",
    slateblue: "#6a5acd",
    slategray: "#708090",
    slategrey: "#708090",
    snow: "#fffafa",
    springgreen: "#00ff7f",
    steelblue: "#4682b4",
    tan: "#d2b48c",
    teal: "#008080",
    thistle: "#d8bfd8",
    tomato: "#ff6347",
    turquoise: "#40e0d0",
    violet: "#ee82ee",
    wheat: "#f5deb3",
    white: "#ffffff",
    whitesmoke: "#f5f5f5",
    yellow: "#ffff00",
    yellowgreen: "#9acd32"
};
