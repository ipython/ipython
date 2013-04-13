(function(){if (!Date.now) Date.now = function() {
  return +new Date;
};
try {
  document.createElement("div").style.setProperty("opacity", 0, "");
} catch (error) {
  var d3_style_prototype = CSSStyleDeclaration.prototype,
      d3_style_setProperty = d3_style_prototype.setProperty;
  d3_style_prototype.setProperty = function(name, value, priority) {
    d3_style_setProperty.call(this, name, value + "", priority);
  };
}
d3 = {version: "2.8.1"}; // semver
function d3_class(ctor, properties) {
  try {
    for (var key in properties) {
      Object.defineProperty(ctor.prototype, key, {
        value: properties[key],
        enumerable: false
      });
    }
  } catch (e) {
    ctor.prototype = properties;
  }
}
var d3_array = d3_arraySlice; // conversion for NodeLists

function d3_arrayCopy(pseudoarray) {
  var i = -1, n = pseudoarray.length, array = [];
  while (++i < n) array.push(pseudoarray[i]);
  return array;
}

function d3_arraySlice(pseudoarray) {
  return Array.prototype.slice.call(pseudoarray);
}

try {
  d3_array(document.documentElement.childNodes)[0].nodeType;
} catch(e) {
  d3_array = d3_arrayCopy;
}

var d3_arraySubclass = [].__proto__?

// Until ECMAScript supports array subclassing, prototype injection works well.
function(array, prototype) {
  array.__proto__ = prototype;
}:

// And if your browser doesn't support __proto__, we'll use direct extension.
function(array, prototype) {
  for (var property in prototype) array[property] = prototype[property];
};
d3.map = function(object) {
  var map = new d3_Map;
  for (var key in object) map.set(key, object[key]);
  return map;
};

function d3_Map() {}

d3_class(d3_Map, {
  has: function(key) {
    return d3_map_prefix + key in this;
  },
  get: function(key) {
    return this[d3_map_prefix + key];
  },
  set: function(key, value) {
    return this[d3_map_prefix + key] = value;
  },
  remove: function(key) {
    key = d3_map_prefix + key;
    return key in this && delete this[key];
  },
  keys: function() {
    var keys = [];
    this.forEach(function(key) { keys.push(key); });
    return keys;
  },
  values: function() {
    var values = [];
    this.forEach(function(key, value) { values.push(value); });
    return values;
  },
  entries: function() {
    var entries = [];
    this.forEach(function(key, value) { entries.push({key: key, value: value}); });
    return entries;
  },
  forEach: function(f) {
    for (var key in this) {
      if (key.charCodeAt(0) === d3_map_prefixCode) {
        f.call(this, key.substring(1), this[key]);
      }
    }
  }
});

var d3_map_prefix = "\0", // prevent collision with built-ins
    d3_map_prefixCode = d3_map_prefix.charCodeAt(0);
function d3_this() {
  return this;
}
d3.functor = function(v) {
  return typeof v === "function" ? v : function() { return v; };
};
// Copies a variable number of methods from source to target.
d3.rebind = function(target, source) {
  var i = 1, n = arguments.length, method;
  while (++i < n) target[method = arguments[i]] = d3_rebind(target, source, source[method]);
  return target;
};

// Method is assumed to be a standard D3 getter-setter:
// If passed with no arguments, gets the value.
// If passed with arguments, sets the value and returns the target.
function d3_rebind(target, source, method) {
  return function() {
    var value = method.apply(source, arguments);
    return arguments.length ? target : value;
  };
}
d3.ascending = function(a, b) {
  return a < b ? -1 : a > b ? 1 : a >= b ? 0 : NaN;
};
d3.descending = function(a, b) {
  return b < a ? -1 : b > a ? 1 : b >= a ? 0 : NaN;
};
d3.mean = function(array, f) {
  var n = array.length,
      a,
      m = 0,
      i = -1,
      j = 0;
  if (arguments.length === 1) {
    while (++i < n) if (d3_number(a = array[i])) m += (a - m) / ++j;
  } else {
    while (++i < n) if (d3_number(a = f.call(array, array[i], i))) m += (a - m) / ++j;
  }
  return j ? m : undefined;
};
d3.median = function(array, f) {
  if (arguments.length > 1) array = array.map(f);
  array = array.filter(d3_number);
  return array.length ? d3.quantile(array.sort(d3.ascending), .5) : undefined;
};
d3.min = function(array, f) {
  var i = -1,
      n = array.length,
      a,
      b;
  if (arguments.length === 1) {
    while (++i < n && ((a = array[i]) == null || a != a)) a = undefined;
    while (++i < n) if ((b = array[i]) != null && a > b) a = b;
  } else {
    while (++i < n && ((a = f.call(array, array[i], i)) == null || a != a)) a = undefined;
    while (++i < n) if ((b = f.call(array, array[i], i)) != null && a > b) a = b;
  }
  return a;
};
d3.max = function(array, f) {
  var i = -1,
      n = array.length,
      a,
      b;
  if (arguments.length === 1) {
    while (++i < n && ((a = array[i]) == null || a != a)) a = undefined;
    while (++i < n) if ((b = array[i]) != null && b > a) a = b;
  } else {
    while (++i < n && ((a = f.call(array, array[i], i)) == null || a != a)) a = undefined;
    while (++i < n) if ((b = f.call(array, array[i], i)) != null && b > a) a = b;
  }
  return a;
};
d3.extent = function(array, f) {
  var i = -1,
      n = array.length,
      a,
      b,
      c;
  if (arguments.length === 1) {
    while (++i < n && ((a = c = array[i]) == null || a != a)) a = c = undefined;
    while (++i < n) if ((b = array[i]) != null) {
      if (a > b) a = b;
      if (c < b) c = b;
    }
  } else {
    while (++i < n && ((a = c = f.call(array, array[i], i)) == null || a != a)) a = undefined;
    while (++i < n) if ((b = f.call(array, array[i], i)) != null) {
      if (a > b) a = b;
      if (c < b) c = b;
    }
  }
  return [a, c];
};
d3.random = {
  normal: function(mean, deviation) {
    if (arguments.length < 2) deviation = 1;
    if (arguments.length < 1) mean = 0;
    return function() {
      var x, y, r;
      do {
        x = Math.random() * 2 - 1;
        y = Math.random() * 2 - 1;
        r = x * x + y * y;
      } while (!r || r > 1);
      return mean + deviation * x * Math.sqrt(-2 * Math.log(r) / r);
    };
  }
};
function d3_number(x) {
  return x != null && !isNaN(x);
}
d3.sum = function(array, f) {
  var s = 0,
      n = array.length,
      a,
      i = -1;

  if (arguments.length === 1) {
    while (++i < n) if (!isNaN(a = +array[i])) s += a;
  } else {
    while (++i < n) if (!isNaN(a = +f.call(array, array[i], i))) s += a;
  }

  return s;
};
// R-7 per <http://en.wikipedia.org/wiki/Quantile>
d3.quantile = function(values, p) {
  var H = (values.length - 1) * p + 1,
      h = Math.floor(H),
      v = values[h - 1],
      e = H - h;
  return e ? v + e * (values[h] - v) : v;
};
d3.transpose = function(matrix) {
  return d3.zip.apply(d3, matrix);
};
d3.zip = function() {
  if (!(n = arguments.length)) return [];
  for (var i = -1, m = d3.min(arguments, d3_zipLength), zips = new Array(m); ++i < m;) {
    for (var j = -1, n, zip = zips[i] = new Array(n); ++j < n;) {
      zip[j] = arguments[j][i];
    }
  }
  return zips;
};

function d3_zipLength(d) {
  return d.length;
}
d3.bisector = function(f) {
  return {
    left: function(a, x, lo, hi) {
      if (arguments.length < 3) lo = 0;
      if (arguments.length < 4) hi = a.length;
      while (lo < hi) {
        var mid = lo + hi >> 1;
        if (f.call(a, a[mid], mid) < x) lo = mid + 1;
        else hi = mid;
      }
      return lo;
    },
    right: function(a, x, lo, hi) {
      if (arguments.length < 3) lo = 0;
      if (arguments.length < 4) hi = a.length;
      while (lo < hi) {
        var mid = lo + hi >> 1;
        if (x < f.call(a, a[mid], mid)) hi = mid;
        else lo = mid + 1;
      }
      return lo;
    }
  };
};

var d3_bisector = d3.bisector(function(d) { return d; });
d3.bisectLeft = d3_bisector.left;
d3.bisect = d3.bisectRight = d3_bisector.right;
d3.first = function(array, f) {
  var i = 0,
      n = array.length,
      a = array[0],
      b;
  if (arguments.length === 1) f = d3.ascending;
  while (++i < n) {
    if (f.call(array, a, b = array[i]) > 0) {
      a = b;
    }
  }
  return a;
};
d3.last = function(array, f) {
  var i = 0,
      n = array.length,
      a = array[0],
      b;
  if (arguments.length === 1) f = d3.ascending;
  while (++i < n) {
    if (f.call(array, a, b = array[i]) <= 0) {
      a = b;
    }
  }
  return a;
};
d3.nest = function() {
  var nest = {},
      keys = [],
      sortKeys = [],
      sortValues,
      rollup;

  function map(array, depth) {
    if (depth >= keys.length) return rollup
        ? rollup.call(nest, array) : (sortValues
        ? array.sort(sortValues)
        : array);

    var i = -1,
        n = array.length,
        key = keys[depth++],
        keyValue,
        object,
        valuesByKey = new d3_Map,
        values,
        o = {};

    while (++i < n) {
      if (values = valuesByKey.get(keyValue = key(object = array[i]))) {
        values.push(object);
      } else {
        valuesByKey.set(keyValue, [object]);
      }
    }

    valuesByKey.forEach(function(keyValue) {
      o[keyValue] = map(valuesByKey.get(keyValue), depth);
    });

    return o;
  }

  function entries(map, depth) {
    if (depth >= keys.length) return map;

    var a = [],
        sortKey = sortKeys[depth++],
        key;

    for (key in map) {
      a.push({key: key, values: entries(map[key], depth)});
    }

    if (sortKey) a.sort(function(a, b) {
      return sortKey(a.key, b.key);
    });

    return a;
  }

  nest.map = function(array) {
    return map(array, 0);
  };

  nest.entries = function(array) {
    return entries(map(array, 0), 0);
  };

  nest.key = function(d) {
    keys.push(d);
    return nest;
  };

  // Specifies the order for the most-recently specified key.
  // Note: only applies to entries. Map keys are unordered!
  nest.sortKeys = function(order) {
    sortKeys[keys.length - 1] = order;
    return nest;
  };

  // Specifies the order for leaf values.
  // Applies to both maps and entries array.
  nest.sortValues = function(order) {
    sortValues = order;
    return nest;
  };

  nest.rollup = function(f) {
    rollup = f;
    return nest;
  };

  return nest;
};
d3.keys = function(map) {
  var keys = [];
  for (var key in map) keys.push(key);
  return keys;
};
d3.values = function(map) {
  var values = [];
  for (var key in map) values.push(map[key]);
  return values;
};
d3.entries = function(map) {
  var entries = [];
  for (var key in map) entries.push({key: key, value: map[key]});
  return entries;
};
d3.permute = function(array, indexes) {
  var permutes = [],
      i = -1,
      n = indexes.length;
  while (++i < n) permutes[i] = array[indexes[i]];
  return permutes;
};
d3.merge = function(arrays) {
  return Array.prototype.concat.apply([], arrays);
};
d3.split = function(array, f) {
  var arrays = [],
      values = [],
      value,
      i = -1,
      n = array.length;
  if (arguments.length < 2) f = d3_splitter;
  while (++i < n) {
    if (f.call(values, value = array[i], i)) {
      values = [];
    } else {
      if (!values.length) arrays.push(values);
      values.push(value);
    }
  }
  return arrays;
};

function d3_splitter(d) {
  return d == null;
}
function d3_collapse(s) {
  return s.replace(/(^\s+)|(\s+$)/g, "").replace(/\s+/g, " ");
}
d3.range = function(start, stop, step) {
  if (arguments.length < 3) {
    step = 1;
    if (arguments.length < 2) {
      stop = start;
      start = 0;
    }
  }
  if ((stop - start) / step === Infinity) throw new Error("infinite range");
  var range = [],
       k = d3_range_integerScale(Math.abs(step)),
       i = -1,
       j;
  start *= k, stop *= k, step *= k;
  if (step < 0) while ((j = start + step * ++i) > stop) range.push(j / k);
  else while ((j = start + step * ++i) < stop) range.push(j / k);
  return range;
};

function d3_range_integerScale(x) {
  var k = 1;
  while (x * k % 1) k *= 10;
  return k;
}
d3.requote = function(s) {
  return s.replace(d3_requote_re, "\\$&");
};

var d3_requote_re = /[\\\^\$\*\+\?\|\[\]\(\)\.\{\}]/g;
d3.round = function(x, n) {
  return n
      ? Math.round(x * (n = Math.pow(10, n))) / n
      : Math.round(x);
};
d3.xhr = function(url, mime, callback) {
  var req = new XMLHttpRequest;
  if (arguments.length < 3) callback = mime, mime = null;
  else if (mime && req.overrideMimeType) req.overrideMimeType(mime);
  req.open("GET", url, true);
  if (mime) req.setRequestHeader("Accept", mime);
  req.onreadystatechange = function() {
    if (req.readyState === 4) callback(req.status < 300 ? req : null);
  };
  req.send(null);
};
d3.text = function(url, mime, callback) {
  function ready(req) {
    callback(req && req.responseText);
  }
  if (arguments.length < 3) {
    callback = mime;
    mime = null;
  }
  d3.xhr(url, mime, ready);
};
d3.json = function(url, callback) {
  d3.text(url, "application/json", function(text) {
    callback(text ? JSON.parse(text) : null);
  });
};
d3.html = function(url, callback) {
  d3.text(url, "text/html", function(text) {
    if (text != null) { // Treat empty string as valid HTML.
      var range = document.createRange();
      range.selectNode(document.body);
      text = range.createContextualFragment(text);
    }
    callback(text);
  });
};
d3.xml = function(url, mime, callback) {
  function ready(req) {
    callback(req && req.responseXML);
  }
  if (arguments.length < 3) {
    callback = mime;
    mime = null;
  }
  d3.xhr(url, mime, ready);
};
var d3_nsPrefix = {
  svg: "http://www.w3.org/2000/svg",
  xhtml: "http://www.w3.org/1999/xhtml",
  xlink: "http://www.w3.org/1999/xlink",
  xml: "http://www.w3.org/XML/1998/namespace",
  xmlns: "http://www.w3.org/2000/xmlns/"
};

d3.ns = {
  prefix: d3_nsPrefix,
  qualify: function(name) {
    var i = name.indexOf(":"),
        prefix = name;
    if (i >= 0) {
      prefix = name.substring(0, i);
      name = name.substring(i + 1);
    }
    return d3_nsPrefix.hasOwnProperty(prefix)
        ? {space: d3_nsPrefix[prefix], local: name}
        : name;
  }
};
d3.dispatch = function() {
  var dispatch = new d3_dispatch,
      i = -1,
      n = arguments.length;
  while (++i < n) dispatch[arguments[i]] = d3_dispatch_event(dispatch);
  return dispatch;
};

function d3_dispatch() {}

d3_dispatch.prototype.on = function(type, listener) {
  var i = type.indexOf("."),
      name = "";

  // Extract optional namespace, e.g., "click.foo"
  if (i > 0) {
    name = type.substring(i + 1);
    type = type.substring(0, i);
  }

  return arguments.length < 2
      ? this[type].on(name)
      : this[type].on(name, listener);
};

function d3_dispatch_event(dispatch) {
  var listeners = [],
      listenerByName = new d3_Map;

  function event() {
    var z = listeners, // defensive reference
        i = -1,
        n = z.length,
        l;
    while (++i < n) if (l = z[i].on) l.apply(this, arguments);
    return dispatch;
  }

  event.on = function(name, listener) {
    var l = listenerByName.get(name),
        i;

    // return the current listener, if any
    if (arguments.length < 2) return l && l.on;

    // remove the old listener, if any (with copy-on-write)
    if (l) {
      l.on = null;
      listeners = listeners.slice(0, i = listeners.indexOf(l)).concat(listeners.slice(i + 1));
      listenerByName.remove(name);
    }

    // add the new listener, if any
    if (listener) listeners.push(listenerByName.set(name, {on: listener}));

    return dispatch;
  };

  return event;
}
// TODO align
d3.format = function(specifier) {
  var match = d3_format_re.exec(specifier),
      fill = match[1] || " ",
      sign = match[3] || "",
      zfill = match[5],
      width = +match[6],
      comma = match[7],
      precision = match[8],
      type = match[9],
      scale = 1,
      suffix = "",
      integer = false;

  if (precision) precision = +precision.substring(1);

  if (zfill) {
    fill = "0"; // TODO align = "=";
    if (comma) width -= Math.floor((width - 1) / 4);
  }

  switch (type) {
    case "n": comma = true; type = "g"; break;
    case "%": scale = 100; suffix = "%"; type = "f"; break;
    case "p": scale = 100; suffix = "%"; type = "r"; break;
    case "d": integer = true; precision = 0; break;
    case "s": scale = -1; type = "r"; break;
  }

  // If no precision is specified for r, fallback to general notation.
  if (type == "r" && !precision) type = "g";

  type = d3_format_types.get(type) || d3_format_typeDefault;

  return function(value) {

    // Return the empty string for floats formatted as ints.
    if (integer && (value % 1)) return "";

    // Convert negative to positive, and record the sign prefix.
    var negative = (value < 0) && (value = -value) ? "\u2212" : sign;

    // Apply the scale, computing it from the value's exponent for si format.
    if (scale < 0) {
      var prefix = d3.formatPrefix(value, precision);
      value *= prefix.scale;
      suffix = prefix.symbol;
    } else {
      value *= scale;
    }

    // Convert to the desired precision.
    value = type(value, precision);

    // If the fill character is 0, the sign and group is applied after the fill.
    if (zfill) {
      var length = value.length + negative.length;
      if (length < width) value = new Array(width - length + 1).join(fill) + value;
      if (comma) value = d3_format_group(value);
      value = negative + value;
    }

    // Otherwise (e.g., space-filling), the sign and group is applied before.
    else {
      if (comma) value = d3_format_group(value);
      value = negative + value;
      var length = value.length;
      if (length < width) value = new Array(width - length + 1).join(fill) + value;
    }

    return value + suffix;
  };
};

// [[fill]align][sign][#][0][width][,][.precision][type]
var d3_format_re = /(?:([^{])?([<>=^]))?([+\- ])?(#)?(0)?([0-9]+)?(,)?(\.[0-9]+)?([a-zA-Z%])?/;

var d3_format_types = d3.map({
  g: function(x, p) { return x.toPrecision(p); },
  e: function(x, p) { return x.toExponential(p); },
  f: function(x, p) { return x.toFixed(p); },
  r: function(x, p) { return d3.round(x, p = d3_format_precision(x, p)).toFixed(Math.max(0, Math.min(20, p))); }
});

function d3_format_precision(x, p) {
  return p - (x ? 1 + Math.floor(Math.log(x + Math.pow(10, 1 + Math.floor(Math.log(x) / Math.LN10) - p)) / Math.LN10) : 1);
}

function d3_format_typeDefault(x) {
  return x + "";
}

// Apply comma grouping for thousands.
function d3_format_group(value) {
  var i = value.lastIndexOf("."),
      f = i >= 0 ? value.substring(i) : (i = value.length, ""),
      t = [];
  while (i > 0) t.push(value.substring(i -= 3, i + 3));
  return t.reverse().join(",") + f;
}
var d3_formatPrefixes = ["y","z","a","f","p","n","μ","m","","k","M","G","T","P","E","Z","Y"].map(d3_formatPrefix);

d3.formatPrefix = function(value, precision) {
  var i = 0;
  if (value) {
    if (value < 0) value *= -1;
    if (precision) value = d3.round(value, d3_format_precision(value, precision));
    i = 1 + Math.floor(1e-12 + Math.log(value) / Math.LN10);
    i = Math.max(-24, Math.min(24, Math.floor((i <= 0 ? i + 1 : i - 1) / 3) * 3));
  }
  return d3_formatPrefixes[8 + i / 3];
};

function d3_formatPrefix(d, i) {
  return {
    scale: Math.pow(10, (8 - i) * 3),
    symbol: d
  };
}

/*
 * TERMS OF USE - EASING EQUATIONS
 *
 * Open source under the BSD License.
 *
 * Copyright 2001 Robert Penner
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * - Redistributions of source code must retain the above copyright notice, this
 *   list of conditions and the following disclaimer.
 *
 * - Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * - Neither the name of the author nor the names of contributors may be used to
 *   endorse or promote products derived from this software without specific
 *   prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

var d3_ease_quad = d3_ease_poly(2),
    d3_ease_cubic = d3_ease_poly(3),
    d3_ease_default = function() { return d3_ease_identity; };

var d3_ease = d3.map({
  linear: d3_ease_default,
  poly: d3_ease_poly,
  quad: function() { return d3_ease_quad; },
  cubic: function() { return d3_ease_cubic; },
  sin: function() { return d3_ease_sin; },
  exp: function() { return d3_ease_exp; },
  circle: function() { return d3_ease_circle; },
  elastic: d3_ease_elastic,
  back: d3_ease_back,
  bounce: function() { return d3_ease_bounce; }
});

var d3_ease_mode = d3.map({
  "in": d3_ease_identity,
  "out": d3_ease_reverse,
  "in-out": d3_ease_reflect,
  "out-in": function(f) { return d3_ease_reflect(d3_ease_reverse(f)); }
});

d3.ease = function(name) {
  var i = name.indexOf("-"),
      t = i >= 0 ? name.substring(0, i) : name,
      m = i >= 0 ? name.substring(i + 1) : "in";
  t = d3_ease.get(t) || d3_ease_default;
  m = d3_ease_mode.get(m) || d3_ease_identity;
  return d3_ease_clamp(m(t.apply(null, Array.prototype.slice.call(arguments, 1))));
};

function d3_ease_clamp(f) {
  return function(t) {
    return t <= 0 ? 0 : t >= 1 ? 1 : f(t);
  };
}

function d3_ease_reverse(f) {
  return function(t) {
    return 1 - f(1 - t);
  };
}

function d3_ease_reflect(f) {
  return function(t) {
    return .5 * (t < .5 ? f(2 * t) : (2 - f(2 - 2 * t)));
  };
}

function d3_ease_identity(t) {
  return t;
}

function d3_ease_poly(e) {
  return function(t) {
    return Math.pow(t, e);
  };
}

function d3_ease_sin(t) {
  return 1 - Math.cos(t * Math.PI / 2);
}

function d3_ease_exp(t) {
  return Math.pow(2, 10 * (t - 1));
}

function d3_ease_circle(t) {
  return 1 - Math.sqrt(1 - t * t);
}

function d3_ease_elastic(a, p) {
  var s;
  if (arguments.length < 2) p = 0.45;
  if (arguments.length < 1) { a = 1; s = p / 4; }
  else s = p / (2 * Math.PI) * Math.asin(1 / a);
  return function(t) {
    return 1 + a * Math.pow(2, 10 * -t) * Math.sin((t - s) * 2 * Math.PI / p);
  };
}

function d3_ease_back(s) {
  if (!s) s = 1.70158;
  return function(t) {
    return t * t * ((s + 1) * t - s);
  };
}

function d3_ease_bounce(t) {
  return t < 1 / 2.75 ? 7.5625 * t * t
      : t < 2 / 2.75 ? 7.5625 * (t -= 1.5 / 2.75) * t + .75
      : t < 2.5 / 2.75 ? 7.5625 * (t -= 2.25 / 2.75) * t + .9375
      : 7.5625 * (t -= 2.625 / 2.75) * t + .984375;
}
d3.event = null;

function d3_eventCancel() {
  d3.event.stopPropagation();
  d3.event.preventDefault();
}

function d3_eventSource() {
  var e = d3.event, s;
  while (s = e.sourceEvent) e = s;
  return e;
}

// Like d3.dispatch, but for custom events abstracting native UI events. These
// events have a target component (such as a brush), a target element (such as
// the svg:g element containing the brush) and the standard arguments `d` (the
// target element's data) and `i` (the selection index of the target element).
function d3_eventDispatch(target) {
  var dispatch = new d3_dispatch,
      i = 0,
      n = arguments.length;

  while (++i < n) dispatch[arguments[i]] = d3_dispatch_event(dispatch);

  // Creates a dispatch context for the specified `thiz` (typically, the target
  // DOM element that received the source event) and `argumentz` (typically, the
  // data `d` and index `i` of the target element). The returned function can be
  // used to dispatch an event to any registered listeners; the function takes a
  // single argument as input, being the event to dispatch. The event must have
  // a "type" attribute which corresponds to a type registered in the
  // constructor. This context will automatically populate the "sourceEvent" and
  // "target" attributes of the event, as well as setting the `d3.event` global
  // for the duration of the notification.
  dispatch.of = function(thiz, argumentz) {
    return function(e1) {
      try {
        var e0 =
        e1.sourceEvent = d3.event;
        e1.target = target;
        d3.event = e1;
        dispatch[e1.type].apply(thiz, argumentz);
      } finally {
        d3.event = e0;
      }
    };
  };

  return dispatch;
}
d3.interpolate = function(a, b) {
  var i = d3.interpolators.length, f;
  while (--i >= 0 && !(f = d3.interpolators[i](a, b)));
  return f;
};

d3.interpolateNumber = function(a, b) {
  b -= a;
  return function(t) { return a + b * t; };
};

d3.interpolateRound = function(a, b) {
  b -= a;
  return function(t) { return Math.round(a + b * t); };
};

d3.interpolateString = function(a, b) {
  var m, // current match
      i, // current index
      j, // current index (for coallescing)
      s0 = 0, // start index of current string prefix
      s1 = 0, // end index of current string prefix
      s = [], // string constants and placeholders
      q = [], // number interpolators
      n, // q.length
      o;

  // Reset our regular expression!
  d3_interpolate_number.lastIndex = 0;

  // Find all numbers in b.
  for (i = 0; m = d3_interpolate_number.exec(b); ++i) {
    if (m.index) s.push(b.substring(s0, s1 = m.index));
    q.push({i: s.length, x: m[0]});
    s.push(null);
    s0 = d3_interpolate_number.lastIndex;
  }
  if (s0 < b.length) s.push(b.substring(s0));

  // Find all numbers in a.
  for (i = 0, n = q.length; (m = d3_interpolate_number.exec(a)) && i < n; ++i) {
    o = q[i];
    if (o.x == m[0]) { // The numbers match, so coallesce.
      if (o.i) {
        if (s[o.i + 1] == null) { // This match is followed by another number.
          s[o.i - 1] += o.x;
          s.splice(o.i, 1);
          for (j = i + 1; j < n; ++j) q[j].i--;
        } else { // This match is followed by a string, so coallesce twice.
          s[o.i - 1] += o.x + s[o.i + 1];
          s.splice(o.i, 2);
          for (j = i + 1; j < n; ++j) q[j].i -= 2;
        }
      } else {
          if (s[o.i + 1] == null) { // This match is followed by another number.
          s[o.i] = o.x;
        } else { // This match is followed by a string, so coallesce twice.
          s[o.i] = o.x + s[o.i + 1];
          s.splice(o.i + 1, 1);
          for (j = i + 1; j < n; ++j) q[j].i--;
        }
      }
      q.splice(i, 1);
      n--;
      i--;
    } else {
      o.x = d3.interpolateNumber(parseFloat(m[0]), parseFloat(o.x));
    }
  }

  // Remove any numbers in b not found in a.
  while (i < n) {
    o = q.pop();
    if (s[o.i + 1] == null) { // This match is followed by another number.
      s[o.i] = o.x;
    } else { // This match is followed by a string, so coallesce twice.
      s[o.i] = o.x + s[o.i + 1];
      s.splice(o.i + 1, 1);
    }
    n--;
  }

  // Special optimization for only a single match.
  if (s.length === 1) {
    return s[0] == null ? q[0].x : function() { return b; };
  }

  // Otherwise, interpolate each of the numbers and rejoin the string.
  return function(t) {
    for (i = 0; i < n; ++i) s[(o = q[i]).i] = o.x(t);
    return s.join("");
  };
};

d3.interpolateTransform = function(a, b) {
  var s = [], // string constants and placeholders
      q = [], // number interpolators
      n,
      A = d3.transform(a),
      B = d3.transform(b),
      ta = A.translate,
      tb = B.translate,
      ra = A.rotate,
      rb = B.rotate,
      wa = A.skew,
      wb = B.skew,
      ka = A.scale,
      kb = B.scale;

  if (ta[0] != tb[0] || ta[1] != tb[1]) {
    s.push("translate(", null, ",", null, ")");
    q.push({i: 1, x: d3.interpolateNumber(ta[0], tb[0])}, {i: 3, x: d3.interpolateNumber(ta[1], tb[1])});
  } else if (tb[0] || tb[1]) {
    s.push("translate(" + tb + ")");
  } else {
    s.push("");
  }

  if (ra != rb) {
    q.push({i: s.push(s.pop() + "rotate(", null, ")") - 2, x: d3.interpolateNumber(ra, rb)});
  } else if (rb) {
    s.push(s.pop() + "rotate(" + rb + ")");
  }

  if (wa != wb) {
    q.push({i: s.push(s.pop() + "skewX(", null, ")") - 2, x: d3.interpolateNumber(wa, wb)});
  } else if (wb) {
    s.push(s.pop() + "skewX(" + wb + ")");
  }

  if (ka[0] != kb[0] || ka[1] != kb[1]) {
    n = s.push(s.pop() + "scale(", null, ",", null, ")");
    q.push({i: n - 4, x: d3.interpolateNumber(ka[0], kb[0])}, {i: n - 2, x: d3.interpolateNumber(ka[1], kb[1])});
  } else if (kb[0] != 1 || kb[1] != 1) {
    s.push(s.pop() + "scale(" + kb + ")");
  }

  n = q.length;
  return function(t) {
    var i = -1, o;
    while (++i < n) s[(o = q[i]).i] = o.x(t);
    return s.join("");
  };
};

d3.interpolateRgb = function(a, b) {
  a = d3.rgb(a);
  b = d3.rgb(b);
  var ar = a.r,
      ag = a.g,
      ab = a.b,
      br = b.r - ar,
      bg = b.g - ag,
      bb = b.b - ab;
  return function(t) {
    return "#"
        + d3_rgb_hex(Math.round(ar + br * t))
        + d3_rgb_hex(Math.round(ag + bg * t))
        + d3_rgb_hex(Math.round(ab + bb * t));
  };
};

// interpolates HSL space, but outputs RGB string (for compatibility)
d3.interpolateHsl = function(a, b) {
  a = d3.hsl(a);
  b = d3.hsl(b);
  var h0 = a.h,
      s0 = a.s,
      l0 = a.l,
      h1 = b.h - h0,
      s1 = b.s - s0,
      l1 = b.l - l0;
  return function(t) {
    return d3_hsl_rgb(h0 + h1 * t, s0 + s1 * t, l0 + l1 * t).toString();
  };
};

d3.interpolateArray = function(a, b) {
  var x = [],
      c = [],
      na = a.length,
      nb = b.length,
      n0 = Math.min(a.length, b.length),
      i;
  for (i = 0; i < n0; ++i) x.push(d3.interpolate(a[i], b[i]));
  for (; i < na; ++i) c[i] = a[i];
  for (; i < nb; ++i) c[i] = b[i];
  return function(t) {
    for (i = 0; i < n0; ++i) c[i] = x[i](t);
    return c;
  };
};

d3.interpolateObject = function(a, b) {
  var i = {},
      c = {},
      k;
  for (k in a) {
    if (k in b) {
      i[k] = d3_interpolateByName(k)(a[k], b[k]);
    } else {
      c[k] = a[k];
    }
  }
  for (k in b) {
    if (!(k in a)) {
      c[k] = b[k];
    }
  }
  return function(t) {
    for (k in i) c[k] = i[k](t);
    return c;
  };
}

var d3_interpolate_number = /[-+]?(?:\d*\.?\d+)(?:[eE][-+]?\d+)?/g;

function d3_interpolateByName(n) {
  return n == "transform"
      ? d3.interpolateTransform
      : d3.interpolate;
}

d3.interpolators = [
  d3.interpolateObject,
  function(a, b) { return (b instanceof Array) && d3.interpolateArray(a, b); },
  function(a, b) { return (typeof a === "string" || typeof b === "string") && d3.interpolateString(a + "", b + ""); },
  function(a, b) { return (typeof b === "string" ? d3_rgb_names.has(b) || /^(#|rgb\(|hsl\()/.test(b) : b instanceof d3_Rgb || b instanceof d3_Hsl) && d3.interpolateRgb(a, b); },
  function(a, b) { return !isNaN(a = +a) && !isNaN(b = +b) && d3.interpolateNumber(a, b); }
];
function d3_uninterpolateNumber(a, b) {
  b = b - (a = +a) ? 1 / (b - a) : 0;
  return function(x) { return (x - a) * b; };
}

function d3_uninterpolateClamp(a, b) {
  b = b - (a = +a) ? 1 / (b - a) : 0;
  return function(x) { return Math.max(0, Math.min(1, (x - a) * b)); };
}
d3.rgb = function(r, g, b) {
  return arguments.length === 1
      ? (r instanceof d3_Rgb ? d3_rgb(r.r, r.g, r.b)
      : d3_rgb_parse("" + r, d3_rgb, d3_hsl_rgb))
      : d3_rgb(~~r, ~~g, ~~b);
};

function d3_rgb(r, g, b) {
  return new d3_Rgb(r, g, b);
}

function d3_Rgb(r, g, b) {
  this.r = r;
  this.g = g;
  this.b = b;
}

d3_Rgb.prototype.brighter = function(k) {
  k = Math.pow(0.7, arguments.length ? k : 1);
  var r = this.r,
      g = this.g,
      b = this.b,
      i = 30;
  if (!r && !g && !b) return d3_rgb(i, i, i);
  if (r && r < i) r = i;
  if (g && g < i) g = i;
  if (b && b < i) b = i;
  return d3_rgb(
      Math.min(255, Math.floor(r / k)),
      Math.min(255, Math.floor(g / k)),
      Math.min(255, Math.floor(b / k)));
};

d3_Rgb.prototype.darker = function(k) {
  k = Math.pow(0.7, arguments.length ? k : 1);
  return d3_rgb(
      Math.floor(k * this.r),
      Math.floor(k * this.g),
      Math.floor(k * this.b));
};

d3_Rgb.prototype.hsl = function() {
  return d3_rgb_hsl(this.r, this.g, this.b);
};

d3_Rgb.prototype.toString = function() {
  return "#" + d3_rgb_hex(this.r) + d3_rgb_hex(this.g) + d3_rgb_hex(this.b);
};

function d3_rgb_hex(v) {
  return v < 0x10
      ? "0" + Math.max(0, v).toString(16)
      : Math.min(255, v).toString(16);
}

function d3_rgb_parse(format, rgb, hsl) {
  var r = 0, // red channel; int in [0, 255]
      g = 0, // green channel; int in [0, 255]
      b = 0, // blue channel; int in [0, 255]
      m1, // CSS color specification match
      m2, // CSS color specification type (e.g., rgb)
      name;

  /* Handle hsl, rgb. */
  m1 = /([a-z]+)\((.*)\)/i.exec(format);
  if (m1) {
    m2 = m1[2].split(",");
    switch (m1[1]) {
      case "hsl": {
        return hsl(
          parseFloat(m2[0]), // degrees
          parseFloat(m2[1]) / 100, // percentage
          parseFloat(m2[2]) / 100 // percentage
        );
      }
      case "rgb": {
        return rgb(
          d3_rgb_parseNumber(m2[0]),
          d3_rgb_parseNumber(m2[1]),
          d3_rgb_parseNumber(m2[2])
        );
      }
    }
  }

  /* Named colors. */
  if (name = d3_rgb_names.get(format)) return rgb(name.r, name.g, name.b);

  /* Hexadecimal colors: #rgb and #rrggbb. */
  if (format != null && format.charAt(0) === "#") {
    if (format.length === 4) {
      r = format.charAt(1); r += r;
      g = format.charAt(2); g += g;
      b = format.charAt(3); b += b;
    } else if (format.length === 7) {
      r = format.substring(1, 3);
      g = format.substring(3, 5);
      b = format.substring(5, 7);
    }
    r = parseInt(r, 16);
    g = parseInt(g, 16);
    b = parseInt(b, 16);
  }

  return rgb(r, g, b);
}

function d3_rgb_hsl(r, g, b) {
  var min = Math.min(r /= 255, g /= 255, b /= 255),
      max = Math.max(r, g, b),
      d = max - min,
      h,
      s,
      l = (max + min) / 2;
  if (d) {
    s = l < .5 ? d / (max + min) : d / (2 - max - min);
    if (r == max) h = (g - b) / d + (g < b ? 6 : 0);
    else if (g == max) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
  } else {
    s = h = 0;
  }
  return d3_hsl(h, s, l);
}

function d3_rgb_parseNumber(c) { // either integer or percentage
  var f = parseFloat(c);
  return c.charAt(c.length - 1) === "%" ? Math.round(f * 2.55) : f;
}

var d3_rgb_names = d3.map({
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
});

d3_rgb_names.forEach(function(key, value) {
  d3_rgb_names.set(key, d3_rgb_parse(value, d3_rgb, d3_hsl_rgb));
});
d3.hsl = function(h, s, l) {
  return arguments.length === 1
      ? (h instanceof d3_Hsl ? d3_hsl(h.h, h.s, h.l)
      : d3_rgb_parse("" + h, d3_rgb_hsl, d3_hsl))
      : d3_hsl(+h, +s, +l);
};

function d3_hsl(h, s, l) {
  return new d3_Hsl(h, s, l);
}

function d3_Hsl(h, s, l) {
  this.h = h;
  this.s = s;
  this.l = l;
}

d3_Hsl.prototype.brighter = function(k) {
  k = Math.pow(0.7, arguments.length ? k : 1);
  return d3_hsl(this.h, this.s, this.l / k);
};

d3_Hsl.prototype.darker = function(k) {
  k = Math.pow(0.7, arguments.length ? k : 1);
  return d3_hsl(this.h, this.s, k * this.l);
};

d3_Hsl.prototype.rgb = function() {
  return d3_hsl_rgb(this.h, this.s, this.l);
};

d3_Hsl.prototype.toString = function() {
  return this.rgb().toString();
};

function d3_hsl_rgb(h, s, l) {
  var m1,
      m2;

  /* Some simple corrections for h, s and l. */
  h = h % 360; if (h < 0) h += 360;
  s = s < 0 ? 0 : s > 1 ? 1 : s;
  l = l < 0 ? 0 : l > 1 ? 1 : l;

  /* From FvD 13.37, CSS Color Module Level 3 */
  m2 = l <= .5 ? l * (1 + s) : l + s - l * s;
  m1 = 2 * l - m2;

  function v(h) {
    if (h > 360) h -= 360;
    else if (h < 0) h += 360;
    if (h < 60) return m1 + (m2 - m1) * h / 60;
    if (h < 180) return m2;
    if (h < 240) return m1 + (m2 - m1) * (240 - h) / 60;
    return m1;
  }

  function vv(h) {
    return Math.round(v(h) * 255);
  }

  return d3_rgb(vv(h + 120), vv(h), vv(h - 120));
}
function d3_selection(groups) {
  d3_arraySubclass(groups, d3_selectionPrototype);
  return groups;
}

var d3_select = function(s, n) { return n.querySelector(s); },
    d3_selectAll = function(s, n) { return n.querySelectorAll(s); },
    d3_selectRoot = document.documentElement,
    d3_selectMatcher = d3_selectRoot.matchesSelector || d3_selectRoot.webkitMatchesSelector || d3_selectRoot.mozMatchesSelector || d3_selectRoot.msMatchesSelector || d3_selectRoot.oMatchesSelector,
    d3_selectMatches = function(n, s) { return d3_selectMatcher.call(n, s); };

// Prefer Sizzle, if available.
if (typeof Sizzle === "function") {
  d3_select = function(s, n) { return Sizzle(s, n)[0]; };
  d3_selectAll = function(s, n) { return Sizzle.uniqueSort(Sizzle(s, n)); };
  d3_selectMatches = Sizzle.matchesSelector;
}

var d3_selectionPrototype = [];

d3.selection = function() {
  return d3_selectionRoot;
};

d3.selection.prototype = d3_selectionPrototype;
d3_selectionPrototype.select = function(selector) {
  var subgroups = [],
      subgroup,
      subnode,
      group,
      node;

  if (typeof selector !== "function") selector = d3_selection_selector(selector);

  for (var j = -1, m = this.length; ++j < m;) {
    subgroups.push(subgroup = []);
    subgroup.parentNode = (group = this[j]).parentNode;
    for (var i = -1, n = group.length; ++i < n;) {
      if (node = group[i]) {
        subgroup.push(subnode = selector.call(node, node.__data__, i));
        if (subnode && "__data__" in node) subnode.__data__ = node.__data__;
      } else {
        subgroup.push(null);
      }
    }
  }

  return d3_selection(subgroups);
};

function d3_selection_selector(selector) {
  return function() {
    return d3_select(selector, this);
  };
}
d3_selectionPrototype.selectAll = function(selector) {
  var subgroups = [],
      subgroup,
      node;

  if (typeof selector !== "function") selector = d3_selection_selectorAll(selector);

  for (var j = -1, m = this.length; ++j < m;) {
    for (var group = this[j], i = -1, n = group.length; ++i < n;) {
      if (node = group[i]) {
        subgroups.push(subgroup = d3_array(selector.call(node, node.__data__, i)));
        subgroup.parentNode = node;
      }
    }
  }

  return d3_selection(subgroups);
};

function d3_selection_selectorAll(selector) {
  return function() {
    return d3_selectAll(selector, this);
  };
}
d3_selectionPrototype.attr = function(name, value) {
  name = d3.ns.qualify(name);

  // If no value is specified, return the first value.
  if (arguments.length < 2) {
    var node = this.node();
    return name.local
        ? node.getAttributeNS(name.space, name.local)
        : node.getAttribute(name);
  }

  function attrNull() {
    this.removeAttribute(name);
  }

  function attrNullNS() {
    this.removeAttributeNS(name.space, name.local);
  }

  function attrConstant() {
    this.setAttribute(name, value);
  }

  function attrConstantNS() {
    this.setAttributeNS(name.space, name.local, value);
  }

  function attrFunction() {
    var x = value.apply(this, arguments);
    if (x == null) this.removeAttribute(name);
    else this.setAttribute(name, x);
  }

  function attrFunctionNS() {
    var x = value.apply(this, arguments);
    if (x == null) this.removeAttributeNS(name.space, name.local);
    else this.setAttributeNS(name.space, name.local, x);
  }

  return this.each(value == null
      ? (name.local ? attrNullNS : attrNull) : (typeof value === "function"
      ? (name.local ? attrFunctionNS : attrFunction)
      : (name.local ? attrConstantNS : attrConstant)));
};
d3_selectionPrototype.classed = function(name, value) {
  var names = name.split(d3_selection_classedWhitespace),
      n = names.length,
      i = -1;
  if (arguments.length > 1) {
    while (++i < n) d3_selection_classed.call(this, names[i], value);
    return this;
  } else {
    while (++i < n) if (!d3_selection_classed.call(this, names[i])) return false;
    return true;
  }
};

var d3_selection_classedWhitespace = /\s+/g;

function d3_selection_classed(name, value) {
  var re = new RegExp("(^|\\s+)" + d3.requote(name) + "(\\s+|$)", "g");

  // If no value is specified, return the first value.
  if (arguments.length < 2) {
    var node = this.node();
    if (c = node.classList) return c.contains(name);
    var c = node.className;
    re.lastIndex = 0;
    return re.test(c.baseVal != null ? c.baseVal : c);
  }

  function classedAdd() {
    if (c = this.classList) return c.add(name);
    var c = this.className,
        cb = c.baseVal != null,
        cv = cb ? c.baseVal : c;
    re.lastIndex = 0;
    if (!re.test(cv)) {
      cv = d3_collapse(cv + " " + name);
      if (cb) c.baseVal = cv;
      else this.className = cv;
    }
  }

  function classedRemove() {
    if (c = this.classList) return c.remove(name);
    var c = this.className,
        cb = c.baseVal != null,
        cv = cb ? c.baseVal : c;
    cv = d3_collapse(cv.replace(re, " "));
    if (cb) c.baseVal = cv;
    else this.className = cv;
  }

  function classedFunction() {
    (value.apply(this, arguments)
        ? classedAdd
        : classedRemove).call(this);
  }

  return this.each(typeof value === "function"
      ? classedFunction : value
      ? classedAdd
      : classedRemove);
}
d3_selectionPrototype.style = function(name, value, priority) {
  if (arguments.length < 3) priority = "";

  // If no value is specified, return the first value.
  if (arguments.length < 2) return window
      .getComputedStyle(this.node(), null)
      .getPropertyValue(name);

  function styleNull() {
    this.style.removeProperty(name);
  }

  function styleConstant() {
    this.style.setProperty(name, value, priority);
  }

  function styleFunction() {
    var x = value.apply(this, arguments);
    if (x == null) this.style.removeProperty(name);
    else this.style.setProperty(name, x, priority);
  }

  return this.each(value == null
      ? styleNull : (typeof value === "function"
      ? styleFunction : styleConstant));
};
d3_selectionPrototype.property = function(name, value) {

  // If no value is specified, return the first value.
  if (arguments.length < 2) return this.node()[name];

  function propertyNull() {
    delete this[name];
  }

  function propertyConstant() {
    this[name] = value;
  }

  function propertyFunction() {
    var x = value.apply(this, arguments);
    if (x == null) delete this[name];
    else this[name] = x;
  }

  return this.each(value == null
      ? propertyNull : (typeof value === "function"
      ? propertyFunction : propertyConstant));
};
d3_selectionPrototype.text = function(value) {
  return arguments.length < 1
      ? this.node().textContent : this.each(typeof value === "function"
      ? function() { var v = value.apply(this, arguments); this.textContent = v == null ? "" : v; } : value == null
      ? function() { this.textContent = ""; }
      : function() { this.textContent = value; });
};
d3_selectionPrototype.html = function(value) {
  return arguments.length < 1
      ? this.node().innerHTML : this.each(typeof value === "function"
      ? function() { var v = value.apply(this, arguments); this.innerHTML = v == null ? "" : v; } : value == null
      ? function() { this.innerHTML = ""; }
      : function() { this.innerHTML = value; });
};
// TODO append(node)?
// TODO append(function)?
d3_selectionPrototype.append = function(name) {
  name = d3.ns.qualify(name);

  function append() {
    return this.appendChild(document.createElementNS(this.namespaceURI, name));
  }

  function appendNS() {
    return this.appendChild(document.createElementNS(name.space, name.local));
  }

  return this.select(name.local ? appendNS : append);
};
// TODO insert(node, function)?
// TODO insert(function, string)?
// TODO insert(function, function)?
d3_selectionPrototype.insert = function(name, before) {
  name = d3.ns.qualify(name);

  function insert() {
    return this.insertBefore(
        document.createElementNS(this.namespaceURI, name),
        d3_select(before, this));
  }

  function insertNS() {
    return this.insertBefore(
        document.createElementNS(name.space, name.local),
        d3_select(before, this));
  }

  return this.select(name.local ? insertNS : insert);
};
// TODO remove(selector)?
// TODO remove(node)?
// TODO remove(function)?
d3_selectionPrototype.remove = function() {
  return this.each(function() {
    var parent = this.parentNode;
    if (parent) parent.removeChild(this);
  });
};
d3_selectionPrototype.data = function(value, key) {
  var i = -1,
      n = this.length,
      group,
      node;

  // If no value is specified, return the first value.
  if (!arguments.length) {
    value = new Array(n = (group = this[0]).length);
    while (++i < n) {
      if (node = group[i]) {
        value[i] = node.__data__;
      }
    }
    return value;
  }

  function bind(group, groupData) {
    var i,
        n = group.length,
        m = groupData.length,
        n0 = Math.min(n, m),
        n1 = Math.max(n, m),
        updateNodes = [],
        enterNodes = [],
        exitNodes = [],
        node,
        nodeData;

    if (key) {
      var nodeByKeyValue = new d3_Map,
          keyValues = [],
          keyValue,
          j = groupData.length;

      for (i = -1; ++i < n;) {
        keyValue = key.call(node = group[i], node.__data__, i);
        if (nodeByKeyValue.has(keyValue)) {
          exitNodes[j++] = node; // duplicate key
        } else {
          nodeByKeyValue.set(keyValue, node);
        }
        keyValues.push(keyValue);
      }

      for (i = -1; ++i < m;) {
        keyValue = key.call(groupData, nodeData = groupData[i], i)
        if (nodeByKeyValue.has(keyValue)) {
          updateNodes[i] = node = nodeByKeyValue.get(keyValue);
          node.__data__ = nodeData;
          enterNodes[i] = exitNodes[i] = null;
        } else {
          enterNodes[i] = d3_selection_dataNode(nodeData);
          updateNodes[i] = exitNodes[i] = null;
        }
        nodeByKeyValue.remove(keyValue);
      }

      for (i = -1; ++i < n;) {
        if (nodeByKeyValue.has(keyValues[i])) {
          exitNodes[i] = group[i];
        }
      }
    } else {
      for (i = -1; ++i < n0;) {
        node = group[i];
        nodeData = groupData[i];
        if (node) {
          node.__data__ = nodeData;
          updateNodes[i] = node;
          enterNodes[i] = exitNodes[i] = null;
        } else {
          enterNodes[i] = d3_selection_dataNode(nodeData);
          updateNodes[i] = exitNodes[i] = null;
        }
      }
      for (; i < m; ++i) {
        enterNodes[i] = d3_selection_dataNode(groupData[i]);
        updateNodes[i] = exitNodes[i] = null;
      }
      for (; i < n1; ++i) {
        exitNodes[i] = group[i];
        enterNodes[i] = updateNodes[i] = null;
      }
    }

    enterNodes.update
        = updateNodes;

    enterNodes.parentNode
        = updateNodes.parentNode
        = exitNodes.parentNode
        = group.parentNode;

    enter.push(enterNodes);
    update.push(updateNodes);
    exit.push(exitNodes);
  }

  var enter = d3_selection_enter([]),
      update = d3_selection([]),
      exit = d3_selection([]);

  if (typeof value === "function") {
    while (++i < n) {
      bind(group = this[i], value.call(group, group.parentNode.__data__, i));
    }
  } else {
    while (++i < n) {
      bind(group = this[i], value);
    }
  }

  update.enter = function() { return enter; };
  update.exit = function() { return exit; };
  return update;
};

function d3_selection_dataNode(data) {
  return {__data__: data};
}
d3_selectionPrototype.datum =
d3_selectionPrototype.map = function(value) {
  return arguments.length < 1
      ? this.property("__data__")
      : this.property("__data__", value);
};
d3_selectionPrototype.filter = function(filter) {
  var subgroups = [],
      subgroup,
      group,
      node;

  if (typeof filter !== "function") filter = d3_selection_filter(filter);

  for (var j = 0, m = this.length; j < m; j++) {
    subgroups.push(subgroup = []);
    subgroup.parentNode = (group = this[j]).parentNode;
    for (var i = 0, n = group.length; i < n; i++) {
      if ((node = group[i]) && filter.call(node, node.__data__, i)) {
        subgroup.push(node);
      }
    }
  }

  return d3_selection(subgroups);
};

function d3_selection_filter(selector) {
  return function() {
    return d3_selectMatches(this, selector);
  };
}
d3_selectionPrototype.order = function() {
  for (var j = -1, m = this.length; ++j < m;) {
    for (var group = this[j], i = group.length - 1, next = group[i], node; --i >= 0;) {
      if (node = group[i]) {
        if (next && next !== node.nextSibling) next.parentNode.insertBefore(node, next);
        next = node;
      }
    }
  }
  return this;
};
d3_selectionPrototype.sort = function(comparator) {
  comparator = d3_selection_sortComparator.apply(this, arguments);
  for (var j = -1, m = this.length; ++j < m;) this[j].sort(comparator);
  return this.order();
};

function d3_selection_sortComparator(comparator) {
  if (!arguments.length) comparator = d3.ascending;
  return function(a, b) {
    return comparator(a && a.__data__, b && b.__data__);
  };
}
// type can be namespaced, e.g., "click.foo"
// listener can be null for removal
d3_selectionPrototype.on = function(type, listener, capture) {
  if (arguments.length < 3) capture = false;

  // parse the type specifier
  var name = "__on" + type, i = type.indexOf(".");
  if (i > 0) type = type.substring(0, i);

  // if called with only one argument, return the current listener
  if (arguments.length < 2) return (i = this.node()[name]) && i._;

  // remove the old event listener, and add the new event listener
  return this.each(function(d, i) {
    var node = this,
        o = node[name];

    // remove the old listener, if any (using the previously-set capture)
    if (o) {
      node.removeEventListener(type, o, o.$);
      delete node[name];
    }

    // add the new listener, if any (remembering the capture flag)
    if (listener) {
      node.addEventListener(type, node[name] = l, l.$ = capture);
      l._ = listener; // stash the unwrapped listener for get
    }

    // wrapped event listener that preserves i
    function l(e) {
      var o = d3.event; // Events can be reentrant (e.g., focus).
      d3.event = e;
      try {
        listener.call(node, node.__data__, i);
      } finally {
        d3.event = o;
      }
    }
  });
};
d3_selectionPrototype.each = function(callback) {
  for (var j = -1, m = this.length; ++j < m;) {
    for (var group = this[j], i = -1, n = group.length; ++i < n;) {
      var node = group[i];
      if (node) callback.call(node, node.__data__, i, j);
    }
  }
  return this;
};
//
// Note: assigning to the arguments array simultaneously changes the value of
// the corresponding argument!
//
// TODO The `this` argument probably shouldn't be the first argument to the
// callback, anyway, since it's redundant. However, that will require a major
// version bump due to backwards compatibility, so I'm not changing it right
// away.
//
d3_selectionPrototype.call = function(callback) {
  callback.apply(this, (arguments[0] = this, arguments));
  return this;
};
d3_selectionPrototype.empty = function() {
  return !this.node();
};
d3_selectionPrototype.node = function(callback) {
  for (var j = 0, m = this.length; j < m; j++) {
    for (var group = this[j], i = 0, n = group.length; i < n; i++) {
      var node = group[i];
      if (node) return node;
    }
  }
  return null;
};
d3_selectionPrototype.transition = function() {
  var subgroups = [],
      subgroup,
      node;

  for (var j = -1, m = this.length; ++j < m;) {
    subgroups.push(subgroup = []);
    for (var group = this[j], i = -1, n = group.length; ++i < n;) {
      subgroup.push((node = group[i]) ? {node: node, delay: d3_transitionDelay, duration: d3_transitionDuration} : null);
    }
  }

  return d3_transition(subgroups, d3_transitionId || ++d3_transitionNextId, Date.now());
};
var d3_selectionRoot = d3_selection([[document]]);

d3_selectionRoot[0].parentNode = d3_selectRoot;

// TODO fast singleton implementation!
// TODO select(function)
d3.select = function(selector) {
  return typeof selector === "string"
      ? d3_selectionRoot.select(selector)
      : d3_selection([[selector]]); // assume node
};

// TODO selectAll(function)
d3.selectAll = function(selector) {
  return typeof selector === "string"
      ? d3_selectionRoot.selectAll(selector)
      : d3_selection([d3_array(selector)]); // assume node[]
};
function d3_selection_enter(selection) {
  d3_arraySubclass(selection, d3_selection_enterPrototype);
  return selection;
}

var d3_selection_enterPrototype = [];

d3.selection.enter = d3_selection_enter;
d3.selection.enter.prototype = d3_selection_enterPrototype;

d3_selection_enterPrototype.append = d3_selectionPrototype.append;
d3_selection_enterPrototype.insert = d3_selectionPrototype.insert;
d3_selection_enterPrototype.empty = d3_selectionPrototype.empty;
d3_selection_enterPrototype.node = d3_selectionPrototype.node;
d3_selection_enterPrototype.select = function(selector) {
  var subgroups = [],
      subgroup,
      subnode,
      upgroup,
      group,
      node;

  for (var j = -1, m = this.length; ++j < m;) {
    upgroup = (group = this[j]).update;
    subgroups.push(subgroup = []);
    subgroup.parentNode = group.parentNode;
    for (var i = -1, n = group.length; ++i < n;) {
      if (node = group[i]) {
        subgroup.push(upgroup[i] = subnode = selector.call(group.parentNode, node.__data__, i));
        subnode.__data__ = node.__data__;
      } else {
        subgroup.push(null);
      }
    }
  }

  return d3_selection(subgroups);
};
function d3_transition(groups, id, time) {
  d3_arraySubclass(groups, d3_transitionPrototype);

  var tweens = new d3_Map,
      event = d3.dispatch("start", "end"),
      ease = d3_transitionEase;

  groups.id = id;

  groups.time = time;

  groups.tween = function(name, tween) {
    if (arguments.length < 2) return tweens.get(name);
    if (tween == null) tweens.remove(name);
    else tweens.set(name, tween);
    return groups;
  };

  groups.ease = function(value) {
    if (!arguments.length) return ease;
    ease = typeof value === "function" ? value : d3.ease.apply(d3, arguments);
    return groups;
  };

  groups.each = function(type, listener) {
    if (arguments.length < 2) return d3_transition_each.call(groups, type);
    event.on(type, listener);
    return groups;
  };

  d3.timer(function(elapsed) {
    groups.each(function(d, i, j) {
      var tweened = [],
          node = this,
          delay = groups[j][i].delay,
          duration = groups[j][i].duration,
          lock = node.__transition__ || (node.__transition__ = {active: 0, count: 0});

      ++lock.count;

      delay <= elapsed ? start(elapsed) : d3.timer(start, delay, time);

      function start(elapsed) {
        if (lock.active > id) return stop();
        lock.active = id;

        tweens.forEach(function(key, value) {
          if (tween = value.call(node, d, i)) {
            tweened.push(tween);
          }
        });

        event.start.call(node, d, i);
        if (!tick(elapsed)) d3.timer(tick, 0, time);
        return 1;
      }

      function tick(elapsed) {
        if (lock.active !== id) return stop();

        var t = (elapsed - delay) / duration,
            e = ease(t),
            n = tweened.length;

        while (n > 0) {
          tweened[--n].call(node, e);
        }

        if (t >= 1) {
          stop();
          d3_transitionId = id;
          event.end.call(node, d, i);
          d3_transitionId = 0;
          return 1;
        }
      }

      function stop() {
        if (!--lock.count) delete node.__transition__;
        return 1;
      }
    });
    return 1;
  }, 0, time);

  return groups;
}

var d3_transitionRemove = {};

function d3_transitionNull(d, i, a) {
  return a != "" && d3_transitionRemove;
}

function d3_transitionTween(name, b) {
  var interpolate = d3_interpolateByName(name);

  function transitionFunction(d, i, a) {
    var v = b.call(this, d, i);
    return v == null
        ? a != "" && d3_transitionRemove
        : a != v && interpolate(a, v);
  }

  function transitionString(d, i, a) {
    return a != b && interpolate(a, b);
  }

  return typeof b === "function" ? transitionFunction
      : b == null ? d3_transitionNull
      : (b += "", transitionString);
}

var d3_transitionPrototype = [],
    d3_transitionNextId = 0,
    d3_transitionId = 0,
    d3_transitionDefaultDelay = 0,
    d3_transitionDefaultDuration = 250,
    d3_transitionDefaultEase = d3.ease("cubic-in-out"),
    d3_transitionDelay = d3_transitionDefaultDelay,
    d3_transitionDuration = d3_transitionDefaultDuration,
    d3_transitionEase = d3_transitionDefaultEase;

d3_transitionPrototype.call = d3_selectionPrototype.call;

d3.transition = function(selection) {
  return arguments.length
      ? (d3_transitionId ? selection.transition() : selection)
      : d3_selectionRoot.transition();
};

d3.transition.prototype = d3_transitionPrototype;
d3_transitionPrototype.select = function(selector) {
  var subgroups = [],
      subgroup,
      subnode,
      node;

  if (typeof selector !== "function") selector = d3_selection_selector(selector);

  for (var j = -1, m = this.length; ++j < m;) {
    subgroups.push(subgroup = []);
    for (var group = this[j], i = -1, n = group.length; ++i < n;) {
      if ((node = group[i]) && (subnode = selector.call(node.node, node.node.__data__, i))) {
        if ("__data__" in node.node) subnode.__data__ = node.node.__data__;
        subgroup.push({node: subnode, delay: node.delay, duration: node.duration});
      } else {
        subgroup.push(null);
      }
    }
  }

  return d3_transition(subgroups, this.id, this.time).ease(this.ease());
};
d3_transitionPrototype.selectAll = function(selector) {
  var subgroups = [],
      subgroup,
      subnodes,
      node;

  if (typeof selector !== "function") selector = d3_selection_selectorAll(selector);

  for (var j = -1, m = this.length; ++j < m;) {
    for (var group = this[j], i = -1, n = group.length; ++i < n;) {
      if (node = group[i]) {
        subnodes = selector.call(node.node, node.node.__data__, i);
        subgroups.push(subgroup = []);
        for (var k = -1, o = subnodes.length; ++k < o;) {
          subgroup.push({node: subnodes[k], delay: node.delay, duration: node.duration});
        }
      }
    }
  }

  return d3_transition(subgroups, this.id, this.time).ease(this.ease());
};
d3_transitionPrototype.attr = function(name, value) {
  return this.attrTween(name, d3_transitionTween(name, value));
};

d3_transitionPrototype.attrTween = function(nameNS, tween) {
  var name = d3.ns.qualify(nameNS);

  function attrTween(d, i) {
    var f = tween.call(this, d, i, this.getAttribute(name));
    return f === d3_transitionRemove
        ? (this.removeAttribute(name), null)
        : f && function(t) { this.setAttribute(name, f(t)); };
  }

  function attrTweenNS(d, i) {
    var f = tween.call(this, d, i, this.getAttributeNS(name.space, name.local));
    return f === d3_transitionRemove
        ? (this.removeAttributeNS(name.space, name.local), null)
        : f && function(t) { this.setAttributeNS(name.space, name.local, f(t)); };
  }

  return this.tween("attr." + nameNS, name.local ? attrTweenNS : attrTween);
};
d3_transitionPrototype.style = function(name, value, priority) {
  if (arguments.length < 3) priority = "";
  return this.styleTween(name, d3_transitionTween(name, value), priority);
};

d3_transitionPrototype.styleTween = function(name, tween, priority) {
  if (arguments.length < 3) priority = "";
  return this.tween("style." + name, function(d, i) {
    var f = tween.call(this, d, i, window.getComputedStyle(this, null).getPropertyValue(name));
    return f === d3_transitionRemove
        ? (this.style.removeProperty(name), null)
        : f && function(t) { this.style.setProperty(name, f(t), priority); };
  });
};
d3_transitionPrototype.text = function(value) {
  return this.tween("text", function(d, i) {
    this.textContent = typeof value === "function"
        ? value.call(this, d, i)
        : value;
  });
};
d3_transitionPrototype.remove = function() {
  return this.each("end.transition", function() {
    var p;
    if (!this.__transition__ && (p = this.parentNode)) p.removeChild(this);
  });
};
d3_transitionPrototype.delay = function(value) {
  var groups = this;
  return groups.each(typeof value === "function"
      ? function(d, i, j) { groups[j][i].delay = value.apply(this, arguments) | 0; }
      : (value = value | 0, function(d, i, j) { groups[j][i].delay = value; }));
};
d3_transitionPrototype.duration = function(value) {
  var groups = this;
  return groups.each(typeof value === "function"
      ? function(d, i, j) { groups[j][i].duration = Math.max(1, value.apply(this, arguments) | 0); }
      : (value = Math.max(1, value | 0), function(d, i, j) { groups[j][i].duration = value; }));
};
function d3_transition_each(callback) {
  var id = d3_transitionId,
      ease = d3_transitionEase,
      delay = d3_transitionDelay,
      duration = d3_transitionDuration;

  d3_transitionId = this.id;
  d3_transitionEase = this.ease();
  for (var j = 0, m = this.length; j < m; j++) {
    for (var group = this[j], i = 0, n = group.length; i < n; i++) {
      var node = group[i];
      if (node) {
        d3_transitionDelay = this[j][i].delay;
        d3_transitionDuration = this[j][i].duration;
        callback.call(node = node.node, node.__data__, i, j);
      }
    }
  }

  d3_transitionId = id;
  d3_transitionEase = ease;
  d3_transitionDelay = delay;
  d3_transitionDuration = duration;
  return this;
}
d3_transitionPrototype.transition = function() {
  return this.select(d3_this);
};
var d3_timer_queue = null,
    d3_timer_interval, // is an interval (or frame) active?
    d3_timer_timeout; // is a timeout active?

// The timer will continue to fire until callback returns true.
d3.timer = function(callback, delay, then) {
  var found = false,
      t0,
      t1 = d3_timer_queue;

  if (arguments.length < 3) {
    if (arguments.length < 2) delay = 0;
    else if (!isFinite(delay)) return;
    then = Date.now();
  }

  // See if the callback's already in the queue.
  while (t1) {
    if (t1.callback === callback) {
      t1.then = then;
      t1.delay = delay;
      found = true;
      break;
    }
    t0 = t1;
    t1 = t1.next;
  }

  // Otherwise, add the callback to the queue.
  if (!found) d3_timer_queue = {
    callback: callback,
    then: then,
    delay: delay,
    next: d3_timer_queue
  };

  // Start animatin'!
  if (!d3_timer_interval) {
    d3_timer_timeout = clearTimeout(d3_timer_timeout);
    d3_timer_interval = 1;
    d3_timer_frame(d3_timer_step);
  }
}

function d3_timer_step() {
  var elapsed,
      now = Date.now(),
      t1 = d3_timer_queue;

  while (t1) {
    elapsed = now - t1.then;
    if (elapsed >= t1.delay) t1.flush = t1.callback(elapsed);
    t1 = t1.next;
  }

  var delay = d3_timer_flush() - now;
  if (delay > 24) {
    if (isFinite(delay)) {
      clearTimeout(d3_timer_timeout);
      d3_timer_timeout = setTimeout(d3_timer_step, delay);
    }
    d3_timer_interval = 0;
  } else {
    d3_timer_interval = 1;
    d3_timer_frame(d3_timer_step);
  }
}

d3.timer.flush = function() {
  var elapsed,
      now = Date.now(),
      t1 = d3_timer_queue;

  while (t1) {
    elapsed = now - t1.then;
    if (!t1.delay) t1.flush = t1.callback(elapsed);
    t1 = t1.next;
  }

  d3_timer_flush();
};

// Flush after callbacks, to avoid concurrent queue modification.
function d3_timer_flush() {
  var t0 = null,
      t1 = d3_timer_queue,
      then = Infinity;
  while (t1) {
    if (t1.flush) {
      t1 = t0 ? t0.next = t1.next : d3_timer_queue = t1.next;
    } else {
      then = Math.min(then, t1.then + t1.delay);
      t1 = (t0 = t1).next;
    }
  }
  return then;
}

var d3_timer_frame = window.requestAnimationFrame
    || window.webkitRequestAnimationFrame
    || window.mozRequestAnimationFrame
    || window.oRequestAnimationFrame
    || window.msRequestAnimationFrame
    || function(callback) { setTimeout(callback, 17); };
d3.transform = function(string) {
  var g = document.createElementNS(d3.ns.prefix.svg, "g"),
      identity = {a: 1, b: 0, c: 0, d: 1, e: 0, f: 0};
  return (d3.transform = function(string) {
    g.setAttribute("transform", string);
    var t = g.transform.baseVal.consolidate();
    return new d3_transform(t ? t.matrix : identity);
  })(string);
};

// Compute x-scale and normalize the first row.
// Compute shear and make second row orthogonal to first.
// Compute y-scale and normalize the second row.
// Finally, compute the rotation.
function d3_transform(m) {
  var r0 = [m.a, m.b],
      r1 = [m.c, m.d],
      kx = d3_transformNormalize(r0),
      kz = d3_transformDot(r0, r1),
      ky = d3_transformNormalize(d3_transformCombine(r1, r0, -kz)) || 0;
  if (r0[0] * r1[1] < r1[0] * r0[1]) {
    r0[0] *= -1;
    r0[1] *= -1;
    kx *= -1;
    kz *= -1;
  }
  this.rotate = (kx ? Math.atan2(r0[1], r0[0]) : Math.atan2(-r1[0], r1[1])) * d3_transformDegrees;
  this.translate = [m.e, m.f];
  this.scale = [kx, ky];
  this.skew = ky ? Math.atan2(kz, ky) * d3_transformDegrees : 0;
};

d3_transform.prototype.toString = function() {
  return "translate(" + this.translate
      + ")rotate(" + this.rotate
      + ")skewX(" + this.skew
      + ")scale(" + this.scale
      + ")";
};

function d3_transformDot(a, b) {
  return a[0] * b[0] + a[1] * b[1];
}

function d3_transformNormalize(a) {
  var k = Math.sqrt(d3_transformDot(a, a));
  if (k) {
    a[0] /= k;
    a[1] /= k;
  }
  return k;
}

function d3_transformCombine(a, b, k) {
  a[0] += k * b[0];
  a[1] += k * b[1];
  return a;
}

var d3_transformDegrees = 180 / Math.PI;
d3.mouse = function(container) {
  return d3_mousePoint(container, d3_eventSource());
};

// https://bugs.webkit.org/show_bug.cgi?id=44083
var d3_mouse_bug44083 = /WebKit/.test(navigator.userAgent) ? -1 : 0;

function d3_mousePoint(container, e) {
  var svg = container.ownerSVGElement || container;
  if (svg.createSVGPoint) {
    var point = svg.createSVGPoint();
    if ((d3_mouse_bug44083 < 0) && (window.scrollX || window.scrollY)) {
      svg = d3.select(document.body)
        .append("svg")
          .style("position", "absolute")
          .style("top", 0)
          .style("left", 0);
      var ctm = svg[0][0].getScreenCTM();
      d3_mouse_bug44083 = !(ctm.f || ctm.e);
      svg.remove();
    }
    if (d3_mouse_bug44083) {
      point.x = e.pageX;
      point.y = e.pageY;
    } else {
      point.x = e.clientX;
      point.y = e.clientY;
    }
    point = point.matrixTransform(container.getScreenCTM().inverse());
    return [point.x, point.y];
  }
  var rect = container.getBoundingClientRect();
  return [e.clientX - rect.left - container.clientLeft, e.clientY - rect.top - container.clientTop];
};
d3.touches = function(container, touches) {
  if (arguments.length < 2) touches = d3_eventSource().touches;
  return touches ? d3_array(touches).map(function(touch) {
    var point = d3_mousePoint(container, touch);
    point.identifier = touch.identifier;
    return point;
  }) : [];
};
function d3_noop() {}
d3.scale = {};

function d3_scaleExtent(domain) {
  var start = domain[0], stop = domain[domain.length - 1];
  return start < stop ? [start, stop] : [stop, start];
}

function d3_scaleRange(scale) {
  return scale.rangeExtent ? scale.rangeExtent() : d3_scaleExtent(scale.range());
}
function d3_scale_nice(domain, nice) {
  var i0 = 0,
      i1 = domain.length - 1,
      x0 = domain[i0],
      x1 = domain[i1],
      dx;

  if (x1 < x0) {
    dx = i0; i0 = i1; i1 = dx;
    dx = x0; x0 = x1; x1 = dx;
  }

  if (dx = x1 - x0) {
    nice = nice(dx);
    domain[i0] = nice.floor(x0);
    domain[i1] = nice.ceil(x1);
  }

  return domain;
}

function d3_scale_niceDefault() {
  return Math;
}
d3.scale.linear = function() {
  return d3_scale_linear([0, 1], [0, 1], d3.interpolate, false);
};

function d3_scale_linear(domain, range, interpolate, clamp) {
  var output,
      input;

  function rescale() {
    var linear = Math.min(domain.length, range.length) > 2 ? d3_scale_polylinear : d3_scale_bilinear,
        uninterpolate = clamp ? d3_uninterpolateClamp : d3_uninterpolateNumber;
    output = linear(domain, range, uninterpolate, interpolate);
    input = linear(range, domain, uninterpolate, d3.interpolate);
    return scale;
  }

  function scale(x) {
    return output(x);
  }

  // Note: requires range is coercible to number!
  scale.invert = function(y) {
    return input(y);
  };

  scale.domain = function(x) {
    if (!arguments.length) return domain;
    domain = x.map(Number);
    return rescale();
  };

  scale.range = function(x) {
    if (!arguments.length) return range;
    range = x;
    return rescale();
  };

  scale.rangeRound = function(x) {
    return scale.range(x).interpolate(d3.interpolateRound);
  };

  scale.clamp = function(x) {
    if (!arguments.length) return clamp;
    clamp = x;
    return rescale();
  };

  scale.interpolate = function(x) {
    if (!arguments.length) return interpolate;
    interpolate = x;
    return rescale();
  };

  scale.ticks = function(m) {
    return d3_scale_linearTicks(domain, m);
  };

  scale.tickFormat = function(m) {
    return d3_scale_linearTickFormat(domain, m);
  };

  scale.nice = function() {
    d3_scale_nice(domain, d3_scale_linearNice);
    return rescale();
  };

  scale.copy = function() {
    return d3_scale_linear(domain, range, interpolate, clamp);
  };

  return rescale();
}

function d3_scale_linearRebind(scale, linear) {
  return d3.rebind(scale, linear, "range", "rangeRound", "interpolate", "clamp");
}

function d3_scale_linearNice(dx) {
  dx = Math.pow(10, Math.round(Math.log(dx) / Math.LN10) - 1);
  return {
    floor: function(x) { return Math.floor(x / dx) * dx; },
    ceil: function(x) { return Math.ceil(x / dx) * dx; }
  };
}

function d3_scale_linearTickRange(domain, m) {
  var extent = d3_scaleExtent(domain),
      span = extent[1] - extent[0],
      step = Math.pow(10, Math.floor(Math.log(span / m) / Math.LN10)),
      err = m / span * step;

  // Filter ticks to get closer to the desired count.
  if (err <= .15) step *= 10;
  else if (err <= .35) step *= 5;
  else if (err <= .75) step *= 2;

  // Round start and stop values to step interval.
  extent[0] = Math.ceil(extent[0] / step) * step;
  extent[1] = Math.floor(extent[1] / step) * step + step * .5; // inclusive
  extent[2] = step;
  return extent;
}

function d3_scale_linearTicks(domain, m) {
  return d3.range.apply(d3, d3_scale_linearTickRange(domain, m));
}

function d3_scale_linearTickFormat(domain, m) {
  return d3.format(",." + Math.max(0, -Math.floor(Math.log(d3_scale_linearTickRange(domain, m)[2]) / Math.LN10 + .01)) + "f");
}
function d3_scale_bilinear(domain, range, uninterpolate, interpolate) {
  var u = uninterpolate(domain[0], domain[1]),
      i = interpolate(range[0], range[1]);
  return function(x) {
    return i(u(x));
  };
}
function d3_scale_polylinear(domain, range, uninterpolate, interpolate) {
  var u = [],
      i = [],
      j = 0,
      k = Math.min(domain.length, range.length) - 1;

  // Handle descending domains.
  if (domain[k] < domain[0]) {
    domain = domain.slice().reverse();
    range = range.slice().reverse();
  }

  while (++j <= k) {
    u.push(uninterpolate(domain[j - 1], domain[j]));
    i.push(interpolate(range[j - 1], range[j]));
  }

  return function(x) {
    var j = d3.bisect(domain, x, 1, k) - 1;
    return i[j](u[j](x));
  };
}
d3.scale.log = function() {
  return d3_scale_log(d3.scale.linear(), d3_scale_logp);
};

function d3_scale_log(linear, log) {
  var pow = log.pow;

  function scale(x) {
    return linear(log(x));
  }

  scale.invert = function(x) {
    return pow(linear.invert(x));
  };

  scale.domain = function(x) {
    if (!arguments.length) return linear.domain().map(pow);
    log = x[0] < 0 ? d3_scale_logn : d3_scale_logp;
    pow = log.pow;
    linear.domain(x.map(log));
    return scale;
  };

  scale.nice = function() {
    linear.domain(d3_scale_nice(linear.domain(), d3_scale_niceDefault));
    return scale;
  };

  scale.ticks = function() {
    var extent = d3_scaleExtent(linear.domain()),
        ticks = [];
    if (extent.every(isFinite)) {
      var i = Math.floor(extent[0]),
          j = Math.ceil(extent[1]),
          u = pow(extent[0]),
          v = pow(extent[1]);
      if (log === d3_scale_logn) {
        ticks.push(pow(i));
        for (; i++ < j;) for (var k = 9; k > 0; k--) ticks.push(pow(i) * k);
      } else {
        for (; i < j; i++) for (var k = 1; k < 10; k++) ticks.push(pow(i) * k);
        ticks.push(pow(i));
      }
      for (i = 0; ticks[i] < u; i++) {} // strip small values
      for (j = ticks.length; ticks[j - 1] > v; j--) {} // strip big values
      ticks = ticks.slice(i, j);
    }
    return ticks;
  };

  scale.tickFormat = function(n, format) {
    if (arguments.length < 2) format = d3_scale_logFormat;
    if (arguments.length < 1) return format;
    var k = n / scale.ticks().length,
        f = log === d3_scale_logn ? (e = -1e-12, Math.floor) : (e = 1e-12, Math.ceil),
        e;
    return function(d) {
      return d / pow(f(log(d) + e)) < k ? format(d) : "";
    };
  };

  scale.copy = function() {
    return d3_scale_log(linear.copy(), log);
  };

  return d3_scale_linearRebind(scale, linear);
}

var d3_scale_logFormat = d3.format(".0e");

function d3_scale_logp(x) {
  return Math.log(x < 0 ? 0 : x) / Math.LN10;
}

function d3_scale_logn(x) {
  return -Math.log(x > 0 ? 0 : -x) / Math.LN10;
}

d3_scale_logp.pow = function(x) {
  return Math.pow(10, x);
};

d3_scale_logn.pow = function(x) {
  return -Math.pow(10, -x);
};
d3.scale.pow = function() {
  return d3_scale_pow(d3.scale.linear(), 1);
};

function d3_scale_pow(linear, exponent) {
  var powp = d3_scale_powPow(exponent),
      powb = d3_scale_powPow(1 / exponent);

  function scale(x) {
    return linear(powp(x));
  }

  scale.invert = function(x) {
    return powb(linear.invert(x));
  };

  scale.domain = function(x) {
    if (!arguments.length) return linear.domain().map(powb);
    linear.domain(x.map(powp));
    return scale;
  };

  scale.ticks = function(m) {
    return d3_scale_linearTicks(scale.domain(), m);
  };

  scale.tickFormat = function(m) {
    return d3_scale_linearTickFormat(scale.domain(), m);
  };

  scale.nice = function() {
    return scale.domain(d3_scale_nice(scale.domain(), d3_scale_linearNice));
  };

  scale.exponent = function(x) {
    if (!arguments.length) return exponent;
    var domain = scale.domain();
    powp = d3_scale_powPow(exponent = x);
    powb = d3_scale_powPow(1 / exponent);
    return scale.domain(domain);
  };

  scale.copy = function() {
    return d3_scale_pow(linear.copy(), exponent);
  };

  return d3_scale_linearRebind(scale, linear);
}

function d3_scale_powPow(e) {
  return function(x) {
    return x < 0 ? -Math.pow(-x, e) : Math.pow(x, e);
  };
}
d3.scale.sqrt = function() {
  return d3.scale.pow().exponent(.5);
};
d3.scale.ordinal = function() {
  return d3_scale_ordinal([], {t: "range", x: []});
};

function d3_scale_ordinal(domain, ranger) {
  var index,
      range,
      rangeBand;

  function scale(x) {
    return range[((index.get(x) || index.set(x, domain.push(x))) - 1) % range.length];
  }

  function steps(start, step) {
    return d3.range(domain.length).map(function(i) { return start + step * i; });
  }

  scale.domain = function(x) {
    if (!arguments.length) return domain;
    domain = [];
    index = new d3_Map;
    var i = -1, n = x.length, xi;
    while (++i < n) if (!index.has(xi = x[i])) index.set(xi, domain.push(xi));
    return scale[ranger.t](ranger.x, ranger.p);
  };

  scale.range = function(x) {
    if (!arguments.length) return range;
    range = x;
    rangeBand = 0;
    ranger = {t: "range", x: x};
    return scale;
  };

  scale.rangePoints = function(x, padding) {
    if (arguments.length < 2) padding = 0;
    var start = x[0],
        stop = x[1],
        step = (stop - start) / (domain.length - 1 + padding);
    range = steps(domain.length < 2 ? (start + stop) / 2 : start + step * padding / 2, step);
    rangeBand = 0;
    ranger = {t: "rangePoints", x: x, p: padding};
    return scale;
  };

  scale.rangeBands = function(x, padding) {
    if (arguments.length < 2) padding = 0;
    var reverse = x[1] < x[0],
        start = x[reverse - 0],
        stop = x[1 - reverse],
        step = (stop - start) / (domain.length + padding);
    range = steps(start + step * padding, step);
    if (reverse) range.reverse();
    rangeBand = step * (1 - padding);
    ranger = {t: "rangeBands", x: x, p: padding};
    return scale;
  };

  scale.rangeRoundBands = function(x, padding) {
    if (arguments.length < 2) padding = 0;
    var reverse = x[1] < x[0],
        start = x[reverse - 0],
        stop = x[1 - reverse],
        step = Math.floor((stop - start) / (domain.length + padding)),
        error = stop - start - (domain.length - padding) * step;
    range = steps(start + Math.round(error / 2), step);
    if (reverse) range.reverse();
    rangeBand = Math.round(step * (1 - padding));
    ranger = {t: "rangeRoundBands", x: x, p: padding};
    return scale;
  };

  scale.rangeBand = function() {
    return rangeBand;
  };

  scale.rangeExtent = function() {
    return d3_scaleExtent(ranger.x);
  };

  scale.copy = function() {
    return d3_scale_ordinal(domain, ranger);
  };

  return scale.domain(domain);
}
/*
 * This product includes color specifications and designs developed by Cynthia
 * Brewer (http://colorbrewer.org/). See lib/colorbrewer for more information.
 */

d3.scale.category10 = function() {
  return d3.scale.ordinal().range(d3_category10);
};

d3.scale.category20 = function() {
  return d3.scale.ordinal().range(d3_category20);
};

d3.scale.category20b = function() {
  return d3.scale.ordinal().range(d3_category20b);
};

d3.scale.category20c = function() {
  return d3.scale.ordinal().range(d3_category20c);
};

var d3_category10 = [
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
];

var d3_category20 = [
  "#1f77b4", "#aec7e8",
  "#ff7f0e", "#ffbb78",
  "#2ca02c", "#98df8a",
  "#d62728", "#ff9896",
  "#9467bd", "#c5b0d5",
  "#8c564b", "#c49c94",
  "#e377c2", "#f7b6d2",
  "#7f7f7f", "#c7c7c7",
  "#bcbd22", "#dbdb8d",
  "#17becf", "#9edae5"
];

var d3_category20b = [
  "#393b79", "#5254a3", "#6b6ecf", "#9c9ede",
  "#637939", "#8ca252", "#b5cf6b", "#cedb9c",
  "#8c6d31", "#bd9e39", "#e7ba52", "#e7cb94",
  "#843c39", "#ad494a", "#d6616b", "#e7969c",
  "#7b4173", "#a55194", "#ce6dbd", "#de9ed6"
];

var d3_category20c = [
  "#3182bd", "#6baed6", "#9ecae1", "#c6dbef",
  "#e6550d", "#fd8d3c", "#fdae6b", "#fdd0a2",
  "#31a354", "#74c476", "#a1d99b", "#c7e9c0",
  "#756bb1", "#9e9ac8", "#bcbddc", "#dadaeb",
  "#636363", "#969696", "#bdbdbd", "#d9d9d9"
];
d3.scale.quantile = function() {
  return d3_scale_quantile([], []);
};

function d3_scale_quantile(domain, range) {
  var thresholds;

  function rescale() {
    var k = 0,
        n = domain.length,
        q = range.length;
    thresholds = [];
    while (++k < q) thresholds[k - 1] = d3.quantile(domain, k / q);
    return scale;
  }

  function scale(x) {
    if (isNaN(x = +x)) return NaN;
    return range[d3.bisect(thresholds, x)];
  }

  scale.domain = function(x) {
    if (!arguments.length) return domain;
    domain = x.filter(function(d) { return !isNaN(d); }).sort(d3.ascending);
    return rescale();
  };

  scale.range = function(x) {
    if (!arguments.length) return range;
    range = x;
    return rescale();
  };

  scale.quantiles = function() {
    return thresholds;
  };

  scale.copy = function() {
    return d3_scale_quantile(domain, range); // copy on write!
  };

  return rescale();
}
d3.scale.quantize = function() {
  return d3_scale_quantize(0, 1, [0, 1]);
};

function d3_scale_quantize(x0, x1, range) {
  var kx, i;

  function scale(x) {
    return range[Math.max(0, Math.min(i, Math.floor(kx * (x - x0))))];
  }

  function rescale() {
    kx = range.length / (x1 - x0);
    i = range.length - 1;
    return scale;
  }

  scale.domain = function(x) {
    if (!arguments.length) return [x0, x1];
    x0 = +x[0];
    x1 = +x[x.length - 1];
    return rescale();
  };

  scale.range = function(x) {
    if (!arguments.length) return range;
    range = x;
    return rescale();
  };

  scale.copy = function() {
    return d3_scale_quantize(x0, x1, range); // copy on write
  };

  return rescale();
}
d3.scale.identity = function() {
  return d3_scale_identity([0, 1]);
};

function d3_scale_identity(domain) {

  function identity(x) { return +x; }

  identity.invert = identity;

  identity.domain = identity.range = function(x) {
    if (!arguments.length) return domain;
    domain = x.map(identity);
    return identity;
  };

  identity.ticks = function(m) {
    return d3_scale_linearTicks(domain, m);
  };

  identity.tickFormat = function(m) {
    return d3_scale_linearTickFormat(domain, m);
  };

  identity.copy = function() {
    return d3_scale_identity(domain);
  };

  return identity;
}
d3.svg = {};
d3.svg.arc = function() {
  var innerRadius = d3_svg_arcInnerRadius,
      outerRadius = d3_svg_arcOuterRadius,
      startAngle = d3_svg_arcStartAngle,
      endAngle = d3_svg_arcEndAngle;

  function arc() {
    var r0 = innerRadius.apply(this, arguments),
        r1 = outerRadius.apply(this, arguments),
        a0 = startAngle.apply(this, arguments) + d3_svg_arcOffset,
        a1 = endAngle.apply(this, arguments) + d3_svg_arcOffset,
        da = (a1 < a0 && (da = a0, a0 = a1, a1 = da), a1 - a0),
        df = da < Math.PI ? "0" : "1",
        c0 = Math.cos(a0),
        s0 = Math.sin(a0),
        c1 = Math.cos(a1),
        s1 = Math.sin(a1);
    return da >= d3_svg_arcMax
      ? (r0
      ? "M0," + r1
      + "A" + r1 + "," + r1 + " 0 1,1 0," + (-r1)
      + "A" + r1 + "," + r1 + " 0 1,1 0," + r1
      + "M0," + r0
      + "A" + r0 + "," + r0 + " 0 1,0 0," + (-r0)
      + "A" + r0 + "," + r0 + " 0 1,0 0," + r0
      + "Z"
      : "M0," + r1
      + "A" + r1 + "," + r1 + " 0 1,1 0," + (-r1)
      + "A" + r1 + "," + r1 + " 0 1,1 0," + r1
      + "Z")
      : (r0
      ? "M" + r1 * c0 + "," + r1 * s0
      + "A" + r1 + "," + r1 + " 0 " + df + ",1 " + r1 * c1 + "," + r1 * s1
      + "L" + r0 * c1 + "," + r0 * s1
      + "A" + r0 + "," + r0 + " 0 " + df + ",0 " + r0 * c0 + "," + r0 * s0
      + "Z"
      : "M" + r1 * c0 + "," + r1 * s0
      + "A" + r1 + "," + r1 + " 0 " + df + ",1 " + r1 * c1 + "," + r1 * s1
      + "L0,0"
      + "Z");
  }

  arc.innerRadius = function(v) {
    if (!arguments.length) return innerRadius;
    innerRadius = d3.functor(v);
    return arc;
  };

  arc.outerRadius = function(v) {
    if (!arguments.length) return outerRadius;
    outerRadius = d3.functor(v);
    return arc;
  };

  arc.startAngle = function(v) {
    if (!arguments.length) return startAngle;
    startAngle = d3.functor(v);
    return arc;
  };

  arc.endAngle = function(v) {
    if (!arguments.length) return endAngle;
    endAngle = d3.functor(v);
    return arc;
  };

  arc.centroid = function() {
    var r = (innerRadius.apply(this, arguments)
        + outerRadius.apply(this, arguments)) / 2,
        a = (startAngle.apply(this, arguments)
        + endAngle.apply(this, arguments)) / 2 + d3_svg_arcOffset;
    return [Math.cos(a) * r, Math.sin(a) * r];
  };

  return arc;
};

var d3_svg_arcOffset = -Math.PI / 2,
    d3_svg_arcMax = 2 * Math.PI - 1e-6;

function d3_svg_arcInnerRadius(d) {
  return d.innerRadius;
}

function d3_svg_arcOuterRadius(d) {
  return d.outerRadius;
}

function d3_svg_arcStartAngle(d) {
  return d.startAngle;
}

function d3_svg_arcEndAngle(d) {
  return d.endAngle;
}
function d3_svg_line(projection) {
  var x = d3_svg_lineX,
      y = d3_svg_lineY,
      interpolate = d3_svg_lineInterpolatorDefault,
      interpolator = d3_svg_lineInterpolators.get(interpolate),
      tension = .7;

  function line(d) {
    return d.length < 1 ? null : "M" + interpolator(projection(d3_svg_linePoints(this, d, x, y)), tension);
  }

  line.x = function(v) {
    if (!arguments.length) return x;
    x = v;
    return line;
  };

  line.y = function(v) {
    if (!arguments.length) return y;
    y = v;
    return line;
  };

  line.interpolate = function(v) {
    if (!arguments.length) return interpolate;
    if (!d3_svg_lineInterpolators.has(v += "")) v = d3_svg_lineInterpolatorDefault;
    interpolator = d3_svg_lineInterpolators.get(interpolate = v);
    return line;
  };

  line.tension = function(v) {
    if (!arguments.length) return tension;
    tension = v;
    return line;
  };

  return line;
}

d3.svg.line = function() {
  return d3_svg_line(Object);
};

// Converts the specified array of data into an array of points
// (x-y tuples), by evaluating the specified `x` and `y` functions on each
// data point. The `this` context of the evaluated functions is the specified
// "self" object; each function is passed the current datum and index.
function d3_svg_linePoints(self, d, x, y) {
  var points = [],
      i = -1,
      n = d.length,
      fx = typeof x === "function",
      fy = typeof y === "function",
      value;
  if (fx && fy) {
    while (++i < n) points.push([
      x.call(self, value = d[i], i),
      y.call(self, value, i)
    ]);
  } else if (fx) {
    while (++i < n) points.push([x.call(self, d[i], i), y]);
  } else if (fy) {
    while (++i < n) points.push([x, y.call(self, d[i], i)]);
  } else {
    while (++i < n) points.push([x, y]);
  }
  return points;
}

// The default `x` property, which references d[0].
function d3_svg_lineX(d) {
  return d[0];
}

// The default `y` property, which references d[1].
function d3_svg_lineY(d) {
  return d[1];
}

var d3_svg_lineInterpolatorDefault = "linear";

// The various interpolators supported by the `line` class.
var d3_svg_lineInterpolators = d3.map({
  "linear": d3_svg_lineLinear,
  "step-before": d3_svg_lineStepBefore,
  "step-after": d3_svg_lineStepAfter,
  "basis": d3_svg_lineBasis,
  "basis-open": d3_svg_lineBasisOpen,
  "basis-closed": d3_svg_lineBasisClosed,
  "bundle": d3_svg_lineBundle,
  "cardinal": d3_svg_lineCardinal,
  "cardinal-open": d3_svg_lineCardinalOpen,
  "cardinal-closed": d3_svg_lineCardinalClosed,
  "monotone": d3_svg_lineMonotone
});

// Linear interpolation; generates "L" commands.
function d3_svg_lineLinear(points) {
  var i = 0,
      n = points.length,
      p = points[0],
      path = [p[0], ",", p[1]];
  while (++i < n) path.push("L", (p = points[i])[0], ",", p[1]);
  return path.join("");
}

// Step interpolation; generates "H" and "V" commands.
function d3_svg_lineStepBefore(points) {
  var i = 0,
      n = points.length,
      p = points[0],
      path = [p[0], ",", p[1]];
  while (++i < n) path.push("V", (p = points[i])[1], "H", p[0]);
  return path.join("");
}

// Step interpolation; generates "H" and "V" commands.
function d3_svg_lineStepAfter(points) {
  var i = 0,
      n = points.length,
      p = points[0],
      path = [p[0], ",", p[1]];
  while (++i < n) path.push("H", (p = points[i])[0], "V", p[1]);
  return path.join("");
}

// Open cardinal spline interpolation; generates "C" commands.
function d3_svg_lineCardinalOpen(points, tension) {
  return points.length < 4
      ? d3_svg_lineLinear(points)
      : points[1] + d3_svg_lineHermite(points.slice(1, points.length - 1),
        d3_svg_lineCardinalTangents(points, tension));
}

// Closed cardinal spline interpolation; generates "C" commands.
function d3_svg_lineCardinalClosed(points, tension) {
  return points.length < 3
      ? d3_svg_lineLinear(points)
      : points[0] + d3_svg_lineHermite((points.push(points[0]), points),
        d3_svg_lineCardinalTangents([points[points.length - 2]]
        .concat(points, [points[1]]), tension));
}

// Cardinal spline interpolation; generates "C" commands.
function d3_svg_lineCardinal(points, tension, closed) {
  return points.length < 3
      ? d3_svg_lineLinear(points)
      : points[0] + d3_svg_lineHermite(points,
        d3_svg_lineCardinalTangents(points, tension));
}

// Hermite spline construction; generates "C" commands.
function d3_svg_lineHermite(points, tangents) {
  if (tangents.length < 1
      || (points.length != tangents.length
      && points.length != tangents.length + 2)) {
    return d3_svg_lineLinear(points);
  }

  var quad = points.length != tangents.length,
      path = "",
      p0 = points[0],
      p = points[1],
      t0 = tangents[0],
      t = t0,
      pi = 1;

  if (quad) {
    path += "Q" + (p[0] - t0[0] * 2 / 3) + "," + (p[1] - t0[1] * 2 / 3)
        + "," + p[0] + "," + p[1];
    p0 = points[1];
    pi = 2;
  }

  if (tangents.length > 1) {
    t = tangents[1];
    p = points[pi];
    pi++;
    path += "C" + (p0[0] + t0[0]) + "," + (p0[1] + t0[1])
        + "," + (p[0] - t[0]) + "," + (p[1] - t[1])
        + "," + p[0] + "," + p[1];
    for (var i = 2; i < tangents.length; i++, pi++) {
      p = points[pi];
      t = tangents[i];
      path += "S" + (p[0] - t[0]) + "," + (p[1] - t[1])
          + "," + p[0] + "," + p[1];
    }
  }

  if (quad) {
    var lp = points[pi];
    path += "Q" + (p[0] + t[0] * 2 / 3) + "," + (p[1] + t[1] * 2 / 3)
        + "," + lp[0] + "," + lp[1];
  }

  return path;
}

// Generates tangents for a cardinal spline.
function d3_svg_lineCardinalTangents(points, tension) {
  var tangents = [],
      a = (1 - tension) / 2,
      p0,
      p1 = points[0],
      p2 = points[1],
      i = 1,
      n = points.length;
  while (++i < n) {
    p0 = p1;
    p1 = p2;
    p2 = points[i];
    tangents.push([a * (p2[0] - p0[0]), a * (p2[1] - p0[1])]);
  }
  return tangents;
}

// B-spline interpolation; generates "C" commands.
function d3_svg_lineBasis(points) {
  if (points.length < 3) return d3_svg_lineLinear(points);
  var i = 1,
      n = points.length,
      pi = points[0],
      x0 = pi[0],
      y0 = pi[1],
      px = [x0, x0, x0, (pi = points[1])[0]],
      py = [y0, y0, y0, pi[1]],
      path = [x0, ",", y0];
  d3_svg_lineBasisBezier(path, px, py);
  while (++i < n) {
    pi = points[i];
    px.shift(); px.push(pi[0]);
    py.shift(); py.push(pi[1]);
    d3_svg_lineBasisBezier(path, px, py);
  }
  i = -1;
  while (++i < 2) {
    px.shift(); px.push(pi[0]);
    py.shift(); py.push(pi[1]);
    d3_svg_lineBasisBezier(path, px, py);
  }
  return path.join("");
}

// Open B-spline interpolation; generates "C" commands.
function d3_svg_lineBasisOpen(points) {
  if (points.length < 4) return d3_svg_lineLinear(points);
  var path = [],
      i = -1,
      n = points.length,
      pi,
      px = [0],
      py = [0];
  while (++i < 3) {
    pi = points[i];
    px.push(pi[0]);
    py.push(pi[1]);
  }
  path.push(d3_svg_lineDot4(d3_svg_lineBasisBezier3, px)
    + "," + d3_svg_lineDot4(d3_svg_lineBasisBezier3, py));
  --i; while (++i < n) {
    pi = points[i];
    px.shift(); px.push(pi[0]);
    py.shift(); py.push(pi[1]);
    d3_svg_lineBasisBezier(path, px, py);
  }
  return path.join("");
}

// Closed B-spline interpolation; generates "C" commands.
function d3_svg_lineBasisClosed(points) {
  var path,
      i = -1,
      n = points.length,
      m = n + 4,
      pi,
      px = [],
      py = [];
  while (++i < 4) {
    pi = points[i % n];
    px.push(pi[0]);
    py.push(pi[1]);
  }
  path = [
    d3_svg_lineDot4(d3_svg_lineBasisBezier3, px), ",",
    d3_svg_lineDot4(d3_svg_lineBasisBezier3, py)
  ];
  --i; while (++i < m) {
    pi = points[i % n];
    px.shift(); px.push(pi[0]);
    py.shift(); py.push(pi[1]);
    d3_svg_lineBasisBezier(path, px, py);
  }
  return path.join("");
}

function d3_svg_lineBundle(points, tension) {
  var n = points.length - 1,
      x0 = points[0][0],
      y0 = points[0][1],
      dx = points[n][0] - x0,
      dy = points[n][1] - y0,
      i = -1,
      p,
      t;
  while (++i <= n) {
    p = points[i];
    t = i / n;
    p[0] = tension * p[0] + (1 - tension) * (x0 + t * dx);
    p[1] = tension * p[1] + (1 - tension) * (y0 + t * dy);
  }
  return d3_svg_lineBasis(points);
}

// Returns the dot product of the given four-element vectors.
function d3_svg_lineDot4(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
}

// Matrix to transform basis (b-spline) control points to bezier
// control points. Derived from FvD 11.2.8.
var d3_svg_lineBasisBezier1 = [0, 2/3, 1/3, 0],
    d3_svg_lineBasisBezier2 = [0, 1/3, 2/3, 0],
    d3_svg_lineBasisBezier3 = [0, 1/6, 2/3, 1/6];

// Pushes a "C" Bézier curve onto the specified path array, given the
// two specified four-element arrays which define the control points.
function d3_svg_lineBasisBezier(path, x, y) {
  path.push(
      "C", d3_svg_lineDot4(d3_svg_lineBasisBezier1, x),
      ",", d3_svg_lineDot4(d3_svg_lineBasisBezier1, y),
      ",", d3_svg_lineDot4(d3_svg_lineBasisBezier2, x),
      ",", d3_svg_lineDot4(d3_svg_lineBasisBezier2, y),
      ",", d3_svg_lineDot4(d3_svg_lineBasisBezier3, x),
      ",", d3_svg_lineDot4(d3_svg_lineBasisBezier3, y));
}

// Computes the slope from points p0 to p1.
function d3_svg_lineSlope(p0, p1) {
  return (p1[1] - p0[1]) / (p1[0] - p0[0]);
}

// Compute three-point differences for the given points.
// http://en.wikipedia.org/wiki/Cubic_Hermite_spline#Finite_difference
function d3_svg_lineFiniteDifferences(points) {
  var i = 0,
      j = points.length - 1,
      m = [],
      p0 = points[0],
      p1 = points[1],
      d = m[0] = d3_svg_lineSlope(p0, p1);
  while (++i < j) {
    m[i] = d + (d = d3_svg_lineSlope(p0 = p1, p1 = points[i + 1]));
  }
  m[i] = d;
  return m;
}

// Interpolates the given points using Fritsch-Carlson Monotone cubic Hermite
// interpolation. Returns an array of tangent vectors. For details, see
// http://en.wikipedia.org/wiki/Monotone_cubic_interpolation
function d3_svg_lineMonotoneTangents(points) {
  var tangents = [],
      d,
      a,
      b,
      s,
      m = d3_svg_lineFiniteDifferences(points),
      i = -1,
      j = points.length - 1;

  // The first two steps are done by computing finite-differences:
  // 1. Compute the slopes of the secant lines between successive points.
  // 2. Initialize the tangents at every point as the average of the secants.

  // Then, for each segment…
  while (++i < j) {
    d = d3_svg_lineSlope(points[i], points[i + 1]);

    // 3. If two successive yk = y{k + 1} are equal (i.e., d is zero), then set
    // mk = m{k + 1} = 0 as the spline connecting these points must be flat to
    // preserve monotonicity. Ignore step 4 and 5 for those k.

    if (Math.abs(d) < 1e-6) {
      m[i] = m[i + 1] = 0;
    } else {
      // 4. Let ak = mk / dk and bk = m{k + 1} / dk.
      a = m[i] / d;
      b = m[i + 1] / d;

      // 5. Prevent overshoot and ensure monotonicity by restricting the
      // magnitude of vector <ak, bk> to a circle of radius 3.
      s = a * a + b * b;
      if (s > 9) {
        s = d * 3 / Math.sqrt(s);
        m[i] = s * a;
        m[i + 1] = s * b;
      }
    }
  }

  // Compute the normalized tangent vector from the slopes. Note that if x is
  // not monotonic, it's possible that the slope will be infinite, so we protect
  // against NaN by setting the coordinate to zero.
  i = -1; while (++i <= j) {
    s = (points[Math.min(j, i + 1)][0] - points[Math.max(0, i - 1)][0])
      / (6 * (1 + m[i] * m[i]));
    tangents.push([s || 0, m[i] * s || 0]);
  }

  return tangents;
}

function d3_svg_lineMonotone(points) {
  return points.length < 3
      ? d3_svg_lineLinear(points)
      : points[0] +
        d3_svg_lineHermite(points, d3_svg_lineMonotoneTangents(points));
}
d3.svg.line.radial = function() {
  var line = d3_svg_line(d3_svg_lineRadial);
  line.radius = line.x, delete line.x;
  line.angle = line.y, delete line.y;
  return line;
};

function d3_svg_lineRadial(points) {
  var point,
      i = -1,
      n = points.length,
      r,
      a;
  while (++i < n) {
    point = points[i];
    r = point[0];
    a = point[1] + d3_svg_arcOffset;
    point[0] = r * Math.cos(a);
    point[1] = r * Math.sin(a);
  }
  return points;
}
function d3_svg_area(projection) {
  var x0 = d3_svg_lineX,
      x1 = d3_svg_lineX,
      y0 = 0,
      y1 = d3_svg_lineY,
      interpolate,
      i0,
      i1,
      tension = .7;

  function area(d) {
    if (d.length < 1) return null;
    var points0 = d3_svg_linePoints(this, d, x0, y0),
        points1 = d3_svg_linePoints(this, d, x0 === x1 ? d3_svg_areaX(points0) : x1, y0 === y1 ? d3_svg_areaY(points0) : y1);
    return "M" + i0(projection(points1), tension)
         + "L" + i1(projection(points0.reverse()), tension)
         + "Z";
  }

  area.x = function(x) {
    if (!arguments.length) return x1;
    x0 = x1 = x;
    return area;
  };

  area.x0 = function(x) {
    if (!arguments.length) return x0;
    x0 = x;
    return area;
  };

  area.x1 = function(x) {
    if (!arguments.length) return x1;
    x1 = x;
    return area;
  };

  area.y = function(y) {
    if (!arguments.length) return y1;
    y0 = y1 = y;
    return area;
  };

  area.y0 = function(y) {
    if (!arguments.length) return y0;
    y0 = y;
    return area;
  };

  area.y1 = function(y) {
    if (!arguments.length) return y1;
    y1 = y;
    return area;
  };

  area.interpolate = function(x) {
    if (!arguments.length) return interpolate;
    if (!d3_svg_lineInterpolators.has(x += "")) x = d3_svg_lineInterpolatorDefault;
    i0 = d3_svg_lineInterpolators.get(interpolate = x);
    i1 = i0.reverse || i0;
    return area;
  };

  area.tension = function(x) {
    if (!arguments.length) return tension;
    tension = x;
    return area;
  };

  return area.interpolate("linear");
}

d3_svg_lineStepBefore.reverse = d3_svg_lineStepAfter;
d3_svg_lineStepAfter.reverse = d3_svg_lineStepBefore;

d3.svg.area = function() {
  return d3_svg_area(Object);
};

function d3_svg_areaX(points) {
  return function(d, i) {
    return points[i][0];
  };
}

function d3_svg_areaY(points) {
  return function(d, i) {
    return points[i][1];
  };
}
d3.svg.area.radial = function() {
  var area = d3_svg_area(d3_svg_lineRadial);
  area.radius = area.x, delete area.x;
  area.innerRadius = area.x0, delete area.x0;
  area.outerRadius = area.x1, delete area.x1;
  area.angle = area.y, delete area.y;
  area.startAngle = area.y0, delete area.y0;
  area.endAngle = area.y1, delete area.y1;
  return area;
};
d3.svg.chord = function() {
  var source = d3_svg_chordSource,
      target = d3_svg_chordTarget,
      radius = d3_svg_chordRadius,
      startAngle = d3_svg_arcStartAngle,
      endAngle = d3_svg_arcEndAngle;

  // TODO Allow control point to be customized.

  function chord(d, i) {
    var s = subgroup(this, source, d, i),
        t = subgroup(this, target, d, i);
    return "M" + s.p0
      + arc(s.r, s.p1, s.a1 - s.a0) + (equals(s, t)
      ? curve(s.r, s.p1, s.r, s.p0)
      : curve(s.r, s.p1, t.r, t.p0)
      + arc(t.r, t.p1, t.a1 - t.a0)
      + curve(t.r, t.p1, s.r, s.p0))
      + "Z";
  }

  function subgroup(self, f, d, i) {
    var subgroup = f.call(self, d, i),
        r = radius.call(self, subgroup, i),
        a0 = startAngle.call(self, subgroup, i) + d3_svg_arcOffset,
        a1 = endAngle.call(self, subgroup, i) + d3_svg_arcOffset;
    return {
      r: r,
      a0: a0,
      a1: a1,
      p0: [r * Math.cos(a0), r * Math.sin(a0)],
      p1: [r * Math.cos(a1), r * Math.sin(a1)]
    };
  }

  function equals(a, b) {
    return a.a0 == b.a0 && a.a1 == b.a1;
  }

  function arc(r, p, a) {
    return "A" + r + "," + r + " 0 " + +(a > Math.PI) + ",1 " + p;
  }

  function curve(r0, p0, r1, p1) {
    return "Q 0,0 " + p1;
  }

  chord.radius = function(v) {
    if (!arguments.length) return radius;
    radius = d3.functor(v);
    return chord;
  };

  chord.source = function(v) {
    if (!arguments.length) return source;
    source = d3.functor(v);
    return chord;
  };

  chord.target = function(v) {
    if (!arguments.length) return target;
    target = d3.functor(v);
    return chord;
  };

  chord.startAngle = function(v) {
    if (!arguments.length) return startAngle;
    startAngle = d3.functor(v);
    return chord;
  };

  chord.endAngle = function(v) {
    if (!arguments.length) return endAngle;
    endAngle = d3.functor(v);
    return chord;
  };

  return chord;
};

function d3_svg_chordSource(d) {
  return d.source;
}

function d3_svg_chordTarget(d) {
  return d.target;
}

function d3_svg_chordRadius(d) {
  return d.radius;
}

function d3_svg_chordStartAngle(d) {
  return d.startAngle;
}

function d3_svg_chordEndAngle(d) {
  return d.endAngle;
}
d3.svg.diagonal = function() {
  var source = d3_svg_chordSource,
      target = d3_svg_chordTarget,
      projection = d3_svg_diagonalProjection;

  function diagonal(d, i) {
    var p0 = source.call(this, d, i),
        p3 = target.call(this, d, i),
        m = (p0.y + p3.y) / 2,
        p = [p0, {x: p0.x, y: m}, {x: p3.x, y: m}, p3];
    p = p.map(projection);
    return "M" + p[0] + "C" + p[1] + " " + p[2] + " " + p[3];
  }

  diagonal.source = function(x) {
    if (!arguments.length) return source;
    source = d3.functor(x);
    return diagonal;
  };

  diagonal.target = function(x) {
    if (!arguments.length) return target;
    target = d3.functor(x);
    return diagonal;
  };

  diagonal.projection = function(x) {
    if (!arguments.length) return projection;
    projection = x;
    return diagonal;
  };

  return diagonal;
};

function d3_svg_diagonalProjection(d) {
  return [d.x, d.y];
}
d3.svg.diagonal.radial = function() {
  var diagonal = d3.svg.diagonal(),
      projection = d3_svg_diagonalProjection,
      projection_ = diagonal.projection;

  diagonal.projection = function(x) {
    return arguments.length
        ? projection_(d3_svg_diagonalRadialProjection(projection = x))
        : projection;
  };

  return diagonal;
};

function d3_svg_diagonalRadialProjection(projection) {
  return function() {
    var d = projection.apply(this, arguments),
        r = d[0],
        a = d[1] + d3_svg_arcOffset;
    return [r * Math.cos(a), r * Math.sin(a)];
  };
}
d3.svg.mouse = d3.mouse;
d3.svg.touches = d3.touches;
d3.svg.symbol = function() {
  var type = d3_svg_symbolType,
      size = d3_svg_symbolSize;

  function symbol(d, i) {
    return (d3_svg_symbols.get(type.call(this, d, i))
        || d3_svg_symbolCircle)
        (size.call(this, d, i));
  }

  symbol.type = function(x) {
    if (!arguments.length) return type;
    type = d3.functor(x);
    return symbol;
  };

  // size of symbol in square pixels
  symbol.size = function(x) {
    if (!arguments.length) return size;
    size = d3.functor(x);
    return symbol;
  };

  return symbol;
};

function d3_svg_symbolSize() {
  return 64;
}

function d3_svg_symbolType() {
  return "circle";
}

function d3_svg_symbolCircle(size) {
  var r = Math.sqrt(size / Math.PI);
  return "M0," + r
      + "A" + r + "," + r + " 0 1,1 0," + (-r)
      + "A" + r + "," + r + " 0 1,1 0," + r
      + "Z";
}

// TODO cross-diagonal?
var d3_svg_symbols = d3.map({
  "circle": d3_svg_symbolCircle,
  "cross": function(size) {
    var r = Math.sqrt(size / 5) / 2;
    return "M" + -3 * r + "," + -r
        + "H" + -r
        + "V" + -3 * r
        + "H" + r
        + "V" + -r
        + "H" + 3 * r
        + "V" + r
        + "H" + r
        + "V" + 3 * r
        + "H" + -r
        + "V" + r
        + "H" + -3 * r
        + "Z";
  },
  "diamond": function(size) {
    var ry = Math.sqrt(size / (2 * d3_svg_symbolTan30)),
        rx = ry * d3_svg_symbolTan30;
    return "M0," + -ry
        + "L" + rx + ",0"
        + " 0," + ry
        + " " + -rx + ",0"
        + "Z";
  },
  "square": function(size) {
    var r = Math.sqrt(size) / 2;
    return "M" + -r + "," + -r
        + "L" + r + "," + -r
        + " " + r + "," + r
        + " " + -r + "," + r
        + "Z";
  },
  "triangle-down": function(size) {
    var rx = Math.sqrt(size / d3_svg_symbolSqrt3),
        ry = rx * d3_svg_symbolSqrt3 / 2;
    return "M0," + ry
        + "L" + rx +"," + -ry
        + " " + -rx + "," + -ry
        + "Z";
  },
  "triangle-up": function(size) {
    var rx = Math.sqrt(size / d3_svg_symbolSqrt3),
        ry = rx * d3_svg_symbolSqrt3 / 2;
    return "M0," + -ry
        + "L" + rx +"," + ry
        + " " + -rx + "," + ry
        + "Z";
  }
});

d3.svg.symbolTypes = d3_svg_symbols.keys();

var d3_svg_symbolSqrt3 = Math.sqrt(3),
    d3_svg_symbolTan30 = Math.tan(30 * Math.PI / 180);
d3.svg.axis = function() {
  var scale = d3.scale.linear(),
      orient = "bottom",
      tickMajorSize = 6,
      tickMinorSize = 6,
      tickEndSize = 6,
      tickPadding = 3,
      tickArguments_ = [10],
      tickValues = null,
      tickFormat_,
      tickSubdivide = 0;

  function axis(g) {
    g.each(function() {
      var g = d3.select(this);

      // Ticks, or domain values for ordinal scales.
      var ticks = tickValues == null ? (scale.ticks ? scale.ticks.apply(scale, tickArguments_) : scale.domain()) : tickValues,
          tickFormat = tickFormat_ == null ? (scale.tickFormat ? scale.tickFormat.apply(scale, tickArguments_) : String) : tickFormat_;

      // Minor ticks.
      var subticks = d3_svg_axisSubdivide(scale, ticks, tickSubdivide),
          subtick = g.selectAll(".minor").data(subticks, String),
          subtickEnter = subtick.enter().insert("line", "g").attr("class", "tick minor").style("opacity", 1e-6),
          subtickExit = d3.transition(subtick.exit()).style("opacity", 1e-6).remove(),
          subtickUpdate = d3.transition(subtick).style("opacity", 1);

      // Major ticks.
      var tick = g.selectAll("g").data(ticks, String),
          tickEnter = tick.enter().insert("g", "path").style("opacity", 1e-6),
          tickExit = d3.transition(tick.exit()).style("opacity", 1e-6).remove(),
          tickUpdate = d3.transition(tick).style("opacity", 1),
          tickTransform;

      // Domain.
      var range = d3_scaleRange(scale),
          path = g.selectAll(".domain").data([0]),
          pathEnter = path.enter().append("path").attr("class", "domain"),
          pathUpdate = d3.transition(path);

      // Stash a snapshot of the new scale, and retrieve the old snapshot.
      var scale1 = scale.copy(),
          scale0 = this.__chart__ || scale1;
      this.__chart__ = scale1;

      tickEnter.append("line").attr("class", "tick");
      tickEnter.append("text");
      tickUpdate.select("text").text(tickFormat);

      switch (orient) {
        case "bottom": {
          tickTransform = d3_svg_axisX;
          subtickEnter.attr("y2", tickMinorSize);
          subtickUpdate.attr("x2", 0).attr("y2", tickMinorSize);
          tickEnter.select("line").attr("y2", tickMajorSize);
          tickEnter.select("text").attr("y", Math.max(tickMajorSize, 0) + tickPadding);
          tickUpdate.select("line").attr("x2", 0).attr("y2", tickMajorSize);
          tickUpdate.select("text").attr("x", 0).attr("y", Math.max(tickMajorSize, 0) + tickPadding).attr("dy", ".71em").attr("text-anchor", "middle");
          pathUpdate.attr("d", "M" + range[0] + "," + tickEndSize + "V0H" + range[1] + "V" + tickEndSize);
          break;
        }
        case "top": {
          tickTransform = d3_svg_axisX;
          subtickEnter.attr("y2", -tickMinorSize);
          subtickUpdate.attr("x2", 0).attr("y2", -tickMinorSize);
          tickEnter.select("line").attr("y2", -tickMajorSize);
          tickEnter.select("text").attr("y", -(Math.max(tickMajorSize, 0) + tickPadding));
          tickUpdate.select("line").attr("x2", 0).attr("y2", -tickMajorSize);
          tickUpdate.select("text").attr("x", 0).attr("y", -(Math.max(tickMajorSize, 0) + tickPadding)).attr("dy", "0em").attr("text-anchor", "middle");
          pathUpdate.attr("d", "M" + range[0] + "," + -tickEndSize + "V0H" + range[1] + "V" + -tickEndSize);
          break;
        }
        case "left": {
          tickTransform = d3_svg_axisY;
          subtickEnter.attr("x2", -tickMinorSize);
          subtickUpdate.attr("x2", -tickMinorSize).attr("y2", 0);
          tickEnter.select("line").attr("x2", -tickMajorSize);
          tickEnter.select("text").attr("x", -(Math.max(tickMajorSize, 0) + tickPadding));
          tickUpdate.select("line").attr("x2", -tickMajorSize).attr("y2", 0);
          tickUpdate.select("text").attr("x", -(Math.max(tickMajorSize, 0) + tickPadding)).attr("y", 0).attr("dy", ".32em").attr("text-anchor", "end");
          pathUpdate.attr("d", "M" + -tickEndSize + "," + range[0] + "H0V" + range[1] + "H" + -tickEndSize);
          break;
        }
        case "right": {
          tickTransform = d3_svg_axisY;
          subtickEnter.attr("x2", tickMinorSize);
          subtickUpdate.attr("x2", tickMinorSize).attr("y2", 0);
          tickEnter.select("line").attr("x2", tickMajorSize);
          tickEnter.select("text").attr("x", Math.max(tickMajorSize, 0) + tickPadding);
          tickUpdate.select("line").attr("x2", tickMajorSize).attr("y2", 0);
          tickUpdate.select("text").attr("x", Math.max(tickMajorSize, 0) + tickPadding).attr("y", 0).attr("dy", ".32em").attr("text-anchor", "start");
          pathUpdate.attr("d", "M" + tickEndSize + "," + range[0] + "H0V" + range[1] + "H" + tickEndSize);
          break;
        }
      }

      // For quantitative scales:
      // - enter new ticks from the old scale
      // - exit old ticks to the new scale
      if (scale.ticks) {
        tickEnter.call(tickTransform, scale0);
        tickUpdate.call(tickTransform, scale1);
        tickExit.call(tickTransform, scale1);
        subtickEnter.call(tickTransform, scale0);
        subtickUpdate.call(tickTransform, scale1);
        subtickExit.call(tickTransform, scale1);
      }

      // For ordinal scales:
      // - any entering ticks are undefined in the old scale
      // - any exiting ticks are undefined in the new scale
      // Therefore, we only need to transition updating ticks.
      else {
        var dx = scale1.rangeBand() / 2, x = function(d) { return scale1(d) + dx; };
        tickEnter.call(tickTransform, x);
        tickUpdate.call(tickTransform, x);
      }
    });
  }

  axis.scale = function(x) {
    if (!arguments.length) return scale;
    scale = x;
    return axis;
  };

  axis.orient = function(x) {
    if (!arguments.length) return orient;
    orient = x;
    return axis;
  };

  axis.ticks = function() {
    if (!arguments.length) return tickArguments_;
    tickArguments_ = arguments;
    return axis;
  };

  axis.tickValues = function(x) {
    if (!arguments.length) return tickValues;
    tickValues = x;
    return axis;
  };

  axis.tickFormat = function(x) {
    if (!arguments.length) return tickFormat_;
    tickFormat_ = x;
    return axis;
  };

  axis.tickSize = function(x, y, z) {
    if (!arguments.length) return tickMajorSize;
    var n = arguments.length - 1;
    tickMajorSize = +x;
    tickMinorSize = n > 1 ? +y : tickMajorSize;
    tickEndSize = n > 0 ? +arguments[n] : tickMajorSize;
    return axis;
  };

  axis.tickPadding = function(x) {
    if (!arguments.length) return tickPadding;
    tickPadding = +x;
    return axis;
  };

  axis.tickSubdivide = function(x) {
    if (!arguments.length) return tickSubdivide;
    tickSubdivide = +x;
    return axis;
  };

  return axis;
};

function d3_svg_axisX(selection, x) {
  selection.attr("transform", function(d) { return "translate(" + x(d) + ",0)"; });
}

function d3_svg_axisY(selection, y) {
  selection.attr("transform", function(d) { return "translate(0," + y(d) + ")"; });
}

function d3_svg_axisSubdivide(scale, ticks, m) {
  subticks = [];
  if (m && ticks.length > 1) {
    var extent = d3_scaleExtent(scale.domain()),
        subticks,
        i = -1,
        n = ticks.length,
        d = (ticks[1] - ticks[0]) / ++m,
        j,
        v;
    while (++i < n) {
      for (j = m; --j > 0;) {
        if ((v = +ticks[i] - j * d) >= extent[0]) {
          subticks.push(v);
        }
      }
    }
    for (--i, j = 0; ++j < m && (v = +ticks[i] + j * d) < extent[1];) {
      subticks.push(v);
    }
  }
  return subticks;
}
d3.svg.brush = function() {
  var event = d3_eventDispatch(brush, "brushstart", "brush", "brushend"),
      x = null, // x-scale, optional
      y = null, // y-scale, optional
      resizes = d3_svg_brushResizes[0],
      extent = [[0, 0], [0, 0]], // [x0, y0], [x1, y1], in pixels (integers)
      extentDomain; // the extent in data space, lazily created

  function brush(g) {
    g.each(function() {
      var g = d3.select(this),
          bg = g.selectAll(".background").data([0]),
          fg = g.selectAll(".extent").data([0]),
          tz = g.selectAll(".resize").data(resizes, String),
          e;

      // Prepare the brush container for events.
      g
          .style("pointer-events", "all")
          .on("mousedown.brush", brushstart)
          .on("touchstart.brush", brushstart);

      // An invisible, mouseable area for starting a new brush.
      bg.enter().append("rect")
          .attr("class", "background")
          .style("visibility", "hidden")
          .style("cursor", "crosshair");

      // The visible brush extent; style this as you like!
      fg.enter().append("rect")
          .attr("class", "extent")
          .style("cursor", "move");

      // More invisible rects for resizing the extent.
      tz.enter().append("g")
          .attr("class", function(d) { return "resize " + d; })
          .style("cursor", function(d) { return d3_svg_brushCursor[d]; })
        .append("rect")
          .attr("x", function(d) { return /[ew]$/.test(d) ? -3 : null; })
          .attr("y", function(d) { return /^[ns]/.test(d) ? -3 : null; })
          .attr("width", 6)
          .attr("height", 6)
          .style("visibility", "hidden");

      // Show or hide the resizers.
      tz.style("display", brush.empty() ? "none" : null);

      // Remove any superfluous resizers.
      tz.exit().remove();

      // Initialize the background to fill the defined range.
      // If the range isn't defined, you can post-process.
      if (x) {
        e = d3_scaleRange(x);
        bg.attr("x", e[0]).attr("width", e[1] - e[0]);
        redrawX(g);
      }
      if (y) {
        e = d3_scaleRange(y);
        bg.attr("y", e[0]).attr("height", e[1] - e[0]);
        redrawY(g);
      }
      redraw(g);
    });
  }

  function redraw(g) {
    g.selectAll(".resize").attr("transform", function(d) {
      return "translate(" + extent[+/e$/.test(d)][0] + "," + extent[+/^s/.test(d)][1] + ")";
    });
  }

  function redrawX(g) {
    g.select(".extent").attr("x", extent[0][0]);
    g.selectAll(".extent,.n>rect,.s>rect").attr("width", extent[1][0] - extent[0][0]);
  }

  function redrawY(g) {
    g.select(".extent").attr("y", extent[0][1]);
    g.selectAll(".extent,.e>rect,.w>rect").attr("height", extent[1][1] - extent[0][1]);
  }

  function brushstart() {
    var target = this,
        eventTarget = d3.select(d3.event.target),
        event_ = event.of(target, arguments),
        g = d3.select(target),
        resizing = eventTarget.datum(),
        resizingX = !/^(n|s)$/.test(resizing) && x,
        resizingY = !/^(e|w)$/.test(resizing) && y,
        dragging = eventTarget.classed("extent"),
        center,
        origin = mouse(),
        offset;

    var w = d3.select(window)
        .on("mousemove.brush", brushmove)
        .on("mouseup.brush", brushend)
        .on("touchmove.brush", brushmove)
        .on("touchend.brush", brushend)
        .on("keydown.brush", keydown)
        .on("keyup.brush", keyup);

    // If the extent was clicked on, drag rather than brush;
    // store the point between the mouse and extent origin instead.
    if (dragging) {
      origin[0] = extent[0][0] - origin[0];
      origin[1] = extent[0][1] - origin[1];
    }

    // If a resizer was clicked on, record which side is to be resized.
    // Also, set the origin to the opposite side.
    else if (resizing) {
      var ex = +/w$/.test(resizing),
          ey = +/^n/.test(resizing);
      offset = [extent[1 - ex][0] - origin[0], extent[1 - ey][1] - origin[1]];
      origin[0] = extent[ex][0];
      origin[1] = extent[ey][1];
    }

    // If the ALT key is down when starting a brush, the center is at the mouse.
    else if (d3.event.altKey) center = origin.slice();

    // Propagate the active cursor to the body for the drag duration.
    g.style("pointer-events", "none").selectAll(".resize").style("display", null);
    d3.select("body").style("cursor", eventTarget.style("cursor"));

    // Notify listeners.
    event_({type: "brushstart"});
    brushmove();
    d3_eventCancel();

    function mouse() {
      var touches = d3.event.changedTouches;
      return touches ? d3.touches(target, touches)[0] : d3.mouse(target);
    }

    function keydown() {
      if (d3.event.keyCode == 32) {
        if (!dragging) {
          center = null;
          origin[0] -= extent[1][0];
          origin[1] -= extent[1][1];
          dragging = 2;
        }
        d3_eventCancel();
      }
    }

    function keyup() {
      if (d3.event.keyCode == 32 && dragging == 2) {
        origin[0] += extent[1][0];
        origin[1] += extent[1][1];
        dragging = 0;
        d3_eventCancel();
      }
    }

    function brushmove() {
      var point = mouse(),
          moved = false;

      // Preserve the offset for thick resizers.
      if (offset) {
        point[0] += offset[0];
        point[1] += offset[1];
      }

      if (!dragging) {

        // If needed, determine the center from the current extent.
        if (d3.event.altKey) {
          if (!center) center = [(extent[0][0] + extent[1][0]) / 2, (extent[0][1] + extent[1][1]) / 2];

          // Update the origin, for when the ALT key is released.
          origin[0] = extent[+(point[0] < center[0])][0];
          origin[1] = extent[+(point[1] < center[1])][1];
        }

        // When the ALT key is released, we clear the center.
        else center = null;
      }

      // Update the brush extent for each dimension.
      if (resizingX && move1(point, x, 0)) {
        redrawX(g);
        moved = true;
      }
      if (resizingY && move1(point, y, 1)) {
        redrawY(g);
        moved = true;
      }

      // Final redraw and notify listeners.
      if (moved) {
        redraw(g);
        event_({type: "brush", mode: dragging ? "move" : "resize"});
      }
    }

    function move1(point, scale, i) {
      var range = d3_scaleRange(scale),
          r0 = range[0],
          r1 = range[1],
          position = origin[i],
          size = extent[1][i] - extent[0][i],
          min,
          max;

      // When dragging, reduce the range by the extent size and position.
      if (dragging) {
        r0 -= position;
        r1 -= size + position;
      }

      // Clamp the point so that the extent fits within the range extent.
      min = Math.max(r0, Math.min(r1, point[i]));

      // Compute the new extent bounds.
      if (dragging) {
        max = (min += position) + size;
      } else {

        // If the ALT key is pressed, then preserve the center of the extent.
        if (center) position = Math.max(r0, Math.min(r1, 2 * center[i] - min));

        // Compute the min and max of the position and point.
        if (position < min) {
          max = min;
          min = position;
        } else {
          max = position;
        }
      }

      // Update the stored bounds.
      if (extent[0][i] !== min || extent[1][i] !== max) {
        extentDomain = null;
        extent[0][i] = min;
        extent[1][i] = max;
        return true;
      }
    }

    function brushend() {
      brushmove();

      // reset the cursor styles
      g.style("pointer-events", "all").selectAll(".resize").style("display", brush.empty() ? "none" : null);
      d3.select("body").style("cursor", null);

      w .on("mousemove.brush", null)
        .on("mouseup.brush", null)
        .on("touchmove.brush", null)
        .on("touchend.brush", null)
        .on("keydown.brush", null)
        .on("keyup.brush", null);

      event_({type: "brushend"});
      d3_eventCancel();
    }
  }

  brush.x = function(z) {
    if (!arguments.length) return x;
    x = z;
    resizes = d3_svg_brushResizes[!x << 1 | !y]; // fore!
    return brush;
  };

  brush.y = function(z) {
    if (!arguments.length) return y;
    y = z;
    resizes = d3_svg_brushResizes[!x << 1 | !y]; // fore!
    return brush;
  };

  brush.extent = function(z) {
    var x0, x1, y0, y1, t;

    // Invert the pixel extent to data-space.
    if (!arguments.length) {
      z = extentDomain || extent;
      if (x) {
        x0 = z[0][0], x1 = z[1][0];
        if (!extentDomain) {
          x0 = extent[0][0], x1 = extent[1][0];
          if (x.invert) x0 = x.invert(x0), x1 = x.invert(x1);
          if (x1 < x0) t = x0, x0 = x1, x1 = t;
        }
      }
      if (y) {
        y0 = z[0][1], y1 = z[1][1];
        if (!extentDomain) {
          y0 = extent[0][1], y1 = extent[1][1];
          if (y.invert) y0 = y.invert(y0), y1 = y.invert(y1);
          if (y1 < y0) t = y0, y0 = y1, y1 = t;
        }
      }
      return x && y ? [[x0, y0], [x1, y1]] : x ? [x0, x1] : y && [y0, y1];
    }

    // Scale the data-space extent to pixels.
    extentDomain = [[0, 0], [0, 0]];
    if (x) {
      x0 = z[0], x1 = z[1];
      if (y) x0 = x0[0], x1 = x1[0];
      extentDomain[0][0] = x0, extentDomain[1][0] = x1;
      if (x.invert) x0 = x(x0), x1 = x(x1);
      if (x1 < x0) t = x0, x0 = x1, x1 = t;
      extent[0][0] = x0 | 0, extent[1][0] = x1 | 0;
    }
    if (y) {
      y0 = z[0], y1 = z[1];
      if (x) y0 = y0[1], y1 = y1[1];
      extentDomain[0][1] = y0, extentDomain[1][1] = y1;
      if (y.invert) y0 = y(y0), y1 = y(y1);
      if (y1 < y0) t = y0, y0 = y1, y1 = t;
      extent[0][1] = y0 | 0, extent[1][1] = y1 | 0;
    }

    return brush;
  };

  brush.clear = function() {
    extentDomain = null;
    extent[0][0] =
    extent[0][1] =
    extent[1][0] =
    extent[1][1] = 0;
    return brush;
  };

  brush.empty = function() {
    return (x && extent[0][0] === extent[1][0])
        || (y && extent[0][1] === extent[1][1]);
  };

  return d3.rebind(brush, event, "on");
};

var d3_svg_brushCursor = {
  n: "ns-resize",
  e: "ew-resize",
  s: "ns-resize",
  w: "ew-resize",
  nw: "nwse-resize",
  ne: "nesw-resize",
  se: "nwse-resize",
  sw: "nesw-resize"
};

var d3_svg_brushResizes = [
  ["n", "e", "s", "w", "nw", "ne", "se", "sw"],
  ["e", "w"],
  ["n", "s"],
  []
];
d3.behavior = {};
// TODO Track touch points by identifier.

d3.behavior.drag = function() {
  var event = d3_eventDispatch(drag, "drag", "dragstart", "dragend"),
      origin = null;

  function drag() {
    this.on("mousedown.drag", mousedown)
        .on("touchstart.drag", mousedown);
  }

  function mousedown() {
    var target = this,
        event_ = event.of(target, arguments),
        eventTarget = d3.event.target,
        offset,
        origin_ = point(),
        moved = 0;

    var w = d3.select(window)
        .on("mousemove.drag", dragmove)
        .on("touchmove.drag", dragmove)
        .on("mouseup.drag", dragend, true)
        .on("touchend.drag", dragend, true);

    if (origin) {
      offset = origin.apply(target, arguments);
      offset = [offset.x - origin_[0], offset.y - origin_[1]];
    } else {
      offset = [0, 0];
    }

    event_({type: "dragstart"});

    function point() {
      var p = target.parentNode,
          t = d3.event.changedTouches;
      return t ? d3.touches(p, t)[0] : d3.mouse(p);
    }

    function dragmove() {
      if (!target.parentNode) return dragend(); // target removed from DOM

      var p = point(),
          dx = p[0] - origin_[0],
          dy = p[1] - origin_[1];

      moved |= dx | dy;
      origin_ = p;
      d3_eventCancel();

      event_({type: "drag", x: p[0] + offset[0], y: p[1] + offset[1], dx: dx, dy: dy});
    }

    function dragend() {
      event_({type: "dragend"});

      // if moved, prevent the mouseup (and possibly click) from propagating
      if (moved) {
        d3_eventCancel();
        if (d3.event.target === eventTarget) w.on("click.drag", click, true);
      }

      w .on("mousemove.drag", null)
        .on("touchmove.drag", null)
        .on("mouseup.drag", null)
        .on("touchend.drag", null);
    }

    // prevent the subsequent click from propagating (e.g., for anchors)
    function click() {
      d3_eventCancel();
      w.on("click.drag", null);
    }
  }

  drag.origin = function(x) {
    if (!arguments.length) return origin;
    origin = x;
    return drag;
  };

  return d3.rebind(drag, event, "on");
};
d3.behavior.zoom = function() {
  var translate = [0, 0],
      translate0, // translate when we started zooming (to avoid drift)
      scale = 1,
      scale0, // scale when we started touching
      scaleExtent = d3_behavior_zoomInfinity,
      event = d3_eventDispatch(zoom, "zoom"),
      x0,
      x1,
      y0,
      y1,
      touchtime; // time of last touchstart (to detect double-tap)

  function zoom() {
    this
        .on("mousedown.zoom", mousedown)
        .on("mousewheel.zoom", mousewheel)
        .on("mousemove.zoom", mousemove)
        .on("DOMMouseScroll.zoom", mousewheel)
        .on("dblclick.zoom", dblclick)
        .on("touchstart.zoom", touchstart)
        .on("touchmove.zoom", touchmove)
        .on("touchend.zoom", touchstart);
  }

  zoom.translate = function(x) {
    if (!arguments.length) return translate;
    translate = x.map(Number);
    return zoom;
  };

  zoom.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return zoom;
  };

  zoom.scaleExtent = function(x) {
    if (!arguments.length) return scaleExtent;
    scaleExtent = x == null ? d3_behavior_zoomInfinity : x.map(Number);
    return zoom;
  };

  zoom.x = function(z) {
    if (!arguments.length) return x1;
    x1 = z;
    x0 = z.copy();
    return zoom;
  };

  zoom.y = function(z) {
    if (!arguments.length) return y1;
    y1 = z;
    y0 = z.copy();
    return zoom;
  };

  function location(p) {
    return [(p[0] - translate[0]) / scale, (p[1] - translate[1]) / scale];
  }

  function point(l) {
    return [l[0] * scale + translate[0], l[1] * scale + translate[1]];
  }

  function scaleTo(s) {
    scale = Math.max(scaleExtent[0], Math.min(scaleExtent[1], s));
  }

  function translateTo(p, l) {
    l = point(l);
    translate[0] += p[0] - l[0];
    translate[1] += p[1] - l[1];
  }

  function dispatch(event) {
    if (x1) x1.domain(x0.range().map(function(x) { return (x - translate[0]) / scale; }).map(x0.invert));
    if (y1) y1.domain(y0.range().map(function(y) { return (y - translate[1]) / scale; }).map(y0.invert));
    d3.event.preventDefault();
    event({type: "zoom", scale: scale, translate: translate});
  }

  function mousedown() {
    var target = this,
        event_ = event.of(target, arguments),
        eventTarget = d3.event.target,
        moved = 0,
        w = d3.select(window).on("mousemove.zoom", mousemove).on("mouseup.zoom", mouseup),
        l = location(d3.mouse(target));

    window.focus();
    d3_eventCancel();

    function mousemove() {
      moved = 1;
      translateTo(d3.mouse(target), l);
      dispatch(event_);
    }

    function mouseup() {
      if (moved) d3_eventCancel();
      w.on("mousemove.zoom", null).on("mouseup.zoom", null);
      if (moved && d3.event.target === eventTarget) w.on("click.zoom", click);
    }

    function click() {
      d3_eventCancel();
      w.on("click.zoom", null);
    }
  }

  function mousewheel() {
    if (!translate0) translate0 = location(d3.mouse(this));
    scaleTo(Math.pow(2, d3_behavior_zoomDelta() * .002) * scale);
    translateTo(d3.mouse(this), translate0);
    dispatch(event.of(this, arguments));
  }

  function mousemove() {
    translate0 = null;
  }

  function dblclick() {
    var p = d3.mouse(this), l = location(p);
    scaleTo(d3.event.shiftKey ? scale / 2 : scale * 2);
    translateTo(p, l);
    dispatch(event.of(this, arguments));
  }

  function touchstart() {
    var touches = d3.touches(this),
        now = Date.now();

    scale0 = scale;
    translate0 = {};
    touches.forEach(function(t) { translate0[t.identifier] = location(t); });
    d3_eventCancel();

    if ((touches.length === 1) && (now - touchtime < 500)) { // dbltap
      var p = touches[0], l = location(touches[0]);
      scaleTo(scale * 2);
      translateTo(p, l);
      dispatch(event.of(this, arguments));
    }
    touchtime = now;
  }

  function touchmove() {
    var touches = d3.touches(this),
        p0 = touches[0],
        l0 = translate0[p0.identifier];
    if (p1 = touches[1]) {
      var p1, l1 = translate0[p1.identifier];
      p0 = [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2];
      l0 = [(l0[0] + l1[0]) / 2, (l0[1] + l1[1]) / 2];
      scaleTo(d3.event.scale * scale0);
    }
    translateTo(p0, l0);
    dispatch(event.of(this, arguments));
  }

  return d3.rebind(zoom, event, "on");
};

var d3_behavior_zoomDiv, // for interpreting mousewheel events
    d3_behavior_zoomInfinity = [0, Infinity]; // default scale extent

function d3_behavior_zoomDelta() {

  // mousewheel events are totally broken!
  // https://bugs.webkit.org/show_bug.cgi?id=40441
  // not only that, but Chrome and Safari differ in re. to acceleration!
  if (!d3_behavior_zoomDiv) {
    d3_behavior_zoomDiv = d3.select("body").append("div")
        .style("visibility", "hidden")
        .style("top", 0)
        .style("height", 0)
        .style("width", 0)
        .style("overflow-y", "scroll")
      .append("div")
        .style("height", "2000px")
      .node().parentNode;
  }

  var e = d3.event, delta;
  try {
    d3_behavior_zoomDiv.scrollTop = 1000;
    d3_behavior_zoomDiv.dispatchEvent(e);
    delta = 1000 - d3_behavior_zoomDiv.scrollTop;
  } catch (error) {
    delta = e.wheelDelta || (-e.detail * 5);
  }

  return delta;
}
d3.layout = {};
// Implements hierarchical edge bundling using Holten's algorithm. For each
// input link, a path is computed that travels through the tree, up the parent
// hierarchy to the least common ancestor, and then back down to the destination
// node. Each path is simply an array of nodes.
d3.layout.bundle = function() {
  return function(links) {
    var paths = [],
        i = -1,
        n = links.length;
    while (++i < n) paths.push(d3_layout_bundlePath(links[i]));
    return paths;
  };
};

function d3_layout_bundlePath(link) {
  var start = link.source,
      end = link.target,
      lca = d3_layout_bundleLeastCommonAncestor(start, end),
      points = [start];
  while (start !== lca) {
    start = start.parent;
    points.push(start);
  }
  var k = points.length;
  while (end !== lca) {
    points.splice(k, 0, end);
    end = end.parent;
  }
  return points;
}

function d3_layout_bundleAncestors(node) {
  var ancestors = [],
      parent = node.parent;
  while (parent != null) {
    ancestors.push(node);
    node = parent;
    parent = parent.parent;
  }
  ancestors.push(node);
  return ancestors;
}

function d3_layout_bundleLeastCommonAncestor(a, b) {
  if (a === b) return a;
  var aNodes = d3_layout_bundleAncestors(a),
      bNodes = d3_layout_bundleAncestors(b),
      aNode = aNodes.pop(),
      bNode = bNodes.pop(),
      sharedNode = null;
  while (aNode === bNode) {
    sharedNode = aNode;
    aNode = aNodes.pop();
    bNode = bNodes.pop();
  }
  return sharedNode;
}
d3.layout.chord = function() {
  var chord = {},
      chords,
      groups,
      matrix,
      n,
      padding = 0,
      sortGroups,
      sortSubgroups,
      sortChords;

  function relayout() {
    var subgroups = {},
        groupSums = [],
        groupIndex = d3.range(n),
        subgroupIndex = [],
        k,
        x,
        x0,
        i,
        j;

    chords = [];
    groups = [];

    // Compute the sum.
    k = 0, i = -1; while (++i < n) {
      x = 0, j = -1; while (++j < n) {
        x += matrix[i][j];
      }
      groupSums.push(x);
      subgroupIndex.push(d3.range(n));
      k += x;
    }

    // Sort groups…
    if (sortGroups) {
      groupIndex.sort(function(a, b) {
        return sortGroups(groupSums[a], groupSums[b]);
      });
    }

    // Sort subgroups…
    if (sortSubgroups) {
      subgroupIndex.forEach(function(d, i) {
        d.sort(function(a, b) {
          return sortSubgroups(matrix[i][a], matrix[i][b]);
        });
      });
    }

    // Convert the sum to scaling factor for [0, 2pi].
    // TODO Allow start and end angle to be specified.
    // TODO Allow padding to be specified as percentage?
    k = (2 * Math.PI - padding * n) / k;

    // Compute the start and end angle for each group and subgroup.
    // Note: Opera has a bug reordering object literal properties!
    x = 0, i = -1; while (++i < n) {
      x0 = x, j = -1; while (++j < n) {
        var di = groupIndex[i],
            dj = subgroupIndex[di][j],
            v = matrix[di][dj],
            a0 = x,
            a1 = x += v * k;
        subgroups[di + "-" + dj] = {
          index: di,
          subindex: dj,
          startAngle: a0,
          endAngle: a1,
          value: v
        };
      }
      groups.push({
        index: di,
        startAngle: x0,
        endAngle: x,
        value: (x - x0) / k
      });
      x += padding;
    }

    // Generate chords for each (non-empty) subgroup-subgroup link.
    i = -1; while (++i < n) {
      j = i - 1; while (++j < n) {
        var source = subgroups[i + "-" + j],
            target = subgroups[j + "-" + i];
        if (source.value || target.value) {
          chords.push(source.value < target.value
              ? {source: target, target: source}
              : {source: source, target: target});
        }
      }
    }

    if (sortChords) resort();
  }

  function resort() {
    chords.sort(function(a, b) {
      return sortChords(
          (a.source.value + a.target.value) / 2,
          (b.source.value + b.target.value) / 2);
    });
  }

  chord.matrix = function(x) {
    if (!arguments.length) return matrix;
    n = (matrix = x) && matrix.length;
    chords = groups = null;
    return chord;
  };

  chord.padding = function(x) {
    if (!arguments.length) return padding;
    padding = x;
    chords = groups = null;
    return chord;
  };

  chord.sortGroups = function(x) {
    if (!arguments.length) return sortGroups;
    sortGroups = x;
    chords = groups = null;
    return chord;
  };

  chord.sortSubgroups = function(x) {
    if (!arguments.length) return sortSubgroups;
    sortSubgroups = x;
    chords = null;
    return chord;
  };

  chord.sortChords = function(x) {
    if (!arguments.length) return sortChords;
    sortChords = x;
    if (chords) resort();
    return chord;
  };

  chord.chords = function() {
    if (!chords) relayout();
    return chords;
  };

  chord.groups = function() {
    if (!groups) relayout();
    return groups;
  };

  return chord;
};
// A rudimentary force layout using Gauss-Seidel.
d3.layout.force = function() {
  var force = {},
      event = d3.dispatch("start", "tick", "end"),
      size = [1, 1],
      drag,
      alpha,
      friction = .9,
      linkDistance = d3_layout_forceLinkDistance,
      linkStrength = d3_layout_forceLinkStrength,
      charge = -30,
      gravity = .1,
      theta = .8,
      interval,
      nodes = [],
      links = [],
      distances,
      strengths,
      charges;

  function repulse(node) {
    return function(quad, x1, y1, x2, y2) {
      if (quad.point !== node) {
        var dx = quad.cx - node.x,
            dy = quad.cy - node.y,
            dn = 1 / Math.sqrt(dx * dx + dy * dy);

        /* Barnes-Hut criterion. */
        if ((x2 - x1) * dn < theta) {
          var k = quad.charge * dn * dn;
          node.px -= dx * k;
          node.py -= dy * k;
          return true;
        }

        if (quad.point && isFinite(dn)) {
          var k = quad.pointCharge * dn * dn;
          node.px -= dx * k;
          node.py -= dy * k;
        }
      }
      return !quad.charge;
    };
  }

  force.tick = function() {
    // simulated annealing, basically
    if ((alpha *= .99) < .005) {
      event.end({type: "end", alpha: alpha = 0});
      return true;
    }

    var n = nodes.length,
        m = links.length,
        q,
        i, // current index
        o, // current object
        s, // current source
        t, // current target
        l, // current distance
        k, // current force
        x, // x-distance
        y; // y-distance

    // gauss-seidel relaxation for links
    for (i = 0; i < m; ++i) {
      o = links[i];
      s = o.source;
      t = o.target;
      x = t.x - s.x;
      y = t.y - s.y;
      if (l = (x * x + y * y)) {
        l = alpha * strengths[i] * ((l = Math.sqrt(l)) - distances[i]) / l;
        x *= l;
        y *= l;
        t.x -= x * (k = s.weight / (t.weight + s.weight));
        t.y -= y * k;
        s.x += x * (k = 1 - k);
        s.y += y * k;
      }
    }

    // apply gravity forces
    if (k = alpha * gravity) {
      x = size[0] / 2;
      y = size[1] / 2;
      i = -1; if (k) while (++i < n) {
        o = nodes[i];
        o.x += (x - o.x) * k;
        o.y += (y - o.y) * k;
      }
    }

    // compute quadtree center of mass and apply charge forces
    if (charge) {
      d3_layout_forceAccumulate(q = d3.geom.quadtree(nodes), alpha, charges);
      i = -1; while (++i < n) {
        if (!(o = nodes[i]).fixed) {
          q.visit(repulse(o));
        }
      }
    }

    // position verlet integration
    i = -1; while (++i < n) {
      o = nodes[i];
      if (o.fixed) {
        o.x = o.px;
        o.y = o.py;
      } else {
        o.x -= (o.px - (o.px = o.x)) * friction;
        o.y -= (o.py - (o.py = o.y)) * friction;
      }
    }

    event.tick({type: "tick", alpha: alpha});
  };

  force.nodes = function(x) {
    if (!arguments.length) return nodes;
    nodes = x;
    return force;
  };

  force.links = function(x) {
    if (!arguments.length) return links;
    links = x;
    return force;
  };

  force.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return force;
  };

  force.linkDistance = function(x) {
    if (!arguments.length) return linkDistance;
    linkDistance = d3.functor(x);
    return force;
  };

  // For backwards-compatibility.
  force.distance = force.linkDistance;

  force.linkStrength = function(x) {
    if (!arguments.length) return linkStrength;
    linkStrength = d3.functor(x);
    return force;
  };

  force.friction = function(x) {
    if (!arguments.length) return friction;
    friction = x;
    return force;
  };

  force.charge = function(x) {
    if (!arguments.length) return charge;
    charge = typeof x === "function" ? x : +x;
    return force;
  };

  force.gravity = function(x) {
    if (!arguments.length) return gravity;
    gravity = x;
    return force;
  };

  force.theta = function(x) {
    if (!arguments.length) return theta;
    theta = x;
    return force;
  };

  force.alpha = function(x) {
    if (!arguments.length) return alpha;

    if (alpha) { // if we're already running
      if (x > 0) alpha = x; // we might keep it hot
      else alpha = 0; // or, next tick will dispatch "end"
    } else if (x > 0) { // otherwise, fire it up!
      event.start({type: "start", alpha: alpha = x});
      d3.timer(force.tick);
    }

    return force;
  };

  force.start = function() {
    var i,
        j,
        n = nodes.length,
        m = links.length,
        w = size[0],
        h = size[1],
        neighbors,
        o;

    for (i = 0; i < n; ++i) {
      (o = nodes[i]).index = i;
      o.weight = 0;
    }

    distances = [];
    strengths = [];
    for (i = 0; i < m; ++i) {
      o = links[i];
      if (typeof o.source == "number") o.source = nodes[o.source];
      if (typeof o.target == "number") o.target = nodes[o.target];
      distances[i] = linkDistance.call(this, o, i);
      strengths[i] = linkStrength.call(this, o, i);
      ++o.source.weight;
      ++o.target.weight;
    }

    for (i = 0; i < n; ++i) {
      o = nodes[i];
      if (isNaN(o.x)) o.x = position("x", w);
      if (isNaN(o.y)) o.y = position("y", h);
      if (isNaN(o.px)) o.px = o.x;
      if (isNaN(o.py)) o.py = o.y;
    }

    charges = [];
    if (typeof charge === "function") {
      for (i = 0; i < n; ++i) {
        charges[i] = +charge.call(this, nodes[i], i);
      }
    } else {
      for (i = 0; i < n; ++i) {
        charges[i] = charge;
      }
    }

    // initialize node position based on first neighbor
    function position(dimension, size) {
      var neighbors = neighbor(i),
          j = -1,
          m = neighbors.length,
          x;
      while (++j < m) if (!isNaN(x = neighbors[j][dimension])) return x;
      return Math.random() * size;
    }

    // initialize neighbors lazily
    function neighbor() {
      if (!neighbors) {
        neighbors = [];
        for (j = 0; j < n; ++j) {
          neighbors[j] = [];
        }
        for (j = 0; j < m; ++j) {
          var o = links[j];
          neighbors[o.source.index].push(o.target);
          neighbors[o.target.index].push(o.source);
        }
      }
      return neighbors[i];
    }

    return force.resume();
  };

  force.resume = function() {
    return force.alpha(.1);
  };

  force.stop = function() {
    return force.alpha(0);
  };

  // use `node.call(force.drag)` to make nodes draggable
  force.drag = function() {
    if (!drag) drag = d3.behavior.drag()
        .origin(Object)
        .on("dragstart", dragstart)
        .on("drag", d3_layout_forceDrag)
        .on("dragend", d3_layout_forceDragEnd);

    this.on("mouseover.force", d3_layout_forceDragOver)
        .on("mouseout.force", d3_layout_forceDragOut)
        .call(drag);
  };

  function dragstart(d) {
    d3_layout_forceDragOver(d3_layout_forceDragNode = d);
    d3_layout_forceDragForce = force;
  }

  return d3.rebind(force, event, "on");
};

var d3_layout_forceDragForce,
    d3_layout_forceDragNode;

function d3_layout_forceDragOver(d) {
  d.fixed |= 2;
}

function d3_layout_forceDragOut(d) {
  if (d !== d3_layout_forceDragNode) d.fixed &= 1;
}

function d3_layout_forceDragEnd() {
  d3_layout_forceDragNode.fixed &= 1;
  d3_layout_forceDragForce = d3_layout_forceDragNode = null;
}

function d3_layout_forceDrag() {
  d3_layout_forceDragNode.px = d3.event.x;
  d3_layout_forceDragNode.py = d3.event.y;
  d3_layout_forceDragForce.resume(); // restart annealing
}

function d3_layout_forceAccumulate(quad, alpha, charges) {
  var cx = 0,
      cy = 0;
  quad.charge = 0;
  if (!quad.leaf) {
    var nodes = quad.nodes,
        n = nodes.length,
        i = -1,
        c;
    while (++i < n) {
      c = nodes[i];
      if (c == null) continue;
      d3_layout_forceAccumulate(c, alpha, charges);
      quad.charge += c.charge;
      cx += c.charge * c.cx;
      cy += c.charge * c.cy;
    }
  }
  if (quad.point) {
    // jitter internal nodes that are coincident
    if (!quad.leaf) {
      quad.point.x += Math.random() - .5;
      quad.point.y += Math.random() - .5;
    }
    var k = alpha * charges[quad.point.index];
    quad.charge += quad.pointCharge = k;
    cx += k * quad.point.x;
    cy += k * quad.point.y;
  }
  quad.cx = cx / quad.charge;
  quad.cy = cy / quad.charge;
}

function d3_layout_forceLinkDistance(link) {
  return 20;
}

function d3_layout_forceLinkStrength(link) {
  return 1;
}
d3.layout.partition = function() {
  var hierarchy = d3.layout.hierarchy(),
      size = [1, 1]; // width, height

  function position(node, x, dx, dy) {
    var children = node.children;
    node.x = x;
    node.y = node.depth * dy;
    node.dx = dx;
    node.dy = dy;
    if (children && (n = children.length)) {
      var i = -1,
          n,
          c,
          d;
      dx = node.value ? dx / node.value : 0;
      while (++i < n) {
        position(c = children[i], x, d = c.value * dx, dy);
        x += d;
      }
    }
  }

  function depth(node) {
    var children = node.children,
        d = 0;
    if (children && (n = children.length)) {
      var i = -1,
          n;
      while (++i < n) d = Math.max(d, depth(children[i]));
    }
    return 1 + d;
  }

  function partition(d, i) {
    var nodes = hierarchy.call(this, d, i);
    position(nodes[0], 0, size[0], size[1] / depth(nodes[0]));
    return nodes;
  }

  partition.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return partition;
  };

  return d3_layout_hierarchyRebind(partition, hierarchy);
};
d3.layout.pie = function() {
  var value = Number,
      sort = d3_layout_pieSortByValue,
      startAngle = 0,
      endAngle = 2 * Math.PI;

  function pie(data, i) {

    // Compute the numeric values for each data element.
    var values = data.map(function(d, i) { return +value.call(pie, d, i); });

    // Compute the start angle.
    var a = +(typeof startAngle === "function"
        ? startAngle.apply(this, arguments)
        : startAngle);

    // Compute the angular scale factor: from value to radians.
    var k = ((typeof endAngle === "function"
        ? endAngle.apply(this, arguments)
        : endAngle) - startAngle)
        / d3.sum(values);

    // Optionally sort the data.
    var index = d3.range(data.length);
    if (sort != null) index.sort(sort === d3_layout_pieSortByValue
        ? function(i, j) { return values[j] - values[i]; }
        : function(i, j) { return sort(data[i], data[j]); });

    // Compute the arcs!
    // They are stored in the original data's order.
    var arcs = [];
    index.forEach(function(i) {
      arcs[i] = {
        data: data[i],
        value: d = values[i],
        startAngle: a,
        endAngle: a += d * k
      };
    });
    return arcs;
  }

  /**
   * Specifies the value function *x*, which returns a nonnegative numeric value
   * for each datum. The default value function is `Number`. The value function
   * is passed two arguments: the current datum and the current index.
   */
  pie.value = function(x) {
    if (!arguments.length) return value;
    value = x;
    return pie;
  };

  /**
   * Specifies a sort comparison operator *x*. The comparator is passed two data
   * elements from the data array, a and b; it returns a negative value if a is
   * less than b, a positive value if a is greater than b, and zero if a equals
   * b.
   */
  pie.sort = function(x) {
    if (!arguments.length) return sort;
    sort = x;
    return pie;
  };

  /**
   * Specifies the overall start angle of the pie chart. Defaults to 0. The
   * start angle can be specified either as a constant or as a function; in the
   * case of a function, it is evaluated once per array (as opposed to per
   * element).
   */
  pie.startAngle = function(x) {
    if (!arguments.length) return startAngle;
    startAngle = x;
    return pie;
  };

  /**
   * Specifies the overall end angle of the pie chart. Defaults to 2π. The
   * end angle can be specified either as a constant or as a function; in the
   * case of a function, it is evaluated once per array (as opposed to per
   * element).
   */
  pie.endAngle = function(x) {
    if (!arguments.length) return endAngle;
    endAngle = x;
    return pie;
  };

  return pie;
};

var d3_layout_pieSortByValue = {};
// data is two-dimensional array of x,y; we populate y0
d3.layout.stack = function() {
  var values = Object,
      order = d3_layout_stackOrderDefault,
      offset = d3_layout_stackOffsetZero,
      out = d3_layout_stackOut,
      x = d3_layout_stackX,
      y = d3_layout_stackY;

  function stack(data, index) {

    // Convert series to canonical two-dimensional representation.
    var series = data.map(function(d, i) {
      return values.call(stack, d, i);
    });

    // Convert each series to canonical [[x,y]] representation.
    var points = series.map(function(d, i) {
      return d.map(function(v, i) {
        return [x.call(stack, v, i), y.call(stack, v, i)];
      });
    });

    // Compute the order of series, and permute them.
    var orders = order.call(stack, points, index);
    series = d3.permute(series, orders);
    points = d3.permute(points, orders);

    // Compute the baseline…
    var offsets = offset.call(stack, points, index);

    // And propagate it to other series.
    var n = series.length,
        m = series[0].length,
        i,
        j,
        o;
    for (j = 0; j < m; ++j) {
      out.call(stack, series[0][j], o = offsets[j], points[0][j][1]);
      for (i = 1; i < n; ++i) {
        out.call(stack, series[i][j], o += points[i - 1][j][1], points[i][j][1]);
      }
    }

    return data;
  }

  stack.values = function(x) {
    if (!arguments.length) return values;
    values = x;
    return stack;
  };

  stack.order = function(x) {
    if (!arguments.length) return order;
    order = typeof x === "function" ? x : d3_layout_stackOrders.get(x) || d3_layout_stackOrderDefault;
    return stack;
  };

  stack.offset = function(x) {
    if (!arguments.length) return offset;
    offset = typeof x === "function" ? x : d3_layout_stackOffsets.get(x) || d3_layout_stackOffsetZero;
    return stack;
  };

  stack.x = function(z) {
    if (!arguments.length) return x;
    x = z;
    return stack;
  };

  stack.y = function(z) {
    if (!arguments.length) return y;
    y = z;
    return stack;
  };

  stack.out = function(z) {
    if (!arguments.length) return out;
    out = z;
    return stack;
  };

  return stack;
}

function d3_layout_stackX(d) {
  return d.x;
}

function d3_layout_stackY(d) {
  return d.y;
}

function d3_layout_stackOut(d, y0, y) {
  d.y0 = y0;
  d.y = y;
}

var d3_layout_stackOrders = d3.map({

  "inside-out": function(data) {
    var n = data.length,
        i,
        j,
        max = data.map(d3_layout_stackMaxIndex),
        sums = data.map(d3_layout_stackReduceSum),
        index = d3.range(n).sort(function(a, b) { return max[a] - max[b]; }),
        top = 0,
        bottom = 0,
        tops = [],
        bottoms = [];
    for (i = 0; i < n; ++i) {
      j = index[i];
      if (top < bottom) {
        top += sums[j];
        tops.push(j);
      } else {
        bottom += sums[j];
        bottoms.push(j);
      }
    }
    return bottoms.reverse().concat(tops);
  },

  "reverse": function(data) {
    return d3.range(data.length).reverse();
  },

  "default": d3_layout_stackOrderDefault

});

var d3_layout_stackOffsets = d3.map({

  "silhouette": function(data) {
    var n = data.length,
        m = data[0].length,
        sums = [],
        max = 0,
        i,
        j,
        o,
        y0 = [];
    for (j = 0; j < m; ++j) {
      for (i = 0, o = 0; i < n; i++) o += data[i][j][1];
      if (o > max) max = o;
      sums.push(o);
    }
    for (j = 0; j < m; ++j) {
      y0[j] = (max - sums[j]) / 2;
    }
    return y0;
  },

  "wiggle": function(data) {
    var n = data.length,
        x = data[0],
        m = x.length,
        max = 0,
        i,
        j,
        k,
        s1,
        s2,
        s3,
        dx,
        o,
        o0,
        y0 = [];
    y0[0] = o = o0 = 0;
    for (j = 1; j < m; ++j) {
      for (i = 0, s1 = 0; i < n; ++i) s1 += data[i][j][1];
      for (i = 0, s2 = 0, dx = x[j][0] - x[j - 1][0]; i < n; ++i) {
        for (k = 0, s3 = (data[i][j][1] - data[i][j - 1][1]) / (2 * dx); k < i; ++k) {
          s3 += (data[k][j][1] - data[k][j - 1][1]) / dx;
        }
        s2 += s3 * data[i][j][1];
      }
      y0[j] = o -= s1 ? s2 / s1 * dx : 0;
      if (o < o0) o0 = o;
    }
    for (j = 0; j < m; ++j) y0[j] -= o0;
    return y0;
  },

  "expand": function(data) {
    var n = data.length,
        m = data[0].length,
        k = 1 / n,
        i,
        j,
        o,
        y0 = [];
    for (j = 0; j < m; ++j) {
      for (i = 0, o = 0; i < n; i++) o += data[i][j][1];
      if (o) for (i = 0; i < n; i++) data[i][j][1] /= o;
      else for (i = 0; i < n; i++) data[i][j][1] = k;
    }
    for (j = 0; j < m; ++j) y0[j] = 0;
    return y0;
  },

  "zero": d3_layout_stackOffsetZero

});

function d3_layout_stackOrderDefault(data) {
  return d3.range(data.length);
}

function d3_layout_stackOffsetZero(data) {
  var j = -1,
      m = data[0].length,
      y0 = [];
  while (++j < m) y0[j] = 0;
  return y0;
}

function d3_layout_stackMaxIndex(array) {
  var i = 1,
      j = 0,
      v = array[0][1],
      k,
      n = array.length;
  for (; i < n; ++i) {
    if ((k = array[i][1]) > v) {
      j = i;
      v = k;
    }
  }
  return j;
}

function d3_layout_stackReduceSum(d) {
  return d.reduce(d3_layout_stackSum, 0);
}

function d3_layout_stackSum(p, d) {
  return p + d[1];
}
d3.layout.histogram = function() {
  var frequency = true,
      valuer = Number,
      ranger = d3_layout_histogramRange,
      binner = d3_layout_histogramBinSturges;

  function histogram(data, i) {
    var bins = [],
        values = data.map(valuer, this),
        range = ranger.call(this, values, i),
        thresholds = binner.call(this, range, values, i),
        bin,
        i = -1,
        n = values.length,
        m = thresholds.length - 1,
        k = frequency ? 1 : 1 / n,
        x;

    // Initialize the bins.
    while (++i < m) {
      bin = bins[i] = [];
      bin.dx = thresholds[i + 1] - (bin.x = thresholds[i]);
      bin.y = 0;
    }

    // Fill the bins, ignoring values outside the range.
    i = -1; while(++i < n) {
      x = values[i];
      if ((x >= range[0]) && (x <= range[1])) {
        bin = bins[d3.bisect(thresholds, x, 1, m) - 1];
        bin.y += k;
        bin.push(data[i]);
      }
    }

    return bins;
  }

  // Specifies how to extract a value from the associated data. The default
  // value function is `Number`, which is equivalent to the identity function.
  histogram.value = function(x) {
    if (!arguments.length) return valuer;
    valuer = x;
    return histogram;
  };

  // Specifies the range of the histogram. Values outside the specified range
  // will be ignored. The argument `x` may be specified either as a two-element
  // array representing the minimum and maximum value of the range, or as a
  // function that returns the range given the array of values and the current
  // index `i`. The default range is the extent (minimum and maximum) of the
  // values.
  histogram.range = function(x) {
    if (!arguments.length) return ranger;
    ranger = d3.functor(x);
    return histogram;
  };

  // Specifies how to bin values in the histogram. The argument `x` may be
  // specified as a number, in which case the range of values will be split
  // uniformly into the given number of bins. Or, `x` may be an array of
  // threshold values, defining the bins; the specified array must contain the
  // rightmost (upper) value, thus specifying n + 1 values for n bins. Or, `x`
  // may be a function which is evaluated, being passed the range, the array of
  // values, and the current index `i`, returning an array of thresholds. The
  // default bin function will divide the values into uniform bins using
  // Sturges' formula.
  histogram.bins = function(x) {
    if (!arguments.length) return binner;
    binner = typeof x === "number"
        ? function(range) { return d3_layout_histogramBinFixed(range, x); }
        : d3.functor(x);
    return histogram;
  };

  // Specifies whether the histogram's `y` value is a count (frequency) or a
  // probability (density). The default value is true.
  histogram.frequency = function(x) {
    if (!arguments.length) return frequency;
    frequency = !!x;
    return histogram;
  };

  return histogram;
};

function d3_layout_histogramBinSturges(range, values) {
  return d3_layout_histogramBinFixed(range, Math.ceil(Math.log(values.length) / Math.LN2 + 1));
}

function d3_layout_histogramBinFixed(range, n) {
  var x = -1,
      b = +range[0],
      m = (range[1] - b) / n,
      f = [];
  while (++x <= n) f[x] = m * x + b;
  return f;
}

function d3_layout_histogramRange(values) {
  return [d3.min(values), d3.max(values)];
}
d3.layout.hierarchy = function() {
  var sort = d3_layout_hierarchySort,
      children = d3_layout_hierarchyChildren,
      value = d3_layout_hierarchyValue;

  // Recursively compute the node depth and value.
  // Also converts the data representation into a standard hierarchy structure.
  function recurse(data, depth, nodes) {
    var childs = children.call(hierarchy, data, depth),
        node = d3_layout_hierarchyInline ? data : {data: data};
    node.depth = depth;
    nodes.push(node);
    if (childs && (n = childs.length)) {
      var i = -1,
          n,
          c = node.children = [],
          v = 0,
          j = depth + 1;
      while (++i < n) {
        d = recurse(childs[i], j, nodes);
        d.parent = node;
        c.push(d);
        v += d.value;
      }
      if (sort) c.sort(sort);
      if (value) node.value = v;
    } else if (value) {
      node.value = +value.call(hierarchy, data, depth) || 0;
    }
    return node;
  }

  // Recursively re-evaluates the node value.
  function revalue(node, depth) {
    var children = node.children,
        v = 0;
    if (children && (n = children.length)) {
      var i = -1,
          n,
          j = depth + 1;
      while (++i < n) v += revalue(children[i], j);
    } else if (value) {
      v = +value.call(hierarchy, d3_layout_hierarchyInline ? node : node.data, depth) || 0;
    }
    if (value) node.value = v;
    return v;
  }

  function hierarchy(d) {
    var nodes = [];
    recurse(d, 0, nodes);
    return nodes;
  }

  hierarchy.sort = function(x) {
    if (!arguments.length) return sort;
    sort = x;
    return hierarchy;
  };

  hierarchy.children = function(x) {
    if (!arguments.length) return children;
    children = x;
    return hierarchy;
  };

  hierarchy.value = function(x) {
    if (!arguments.length) return value;
    value = x;
    return hierarchy;
  };

  // Re-evaluates the `value` property for the specified hierarchy.
  hierarchy.revalue = function(root) {
    revalue(root, 0);
    return root;
  };

  return hierarchy;
};

// A method assignment helper for hierarchy subclasses.
function d3_layout_hierarchyRebind(object, hierarchy) {
  d3.rebind(object, hierarchy, "sort", "children", "value");

  // Add an alias for links, for convenience.
  object.links = d3_layout_hierarchyLinks;

  // If the new API is used, enabling inlining.
  object.nodes = function(d) {
    d3_layout_hierarchyInline = true;
    return (object.nodes = object)(d);
  };

  return object;
}

function d3_layout_hierarchyChildren(d) {
  return d.children;
}

function d3_layout_hierarchyValue(d) {
  return d.value;
}

function d3_layout_hierarchySort(a, b) {
  return b.value - a.value;
}

// Returns an array source+target objects for the specified nodes.
function d3_layout_hierarchyLinks(nodes) {
  return d3.merge(nodes.map(function(parent) {
    return (parent.children || []).map(function(child) {
      return {source: parent, target: child};
    });
  }));
}

// For backwards-compatibility, don't enable inlining by default.
var d3_layout_hierarchyInline = false;
d3.layout.pack = function() {
  var hierarchy = d3.layout.hierarchy().sort(d3_layout_packSort),
      size = [1, 1];

  function pack(d, i) {
    var nodes = hierarchy.call(this, d, i),
        root = nodes[0];

    // Recursively compute the layout.
    root.x = 0;
    root.y = 0;
    d3_layout_packTree(root);

    // Scale the layout to fit the requested size.
    var w = size[0],
        h = size[1],
        k = 1 / Math.max(2 * root.r / w, 2 * root.r / h);
    d3_layout_packTransform(root, w / 2, h / 2, k);

    return nodes;
  }

  pack.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return pack;
  };

  return d3_layout_hierarchyRebind(pack, hierarchy);
};

function d3_layout_packSort(a, b) {
  return a.value - b.value;
}

function d3_layout_packInsert(a, b) {
  var c = a._pack_next;
  a._pack_next = b;
  b._pack_prev = a;
  b._pack_next = c;
  c._pack_prev = b;
}

function d3_layout_packSplice(a, b) {
  a._pack_next = b;
  b._pack_prev = a;
}

function d3_layout_packIntersects(a, b) {
  var dx = b.x - a.x,
      dy = b.y - a.y,
      dr = a.r + b.r;
  return dr * dr - dx * dx - dy * dy > .001; // within epsilon
}

function d3_layout_packCircle(nodes) {
  var xMin = Infinity,
      xMax = -Infinity,
      yMin = Infinity,
      yMax = -Infinity,
      n = nodes.length,
      a, b, c, j, k;

  function bound(node) {
    xMin = Math.min(node.x - node.r, xMin);
    xMax = Math.max(node.x + node.r, xMax);
    yMin = Math.min(node.y - node.r, yMin);
    yMax = Math.max(node.y + node.r, yMax);
  }

  // Create node links.
  nodes.forEach(d3_layout_packLink);

  // Create first node.
  a = nodes[0];
  a.x = -a.r;
  a.y = 0;
  bound(a);

  // Create second node.
  if (n > 1) {
    b = nodes[1];
    b.x = b.r;
    b.y = 0;
    bound(b);

    // Create third node and build chain.
    if (n > 2) {
      c = nodes[2];
      d3_layout_packPlace(a, b, c);
      bound(c);
      d3_layout_packInsert(a, c);
      a._pack_prev = c;
      d3_layout_packInsert(c, b);
      b = a._pack_next;

      // Now iterate through the rest.
      for (var i = 3; i < n; i++) {
        d3_layout_packPlace(a, b, c = nodes[i]);

        // Search for the closest intersection.
        var isect = 0, s1 = 1, s2 = 1;
        for (j = b._pack_next; j !== b; j = j._pack_next, s1++) {
          if (d3_layout_packIntersects(j, c)) {
            isect = 1;
            break;
          }
        }
        if (isect == 1) {
          for (k = a._pack_prev; k !== j._pack_prev; k = k._pack_prev, s2++) {
            if (d3_layout_packIntersects(k, c)) {
              break;
            }
          }
        }

        // Update node chain.
        if (isect) {
          if (s1 < s2 || (s1 == s2 && b.r < a.r)) d3_layout_packSplice(a, b = j);
          else d3_layout_packSplice(a = k, b);
          i--;
        } else {
          d3_layout_packInsert(a, c);
          b = c;
          bound(c);
        }
      }
    }
  }

  // Re-center the circles and return the encompassing radius.
  var cx = (xMin + xMax) / 2,
      cy = (yMin + yMax) / 2,
      cr = 0;
  for (var i = 0; i < n; i++) {
    var node = nodes[i];
    node.x -= cx;
    node.y -= cy;
    cr = Math.max(cr, node.r + Math.sqrt(node.x * node.x + node.y * node.y));
  }

  // Remove node links.
  nodes.forEach(d3_layout_packUnlink);

  return cr;
}

function d3_layout_packLink(node) {
  node._pack_next = node._pack_prev = node;
}

function d3_layout_packUnlink(node) {
  delete node._pack_next;
  delete node._pack_prev;
}

function d3_layout_packTree(node) {
  var children = node.children;
  if (children && children.length) {
    children.forEach(d3_layout_packTree);
    node.r = d3_layout_packCircle(children);
  } else {
    node.r = Math.sqrt(node.value);
  }
}

function d3_layout_packTransform(node, x, y, k) {
  var children = node.children;
  node.x = (x += k * node.x);
  node.y = (y += k * node.y);
  node.r *= k;
  if (children) {
    var i = -1, n = children.length;
    while (++i < n) d3_layout_packTransform(children[i], x, y, k);
  }
}

function d3_layout_packPlace(a, b, c) {
  var db = a.r + c.r,
      dx = b.x - a.x,
      dy = b.y - a.y;
  if (db && (dx || dy)) {
    var da = b.r + c.r,
        dc = Math.sqrt(dx * dx + dy * dy),
        cos = Math.max(-1, Math.min(1, (db * db + dc * dc - da * da) / (2 * db * dc))),
        theta = Math.acos(cos),
        x = cos * (db /= dc),
        y = Math.sin(theta) * db;
    c.x = a.x + x * dx + y * dy;
    c.y = a.y + x * dy - y * dx;
  } else {
    c.x = a.x + db;
    c.y = a.y;
  }
}
// Implements a hierarchical layout using the cluster (or dendrogram)
// algorithm.
d3.layout.cluster = function() {
  var hierarchy = d3.layout.hierarchy().sort(null).value(null),
      separation = d3_layout_treeSeparation,
      size = [1, 1]; // width, height

  function cluster(d, i) {
    var nodes = hierarchy.call(this, d, i),
        root = nodes[0],
        previousNode,
        x = 0,
        kx,
        ky;

    // First walk, computing the initial x & y values.
    d3_layout_treeVisitAfter(root, function(node) {
      var children = node.children;
      if (children && children.length) {
        node.x = d3_layout_clusterX(children);
        node.y = d3_layout_clusterY(children);
      } else {
        node.x = previousNode ? x += separation(node, previousNode) : 0;
        node.y = 0;
        previousNode = node;
      }
    });

    // Compute the left-most, right-most, and depth-most nodes for extents.
    var left = d3_layout_clusterLeft(root),
        right = d3_layout_clusterRight(root),
        x0 = left.x - separation(left, right) / 2,
        x1 = right.x + separation(right, left) / 2;

    // Second walk, normalizing x & y to the desired size.
    d3_layout_treeVisitAfter(root, function(node) {
      node.x = (node.x - x0) / (x1 - x0) * size[0];
      node.y = (1 - (root.y ? node.y / root.y : 1)) * size[1];
    });

    return nodes;
  }

  cluster.separation = function(x) {
    if (!arguments.length) return separation;
    separation = x;
    return cluster;
  };

  cluster.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return cluster;
  };

  return d3_layout_hierarchyRebind(cluster, hierarchy);
};

function d3_layout_clusterY(children) {
  return 1 + d3.max(children, function(child) {
    return child.y;
  });
}

function d3_layout_clusterX(children) {
  return children.reduce(function(x, child) {
    return x + child.x;
  }, 0) / children.length;
}

function d3_layout_clusterLeft(node) {
  var children = node.children;
  return children && children.length ? d3_layout_clusterLeft(children[0]) : node;
}

function d3_layout_clusterRight(node) {
  var children = node.children, n;
  return children && (n = children.length) ? d3_layout_clusterRight(children[n - 1]) : node;
}
// Node-link tree diagram using the Reingold-Tilford "tidy" algorithm
d3.layout.tree = function() {
  var hierarchy = d3.layout.hierarchy().sort(null).value(null),
      separation = d3_layout_treeSeparation,
      size = [1, 1]; // width, height

  function tree(d, i) {
    var nodes = hierarchy.call(this, d, i),
        root = nodes[0];

    function firstWalk(node, previousSibling) {
      var children = node.children,
          layout = node._tree;
      if (children && (n = children.length)) {
        var n,
            firstChild = children[0],
            previousChild,
            ancestor = firstChild,
            child,
            i = -1;
        while (++i < n) {
          child = children[i];
          firstWalk(child, previousChild);
          ancestor = apportion(child, previousChild, ancestor);
          previousChild = child;
        }
        d3_layout_treeShift(node);
        var midpoint = .5 * (firstChild._tree.prelim + child._tree.prelim);
        if (previousSibling) {
          layout.prelim = previousSibling._tree.prelim + separation(node, previousSibling);
          layout.mod = layout.prelim - midpoint;
        } else {
          layout.prelim = midpoint;
        }
      } else {
        if (previousSibling) {
          layout.prelim = previousSibling._tree.prelim + separation(node, previousSibling);
        }
      }
    }

    function secondWalk(node, x) {
      node.x = node._tree.prelim + x;
      var children = node.children;
      if (children && (n = children.length)) {
        var i = -1,
            n;
        x += node._tree.mod;
        while (++i < n) {
          secondWalk(children[i], x);
        }
      }
    }

    function apportion(node, previousSibling, ancestor) {
      if (previousSibling) {
        var vip = node,
            vop = node,
            vim = previousSibling,
            vom = node.parent.children[0],
            sip = vip._tree.mod,
            sop = vop._tree.mod,
            sim = vim._tree.mod,
            som = vom._tree.mod,
            shift;
        while (vim = d3_layout_treeRight(vim), vip = d3_layout_treeLeft(vip), vim && vip) {
          vom = d3_layout_treeLeft(vom);
          vop = d3_layout_treeRight(vop);
          vop._tree.ancestor = node;
          shift = vim._tree.prelim + sim - vip._tree.prelim - sip + separation(vim, vip);
          if (shift > 0) {
            d3_layout_treeMove(d3_layout_treeAncestor(vim, node, ancestor), node, shift);
            sip += shift;
            sop += shift;
          }
          sim += vim._tree.mod;
          sip += vip._tree.mod;
          som += vom._tree.mod;
          sop += vop._tree.mod;
        }
        if (vim && !d3_layout_treeRight(vop)) {
          vop._tree.thread = vim;
          vop._tree.mod += sim - sop;
        }
        if (vip && !d3_layout_treeLeft(vom)) {
          vom._tree.thread = vip;
          vom._tree.mod += sip - som;
          ancestor = node;
        }
      }
      return ancestor;
    }

    // Initialize temporary layout variables.
    d3_layout_treeVisitAfter(root, function(node, previousSibling) {
      node._tree = {
        ancestor: node,
        prelim: 0,
        mod: 0,
        change: 0,
        shift: 0,
        number: previousSibling ? previousSibling._tree.number + 1 : 0
      };
    });

    // Compute the layout using Buchheim et al.'s algorithm.
    firstWalk(root);
    secondWalk(root, -root._tree.prelim);

    // Compute the left-most, right-most, and depth-most nodes for extents.
    var left = d3_layout_treeSearch(root, d3_layout_treeLeftmost),
        right = d3_layout_treeSearch(root, d3_layout_treeRightmost),
        deep = d3_layout_treeSearch(root, d3_layout_treeDeepest),
        x0 = left.x - separation(left, right) / 2,
        x1 = right.x + separation(right, left) / 2,
        y1 = deep.depth || 1;

    // Clear temporary layout variables; transform x and y.
    d3_layout_treeVisitAfter(root, function(node) {
      node.x = (node.x - x0) / (x1 - x0) * size[0];
      node.y = node.depth / y1 * size[1];
      delete node._tree;
    });

    return nodes;
  }

  tree.separation = function(x) {
    if (!arguments.length) return separation;
    separation = x;
    return tree;
  };

  tree.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return tree;
  };

  return d3_layout_hierarchyRebind(tree, hierarchy);
};

function d3_layout_treeSeparation(a, b) {
  return a.parent == b.parent ? 1 : 2;
}

// function d3_layout_treeSeparationRadial(a, b) {
//   return (a.parent == b.parent ? 1 : 2) / a.depth;
// }

function d3_layout_treeLeft(node) {
  var children = node.children;
  return children && children.length ? children[0] : node._tree.thread;
}

function d3_layout_treeRight(node) {
  var children = node.children,
      n;
  return children && (n = children.length) ? children[n - 1] : node._tree.thread;
}

function d3_layout_treeSearch(node, compare) {
  var children = node.children;
  if (children && (n = children.length)) {
    var child,
        n,
        i = -1;
    while (++i < n) {
      if (compare(child = d3_layout_treeSearch(children[i], compare), node) > 0) {
        node = child;
      }
    }
  }
  return node;
}

function d3_layout_treeRightmost(a, b) {
  return a.x - b.x;
}

function d3_layout_treeLeftmost(a, b) {
  return b.x - a.x;
}

function d3_layout_treeDeepest(a, b) {
  return a.depth - b.depth;
}

function d3_layout_treeVisitAfter(node, callback) {
  function visit(node, previousSibling) {
    var children = node.children;
    if (children && (n = children.length)) {
      var child,
          previousChild = null,
          i = -1,
          n;
      while (++i < n) {
        child = children[i];
        visit(child, previousChild);
        previousChild = child;
      }
    }
    callback(node, previousSibling);
  }
  visit(node, null);
}

function d3_layout_treeShift(node) {
  var shift = 0,
      change = 0,
      children = node.children,
      i = children.length,
      child;
  while (--i >= 0) {
    child = children[i]._tree;
    child.prelim += shift;
    child.mod += shift;
    shift += child.shift + (change += child.change);
  }
}

function d3_layout_treeMove(ancestor, node, shift) {
  ancestor = ancestor._tree;
  node = node._tree;
  var change = shift / (node.number - ancestor.number);
  ancestor.change += change;
  node.change -= change;
  node.shift += shift;
  node.prelim += shift;
  node.mod += shift;
}

function d3_layout_treeAncestor(vim, node, ancestor) {
  return vim._tree.ancestor.parent == node.parent
      ? vim._tree.ancestor
      : ancestor;
}
// Squarified Treemaps by Mark Bruls, Kees Huizing, and Jarke J. van Wijk
// Modified to support a target aspect ratio by Jeff Heer
d3.layout.treemap = function() {
  var hierarchy = d3.layout.hierarchy(),
      round = Math.round,
      size = [1, 1], // width, height
      padding = null,
      pad = d3_layout_treemapPadNull,
      sticky = false,
      stickies,
      ratio = 0.5 * (1 + Math.sqrt(5)); // golden ratio

  // Compute the area for each child based on value & scale.
  function scale(children, k) {
    var i = -1,
        n = children.length,
        child,
        area;
    while (++i < n) {
      area = (child = children[i]).value * (k < 0 ? 0 : k);
      child.area = isNaN(area) || area <= 0 ? 0 : area;
    }
  }

  // Recursively arranges the specified node's children into squarified rows.
  function squarify(node) {
    var children = node.children;
    if (children && children.length) {
      var rect = pad(node),
          row = [],
          remaining = children.slice(), // copy-on-write
          child,
          best = Infinity, // the best row score so far
          score, // the current row score
          u = Math.min(rect.dx, rect.dy), // initial orientation
          n;
      scale(remaining, rect.dx * rect.dy / node.value);
      row.area = 0;
      while ((n = remaining.length) > 0) {
        row.push(child = remaining[n - 1]);
        row.area += child.area;
        if ((score = worst(row, u)) <= best) { // continue with this orientation
          remaining.pop();
          best = score;
        } else { // abort, and try a different orientation
          row.area -= row.pop().area;
          position(row, u, rect, false);
          u = Math.min(rect.dx, rect.dy);
          row.length = row.area = 0;
          best = Infinity;
        }
      }
      if (row.length) {
        position(row, u, rect, true);
        row.length = row.area = 0;
      }
      children.forEach(squarify);
    }
  }

  // Recursively resizes the specified node's children into existing rows.
  // Preserves the existing layout!
  function stickify(node) {
    var children = node.children;
    if (children && children.length) {
      var rect = pad(node),
          remaining = children.slice(), // copy-on-write
          child,
          row = [];
      scale(remaining, rect.dx * rect.dy / node.value);
      row.area = 0;
      while (child = remaining.pop()) {
        row.push(child);
        row.area += child.area;
        if (child.z != null) {
          position(row, child.z ? rect.dx : rect.dy, rect, !remaining.length);
          row.length = row.area = 0;
        }
      }
      children.forEach(stickify);
    }
  }

  // Computes the score for the specified row, as the worst aspect ratio.
  function worst(row, u) {
    var s = row.area,
        r,
        rmax = 0,
        rmin = Infinity,
        i = -1,
        n = row.length;
    while (++i < n) {
      if (!(r = row[i].area)) continue;
      if (r < rmin) rmin = r;
      if (r > rmax) rmax = r;
    }
    s *= s;
    u *= u;
    return s
        ? Math.max((u * rmax * ratio) / s, s / (u * rmin * ratio))
        : Infinity;
  }

  // Positions the specified row of nodes. Modifies `rect`.
  function position(row, u, rect, flush) {
    var i = -1,
        n = row.length,
        x = rect.x,
        y = rect.y,
        v = u ? round(row.area / u) : 0,
        o;
    if (u == rect.dx) { // horizontal subdivision
      if (flush || v > rect.dy) v = rect.dy; // over+underflow
      while (++i < n) {
        o = row[i];
        o.x = x;
        o.y = y;
        o.dy = v;
        x += o.dx = Math.min(rect.x + rect.dx - x, v ? round(o.area / v) : 0);
      }
      o.z = true;
      o.dx += rect.x + rect.dx - x; // rounding error
      rect.y += v;
      rect.dy -= v;
    } else { // vertical subdivision
      if (flush || v > rect.dx) v = rect.dx; // over+underflow
      while (++i < n) {
        o = row[i];
        o.x = x;
        o.y = y;
        o.dx = v;
        y += o.dy = Math.min(rect.y + rect.dy - y, v ? round(o.area / v) : 0);
      }
      o.z = false;
      o.dy += rect.y + rect.dy - y; // rounding error
      rect.x += v;
      rect.dx -= v;
    }
  }

  function treemap(d) {
    var nodes = stickies || hierarchy(d),
        root = nodes[0];
    root.x = 0;
    root.y = 0;
    root.dx = size[0];
    root.dy = size[1];
    if (stickies) hierarchy.revalue(root);
    scale([root], root.dx * root.dy / root.value);
    (stickies ? stickify : squarify)(root);
    if (sticky) stickies = nodes;
    return nodes;
  }

  treemap.size = function(x) {
    if (!arguments.length) return size;
    size = x;
    return treemap;
  };

  treemap.padding = function(x) {
    if (!arguments.length) return padding;

    function padFunction(node) {
      var p = x.call(treemap, node, node.depth);
      return p == null
          ? d3_layout_treemapPadNull(node)
          : d3_layout_treemapPad(node, typeof p === "number" ? [p, p, p, p] : p);
    }

    function padConstant(node) {
      return d3_layout_treemapPad(node, x);
    }

    var type;
    pad = (padding = x) == null ? d3_layout_treemapPadNull
        : (type = typeof x) === "function" ? padFunction
        : type === "number" ? (x = [x, x, x, x], padConstant)
        : padConstant;
    return treemap;
  };

  treemap.round = function(x) {
    if (!arguments.length) return round != Number;
    round = x ? Math.round : Number;
    return treemap;
  };

  treemap.sticky = function(x) {
    if (!arguments.length) return sticky;
    sticky = x;
    stickies = null;
    return treemap;
  };

  treemap.ratio = function(x) {
    if (!arguments.length) return ratio;
    ratio = x;
    return treemap;
  };

  return d3_layout_hierarchyRebind(treemap, hierarchy);
};

function d3_layout_treemapPadNull(node) {
  return {x: node.x, y: node.y, dx: node.dx, dy: node.dy};
}

function d3_layout_treemapPad(node, padding) {
  var x = node.x + padding[3],
      y = node.y + padding[0],
      dx = node.dx - padding[1] - padding[3],
      dy = node.dy - padding[0] - padding[2];
  if (dx < 0) { x += dx / 2; dx = 0; }
  if (dy < 0) { y += dy / 2; dy = 0; }
  return {x: x, y: y, dx: dx, dy: dy};
}
d3.csv = function(url, callback) {
  d3.text(url, "text/csv", function(text) {
    callback(text && d3.csv.parse(text));
  });
};
d3.csv.parse = function(text) {
  var header;
  return d3.csv.parseRows(text, function(row, i) {
    if (i) {
      var o = {}, j = -1, m = header.length;
      while (++j < m) o[header[j]] = row[j];
      return o;
    } else {
      header = row;
      return null;
    }
  });
};

d3.csv.parseRows = function(text, f) {
  var EOL = {}, // sentinel value for end-of-line
      EOF = {}, // sentinel value for end-of-file
      rows = [], // output rows
      re = /\r\n|[,\r\n]/g, // field separator regex
      n = 0, // the current line number
      t, // the current token
      eol; // is the current token followed by EOL?

  re.lastIndex = 0; // work-around bug in FF 3.6

  /** @private Returns the next token. */
  function token() {
    if (re.lastIndex >= text.length) return EOF; // special case: end of file
    if (eol) { eol = false; return EOL; } // special case: end of line

    // special case: quotes
    var j = re.lastIndex;
    if (text.charCodeAt(j) === 34) {
      var i = j;
      while (i++ < text.length) {
        if (text.charCodeAt(i) === 34) {
          if (text.charCodeAt(i + 1) !== 34) break;
          i++;
        }
      }
      re.lastIndex = i + 2;
      var c = text.charCodeAt(i + 1);
      if (c === 13) {
        eol = true;
        if (text.charCodeAt(i + 2) === 10) re.lastIndex++;
      } else if (c === 10) {
        eol = true;
      }
      return text.substring(j + 1, i).replace(/""/g, "\"");
    }

    // common case
    var m = re.exec(text);
    if (m) {
      eol = m[0].charCodeAt(0) !== 44;
      return text.substring(j, m.index);
    }
    re.lastIndex = text.length;
    return text.substring(j);
  }

  while ((t = token()) !== EOF) {
    var a = [];
    while ((t !== EOL) && (t !== EOF)) {
      a.push(t);
      t = token();
    }
    if (f && !(a = f(a, n++))) continue;
    rows.push(a);
  }

  return rows;
};
d3.csv.format = function(rows) {
  return rows.map(d3_csv_formatRow).join("\n");
};

function d3_csv_formatRow(row) {
  return row.map(d3_csv_formatValue).join(",");
}

function d3_csv_formatValue(text) {
  return /[",\n]/.test(text)
      ? "\"" + text.replace(/\"/g, "\"\"") + "\""
      : text;
}
d3.geo = {};

var d3_geo_radians = Math.PI / 180;
// TODO clip input coordinates on opposite hemisphere
d3.geo.azimuthal = function() {
  var mode = "orthographic", // or stereographic, gnomonic, equidistant or equalarea
      origin,
      scale = 200,
      translate = [480, 250],
      x0,
      y0,
      cy0,
      sy0;

  function azimuthal(coordinates) {
    var x1 = coordinates[0] * d3_geo_radians - x0,
        y1 = coordinates[1] * d3_geo_radians,
        cx1 = Math.cos(x1),
        sx1 = Math.sin(x1),
        cy1 = Math.cos(y1),
        sy1 = Math.sin(y1),
        cc = mode !== "orthographic" ? sy0 * sy1 + cy0 * cy1 * cx1 : null,
        c,
        k = mode === "stereographic" ? 1 / (1 + cc)
          : mode === "gnomonic" ? 1 / cc
          : mode === "equidistant" ? (c = Math.acos(cc), c ? c / Math.sin(c) : 0)
          : mode === "equalarea" ? Math.sqrt(2 / (1 + cc))
          : 1,
        x = k * cy1 * sx1,
        y = k * (sy0 * cy1 * cx1 - cy0 * sy1);
    return [
      scale * x + translate[0],
      scale * y + translate[1]
    ];
  }

  azimuthal.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale,
        p = Math.sqrt(x * x + y * y),
        c = mode === "stereographic" ? 2 * Math.atan(p)
          : mode === "gnomonic" ? Math.atan(p)
          : mode === "equidistant" ? p
          : mode === "equalarea" ? 2 * Math.asin(.5 * p)
          : Math.asin(p),
        sc = Math.sin(c),
        cc = Math.cos(c);
    return [
      (x0 + Math.atan2(x * sc, p * cy0 * cc + y * sy0 * sc)) / d3_geo_radians,
      Math.asin(cc * sy0 - (p ? (y * sc * cy0) / p : 0)) / d3_geo_radians
    ];
  };

  azimuthal.mode = function(x) {
    if (!arguments.length) return mode;
    mode = x + "";
    return azimuthal;
  };

  azimuthal.origin = function(x) {
    if (!arguments.length) return origin;
    origin = x;
    x0 = origin[0] * d3_geo_radians;
    y0 = origin[1] * d3_geo_radians;
    cy0 = Math.cos(y0);
    sy0 = Math.sin(y0);
    return azimuthal;
  };

  azimuthal.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return azimuthal;
  };

  azimuthal.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return azimuthal;
  };

  return azimuthal.origin([0, 0]);
};
// Derived from Tom Carden's Albers implementation for Protovis.
// http://gist.github.com/476238
// http://mathworld.wolfram.com/AlbersEqual-AreaConicProjection.html

d3.geo.albers = function() {
  var origin = [-98, 38],
      parallels = [29.5, 45.5],
      scale = 1000,
      translate = [480, 250],
      lng0, // d3_geo_radians * origin[0]
      n,
      C,
      p0;

  function albers(coordinates) {
    var t = n * (d3_geo_radians * coordinates[0] - lng0),
        p = Math.sqrt(C - 2 * n * Math.sin(d3_geo_radians * coordinates[1])) / n;
    return [
      scale * p * Math.sin(t) + translate[0],
      scale * (p * Math.cos(t) - p0) + translate[1]
    ];
  }

  albers.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale,
        p0y = p0 + y,
        t = Math.atan2(x, p0y),
        p = Math.sqrt(x * x + p0y * p0y);
    return [
      (lng0 + t / n) / d3_geo_radians,
      Math.asin((C - p * p * n * n) / (2 * n)) / d3_geo_radians
    ];
  };

  function reload() {
    var phi1 = d3_geo_radians * parallels[0],
        phi2 = d3_geo_radians * parallels[1],
        lat0 = d3_geo_radians * origin[1],
        s = Math.sin(phi1),
        c = Math.cos(phi1);
    lng0 = d3_geo_radians * origin[0];
    n = .5 * (s + Math.sin(phi2));
    C = c * c + 2 * n * s;
    p0 = Math.sqrt(C - 2 * n * Math.sin(lat0)) / n;
    return albers;
  }

  albers.origin = function(x) {
    if (!arguments.length) return origin;
    origin = [+x[0], +x[1]];
    return reload();
  };

  albers.parallels = function(x) {
    if (!arguments.length) return parallels;
    parallels = [+x[0], +x[1]];
    return reload();
  };

  albers.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return albers;
  };

  albers.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return albers;
  };

  return reload();
};

// A composite projection for the United States, 960x500. The set of standard
// parallels for each region comes from USGS, which is published here:
// http://egsc.usgs.gov/isb/pubs/MapProjections/projections.html#albers
// TODO allow the composite projection to be rescaled?
d3.geo.albersUsa = function() {
  var lower48 = d3.geo.albers();

  var alaska = d3.geo.albers()
      .origin([-160, 60])
      .parallels([55, 65]);

  var hawaii = d3.geo.albers()
      .origin([-160, 20])
      .parallels([8, 18]);

  var puertoRico = d3.geo.albers()
      .origin([-60, 10])
      .parallels([8, 18]);

  function albersUsa(coordinates) {
    var lon = coordinates[0],
        lat = coordinates[1];
    return (lat > 50 ? alaska
        : lon < -140 ? hawaii
        : lat < 21 ? puertoRico
        : lower48)(coordinates);
  }

  albersUsa.scale = function(x) {
    if (!arguments.length) return lower48.scale();
    lower48.scale(x);
    alaska.scale(x * .6);
    hawaii.scale(x);
    puertoRico.scale(x * 1.5);
    return albersUsa.translate(lower48.translate());
  };

  albersUsa.translate = function(x) {
    if (!arguments.length) return lower48.translate();
    var dz = lower48.scale() / 1000,
        dx = x[0],
        dy = x[1];
    lower48.translate(x);
    alaska.translate([dx - 400 * dz, dy + 170 * dz]);
    hawaii.translate([dx - 190 * dz, dy + 200 * dz]);
    puertoRico.translate([dx + 580 * dz, dy + 430 * dz]);
    return albersUsa;
  };

  return albersUsa.scale(lower48.scale());
};
d3.geo.bonne = function() {
  var scale = 200,
      translate = [480, 250],
      x0, // origin longitude in radians
      y0, // origin latitude in radians
      y1, // parallel latitude in radians
      c1; // cot(y1)

  function bonne(coordinates) {
    var x = coordinates[0] * d3_geo_radians - x0,
        y = coordinates[1] * d3_geo_radians - y0;
    if (y1) {
      var p = c1 + y1 - y, E = x * Math.cos(y) / p;
      x = p * Math.sin(E);
      y = p * Math.cos(E) - c1;
    } else {
      x *= Math.cos(y);
      y *= -1;
    }
    return [
      scale * x + translate[0],
      scale * y + translate[1]
    ];
  }

  bonne.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale;
    if (y1) {
      var c = c1 + y, p = Math.sqrt(x * x + c * c);
      y = c1 + y1 - p;
      x = x0 + p * Math.atan2(x, c) / Math.cos(y);
    } else {
      y *= -1;
      x /= Math.cos(y);
    }
    return [
      x / d3_geo_radians,
      y / d3_geo_radians
    ];
  };

  // 90° for Werner, 0° for Sinusoidal
  bonne.parallel = function(x) {
    if (!arguments.length) return y1 / d3_geo_radians;
    c1 = 1 / Math.tan(y1 = x * d3_geo_radians);
    return bonne;
  };

  bonne.origin = function(x) {
    if (!arguments.length) return [x0 / d3_geo_radians, y0 / d3_geo_radians];
    x0 = x[0] * d3_geo_radians;
    y0 = x[1] * d3_geo_radians;
    return bonne;
  };

  bonne.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return bonne;
  };

  bonne.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return bonne;
  };

  return bonne.origin([0, 0]).parallel(45);
};
d3.geo.equirectangular = function() {
  var scale = 500,
      translate = [480, 250];

  function equirectangular(coordinates) {
    var x = coordinates[0] / 360,
        y = -coordinates[1] / 360;
    return [
      scale * x + translate[0],
      scale * y + translate[1]
    ];
  }

  equirectangular.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale;
    return [
      360 * x,
      -360 * y
    ];
  };

  equirectangular.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return equirectangular;
  };

  equirectangular.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return equirectangular;
  };

  return equirectangular;
};
d3.geo.mercator = function() {
  var scale = 500,
      translate = [480, 250];

  function mercator(coordinates) {
    var x = coordinates[0] / 360,
        y = -(Math.log(Math.tan(Math.PI / 4 + coordinates[1] * d3_geo_radians / 2)) / d3_geo_radians) / 360;
    return [
      scale * x + translate[0],
      scale * Math.max(-.5, Math.min(.5, y)) + translate[1]
    ];
  }

  mercator.invert = function(coordinates) {
    var x = (coordinates[0] - translate[0]) / scale,
        y = (coordinates[1] - translate[1]) / scale;
    return [
      360 * x,
      2 * Math.atan(Math.exp(-360 * y * d3_geo_radians)) / d3_geo_radians - 90
    ];
  };

  mercator.scale = function(x) {
    if (!arguments.length) return scale;
    scale = +x;
    return mercator;
  };

  mercator.translate = function(x) {
    if (!arguments.length) return translate;
    translate = [+x[0], +x[1]];
    return mercator;
  };

  return mercator;
};
function d3_geo_type(types, defaultValue) {
  return function(object) {
    return object && types.hasOwnProperty(object.type) ? types[object.type](object) : defaultValue;
  };
}
/**
 * Returns a function that, given a GeoJSON object (e.g., a feature), returns
 * the corresponding SVG path. The function can be customized by overriding the
 * projection. Point features are mapped to circles with a default radius of
 * 4.5px; the radius can be specified either as a constant or a function that
 * is evaluated per object.
 */
d3.geo.path = function() {
  var pointRadius = 4.5,
      pointCircle = d3_path_circle(pointRadius),
      projection = d3.geo.albersUsa();

  function path(d, i) {
    if (typeof pointRadius === "function") {
      pointCircle = d3_path_circle(pointRadius.apply(this, arguments));
    }
    return pathType(d) || null;
  }

  function project(coordinates) {
    return projection(coordinates).join(",");
  }

  var pathType = d3_geo_type({

    FeatureCollection: function(o) {
      var path = [],
          features = o.features,
          i = -1, // features.index
          n = features.length;
      while (++i < n) path.push(pathType(features[i].geometry));
      return path.join("");
    },

    Feature: function(o) {
      return pathType(o.geometry);
    },

    Point: function(o) {
      return "M" + project(o.coordinates) + pointCircle;
    },

    MultiPoint: function(o) {
      var path = [],
          coordinates = o.coordinates,
          i = -1, // coordinates.index
          n = coordinates.length;
      while (++i < n) path.push("M", project(coordinates[i]), pointCircle);
      return path.join("");
    },

    LineString: function(o) {
      var path = ["M"],
          coordinates = o.coordinates,
          i = -1, // coordinates.index
          n = coordinates.length;
      while (++i < n) path.push(project(coordinates[i]), "L");
      path.pop();
      return path.join("");
    },

    MultiLineString: function(o) {
      var path = [],
          coordinates = o.coordinates,
          i = -1, // coordinates.index
          n = coordinates.length,
          subcoordinates, // coordinates[i]
          j, // subcoordinates.index
          m; // subcoordinates.length
      while (++i < n) {
        subcoordinates = coordinates[i];
        j = -1;
        m = subcoordinates.length;
        path.push("M");
        while (++j < m) path.push(project(subcoordinates[j]), "L");
        path.pop();
      }
      return path.join("");
    },

    Polygon: function(o) {
      var path = [],
          coordinates = o.coordinates,
          i = -1, // coordinates.index
          n = coordinates.length,
          subcoordinates, // coordinates[i]
          j, // subcoordinates.index
          m; // subcoordinates.length
      while (++i < n) {
        subcoordinates = coordinates[i];
        j = -1;
        if ((m = subcoordinates.length - 1) > 0) {
          path.push("M");
          while (++j < m) path.push(project(subcoordinates[j]), "L");
          path[path.length - 1] = "Z";
        }
      }
      return path.join("");
    },

    MultiPolygon: function(o) {
      var path = [],
          coordinates = o.coordinates,
          i = -1, // coordinates index
          n = coordinates.length,
          subcoordinates, // coordinates[i]
          j, // subcoordinates index
          m, // subcoordinates.length
          subsubcoordinates, // subcoordinates[j]
          k, // subsubcoordinates index
          p; // subsubcoordinates.length
      while (++i < n) {
        subcoordinates = coordinates[i];
        j = -1;
        m = subcoordinates.length;
        while (++j < m) {
          subsubcoordinates = subcoordinates[j];
          k = -1;
          if ((p = subsubcoordinates.length - 1) > 0) {
            path.push("M");
            while (++k < p) path.push(project(subsubcoordinates[k]), "L");
            path[path.length - 1] = "Z";
          }
        }
      }
      return path.join("");
    },

    GeometryCollection: function(o) {
      var path = [],
          geometries = o.geometries,
          i = -1, // geometries index
          n = geometries.length;
      while (++i < n) path.push(pathType(geometries[i]));
      return path.join("");
    }

  });

  var areaType = path.area = d3_geo_type({

    FeatureCollection: function(o) {
      var area = 0,
          features = o.features,
          i = -1, // features.index
          n = features.length;
      while (++i < n) area += areaType(features[i]);
      return area;
    },

    Feature: function(o) {
      return areaType(o.geometry);
    },

    Polygon: function(o) {
      return polygonArea(o.coordinates);
    },

    MultiPolygon: function(o) {
      var sum = 0,
          coordinates = o.coordinates,
          i = -1, // coordinates index
          n = coordinates.length;
      while (++i < n) sum += polygonArea(coordinates[i]);
      return sum;
    },

    GeometryCollection: function(o) {
      var sum = 0,
          geometries = o.geometries,
          i = -1, // geometries index
          n = geometries.length;
      while (++i < n) sum += areaType(geometries[i]);
      return sum;
    }

  }, 0);

  function polygonArea(coordinates) {
    var sum = area(coordinates[0]), // exterior ring
        i = 0, // coordinates.index
        n = coordinates.length;
    while (++i < n) sum -= area(coordinates[i]); // holes
    return sum;
  }

  function polygonCentroid(coordinates) {
    var polygon = d3.geom.polygon(coordinates[0].map(projection)), // exterior ring
        area = polygon.area(),
        centroid = polygon.centroid(area < 0 ? (area *= -1, 1) : -1),
        x = centroid[0],
        y = centroid[1],
        z = area,
        i = 0, // coordinates index
        n = coordinates.length;
    while (++i < n) {
      polygon = d3.geom.polygon(coordinates[i].map(projection)); // holes
      area = polygon.area();
      centroid = polygon.centroid(area < 0 ? (area *= -1, 1) : -1);
      x -= centroid[0];
      y -= centroid[1];
      z -= area;
    }
    return [x, y, 6 * z]; // weighted centroid
  }

  var centroidType = path.centroid = d3_geo_type({

    // TODO FeatureCollection
    // TODO Point
    // TODO MultiPoint
    // TODO LineString
    // TODO MultiLineString
    // TODO GeometryCollection

    Feature: function(o) {
      return centroidType(o.geometry);
    },

    Polygon: function(o) {
      var centroid = polygonCentroid(o.coordinates);
      return [centroid[0] / centroid[2], centroid[1] / centroid[2]];
    },

    MultiPolygon: function(o) {
      var area = 0,
          coordinates = o.coordinates,
          centroid,
          x = 0,
          y = 0,
          z = 0,
          i = -1, // coordinates index
          n = coordinates.length;
      while (++i < n) {
        centroid = polygonCentroid(coordinates[i]);
        x += centroid[0];
        y += centroid[1];
        z += centroid[2];
      }
      return [x / z, y / z];
    }

  });

  function area(coordinates) {
    return Math.abs(d3.geom.polygon(coordinates.map(projection)).area());
  }

  path.projection = function(x) {
    projection = x;
    return path;
  };

  path.pointRadius = function(x) {
    if (typeof x === "function") pointRadius = x;
    else {
      pointRadius = +x;
      pointCircle = d3_path_circle(pointRadius);
    }
    return path;
  };

  return path;
};

function d3_path_circle(radius) {
  return "m0," + radius
      + "a" + radius + "," + radius + " 0 1,1 0," + (-2 * radius)
      + "a" + radius + "," + radius + " 0 1,1 0," + (+2 * radius)
      + "z";
}
/**
 * Given a GeoJSON object, returns the corresponding bounding box. The bounding
 * box is represented by a two-dimensional array: [[left, bottom], [right,
 * top]], where left is the minimum longitude, bottom is the minimum latitude,
 * right is maximum longitude, and top is the maximum latitude.
 */
d3.geo.bounds = function(feature) {
  var left = Infinity,
      bottom = Infinity,
      right = -Infinity,
      top = -Infinity;
  d3_geo_bounds(feature, function(x, y) {
    if (x < left) left = x;
    if (x > right) right = x;
    if (y < bottom) bottom = y;
    if (y > top) top = y;
  });
  return [[left, bottom], [right, top]];
};

function d3_geo_bounds(o, f) {
  if (d3_geo_boundsTypes.hasOwnProperty(o.type)) d3_geo_boundsTypes[o.type](o, f);
}

var d3_geo_boundsTypes = {
  Feature: d3_geo_boundsFeature,
  FeatureCollection: d3_geo_boundsFeatureCollection,
  GeometryCollection: d3_geo_boundsGeometryCollection,
  LineString: d3_geo_boundsLineString,
  MultiLineString: d3_geo_boundsMultiLineString,
  MultiPoint: d3_geo_boundsLineString,
  MultiPolygon: d3_geo_boundsMultiPolygon,
  Point: d3_geo_boundsPoint,
  Polygon: d3_geo_boundsPolygon
};

function d3_geo_boundsFeature(o, f) {
  d3_geo_bounds(o.geometry, f);
}

function d3_geo_boundsFeatureCollection(o, f) {
  for (var a = o.features, i = 0, n = a.length; i < n; i++) {
    d3_geo_bounds(a[i].geometry, f);
  }
}

function d3_geo_boundsGeometryCollection(o, f) {
  for (var a = o.geometries, i = 0, n = a.length; i < n; i++) {
    d3_geo_bounds(a[i], f);
  }
}

function d3_geo_boundsLineString(o, f) {
  for (var a = o.coordinates, i = 0, n = a.length; i < n; i++) {
    f.apply(null, a[i]);
  }
}

function d3_geo_boundsMultiLineString(o, f) {
  for (var a = o.coordinates, i = 0, n = a.length; i < n; i++) {
    for (var b = a[i], j = 0, m = b.length; j < m; j++) {
      f.apply(null, b[j]);
    }
  }
}

function d3_geo_boundsMultiPolygon(o, f) {
  for (var a = o.coordinates, i = 0, n = a.length; i < n; i++) {
    for (var b = a[i][0], j = 0, m = b.length; j < m; j++) {
      f.apply(null, b[j]);
    }
  }
}

function d3_geo_boundsPoint(o, f) {
  f.apply(null, o.coordinates);
}

function d3_geo_boundsPolygon(o, f) {
  for (var a = o.coordinates[0], i = 0, n = a.length; i < n; i++) {
    f.apply(null, a[i]);
  }
}
// TODO breakAtDateLine?

d3.geo.circle = function() {
  var origin = [0, 0],
      degrees = 90 - 1e-2,
      radians = degrees * d3_geo_radians,
      arc = d3.geo.greatArc().target(Object);

  function circle() {
    // TODO render a circle as a Polygon
  }

  function visible(point) {
    return arc.distance(point) < radians;
  }

  circle.clip = function(d) {
    arc.source(typeof origin === "function" ? origin.apply(this, arguments) : origin);
    return clipType(d);
  };

  var clipType = d3_geo_type({

    FeatureCollection: function(o) {
      var features = o.features.map(clipType).filter(Object);
      return features && (o = Object.create(o), o.features = features, o);
    },

    Feature: function(o) {
      var geometry = clipType(o.geometry);
      return geometry && (o = Object.create(o), o.geometry = geometry, o);
    },

    Point: function(o) {
      return visible(o.coordinates) && o;
    },

    MultiPoint: function(o) {
      var coordinates = o.coordinates.filter(visible);
      return coordinates.length && {
        type: o.type,
        coordinates: coordinates
      };
    },

    LineString: function(o) {
      var coordinates = clip(o.coordinates);
      return coordinates.length && (o = Object.create(o), o.coordinates = coordinates, o);
    },

    MultiLineString: function(o) {
      var coordinates = o.coordinates.map(clip).filter(function(d) { return d.length; });
      return coordinates.length && (o = Object.create(o), o.coordinates = coordinates, o);
    },

    Polygon: function(o) {
      var coordinates = o.coordinates.map(clip);
      return coordinates[0].length && (o = Object.create(o), o.coordinates = coordinates, o);
    },

    MultiPolygon: function(o) {
      var coordinates = o.coordinates.map(function(d) { return d.map(clip); }).filter(function(d) { return d[0].length; });
      return coordinates.length && (o = Object.create(o), o.coordinates = coordinates, o);
    },

    GeometryCollection: function(o) {
      var geometries = o.geometries.map(clipType).filter(Object);
      return geometries.length && (o = Object.create(o), o.geometries = geometries, o);
    }

  });

  function clip(coordinates) {
    var i = -1,
        n = coordinates.length,
        clipped = [],
        p0,
        p1,
        p2,
        d0,
        d1;

    while (++i < n) {
      d1 = arc.distance(p2 = coordinates[i]);
      if (d1 < radians) {
        if (p1) clipped.push(d3_geo_greatArcInterpolate(p1, p2)((d0 - radians) / (d0 - d1)));
        clipped.push(p2);
        p0 = p1 = null;
      } else {
        p1 = p2;
        if (!p0 && clipped.length) {
          clipped.push(d3_geo_greatArcInterpolate(clipped[clipped.length - 1], p1)((radians - d0) / (d1 - d0)));
          p0 = p1;
        }
      }
      d0 = d1;
    }

    if (p1 && clipped.length) {
      d1 = arc.distance(p2 = clipped[0]);
      clipped.push(d3_geo_greatArcInterpolate(p1, p2)((d0 - radians) / (d0 - d1)));
    }

    return resample(clipped);
  }

  // Resample coordinates, creating great arcs between each.
  function resample(coordinates) {
    var i = 0,
        n = coordinates.length,
        j,
        m,
        resampled = n ? [coordinates[0]] : coordinates,
        resamples,
        origin = arc.source();

    while (++i < n) {
      resamples = arc.source(coordinates[i - 1])(coordinates[i]).coordinates;
      for (j = 0, m = resamples.length; ++j < m;) resampled.push(resamples[j]);
    }

    arc.source(origin);
    return resampled;
  }

  circle.origin = function(x) {
    if (!arguments.length) return origin;
    origin = x;
    return circle;
  };

  circle.angle = function(x) {
    if (!arguments.length) return degrees;
    radians = (degrees = +x) * d3_geo_radians;
    return circle;
  };

  // Precision is specified in degrees.
  circle.precision = function(x) {
    if (!arguments.length) return arc.precision();
    arc.precision(x);
    return circle;
  };

  return circle;
}
d3.geo.greatArc = function() {
  var source = d3_geo_greatArcSource,
      target = d3_geo_greatArcTarget,
      precision = 6 * d3_geo_radians;

  function greatArc() {
    var a = typeof source === "function" ? source.apply(this, arguments) : source,
        b = typeof target === "function" ? target.apply(this, arguments) : target,
        i = d3_geo_greatArcInterpolate(a, b),
        dt = precision / i.d,
        t = 0,
        coordinates = [a];
    while ((t += dt) < 1) coordinates.push(i(t));
    coordinates.push(b);
    return {
      type: "LineString",
      coordinates: coordinates
    };
  }

  // Length returned in radians; multiply by radius for distance.
  greatArc.distance = function() {
    var a = typeof source === "function" ? source.apply(this, arguments) : source,
        b = typeof target === "function" ? target.apply(this, arguments) : target;
     return d3_geo_greatArcInterpolate(a, b).d;
  };

  greatArc.source = function(x) {
    if (!arguments.length) return source;
    source = x;
    return greatArc;
  };

  greatArc.target = function(x) {
    if (!arguments.length) return target;
    target = x;
    return greatArc;
  };

  // Precision is specified in degrees.
  greatArc.precision = function(x) {
    if (!arguments.length) return precision / d3_geo_radians;
    precision = x * d3_geo_radians;
    return greatArc;
  };

  return greatArc;
};

function d3_geo_greatArcSource(d) {
  return d.source;
}

function d3_geo_greatArcTarget(d) {
  return d.target;
}

function d3_geo_greatArcInterpolate(a, b) {
  var x0 = a[0] * d3_geo_radians, cx0 = Math.cos(x0), sx0 = Math.sin(x0),
      y0 = a[1] * d3_geo_radians, cy0 = Math.cos(y0), sy0 = Math.sin(y0),
      x1 = b[0] * d3_geo_radians, cx1 = Math.cos(x1), sx1 = Math.sin(x1),
      y1 = b[1] * d3_geo_radians, cy1 = Math.cos(y1), sy1 = Math.sin(y1),
      d = interpolate.d = Math.acos(Math.max(-1, Math.min(1, sy0 * sy1 + cy0 * cy1 * Math.cos(x1 - x0)))),
      sd = Math.sin(d);

  // From http://williams.best.vwh.net/avform.htm#Intermediate
  function interpolate(t) {
    var A = Math.sin(d - (t *= d)) / sd,
        B = Math.sin(t) / sd,
        x = A * cy0 * cx0 + B * cy1 * cx1,
        y = A * cy0 * sx0 + B * cy1 * sx1,
        z = A * sy0       + B * sy1;
    return [
      Math.atan2(y, x) / d3_geo_radians,
      Math.atan2(z, Math.sqrt(x * x + y * y)) / d3_geo_radians
    ];
  }

  return interpolate;
}
d3.geo.greatCircle = d3.geo.circle;
d3.geom = {};
/**
 * Computes a contour for a given input grid function using the <a
 * href="http://en.wikipedia.org/wiki/Marching_squares">marching
 * squares</a> algorithm. Returns the contour polygon as an array of points.
 *
 * @param grid a two-input function(x, y) that returns true for values
 * inside the contour and false for values outside the contour.
 * @param start an optional starting point [x, y] on the grid.
 * @returns polygon [[x1, y1], [x2, y2], …]
 */
d3.geom.contour = function(grid, start) {
  var s = start || d3_geom_contourStart(grid), // starting point
      c = [],    // contour polygon
      x = s[0],  // current x position
      y = s[1],  // current y position
      dx = 0,    // next x direction
      dy = 0,    // next y direction
      pdx = NaN, // previous x direction
      pdy = NaN, // previous y direction
      i = 0;

  do {
    // determine marching squares index
    i = 0;
    if (grid(x-1, y-1)) i += 1;
    if (grid(x,   y-1)) i += 2;
    if (grid(x-1, y  )) i += 4;
    if (grid(x,   y  )) i += 8;

    // determine next direction
    if (i === 6) {
      dx = pdy === -1 ? -1 : 1;
      dy = 0;
    } else if (i === 9) {
      dx = 0;
      dy = pdx === 1 ? -1 : 1;
    } else {
      dx = d3_geom_contourDx[i];
      dy = d3_geom_contourDy[i];
    }

    // update contour polygon
    if (dx != pdx && dy != pdy) {
      c.push([x, y]);
      pdx = dx;
      pdy = dy;
    }

    x += dx;
    y += dy;
  } while (s[0] != x || s[1] != y);

  return c;
};

// lookup tables for marching directions
var d3_geom_contourDx = [1, 0, 1, 1,-1, 0,-1, 1,0, 0,0,0,-1, 0,-1,NaN],
    d3_geom_contourDy = [0,-1, 0, 0, 0,-1, 0, 0,1,-1,1,1, 0,-1, 0,NaN];

function d3_geom_contourStart(grid) {
  var x = 0,
      y = 0;

  // search for a starting point; begin at origin
  // and proceed along outward-expanding diagonals
  while (true) {
    if (grid(x,y)) {
      return [x,y];
    }
    if (x === 0) {
      x = y + 1;
      y = 0;
    } else {
      x = x - 1;
      y = y + 1;
    }
  }
}
/**
 * Computes the 2D convex hull of a set of points using Graham's scanning
 * algorithm. The algorithm has been implemented as described in Cormen,
 * Leiserson, and Rivest's Introduction to Algorithms. The running time of
 * this algorithm is O(n log n), where n is the number of input points.
 *
 * @param vertices [[x1, y1], [x2, y2], …]
 * @returns polygon [[x1, y1], [x2, y2], …]
 */
d3.geom.hull = function(vertices) {
  if (vertices.length < 3) return [];

  var len = vertices.length,
      plen = len - 1,
      points = [],
      stack = [],
      i, j, h = 0, x1, y1, x2, y2, u, v, a, sp;

  // find the starting ref point: leftmost point with the minimum y coord
  for (i=1; i<len; ++i) {
    if (vertices[i][1] < vertices[h][1]) {
      h = i;
    } else if (vertices[i][1] == vertices[h][1]) {
      h = (vertices[i][0] < vertices[h][0] ? i : h);
    }
  }

  // calculate polar angles from ref point and sort
  for (i=0; i<len; ++i) {
    if (i === h) continue;
    y1 = vertices[i][1] - vertices[h][1];
    x1 = vertices[i][0] - vertices[h][0];
    points.push({angle: Math.atan2(y1, x1), index: i});
  }
  points.sort(function(a, b) { return a.angle - b.angle; });

  // toss out duplicate angles
  a = points[0].angle;
  v = points[0].index;
  u = 0;
  for (i=1; i<plen; ++i) {
    j = points[i].index;
    if (a == points[i].angle) {
      // keep angle for point most distant from the reference
      x1 = vertices[v][0] - vertices[h][0];
      y1 = vertices[v][1] - vertices[h][1];
      x2 = vertices[j][0] - vertices[h][0];
      y2 = vertices[j][1] - vertices[h][1];
      if ((x1*x1 + y1*y1) >= (x2*x2 + y2*y2)) {
        points[i].index = -1;
      } else {
        points[u].index = -1;
        a = points[i].angle;
        u = i;
        v = j;
      }
    } else {
      a = points[i].angle;
      u = i;
      v = j;
    }
  }

  // initialize the stack
  stack.push(h);
  for (i=0, j=0; i<2; ++j) {
    if (points[j].index !== -1) {
      stack.push(points[j].index);
      i++;
    }
  }
  sp = stack.length;

  // do graham's scan
  for (; j<plen; ++j) {
    if (points[j].index === -1) continue; // skip tossed out points
    while (!d3_geom_hullCCW(stack[sp-2], stack[sp-1], points[j].index, vertices)) {
      --sp;
    }
    stack[sp++] = points[j].index;
  }

  // construct the hull
  var poly = [];
  for (i=0; i<sp; ++i) {
    poly.push(vertices[stack[i]]);
  }
  return poly;
}

// are three points in counter-clockwise order?
function d3_geom_hullCCW(i1, i2, i3, v) {
  var t, a, b, c, d, e, f;
  t = v[i1]; a = t[0]; b = t[1];
  t = v[i2]; c = t[0]; d = t[1];
  t = v[i3]; e = t[0]; f = t[1];
  return ((f-b)*(c-a) - (d-b)*(e-a)) > 0;
}
// Note: requires coordinates to be counterclockwise and convex!
d3.geom.polygon = function(coordinates) {

  coordinates.area = function() {
    var i = 0,
        n = coordinates.length,
        a = coordinates[n - 1][0] * coordinates[0][1],
        b = coordinates[n - 1][1] * coordinates[0][0];
    while (++i < n) {
      a += coordinates[i - 1][0] * coordinates[i][1];
      b += coordinates[i - 1][1] * coordinates[i][0];
    }
    return (b - a) * .5;
  };

  coordinates.centroid = function(k) {
    var i = -1,
        n = coordinates.length,
        x = 0,
        y = 0,
        a,
        b = coordinates[n - 1],
        c;
    if (!arguments.length) k = -1 / (6 * coordinates.area());
    while (++i < n) {
      a = b;
      b = coordinates[i];
      c = a[0] * b[1] - b[0] * a[1];
      x += (a[0] + b[0]) * c;
      y += (a[1] + b[1]) * c;
    }
    return [x * k, y * k];
  };

  // The Sutherland-Hodgman clipping algorithm.
  coordinates.clip = function(subject) {
    var input,
        i = -1,
        n = coordinates.length,
        j,
        m,
        a = coordinates[n - 1],
        b,
        c,
        d;
    while (++i < n) {
      input = subject.slice();
      subject.length = 0;
      b = coordinates[i];
      c = input[(m = input.length) - 1];
      j = -1;
      while (++j < m) {
        d = input[j];
        if (d3_geom_polygonInside(d, a, b)) {
          if (!d3_geom_polygonInside(c, a, b)) {
            subject.push(d3_geom_polygonIntersect(c, d, a, b));
          }
          subject.push(d);
        } else if (d3_geom_polygonInside(c, a, b)) {
          subject.push(d3_geom_polygonIntersect(c, d, a, b));
        }
        c = d;
      }
      a = b;
    }
    return subject;
  };

  return coordinates;
};

function d3_geom_polygonInside(p, a, b) {
  return (b[0] - a[0]) * (p[1] - a[1]) < (b[1] - a[1]) * (p[0] - a[0]);
}

// Intersect two infinite lines cd and ab.
function d3_geom_polygonIntersect(c, d, a, b) {
  var x1 = c[0], x2 = d[0], x3 = a[0], x4 = b[0],
      y1 = c[1], y2 = d[1], y3 = a[1], y4 = b[1],
      x13 = x1 - x3,
      x21 = x2 - x1,
      x43 = x4 - x3,
      y13 = y1 - y3,
      y21 = y2 - y1,
      y43 = y4 - y3,
      ua = (x43 * y13 - y43 * x13) / (y43 * x21 - x43 * y21);
  return [x1 + ua * x21, y1 + ua * y21];
}
// Adapted from Nicolas Garcia Belmonte's JIT implementation:
// http://blog.thejit.org/2010/02/12/voronoi-tessellation/
// http://blog.thejit.org/assets/voronoijs/voronoi.js
// See lib/jit/LICENSE for details.

// Notes:
//
// This implementation does not clip the returned polygons, so if you want to
// clip them to a particular shape you will need to do that either in SVG or by
// post-processing with d3.geom.polygon's clip method.
//
// If any vertices are coincident or have NaN positions, the behavior of this
// method is undefined. Most likely invalid polygons will be returned. You
// should filter invalid points, and consolidate coincident points, before
// computing the tessellation.

/**
 * @param vertices [[x1, y1], [x2, y2], …]
 * @returns polygons [[[x1, y1], [x2, y2], …], …]
 */
d3.geom.voronoi = function(vertices) {
  var polygons = vertices.map(function() { return []; });

  d3_voronoi_tessellate(vertices, function(e) {
    var s1,
        s2,
        x1,
        x2,
        y1,
        y2;
    if (e.a === 1 && e.b >= 0) {
      s1 = e.ep.r;
      s2 = e.ep.l;
    } else {
      s1 = e.ep.l;
      s2 = e.ep.r;
    }
    if (e.a === 1) {
      y1 = s1 ? s1.y : -1e6;
      x1 = e.c - e.b * y1;
      y2 = s2 ? s2.y : 1e6;
      x2 = e.c - e.b * y2;
    } else {
      x1 = s1 ? s1.x : -1e6;
      y1 = e.c - e.a * x1;
      x2 = s2 ? s2.x : 1e6;
      y2 = e.c - e.a * x2;
    }
    var v1 = [x1, y1],
        v2 = [x2, y2];
    polygons[e.region.l.index].push(v1, v2);
    polygons[e.region.r.index].push(v1, v2);
  });

  // Reconnect the polygon segments into counterclockwise loops.
  return polygons.map(function(polygon, i) {
    var cx = vertices[i][0],
        cy = vertices[i][1];
    polygon.forEach(function(v) {
      v.angle = Math.atan2(v[0] - cx, v[1] - cy);
    });
    return polygon.sort(function(a, b) {
      return a.angle - b.angle;
    }).filter(function(d, i) {
      return !i || (d.angle - polygon[i - 1].angle > 1e-10);
    });
  });
};

var d3_voronoi_opposite = {"l": "r", "r": "l"};

function d3_voronoi_tessellate(vertices, callback) {

  var Sites = {
    list: vertices
      .map(function(v, i) {
        return {
          index: i,
          x: v[0],
          y: v[1]
        };
      })
      .sort(function(a, b) {
        return a.y < b.y ? -1
          : a.y > b.y ? 1
          : a.x < b.x ? -1
          : a.x > b.x ? 1
          : 0;
      }),
    bottomSite: null
  };

  var EdgeList = {
    list: [],
    leftEnd: null,
    rightEnd: null,

    init: function() {
      EdgeList.leftEnd = EdgeList.createHalfEdge(null, "l");
      EdgeList.rightEnd = EdgeList.createHalfEdge(null, "l");
      EdgeList.leftEnd.r = EdgeList.rightEnd;
      EdgeList.rightEnd.l = EdgeList.leftEnd;
      EdgeList.list.unshift(EdgeList.leftEnd, EdgeList.rightEnd);
    },

    createHalfEdge: function(edge, side) {
      return {
        edge: edge,
        side: side,
        vertex: null,
        "l": null,
        "r": null
      };
    },

    insert: function(lb, he) {
      he.l = lb;
      he.r = lb.r;
      lb.r.l = he;
      lb.r = he;
    },

    leftBound: function(p) {
      var he = EdgeList.leftEnd;
      do {
        he = he.r;
      } while (he != EdgeList.rightEnd && Geom.rightOf(he, p));
      he = he.l;
      return he;
    },

    del: function(he) {
      he.l.r = he.r;
      he.r.l = he.l;
      he.edge = null;
    },

    right: function(he) {
      return he.r;
    },

    left: function(he) {
      return he.l;
    },

    leftRegion: function(he) {
      return he.edge == null
          ? Sites.bottomSite
          : he.edge.region[he.side];
    },

    rightRegion: function(he) {
      return he.edge == null
          ? Sites.bottomSite
          : he.edge.region[d3_voronoi_opposite[he.side]];
    }
  };

  var Geom = {

    bisect: function(s1, s2) {
      var newEdge = {
        region: {"l": s1, "r": s2},
        ep: {"l": null, "r": null}
      };

      var dx = s2.x - s1.x,
          dy = s2.y - s1.y,
          adx = dx > 0 ? dx : -dx,
          ady = dy > 0 ? dy : -dy;

      newEdge.c = s1.x * dx + s1.y * dy
          + (dx * dx + dy * dy) * .5;

      if (adx > ady) {
        newEdge.a = 1;
        newEdge.b = dy / dx;
        newEdge.c /= dx;
      } else {
        newEdge.b = 1;
        newEdge.a = dx / dy;
        newEdge.c /= dy;
      }

      return newEdge;
    },

    intersect: function(el1, el2) {
      var e1 = el1.edge,
          e2 = el2.edge;
      if (!e1 || !e2 || (e1.region.r == e2.region.r)) {
        return null;
      }
      var d = (e1.a * e2.b) - (e1.b * e2.a);
      if (Math.abs(d) < 1e-10) {
        return null;
      }
      var xint = (e1.c * e2.b - e2.c * e1.b) / d,
          yint = (e2.c * e1.a - e1.c * e2.a) / d,
          e1r = e1.region.r,
          e2r = e2.region.r,
          el,
          e;
      if ((e1r.y < e2r.y) ||
         (e1r.y == e2r.y && e1r.x < e2r.x)) {
        el = el1;
        e = e1;
      } else {
        el = el2;
        e = e2;
      }
      var rightOfSite = (xint >= e.region.r.x);
      if ((rightOfSite && (el.side === "l")) ||
        (!rightOfSite && (el.side === "r"))) {
        return null;
      }
      return {
        x: xint,
        y: yint
      };
    },

    rightOf: function(he, p) {
      var e = he.edge,
          topsite = e.region.r,
          rightOfSite = (p.x > topsite.x);

      if (rightOfSite && (he.side === "l")) {
        return 1;
      }
      if (!rightOfSite && (he.side === "r")) {
        return 0;
      }
      if (e.a === 1) {
        var dyp = p.y - topsite.y,
            dxp = p.x - topsite.x,
            fast = 0,
            above = 0;

        if ((!rightOfSite && (e.b < 0)) ||
          (rightOfSite && (e.b >= 0))) {
          above = fast = (dyp >= e.b * dxp);
        } else {
          above = ((p.x + p.y * e.b) > e.c);
          if (e.b < 0) {
            above = !above;
          }
          if (!above) {
            fast = 1;
          }
        }
        if (!fast) {
          var dxs = topsite.x - e.region.l.x;
          above = (e.b * (dxp * dxp - dyp * dyp)) <
            (dxs * dyp * (1 + 2 * dxp / dxs + e.b * e.b));

          if (e.b < 0) {
            above = !above;
          }
        }
      } else /* e.b == 1 */ {
        var yl = e.c - e.a * p.x,
            t1 = p.y - yl,
            t2 = p.x - topsite.x,
            t3 = yl - topsite.y;

        above = (t1 * t1) > (t2 * t2 + t3 * t3);
      }
      return he.side === "l" ? above : !above;
    },

    endPoint: function(edge, side, site) {
      edge.ep[side] = site;
      if (!edge.ep[d3_voronoi_opposite[side]]) return;
      callback(edge);
    },

    distance: function(s, t) {
      var dx = s.x - t.x,
          dy = s.y - t.y;
      return Math.sqrt(dx * dx + dy * dy);
    }
  };

  var EventQueue = {
    list: [],

    insert: function(he, site, offset) {
      he.vertex = site;
      he.ystar = site.y + offset;
      for (var i=0, list=EventQueue.list, l=list.length; i<l; i++) {
        var next = list[i];
        if (he.ystar > next.ystar ||
          (he.ystar == next.ystar &&
          site.x > next.vertex.x)) {
          continue;
        } else {
          break;
        }
      }
      list.splice(i, 0, he);
    },

    del: function(he) {
      for (var i=0, ls=EventQueue.list, l=ls.length; i<l && (ls[i] != he); ++i) {}
      ls.splice(i, 1);
    },

    empty: function() { return EventQueue.list.length === 0; },

    nextEvent: function(he) {
      for (var i=0, ls=EventQueue.list, l=ls.length; i<l; ++i) {
        if (ls[i] == he) return ls[i+1];
      }
      return null;
    },

    min: function() {
      var elem = EventQueue.list[0];
      return {
        x: elem.vertex.x,
        y: elem.ystar
      };
    },

    extractMin: function() {
      return EventQueue.list.shift();
    }
  };

  EdgeList.init();
  Sites.bottomSite = Sites.list.shift();

  var newSite = Sites.list.shift(), newIntStar;
  var lbnd, rbnd, llbnd, rrbnd, bisector;
  var bot, top, temp, p, v;
  var e, pm;

  while (true) {
    if (!EventQueue.empty()) {
      newIntStar = EventQueue.min();
    }
    if (newSite && (EventQueue.empty()
      || newSite.y < newIntStar.y
      || (newSite.y == newIntStar.y
      && newSite.x < newIntStar.x))) { //new site is smallest
      lbnd = EdgeList.leftBound(newSite);
      rbnd = EdgeList.right(lbnd);
      bot = EdgeList.rightRegion(lbnd);
      e = Geom.bisect(bot, newSite);
      bisector = EdgeList.createHalfEdge(e, "l");
      EdgeList.insert(lbnd, bisector);
      p = Geom.intersect(lbnd, bisector);
      if (p) {
        EventQueue.del(lbnd);
        EventQueue.insert(lbnd, p, Geom.distance(p, newSite));
      }
      lbnd = bisector;
      bisector = EdgeList.createHalfEdge(e, "r");
      EdgeList.insert(lbnd, bisector);
      p = Geom.intersect(bisector, rbnd);
      if (p) {
        EventQueue.insert(bisector, p, Geom.distance(p, newSite));
      }
      newSite = Sites.list.shift();
    } else if (!EventQueue.empty()) { //intersection is smallest
      lbnd = EventQueue.extractMin();
      llbnd = EdgeList.left(lbnd);
      rbnd = EdgeList.right(lbnd);
      rrbnd = EdgeList.right(rbnd);
      bot = EdgeList.leftRegion(lbnd);
      top = EdgeList.rightRegion(rbnd);
      v = lbnd.vertex;
      Geom.endPoint(lbnd.edge, lbnd.side, v);
      Geom.endPoint(rbnd.edge, rbnd.side, v);
      EdgeList.del(lbnd);
      EventQueue.del(rbnd);
      EdgeList.del(rbnd);
      pm = "l";
      if (bot.y > top.y) {
        temp = bot;
        bot = top;
        top = temp;
        pm = "r";
      }
      e = Geom.bisect(bot, top);
      bisector = EdgeList.createHalfEdge(e, pm);
      EdgeList.insert(llbnd, bisector);
      Geom.endPoint(e, d3_voronoi_opposite[pm], v);
      p = Geom.intersect(llbnd, bisector);
      if (p) {
        EventQueue.del(llbnd);
        EventQueue.insert(llbnd, p, Geom.distance(p, bot));
      }
      p = Geom.intersect(bisector, rrbnd);
      if (p) {
        EventQueue.insert(bisector, p, Geom.distance(p, bot));
      }
    } else {
      break;
    }
  }//end while

  for (lbnd = EdgeList.right(EdgeList.leftEnd);
      lbnd != EdgeList.rightEnd;
      lbnd = EdgeList.right(lbnd)) {
    callback(lbnd.edge);
  }
}
/**
* @param vertices [[x1, y1], [x2, y2], …]
* @returns triangles [[[x1, y1], [x2, y2], [x3, y3]], …]
 */
d3.geom.delaunay = function(vertices) {
  var edges = vertices.map(function() { return []; }),
      triangles = [];

  // Use the Voronoi tessellation to determine Delaunay edges.
  d3_voronoi_tessellate(vertices, function(e) {
    edges[e.region.l.index].push(vertices[e.region.r.index]);
  });

  // Reconnect the edges into counterclockwise triangles.
  edges.forEach(function(edge, i) {
    var v = vertices[i],
        cx = v[0],
        cy = v[1];
    edge.forEach(function(v) {
      v.angle = Math.atan2(v[0] - cx, v[1] - cy);
    });
    edge.sort(function(a, b) {
      return a.angle - b.angle;
    });
    for (var j = 0, m = edge.length - 1; j < m; j++) {
      triangles.push([v, edge[j], edge[j + 1]]);
    }
  });

  return triangles;
};
// Constructs a new quadtree for the specified array of points. A quadtree is a
// two-dimensional recursive spatial subdivision. This implementation uses
// square partitions, dividing each square into four equally-sized squares. Each
// point exists in a unique node; if multiple points are in the same position,
// some points may be stored on internal nodes rather than leaf nodes. Quadtrees
// can be used to accelerate various spatial operations, such as the Barnes-Hut
// approximation for computing n-body forces, or collision detection.
d3.geom.quadtree = function(points, x1, y1, x2, y2) {
  var p,
      i = -1,
      n = points.length;

  // Type conversion for deprecated API.
  if (n && isNaN(points[0].x)) points = points.map(d3_geom_quadtreePoint);

  // Allow bounds to be specified explicitly.
  if (arguments.length < 5) {
    if (arguments.length === 3) {
      y2 = x2 = y1;
      y1 = x1;
    } else {
      x1 = y1 = Infinity;
      x2 = y2 = -Infinity;

      // Compute bounds.
      while (++i < n) {
        p = points[i];
        if (p.x < x1) x1 = p.x;
        if (p.y < y1) y1 = p.y;
        if (p.x > x2) x2 = p.x;
        if (p.y > y2) y2 = p.y;
      }

      // Squarify the bounds.
      var dx = x2 - x1,
          dy = y2 - y1;
      if (dx > dy) y2 = y1 + dx;
      else x2 = x1 + dy;
    }
  }

  // Recursively inserts the specified point p at the node n or one of its
  // descendants. The bounds are defined by [x1, x2] and [y1, y2].
  function insert(n, p, x1, y1, x2, y2) {
    if (isNaN(p.x) || isNaN(p.y)) return; // ignore invalid points
    if (n.leaf) {
      var v = n.point;
      if (v) {
        // If the point at this leaf node is at the same position as the new
        // point we are adding, we leave the point associated with the
        // internal node while adding the new point to a child node. This
        // avoids infinite recursion.
        if ((Math.abs(v.x - p.x) + Math.abs(v.y - p.y)) < .01) {
          insertChild(n, p, x1, y1, x2, y2);
        } else {
          n.point = null;
          insertChild(n, v, x1, y1, x2, y2);
          insertChild(n, p, x1, y1, x2, y2);
        }
      } else {
        n.point = p;
      }
    } else {
      insertChild(n, p, x1, y1, x2, y2);
    }
  }

  // Recursively inserts the specified point p into a descendant of node n. The
  // bounds are defined by [x1, x2] and [y1, y2].
  function insertChild(n, p, x1, y1, x2, y2) {
    // Compute the split point, and the quadrant in which to insert p.
    var sx = (x1 + x2) * .5,
        sy = (y1 + y2) * .5,
        right = p.x >= sx,
        bottom = p.y >= sy,
        i = (bottom << 1) + right;

    // Recursively insert into the child node.
    n.leaf = false;
    n = n.nodes[i] || (n.nodes[i] = d3_geom_quadtreeNode());

    // Update the bounds as we recurse.
    if (right) x1 = sx; else x2 = sx;
    if (bottom) y1 = sy; else y2 = sy;
    insert(n, p, x1, y1, x2, y2);
  }

  // Create the root node.
  var root = d3_geom_quadtreeNode();

  root.add = function(p) {
    insert(root, p, x1, y1, x2, y2);
  };

  root.visit = function(f) {
    d3_geom_quadtreeVisit(f, root, x1, y1, x2, y2);
  };

  // Insert all points.
  points.forEach(root.add);
  return root;
};

function d3_geom_quadtreeNode() {
  return {
    leaf: true,
    nodes: [],
    point: null
  };
}

function d3_geom_quadtreeVisit(f, node, x1, y1, x2, y2) {
  if (!f(node, x1, y1, x2, y2)) {
    var sx = (x1 + x2) * .5,
        sy = (y1 + y2) * .5,
        children = node.nodes;
    if (children[0]) d3_geom_quadtreeVisit(f, children[0], x1, y1, sx, sy);
    if (children[1]) d3_geom_quadtreeVisit(f, children[1], sx, y1, x2, sy);
    if (children[2]) d3_geom_quadtreeVisit(f, children[2], x1, sy, sx, y2);
    if (children[3]) d3_geom_quadtreeVisit(f, children[3], sx, sy, x2, y2);
  }
}

function d3_geom_quadtreePoint(p) {
  return {
    x: p[0],
    y: p[1]
  };
}
d3.time = {};

var d3_time = Date;

function d3_time_utc() {
  this._ = new Date(arguments.length > 1
      ? Date.UTC.apply(this, arguments)
      : arguments[0]);
}

d3_time_utc.prototype = {
  getDate: function() { return this._.getUTCDate(); },
  getDay: function() { return this._.getUTCDay(); },
  getFullYear: function() { return this._.getUTCFullYear(); },
  getHours: function() { return this._.getUTCHours(); },
  getMilliseconds: function() { return this._.getUTCMilliseconds(); },
  getMinutes: function() { return this._.getUTCMinutes(); },
  getMonth: function() { return this._.getUTCMonth(); },
  getSeconds: function() { return this._.getUTCSeconds(); },
  getTime: function() { return this._.getTime(); },
  getTimezoneOffset: function() { return 0; },
  valueOf: function() { return this._.valueOf(); },
  setDate: function() { d3_time_prototype.setUTCDate.apply(this._, arguments); },
  setDay: function() { d3_time_prototype.setUTCDay.apply(this._, arguments); },
  setFullYear: function() { d3_time_prototype.setUTCFullYear.apply(this._, arguments); },
  setHours: function() { d3_time_prototype.setUTCHours.apply(this._, arguments); },
  setMilliseconds: function() { d3_time_prototype.setUTCMilliseconds.apply(this._, arguments); },
  setMinutes: function() { d3_time_prototype.setUTCMinutes.apply(this._, arguments); },
  setMonth: function() { d3_time_prototype.setUTCMonth.apply(this._, arguments); },
  setSeconds: function() { d3_time_prototype.setUTCSeconds.apply(this._, arguments); },
  setTime: function() { d3_time_prototype.setTime.apply(this._, arguments); }
};

var d3_time_prototype = Date.prototype;
d3.time.format = function(template) {
  var n = template.length;

  function format(date) {
    var string = [],
        i = -1,
        j = 0,
        c,
        f;
    while (++i < n) {
      if (template.charCodeAt(i) == 37) {
        string.push(
            template.substring(j, i),
            (f = d3_time_formats[c = template.charAt(++i)])
            ? f(date) : c);
        j = i + 1;
      }
    }
    string.push(template.substring(j, i));
    return string.join("");
  }

  format.parse = function(string) {
    var d = {y: 1900, m: 0, d: 1, H: 0, M: 0, S: 0, L: 0},
        i = d3_time_parse(d, template, string, 0);
    if (i != string.length) return null;

    // The am-pm flag is 0 for AM, and 1 for PM.
    if ("p" in d) d.H = d.H % 12 + d.p * 12;

    var date = new d3_time();
    date.setFullYear(d.y, d.m, d.d);
    date.setHours(d.H, d.M, d.S, d.L);
    return date;
  };

  format.toString = function() {
    return template;
  };

  return format;
};

function d3_time_parse(date, template, string, j) {
  var c,
      p,
      i = 0,
      n = template.length,
      m = string.length;
  while (i < n) {
    if (j >= m) return -1;
    c = template.charCodeAt(i++);
    if (c == 37) {
      p = d3_time_parsers[template.charAt(i++)];
      if (!p || ((j = p(date, string, j)) < 0)) return -1;
    } else if (c != string.charCodeAt(j++)) {
      return -1;
    }
  }
  return j;
}

var d3_time_zfill2 = d3.format("02d"),
    d3_time_zfill3 = d3.format("03d"),
    d3_time_zfill4 = d3.format("04d"),
    d3_time_sfill2 = d3.format("2d");

var d3_time_formats = {
  a: function(d) { return d3_time_weekdays[d.getDay()].substring(0, 3); },
  A: function(d) { return d3_time_weekdays[d.getDay()]; },
  b: function(d) { return d3_time_months[d.getMonth()].substring(0, 3); },
  B: function(d) { return d3_time_months[d.getMonth()]; },
  c: d3.time.format("%a %b %e %H:%M:%S %Y"),
  d: function(d) { return d3_time_zfill2(d.getDate()); },
  e: function(d) { return d3_time_sfill2(d.getDate()); },
  H: function(d) { return d3_time_zfill2(d.getHours()); },
  I: function(d) { return d3_time_zfill2(d.getHours() % 12 || 12); },
  j: function(d) { return d3_time_zfill3(1 + d3.time.dayOfYear(d)); },
  L: function(d) { return d3_time_zfill3(d.getMilliseconds()); },
  m: function(d) { return d3_time_zfill2(d.getMonth() + 1); },
  M: function(d) { return d3_time_zfill2(d.getMinutes()); },
  p: function(d) { return d.getHours() >= 12 ? "PM" : "AM"; },
  S: function(d) { return d3_time_zfill2(d.getSeconds()); },
  U: function(d) { return d3_time_zfill2(d3.time.sundayOfYear(d)); },
  w: function(d) { return d.getDay(); },
  W: function(d) { return d3_time_zfill2(d3.time.mondayOfYear(d)); },
  x: d3.time.format("%m/%d/%y"),
  X: d3.time.format("%H:%M:%S"),
  y: function(d) { return d3_time_zfill2(d.getFullYear() % 100); },
  Y: function(d) { return d3_time_zfill4(d.getFullYear() % 10000); },
  Z: d3_time_zone,
  "%": function(d) { return "%"; }
};

var d3_time_parsers = {
  a: d3_time_parseWeekdayAbbrev,
  A: d3_time_parseWeekday,
  b: d3_time_parseMonthAbbrev,
  B: d3_time_parseMonth,
  c: d3_time_parseLocaleFull,
  d: d3_time_parseDay,
  e: d3_time_parseDay,
  H: d3_time_parseHour24,
  I: d3_time_parseHour24,
  // j: function(d, s, i) { /*TODO day of year [001,366] */ return i; },
  L: d3_time_parseMilliseconds,
  m: d3_time_parseMonthNumber,
  M: d3_time_parseMinutes,
  p: d3_time_parseAmPm,
  S: d3_time_parseSeconds,
  // U: function(d, s, i) { /*TODO week number (sunday) [00,53] */ return i; },
  // w: function(d, s, i) { /*TODO weekday [0,6] */ return i; },
  // W: function(d, s, i) { /*TODO week number (monday) [00,53] */ return i; },
  x: d3_time_parseLocaleDate,
  X: d3_time_parseLocaleTime,
  y: d3_time_parseYear,
  Y: d3_time_parseFullYear
  // ,
  // Z: function(d, s, i) { /*TODO time zone */ return i; },
  // "%": function(d, s, i) { /*TODO literal % */ return i; }
};

// Note: weekday is validated, but does not set the date.
function d3_time_parseWeekdayAbbrev(date, string, i) {
  return d3_time_weekdayAbbrevRe.test(string.substring(i, i += 3)) ? i : -1;
}

// Note: weekday is validated, but does not set the date.
function d3_time_parseWeekday(date, string, i) {
  d3_time_weekdayRe.lastIndex = 0;
  var n = d3_time_weekdayRe.exec(string.substring(i, i + 10));
  return n ? i += n[0].length : -1;
}

var d3_time_weekdayAbbrevRe = /^(?:sun|mon|tue|wed|thu|fri|sat)/i,
    d3_time_weekdayRe = /^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)/i;
    d3_time_weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function d3_time_parseMonthAbbrev(date, string, i) {
  var n = d3_time_monthAbbrevLookup.get(string.substring(i, i += 3).toLowerCase());
  return n == null ? -1 : (date.m = n, i);
}

var d3_time_monthAbbrevLookup = d3.map({
  jan: 0,
  feb: 1,
  mar: 2,
  apr: 3,
  may: 4,
  jun: 5,
  jul: 6,
  aug: 7,
  sep: 8,
  oct: 9,
  nov: 10,
  dec: 11
});

function d3_time_parseMonth(date, string, i) {
  d3_time_monthRe.lastIndex = 0;
  var n = d3_time_monthRe.exec(string.substring(i, i + 12));
  return n ? (date.m = d3_time_monthLookup.get(n[0].toLowerCase()), i += n[0].length) : -1;
}

var d3_time_monthRe = /^(?:January|February|March|April|May|June|July|August|September|October|November|December)/ig;

var d3_time_monthLookup = d3.map({
  january: 0,
  february: 1,
  march: 2,
  april: 3,
  may: 4,
  june: 5,
  july: 6,
  august: 7,
  september: 8,
  october: 9,
  november: 10,
  december: 11
});

var d3_time_months = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December"
];

function d3_time_parseLocaleFull(date, string, i) {
  return d3_time_parse(date, d3_time_formats.c.toString(), string, i);
}

function d3_time_parseLocaleDate(date, string, i) {
  return d3_time_parse(date, d3_time_formats.x.toString(), string, i);
}

function d3_time_parseLocaleTime(date, string, i) {
  return d3_time_parse(date, d3_time_formats.X.toString(), string, i);
}

function d3_time_parseFullYear(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 4));
  return n ? (date.y = +n[0], i += n[0].length) : -1;
}

function d3_time_parseYear(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.y = d3_time_century() + +n[0], i += n[0].length) : -1;
}

function d3_time_century() {
  return ~~(new Date().getFullYear() / 1000) * 1000;
}

function d3_time_parseMonthNumber(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.m = n[0] - 1, i += n[0].length) : -1;
}

function d3_time_parseDay(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.d = +n[0], i += n[0].length) : -1;
}

// Note: we don't validate that the hour is in the range [0,23] or [1,12].
function d3_time_parseHour24(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.H = +n[0], i += n[0].length) : -1;
}

function d3_time_parseMinutes(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.M = +n[0], i += n[0].length) : -1;
}

function d3_time_parseSeconds(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 2));
  return n ? (date.S = +n[0], i += n[0].length) : -1;
}

function d3_time_parseMilliseconds(date, string, i) {
  d3_time_numberRe.lastIndex = 0;
  var n = d3_time_numberRe.exec(string.substring(i, i + 3));
  return n ? (date.L = +n[0], i += n[0].length) : -1;
}

// Note: we don't look at the next directive.
var d3_time_numberRe = /\s*\d+/;

function d3_time_parseAmPm(date, string, i) {
  var n = d3_time_amPmLookup.get(string.substring(i, i += 2).toLowerCase());
  return n == null ? -1 : (date.p = n, i);
}

var d3_time_amPmLookup = d3.map({
  am: 0,
  pm: 1
});

// TODO table of time zone offset names?
function d3_time_zone(d) {
  var z = d.getTimezoneOffset(),
      zs = z > 0 ? "-" : "+",
      zh = ~~(Math.abs(z) / 60),
      zm = Math.abs(z) % 60;
  return zs + d3_time_zfill2(zh) + d3_time_zfill2(zm);
}
d3.time.format.utc = function(template) {
  var local = d3.time.format(template);

  function format(date) {
    try {
      d3_time = d3_time_utc;
      var utc = new d3_time();
      utc._ = date;
      return local(utc);
    } finally {
      d3_time = Date;
    }
  }

  format.parse = function(string) {
    try {
      d3_time = d3_time_utc;
      var date = local.parse(string);
      return date && date._;
    } finally {
      d3_time = Date;
    }
  };

  format.toString = local.toString;

  return format;
};
var d3_time_formatIso = d3.time.format.utc("%Y-%m-%dT%H:%M:%S.%LZ");

d3.time.format.iso = Date.prototype.toISOString ? d3_time_formatIsoNative : d3_time_formatIso;

function d3_time_formatIsoNative(date) {
  return date.toISOString();
}

d3_time_formatIsoNative.parse = function(string) {
  return new Date(string);
};

d3_time_formatIsoNative.toString = d3_time_formatIso.toString;
function d3_time_interval(local, step, number) {

  function round(date) {
    var d0 = local(date), d1 = offset(d0, 1);
    return date - d0 < d1 - date ? d0 : d1;
  }

  function ceil(date) {
    step(date = local(new d3_time(date - 1)), 1);
    return date;
  }

  function offset(date, k) {
    step(date = new d3_time(+date), k);
    return date;
  }

  function range(t0, t1, dt) {
    var time = ceil(t0), times = [];
    if (dt > 1) {
      while (time < t1) {
        if (!(number(time) % dt)) times.push(new Date(+time));
        step(time, 1);
      }
    } else {
      while (time < t1) times.push(new Date(+time)), step(time, 1);
    }
    return times;
  }

  function range_utc(t0, t1, dt) {
    try {
      d3_time = d3_time_utc;
      var utc = new d3_time_utc();
      utc._ = t0;
      return range(utc, t1, dt);
    } finally {
      d3_time = Date;
    }
  }

  local.floor = local;
  local.round = round;
  local.ceil = ceil;
  local.offset = offset;
  local.range = range;

  var utc = local.utc = d3_time_interval_utc(local);
  utc.floor = utc;
  utc.round = d3_time_interval_utc(round);
  utc.ceil = d3_time_interval_utc(ceil);
  utc.offset = d3_time_interval_utc(offset);
  utc.range = range_utc;

  return local;
}

function d3_time_interval_utc(method) {
  return function(date, k) {
    try {
      d3_time = d3_time_utc;
      var utc = new d3_time_utc();
      utc._ = date;
      return method(utc, k)._;
    } finally {
      d3_time = Date;
    }
  };
}
d3.time.second = d3_time_interval(function(date) {
  return new d3_time(Math.floor(date / 1e3) * 1e3);
}, function(date, offset) {
  date.setTime(date.getTime() + Math.floor(offset) * 1e3); // DST breaks setSeconds
}, function(date) {
  return date.getSeconds();
});

d3.time.seconds = d3.time.second.range;
d3.time.seconds.utc = d3.time.second.utc.range;
d3.time.minute = d3_time_interval(function(date) {
  return new d3_time(Math.floor(date / 6e4) * 6e4);
}, function(date, offset) {
  date.setTime(date.getTime() + Math.floor(offset) * 6e4); // DST breaks setMinutes
}, function(date) {
  return date.getMinutes();
});

d3.time.minutes = d3.time.minute.range;
d3.time.minutes.utc = d3.time.minute.utc.range;
d3.time.hour = d3_time_interval(function(date) {
  var timezone = date.getTimezoneOffset() / 60;
  return new d3_time((Math.floor(date / 36e5 - timezone) + timezone) * 36e5);
}, function(date, offset) {
  date.setTime(date.getTime() + Math.floor(offset) * 36e5); // DST breaks setHours
}, function(date) {
  return date.getHours();
});

d3.time.hours = d3.time.hour.range;
d3.time.hours.utc = d3.time.hour.utc.range;
d3.time.day = d3_time_interval(function(date) {
  return new d3_time(date.getFullYear(), date.getMonth(), date.getDate());
}, function(date, offset) {
  date.setDate(date.getDate() + offset);
}, function(date) {
  return date.getDate() - 1;
});

d3.time.days = d3.time.day.range;
d3.time.days.utc = d3.time.day.utc.range;

d3.time.dayOfYear = function(date) {
  var year = d3.time.year(date);
  return Math.floor((date - year) / 864e5 - (date.getTimezoneOffset() - year.getTimezoneOffset()) / 1440);
};
d3_time_weekdays.forEach(function(day, i) {
  day = day.toLowerCase();
  i = 7 - i;

  var interval = d3.time[day] = d3_time_interval(function(date) {
    (date = d3.time.day(date)).setDate(date.getDate() - (date.getDay() + i) % 7);
    return date;
  }, function(date, offset) {
    date.setDate(date.getDate() + Math.floor(offset) * 7);
  }, function(date) {
    var day = d3.time.year(date).getDay();
    return Math.floor((d3.time.dayOfYear(date) + (day + i) % 7) / 7) - (day !== i);
  });

  d3.time[day + "s"] = interval.range;
  d3.time[day + "s"].utc = interval.utc.range;

  d3.time[day + "OfYear"] = function(date) {
    var day = d3.time.year(date).getDay();
    return Math.floor((d3.time.dayOfYear(date) + (day + i) % 7) / 7);
  };
});

d3.time.week = d3.time.sunday;
d3.time.weeks = d3.time.sunday.range;
d3.time.weeks.utc = d3.time.sunday.utc.range;
d3.time.weekOfYear = d3.time.sundayOfYear;
d3.time.month = d3_time_interval(function(date) {
  return new d3_time(date.getFullYear(), date.getMonth(), 1);
}, function(date, offset) {
  date.setMonth(date.getMonth() + offset);
}, function(date) {
  return date.getMonth();
});

d3.time.months = d3.time.month.range;
d3.time.months.utc = d3.time.month.utc.range;
d3.time.year = d3_time_interval(function(date) {
  return new d3_time(date.getFullYear(), 0, 1);
}, function(date, offset) {
  date.setFullYear(date.getFullYear() + offset);
}, function(date) {
  return date.getFullYear();
});

d3.time.years = d3.time.year.range;
d3.time.years.utc = d3.time.year.utc.range;
function d3_time_scale(linear, methods, format) {

  function scale(x) {
    return linear(x);
  }

  scale.invert = function(x) {
    return d3_time_scaleDate(linear.invert(x));
  };

  scale.domain = function(x) {
    if (!arguments.length) return linear.domain().map(d3_time_scaleDate);
    linear.domain(x);
    return scale;
  };

  scale.nice = function(m) {
    var extent = d3_time_scaleExtent(scale.domain());
    return scale.domain([m.floor(extent[0]), m.ceil(extent[1])]);
  };

  scale.ticks = function(m, k) {
    var extent = d3_time_scaleExtent(scale.domain());
    if (typeof m !== "function") {
      var span = extent[1] - extent[0],
          target = span / m,
          i = d3.bisect(d3_time_scaleSteps, target);
      if (i == d3_time_scaleSteps.length) return methods.year(extent, m);
      if (!i) return linear.ticks(m).map(d3_time_scaleDate);
      if (Math.log(target / d3_time_scaleSteps[i - 1]) < Math.log(d3_time_scaleSteps[i] / target)) --i;
      m = methods[i];
      k = m[1];
      m = m[0].range;
    }
    return m(extent[0], new Date(+extent[1] + 1), k); // inclusive upper bound
  };

  scale.tickFormat = function() {
    return format;
  };

  scale.copy = function() {
    return d3_time_scale(linear.copy(), methods, format);
  };

  // TOOD expose d3_scale_linear_rebind?
  return d3.rebind(scale, linear, "range", "rangeRound", "interpolate", "clamp");
}

// TODO expose d3_scaleExtent?
function d3_time_scaleExtent(domain) {
  var start = domain[0], stop = domain[domain.length - 1];
  return start < stop ? [start, stop] : [stop, start];
}

function d3_time_scaleDate(t) {
  return new Date(t);
}

function d3_time_scaleFormat(formats) {
  return function(date) {
    var i = formats.length - 1, f = formats[i];
    while (!f[1](date)) f = formats[--i];
    return f[0](date);
  };
}

function d3_time_scaleSetYear(y) {
  var d = new Date(y, 0, 1);
  d.setFullYear(y); // Y2K fail
  return d;
}

function d3_time_scaleGetYear(d) {
  var y = d.getFullYear(),
      d0 = d3_time_scaleSetYear(y),
      d1 = d3_time_scaleSetYear(y + 1);
  return y + (d - d0) / (d1 - d0);
}

var d3_time_scaleSteps = [
  1e3,    // 1-second
  5e3,    // 5-second
  15e3,   // 15-second
  3e4,    // 30-second
  6e4,    // 1-minute
  3e5,    // 5-minute
  9e5,    // 15-minute
  18e5,   // 30-minute
  36e5,   // 1-hour
  108e5,  // 3-hour
  216e5,  // 6-hour
  432e5,  // 12-hour
  864e5,  // 1-day
  1728e5, // 2-day
  6048e5, // 1-week
  2592e6, // 1-month
  7776e6, // 3-month
  31536e6 // 1-year
];

var d3_time_scaleLocalMethods = [
  [d3.time.second, 1],
  [d3.time.second, 5],
  [d3.time.second, 15],
  [d3.time.second, 30],
  [d3.time.minute, 1],
  [d3.time.minute, 5],
  [d3.time.minute, 15],
  [d3.time.minute, 30],
  [d3.time.hour, 1],
  [d3.time.hour, 3],
  [d3.time.hour, 6],
  [d3.time.hour, 12],
  [d3.time.day, 1],
  [d3.time.day, 2],
  [d3.time.week, 1],
  [d3.time.month, 1],
  [d3.time.month, 3],
  [d3.time.year, 1]
];

var d3_time_scaleLocalFormats = [
  [d3.time.format("%Y"), function(d) { return true; }],
  [d3.time.format("%B"), function(d) { return d.getMonth(); }],
  [d3.time.format("%b %d"), function(d) { return d.getDate() != 1; }],
  [d3.time.format("%a %d"), function(d) { return d.getDay() && d.getDate() != 1; }],
  [d3.time.format("%I %p"), function(d) { return d.getHours(); }],
  [d3.time.format("%I:%M"), function(d) { return d.getMinutes(); }],
  [d3.time.format(":%S"), function(d) { return d.getSeconds(); }],
  [d3.time.format(".%L"), function(d) { return d.getMilliseconds(); }]
];

var d3_time_scaleLinear = d3.scale.linear(),
    d3_time_scaleLocalFormat = d3_time_scaleFormat(d3_time_scaleLocalFormats);

d3_time_scaleLocalMethods.year = function(extent, m) {
  return d3_time_scaleLinear.domain(extent.map(d3_time_scaleGetYear)).ticks(m).map(d3_time_scaleSetYear);
};

d3.time.scale = function() {
  return d3_time_scale(d3.scale.linear(), d3_time_scaleLocalMethods, d3_time_scaleLocalFormat);
};
var d3_time_scaleUTCMethods = d3_time_scaleLocalMethods.map(function(m) {
  return [m[0].utc, m[1]];
});

var d3_time_scaleUTCFormats = [
  [d3.time.format.utc("%Y"), function(d) { return true; }],
  [d3.time.format.utc("%B"), function(d) { return d.getUTCMonth(); }],
  [d3.time.format.utc("%b %d"), function(d) { return d.getUTCDate() != 1; }],
  [d3.time.format.utc("%a %d"), function(d) { return d.getUTCDay() && d.getUTCDate() != 1; }],
  [d3.time.format.utc("%I %p"), function(d) { return d.getUTCHours(); }],
  [d3.time.format.utc("%I:%M"), function(d) { return d.getUTCMinutes(); }],
  [d3.time.format.utc(":%S"), function(d) { return d.getUTCSeconds(); }],
  [d3.time.format.utc(".%L"), function(d) { return d.getUTCMilliseconds(); }]
];

var d3_time_scaleUTCFormat = d3_time_scaleFormat(d3_time_scaleUTCFormats);

function d3_time_scaleUTCSetYear(y) {
  var d = new Date(Date.UTC(y, 0, 1));
  d.setUTCFullYear(y); // Y2K fail
  return d;
}

function d3_time_scaleUTCGetYear(d) {
  var y = d.getUTCFullYear(),
      d0 = d3_time_scaleUTCSetYear(y),
      d1 = d3_time_scaleUTCSetYear(y + 1);
  return y + (d - d0) / (d1 - d0);
}

d3_time_scaleUTCMethods.year = function(extent, m) {
  return d3_time_scaleLinear.domain(extent.map(d3_time_scaleUTCGetYear)).ticks(m).map(d3_time_scaleUTCSetYear);
};

d3.time.scale.utc = function() {
  return d3_time_scale(d3.scale.linear(), d3_time_scaleUTCMethods, d3_time_scaleUTCFormat);
};
})();

/*! jQuery v1.7.2 jquery.com | jquery.org/license */
if (!window.jQuery){
(function(a,b){function cy(a){return f.isWindow(a)?a:a.nodeType===9?a.defaultView||a.parentWindow:!1}function cu(a){if(!cj[a]){var b=c.body,d=f("<"+a+">").appendTo(b),e=d.css("display");d.remove();if(e==="none"||e===""){ck||(ck=c.createElement("iframe"),ck.frameBorder=ck.width=ck.height=0),b.appendChild(ck);if(!cl||!ck.createElement)cl=(ck.contentWindow||ck.contentDocument).document,cl.write((f.support.boxModel?"<!doctype html>":"")+"<html><body>"),cl.close();d=cl.createElement(a),cl.body.appendChild(d),e=f.css(d,"display"),b.removeChild(ck)}cj[a]=e}return cj[a]}function ct(a,b){var c={};f.each(cp.concat.apply([],cp.slice(0,b)),function(){c[this]=a});return c}function cs(){cq=b}function cr(){setTimeout(cs,0);return cq=f.now()}function ci(){try{return new a.ActiveXObject("Microsoft.XMLHTTP")}catch(b){}}function ch(){try{return new a.XMLHttpRequest}catch(b){}}function cb(a,c){a.dataFilter&&(c=a.dataFilter(c,a.dataType));var d=a.dataTypes,e={},g,h,i=d.length,j,k=d[0],l,m,n,o,p;for(g=1;g<i;g++){if(g===1)for(h in a.converters)typeof h=="string"&&(e[h.toLowerCase()]=a.converters[h]);l=k,k=d[g];if(k==="*")k=l;else if(l!=="*"&&l!==k){m=l+" "+k,n=e[m]||e["* "+k];if(!n){p=b;for(o in e){j=o.split(" ");if(j[0]===l||j[0]==="*"){p=e[j[1]+" "+k];if(p){o=e[o],o===!0?n=p:p===!0&&(n=o);break}}}}!n&&!p&&f.error("No conversion from "+m.replace(" "," to ")),n!==!0&&(c=n?n(c):p(o(c)))}}return c}function ca(a,c,d){var e=a.contents,f=a.dataTypes,g=a.responseFields,h,i,j,k;for(i in g)i in d&&(c[g[i]]=d[i]);while(f[0]==="*")f.shift(),h===b&&(h=a.mimeType||c.getResponseHeader("content-type"));if(h)for(i in e)if(e[i]&&e[i].test(h)){f.unshift(i);break}if(f[0]in d)j=f[0];else{for(i in d){if(!f[0]||a.converters[i+" "+f[0]]){j=i;break}k||(k=i)}j=j||k}if(j){j!==f[0]&&f.unshift(j);return d[j]}}function b_(a,b,c,d){if(f.isArray(b))f.each(b,function(b,e){c||bD.test(a)?d(a,e):b_(a+"["+(typeof e=="object"?b:"")+"]",e,c,d)});else if(!c&&f.type(b)==="object")for(var e in b)b_(a+"["+e+"]",b[e],c,d);else d(a,b)}function b$(a,c){var d,e,g=f.ajaxSettings.flatOptions||{};for(d in c)c[d]!==b&&((g[d]?a:e||(e={}))[d]=c[d]);e&&f.extend(!0,a,e)}function bZ(a,c,d,e,f,g){f=f||c.dataTypes[0],g=g||{},g[f]=!0;var h=a[f],i=0,j=h?h.length:0,k=a===bS,l;for(;i<j&&(k||!l);i++)l=h[i](c,d,e),typeof l=="string"&&(!k||g[l]?l=b:(c.dataTypes.unshift(l),l=bZ(a,c,d,e,l,g)));(k||!l)&&!g["*"]&&(l=bZ(a,c,d,e,"*",g));return l}function bY(a){return function(b,c){typeof b!="string"&&(c=b,b="*");if(f.isFunction(c)){var d=b.toLowerCase().split(bO),e=0,g=d.length,h,i,j;for(;e<g;e++)h=d[e],j=/^\+/.test(h),j&&(h=h.substr(1)||"*"),i=a[h]=a[h]||[],i[j?"unshift":"push"](c)}}}function bB(a,b,c){var d=b==="width"?a.offsetWidth:a.offsetHeight,e=b==="width"?1:0,g=4;if(d>0){if(c!=="border")for(;e<g;e+=2)c||(d-=parseFloat(f.css(a,"padding"+bx[e]))||0),c==="margin"?d+=parseFloat(f.css(a,c+bx[e]))||0:d-=parseFloat(f.css(a,"border"+bx[e]+"Width"))||0;return d+"px"}d=by(a,b);if(d<0||d==null)d=a.style[b];if(bt.test(d))return d;d=parseFloat(d)||0;if(c)for(;e<g;e+=2)d+=parseFloat(f.css(a,"padding"+bx[e]))||0,c!=="padding"&&(d+=parseFloat(f.css(a,"border"+bx[e]+"Width"))||0),c==="margin"&&(d+=parseFloat(f.css(a,c+bx[e]))||0);return d+"px"}function bo(a){var b=c.createElement("div");bh.appendChild(b),b.innerHTML=a.outerHTML;return b.firstChild}function bn(a){var b=(a.nodeName||"").toLowerCase();b==="input"?bm(a):b!=="script"&&typeof a.getElementsByTagName!="undefined"&&f.grep(a.getElementsByTagName("input"),bm)}function bm(a){if(a.type==="checkbox"||a.type==="radio")a.defaultChecked=a.checked}function bl(a){return typeof a.getElementsByTagName!="undefined"?a.getElementsByTagName("*"):typeof a.querySelectorAll!="undefined"?a.querySelectorAll("*"):[]}function bk(a,b){var c;b.nodeType===1&&(b.clearAttributes&&b.clearAttributes(),b.mergeAttributes&&b.mergeAttributes(a),c=b.nodeName.toLowerCase(),c==="object"?b.outerHTML=a.outerHTML:c!=="input"||a.type!=="checkbox"&&a.type!=="radio"?c==="option"?b.selected=a.defaultSelected:c==="input"||c==="textarea"?b.defaultValue=a.defaultValue:c==="script"&&b.text!==a.text&&(b.text=a.text):(a.checked&&(b.defaultChecked=b.checked=a.checked),b.value!==a.value&&(b.value=a.value)),b.removeAttribute(f.expando),b.removeAttribute("_submit_attached"),b.removeAttribute("_change_attached"))}function bj(a,b){if(b.nodeType===1&&!!f.hasData(a)){var c,d,e,g=f._data(a),h=f._data(b,g),i=g.events;if(i){delete h.handle,h.events={};for(c in i)for(d=0,e=i[c].length;d<e;d++)f.event.add(b,c,i[c][d])}h.data&&(h.data=f.extend({},h.data))}}function bi(a,b){return f.nodeName(a,"table")?a.getElementsByTagName("tbody")[0]||a.appendChild(a.ownerDocument.createElement("tbody")):a}function U(a){var b=V.split("|"),c=a.createDocumentFragment();if(c.createElement)while(b.length)c.createElement(b.pop());return c}function T(a,b,c){b=b||0;if(f.isFunction(b))return f.grep(a,function(a,d){var e=!!b.call(a,d,a);return e===c});if(b.nodeType)return f.grep(a,function(a,d){return a===b===c});if(typeof b=="string"){var d=f.grep(a,function(a){return a.nodeType===1});if(O.test(b))return f.filter(b,d,!c);b=f.filter(b,d)}return f.grep(a,function(a,d){return f.inArray(a,b)>=0===c})}function S(a){return!a||!a.parentNode||a.parentNode.nodeType===11}function K(){return!0}function J(){return!1}function n(a,b,c){var d=b+"defer",e=b+"queue",g=b+"mark",h=f._data(a,d);h&&(c==="queue"||!f._data(a,e))&&(c==="mark"||!f._data(a,g))&&setTimeout(function(){!f._data(a,e)&&!f._data(a,g)&&(f.removeData(a,d,!0),h.fire())},0)}function m(a){for(var b in a){if(b==="data"&&f.isEmptyObject(a[b]))continue;if(b!=="toJSON")return!1}return!0}function l(a,c,d){if(d===b&&a.nodeType===1){var e="data-"+c.replace(k,"-$1").toLowerCase();d=a.getAttribute(e);if(typeof d=="string"){try{d=d==="true"?!0:d==="false"?!1:d==="null"?null:f.isNumeric(d)?+d:j.test(d)?f.parseJSON(d):d}catch(g){}f.data(a,c,d)}else d=b}return d}function h(a){var b=g[a]={},c,d;a=a.split(/\s+/);for(c=0,d=a.length;c<d;c++)b[a[c]]=!0;return b}var c=a.document,d=a.navigator,e=a.location,f=function(){function J(){if(!e.isReady){try{c.documentElement.doScroll("left")}catch(a){setTimeout(J,1);return}e.ready()}}var e=function(a,b){return new e.fn.init(a,b,h)},f=a.jQuery,g=a.$,h,i=/^(?:[^#<]*(<[\w\W]+>)[^>]*$|#([\w\-]*)$)/,j=/\S/,k=/^\s+/,l=/\s+$/,m=/^<(\w+)\s*\/?>(?:<\/\1>)?$/,n=/^[\],:{}\s]*$/,o=/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g,p=/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,q=/(?:^|:|,)(?:\s*\[)+/g,r=/(webkit)[ \/]([\w.]+)/,s=/(opera)(?:.*version)?[ \/]([\w.]+)/,t=/(msie) ([\w.]+)/,u=/(mozilla)(?:.*? rv:([\w.]+))?/,v=/-([a-z]|[0-9])/ig,w=/^-ms-/,x=function(a,b){return(b+"").toUpperCase()},y=d.userAgent,z,A,B,C=Object.prototype.toString,D=Object.prototype.hasOwnProperty,E=Array.prototype.push,F=Array.prototype.slice,G=String.prototype.trim,H=Array.prototype.indexOf,I={};e.fn=e.prototype={constructor:e,init:function(a,d,f){var g,h,j,k;if(!a)return this;if(a.nodeType){this.context=this[0]=a,this.length=1;return this}if(a==="body"&&!d&&c.body){this.context=c,this[0]=c.body,this.selector=a,this.length=1;return this}if(typeof a=="string"){a.charAt(0)!=="<"||a.charAt(a.length-1)!==">"||a.length<3?g=i.exec(a):g=[null,a,null];if(g&&(g[1]||!d)){if(g[1]){d=d instanceof e?d[0]:d,k=d?d.ownerDocument||d:c,j=m.exec(a),j?e.isPlainObject(d)?(a=[c.createElement(j[1])],e.fn.attr.call(a,d,!0)):a=[k.createElement(j[1])]:(j=e.buildFragment([g[1]],[k]),a=(j.cacheable?e.clone(j.fragment):j.fragment).childNodes);return e.merge(this,a)}h=c.getElementById(g[2]);if(h&&h.parentNode){if(h.id!==g[2])return f.find(a);this.length=1,this[0]=h}this.context=c,this.selector=a;return this}return!d||d.jquery?(d||f).find(a):this.constructor(d).find(a)}if(e.isFunction(a))return f.ready(a);a.selector!==b&&(this.selector=a.selector,this.context=a.context);return e.makeArray(a,this)},selector:"",jquery:"1.7.2",length:0,size:function(){return this.length},toArray:function(){return F.call(this,0)},get:function(a){return a==null?this.toArray():a<0?this[this.length+a]:this[a]},pushStack:function(a,b,c){var d=this.constructor();e.isArray(a)?E.apply(d,a):e.merge(d,a),d.prevObject=this,d.context=this.context,b==="find"?d.selector=this.selector+(this.selector?" ":"")+c:b&&(d.selector=this.selector+"."+b+"("+c+")");return d},each:function(a,b){return e.each(this,a,b)},ready:function(a){e.bindReady(),A.add(a);return this},eq:function(a){a=+a;return a===-1?this.slice(a):this.slice(a,a+1)},first:function(){return this.eq(0)},last:function(){return this.eq(-1)},slice:function(){return this.pushStack(F.apply(this,arguments),"slice",F.call(arguments).join(","))},map:function(a){return this.pushStack(e.map(this,function(b,c){return a.call(b,c,b)}))},end:function(){return this.prevObject||this.constructor(null)},push:E,sort:[].sort,splice:[].splice},e.fn.init.prototype=e.fn,e.extend=e.fn.extend=function(){var a,c,d,f,g,h,i=arguments[0]||{},j=1,k=arguments.length,l=!1;typeof i=="boolean"&&(l=i,i=arguments[1]||{},j=2),typeof i!="object"&&!e.isFunction(i)&&(i={}),k===j&&(i=this,--j);for(;j<k;j++)if((a=arguments[j])!=null)for(c in a){d=i[c],f=a[c];if(i===f)continue;l&&f&&(e.isPlainObject(f)||(g=e.isArray(f)))?(g?(g=!1,h=d&&e.isArray(d)?d:[]):h=d&&e.isPlainObject(d)?d:{},i[c]=e.extend(l,h,f)):f!==b&&(i[c]=f)}return i},e.extend({noConflict:function(b){a.$===e&&(a.$=g),b&&a.jQuery===e&&(a.jQuery=f);return e},isReady:!1,readyWait:1,holdReady:function(a){a?e.readyWait++:e.ready(!0)},ready:function(a){if(a===!0&&!--e.readyWait||a!==!0&&!e.isReady){if(!c.body)return setTimeout(e.ready,1);e.isReady=!0;if(a!==!0&&--e.readyWait>0)return;A.fireWith(c,[e]),e.fn.trigger&&e(c).trigger("ready").off("ready")}},bindReady:function(){if(!A){A=e.Callbacks("once memory");if(c.readyState==="complete")return setTimeout(e.ready,1);if(c.addEventListener)c.addEventListener("DOMContentLoaded",B,!1),a.addEventListener("load",e.ready,!1);else if(c.attachEvent){c.attachEvent("onreadystatechange",B),a.attachEvent("onload",e.ready);var b=!1;try{b=a.frameElement==null}catch(d){}c.documentElement.doScroll&&b&&J()}}},isFunction:function(a){return e.type(a)==="function"},isArray:Array.isArray||function(a){return e.type(a)==="array"},isWindow:function(a){return a!=null&&a==a.window},isNumeric:function(a){return!isNaN(parseFloat(a))&&isFinite(a)},type:function(a){return a==null?String(a):I[C.call(a)]||"object"},isPlainObject:function(a){if(!a||e.type(a)!=="object"||a.nodeType||e.isWindow(a))return!1;try{if(a.constructor&&!D.call(a,"constructor")&&!D.call(a.constructor.prototype,"isPrototypeOf"))return!1}catch(c){return!1}var d;for(d in a);return d===b||D.call(a,d)},isEmptyObject:function(a){for(var b in a)return!1;return!0},error:function(a){throw new Error(a)},parseJSON:function(b){if(typeof b!="string"||!b)return null;b=e.trim(b);if(a.JSON&&a.JSON.parse)return a.JSON.parse(b);if(n.test(b.replace(o,"@").replace(p,"]").replace(q,"")))return(new Function("return "+b))();e.error("Invalid JSON: "+b)},parseXML:function(c){if(typeof c!="string"||!c)return null;var d,f;try{a.DOMParser?(f=new DOMParser,d=f.parseFromString(c,"text/xml")):(d=new ActiveXObject("Microsoft.XMLDOM"),d.async="false",d.loadXML(c))}catch(g){d=b}(!d||!d.documentElement||d.getElementsByTagName("parsererror").length)&&e.error("Invalid XML: "+c);return d},noop:function(){},globalEval:function(b){b&&j.test(b)&&(a.execScript||function(b){a.eval.call(a,b)})(b)},camelCase:function(a){return a.replace(w,"ms-").replace(v,x)},nodeName:function(a,b){return a.nodeName&&a.nodeName.toUpperCase()===b.toUpperCase()},each:function(a,c,d){var f,g=0,h=a.length,i=h===b||e.isFunction(a);if(d){if(i){for(f in a)if(c.apply(a[f],d)===!1)break}else for(;g<h;)if(c.apply(a[g++],d)===!1)break}else if(i){for(f in a)if(c.call(a[f],f,a[f])===!1)break}else for(;g<h;)if(c.call(a[g],g,a[g++])===!1)break;return a},trim:G?function(a){return a==null?"":G.call(a)}:function(a){return a==null?"":(a+"").replace(k,"").replace(l,"")},makeArray:function(a,b){var c=b||[];if(a!=null){var d=e.type(a);a.length==null||d==="string"||d==="function"||d==="regexp"||e.isWindow(a)?E.call(c,a):e.merge(c,a)}return c},inArray:function(a,b,c){var d;if(b){if(H)return H.call(b,a,c);d=b.length,c=c?c<0?Math.max(0,d+c):c:0;for(;c<d;c++)if(c in b&&b[c]===a)return c}return-1},merge:function(a,c){var d=a.length,e=0;if(typeof c.length=="number")for(var f=c.length;e<f;e++)a[d++]=c[e];else while(c[e]!==b)a[d++]=c[e++];a.length=d;return a},grep:function(a,b,c){var d=[],e;c=!!c;for(var f=0,g=a.length;f<g;f++)e=!!b(a[f],f),c!==e&&d.push(a[f]);return d},map:function(a,c,d){var f,g,h=[],i=0,j=a.length,k=a instanceof e||j!==b&&typeof j=="number"&&(j>0&&a[0]&&a[j-1]||j===0||e.isArray(a));if(k)for(;i<j;i++)f=c(a[i],i,d),f!=null&&(h[h.length]=f);else for(g in a)f=c(a[g],g,d),f!=null&&(h[h.length]=f);return h.concat.apply([],h)},guid:1,proxy:function(a,c){if(typeof c=="string"){var d=a[c];c=a,a=d}if(!e.isFunction(a))return b;var f=F.call(arguments,2),g=function(){return a.apply(c,f.concat(F.call(arguments)))};g.guid=a.guid=a.guid||g.guid||e.guid++;return g},access:function(a,c,d,f,g,h,i){var j,k=d==null,l=0,m=a.length;if(d&&typeof d=="object"){for(l in d)e.access(a,c,l,d[l],1,h,f);g=1}else if(f!==b){j=i===b&&e.isFunction(f),k&&(j?(j=c,c=function(a,b,c){return j.call(e(a),c)}):(c.call(a,f),c=null));if(c)for(;l<m;l++)c(a[l],d,j?f.call(a[l],l,c(a[l],d)):f,i);g=1}return g?a:k?c.call(a):m?c(a[0],d):h},now:function(){return(new Date).getTime()},uaMatch:function(a){a=a.toLowerCase();var b=r.exec(a)||s.exec(a)||t.exec(a)||a.indexOf("compatible")<0&&u.exec(a)||[];return{browser:b[1]||"",version:b[2]||"0"}},sub:function(){function a(b,c){return new a.fn.init(b,c)}e.extend(!0,a,this),a.superclass=this,a.fn=a.prototype=this(),a.fn.constructor=a,a.sub=this.sub,a.fn.init=function(d,f){f&&f instanceof e&&!(f instanceof a)&&(f=a(f));return e.fn.init.call(this,d,f,b)},a.fn.init.prototype=a.fn;var b=a(c);return a},browser:{}}),e.each("Boolean Number String Function Array Date RegExp Object".split(" "),function(a,b){I["[object "+b+"]"]=b.toLowerCase()}),z=e.uaMatch(y),z.browser&&(e.browser[z.browser]=!0,e.browser.version=z.version),e.browser.webkit&&(e.browser.safari=!0),j.test(" ")&&(k=/^[\s\xA0]+/,l=/[\s\xA0]+$/),h=e(c),c.addEventListener?B=function(){c.removeEventListener("DOMContentLoaded",B,!1),e.ready()}:c.attachEvent&&(B=function(){c.readyState==="complete"&&(c.detachEvent("onreadystatechange",B),e.ready())});return e}(),g={};f.Callbacks=function(a){a=a?g[a]||h(a):{};var c=[],d=[],e,i,j,k,l,m,n=function(b){var d,e,g,h,i;for(d=0,e=b.length;d<e;d++)g=b[d],h=f.type(g),h==="array"?n(g):h==="function"&&(!a.unique||!p.has(g))&&c.push(g)},o=function(b,f){f=f||[],e=!a.memory||[b,f],i=!0,j=!0,m=k||0,k=0,l=c.length;for(;c&&m<l;m++)if(c[m].apply(b,f)===!1&&a.stopOnFalse){e=!0;break}j=!1,c&&(a.once?e===!0?p.disable():c=[]:d&&d.length&&(e=d.shift(),p.fireWith(e[0],e[1])))},p={add:function(){if(c){var a=c.length;n(arguments),j?l=c.length:e&&e!==!0&&(k=a,o(e[0],e[1]))}return this},remove:function(){if(c){var b=arguments,d=0,e=b.length;for(;d<e;d++)for(var f=0;f<c.length;f++)if(b[d]===c[f]){j&&f<=l&&(l--,f<=m&&m--),c.splice(f--,1);if(a.unique)break}}return this},has:function(a){if(c){var b=0,d=c.length;for(;b<d;b++)if(a===c[b])return!0}return!1},empty:function(){c=[];return this},disable:function(){c=d=e=b;return this},disabled:function(){return!c},lock:function(){d=b,(!e||e===!0)&&p.disable();return this},locked:function(){return!d},fireWith:function(b,c){d&&(j?a.once||d.push([b,c]):(!a.once||!e)&&o(b,c));return this},fire:function(){p.fireWith(this,arguments);return this},fired:function(){return!!i}};return p};var i=[].slice;f.extend({Deferred:function(a){var b=f.Callbacks("once memory"),c=f.Callbacks("once memory"),d=f.Callbacks("memory"),e="pending",g={resolve:b,reject:c,notify:d},h={done:b.add,fail:c.add,progress:d.add,state:function(){return e},isResolved:b.fired,isRejected:c.fired,then:function(a,b,c){i.done(a).fail(b).progress(c);return this},always:function(){i.done.apply(i,arguments).fail.apply(i,arguments);return this},pipe:function(a,b,c){return f.Deferred(function(d){f.each({done:[a,"resolve"],fail:[b,"reject"],progress:[c,"notify"]},function(a,b){var c=b[0],e=b[1],g;f.isFunction(c)?i[a](function(){g=c.apply(this,arguments),g&&f.isFunction(g.promise)?g.promise().then(d.resolve,d.reject,d.notify):d[e+"With"](this===i?d:this,[g])}):i[a](d[e])})}).promise()},promise:function(a){if(a==null)a=h;else for(var b in h)a[b]=h[b];return a}},i=h.promise({}),j;for(j in g)i[j]=g[j].fire,i[j+"With"]=g[j].fireWith;i.done(function(){e="resolved"},c.disable,d.lock).fail(function(){e="rejected"},b.disable,d.lock),a&&a.call(i,i);return i},when:function(a){function m(a){return function(b){e[a]=arguments.length>1?i.call(arguments,0):b,j.notifyWith(k,e)}}function l(a){return function(c){b[a]=arguments.length>1?i.call(arguments,0):c,--g||j.resolveWith(j,b)}}var b=i.call(arguments,0),c=0,d=b.length,e=Array(d),g=d,h=d,j=d<=1&&a&&f.isFunction(a.promise)?a:f.Deferred(),k=j.promise();if(d>1){for(;c<d;c++)b[c]&&b[c].promise&&f.isFunction(b[c].promise)?b[c].promise().then(l(c),j.reject,m(c)):--g;g||j.resolveWith(j,b)}else j!==a&&j.resolveWith(j,d?[a]:[]);return k}}),f.support=function(){var b,d,e,g,h,i,j,k,l,m,n,o,p=c.createElement("div"),q=c.documentElement;p.setAttribute("className","t"),p.innerHTML="   <link/><table></table><a href='/a' style='top:1px;float:left;opacity:.55;'>a</a><input type='checkbox'/>",d=p.getElementsByTagName("*"),e=p.getElementsByTagName("a")[0];if(!d||!d.length||!e)return{};g=c.createElement("select"),h=g.appendChild(c.createElement("option")),i=p.getElementsByTagName("input")[0],b={leadingWhitespace:p.firstChild.nodeType===3,tbody:!p.getElementsByTagName("tbody").length,htmlSerialize:!!p.getElementsByTagName("link").length,style:/top/.test(e.getAttribute("style")),hrefNormalized:e.getAttribute("href")==="/a",opacity:/^0.55/.test(e.style.opacity),cssFloat:!!e.style.cssFloat,checkOn:i.value==="on",optSelected:h.selected,getSetAttribute:p.className!=="t",enctype:!!c.createElement("form").enctype,html5Clone:c.createElement("nav").cloneNode(!0).outerHTML!=="<:nav></:nav>",submitBubbles:!0,changeBubbles:!0,focusinBubbles:!1,deleteExpando:!0,noCloneEvent:!0,inlineBlockNeedsLayout:!1,shrinkWrapBlocks:!1,reliableMarginRight:!0,pixelMargin:!0},f.boxModel=b.boxModel=c.compatMode==="CSS1Compat",i.checked=!0,b.noCloneChecked=i.cloneNode(!0).checked,g.disabled=!0,b.optDisabled=!h.disabled;try{delete p.test}catch(r){b.deleteExpando=!1}!p.addEventListener&&p.attachEvent&&p.fireEvent&&(p.attachEvent("onclick",function(){b.noCloneEvent=!1}),p.cloneNode(!0).fireEvent("onclick")),i=c.createElement("input"),i.value="t",i.setAttribute("type","radio"),b.radioValue=i.value==="t",i.setAttribute("checked","checked"),i.setAttribute("name","t"),p.appendChild(i),j=c.createDocumentFragment(),j.appendChild(p.lastChild),b.checkClone=j.cloneNode(!0).cloneNode(!0).lastChild.checked,b.appendChecked=i.checked,j.removeChild(i),j.appendChild(p);if(p.attachEvent)for(n in{submit:1,change:1,focusin:1})m="on"+n,o=m in p,o||(p.setAttribute(m,"return;"),o=typeof p[m]=="function"),b[n+"Bubbles"]=o;j.removeChild(p),j=g=h=p=i=null,f(function(){var d,e,g,h,i,j,l,m,n,q,r,s,t,u=c.getElementsByTagName("body")[0];!u||(m=1,t="padding:0;margin:0;border:",r="position:absolute;top:0;left:0;width:1px;height:1px;",s=t+"0;visibility:hidden;",n="style='"+r+t+"5px solid #000;",q="<div "+n+"display:block;'><div style='"+t+"0;display:block;overflow:hidden;'></div></div>"+"<table "+n+"' cellpadding='0' cellspacing='0'>"+"<tr><td></td></tr></table>",d=c.createElement("div"),d.style.cssText=s+"width:0;height:0;position:static;top:0;margin-top:"+m+"px",u.insertBefore(d,u.firstChild),p=c.createElement("div"),d.appendChild(p),p.innerHTML="<table><tr><td style='"+t+"0;display:none'></td><td>t</td></tr></table>",k=p.getElementsByTagName("td"),o=k[0].offsetHeight===0,k[0].style.display="",k[1].style.display="none",b.reliableHiddenOffsets=o&&k[0].offsetHeight===0,a.getComputedStyle&&(p.innerHTML="",l=c.createElement("div"),l.style.width="0",l.style.marginRight="0",p.style.width="2px",p.appendChild(l),b.reliableMarginRight=(parseInt((a.getComputedStyle(l,null)||{marginRight:0}).marginRight,10)||0)===0),typeof p.style.zoom!="undefined"&&(p.innerHTML="",p.style.width=p.style.padding="1px",p.style.border=0,p.style.overflow="hidden",p.style.display="inline",p.style.zoom=1,b.inlineBlockNeedsLayout=p.offsetWidth===3,p.style.display="block",p.style.overflow="visible",p.innerHTML="<div style='width:5px;'></div>",b.shrinkWrapBlocks=p.offsetWidth!==3),p.style.cssText=r+s,p.innerHTML=q,e=p.firstChild,g=e.firstChild,i=e.nextSibling.firstChild.firstChild,j={doesNotAddBorder:g.offsetTop!==5,doesAddBorderForTableAndCells:i.offsetTop===5},g.style.position="fixed",g.style.top="20px",j.fixedPosition=g.offsetTop===20||g.offsetTop===15,g.style.position=g.style.top="",e.style.overflow="hidden",e.style.position="relative",j.subtractsBorderForOverflowNotVisible=g.offsetTop===-5,j.doesNotIncludeMarginInBodyOffset=u.offsetTop!==m,a.getComputedStyle&&(p.style.marginTop="1%",b.pixelMargin=(a.getComputedStyle(p,null)||{marginTop:0}).marginTop!=="1%"),typeof d.style.zoom!="undefined"&&(d.style.zoom=1),u.removeChild(d),l=p=d=null,f.extend(b,j))});return b}();var j=/^(?:\{.*\}|\[.*\])$/,k=/([A-Z])/g;f.extend({cache:{},uuid:0,expando:"jQuery"+(f.fn.jquery+Math.random()).replace(/\D/g,""),noData:{embed:!0,object:"clsid:D27CDB6E-AE6D-11cf-96B8-444553540000",applet:!0},hasData:function(a){a=a.nodeType?f.cache[a[f.expando]]:a[f.expando];return!!a&&!m(a)},data:function(a,c,d,e){if(!!f.acceptData(a)){var g,h,i,j=f.expando,k=typeof c=="string",l=a.nodeType,m=l?f.cache:a,n=l?a[j]:a[j]&&j,o=c==="events";if((!n||!m[n]||!o&&!e&&!m[n].data)&&k&&d===b)return;n||(l?a[j]=n=++f.uuid:n=j),m[n]||(m[n]={},l||(m[n].toJSON=f.noop));if(typeof c=="object"||typeof c=="function")e?m[n]=f.extend(m[n],c):m[n].data=f.extend(m[n].data,c);g=h=m[n],e||(h.data||(h.data={}),h=h.data),d!==b&&(h[f.camelCase(c)]=d);if(o&&!h[c])return g.events;k?(i=h[c],i==null&&(i=h[f.camelCase(c)])):i=h;return i}},removeData:function(a,b,c){if(!!f.acceptData(a)){var d,e,g,h=f.expando,i=a.nodeType,j=i?f.cache:a,k=i?a[h]:h;if(!j[k])return;if(b){d=c?j[k]:j[k].data;if(d){f.isArray(b)||(b in d?b=[b]:(b=f.camelCase(b),b in d?b=[b]:b=b.split(" ")));for(e=0,g=b.length;e<g;e++)delete d[b[e]];if(!(c?m:f.isEmptyObject)(d))return}}if(!c){delete j[k].data;if(!m(j[k]))return}f.support.deleteExpando||!j.setInterval?delete j[k]:j[k]=null,i&&(f.support.deleteExpando?delete a[h]:a.removeAttribute?a.removeAttribute(h):a[h]=null)}},_data:function(a,b,c){return f.data(a,b,c,!0)},acceptData:function(a){if(a.nodeName){var b=f.noData[a.nodeName.toLowerCase()];if(b)return b!==!0&&a.getAttribute("classid")===b}return!0}}),f.fn.extend({data:function(a,c){var d,e,g,h,i,j=this[0],k=0,m=null;if(a===b){if(this.length){m=f.data(j);if(j.nodeType===1&&!f._data(j,"parsedAttrs")){g=j.attributes;for(i=g.length;k<i;k++)h=g[k].name,h.indexOf("data-")===0&&(h=f.camelCase(h.substring(5)),l(j,h,m[h]));f._data(j,"parsedAttrs",!0)}}return m}if(typeof a=="object")return this.each(function(){f.data(this,a)});d=a.split(".",2),d[1]=d[1]?"."+d[1]:"",e=d[1]+"!";return f.access(this,function(c){if(c===b){m=this.triggerHandler("getData"+e,[d[0]]),m===b&&j&&(m=f.data(j,a),m=l(j,a,m));return m===b&&d[1]?this.data(d[0]):m}d[1]=c,this.each(function(){var b=f(this);b.triggerHandler("setData"+e,d),f.data(this,a,c),b.triggerHandler("changeData"+e,d)})},null,c,arguments.length>1,null,!1)},removeData:function(a){return this.each(function(){f.removeData(this,a)})}}),f.extend({_mark:function(a,b){a&&(b=(b||"fx")+"mark",f._data(a,b,(f._data(a,b)||0)+1))},_unmark:function(a,b,c){a!==!0&&(c=b,b=a,a=!1);if(b){c=c||"fx";var d=c+"mark",e=a?0:(f._data(b,d)||1)-1;e?f._data(b,d,e):(f.removeData(b,d,!0),n(b,c,"mark"))}},queue:function(a,b,c){var d;if(a){b=(b||"fx")+"queue",d=f._data(a,b),c&&(!d||f.isArray(c)?d=f._data(a,b,f.makeArray(c)):d.push(c));return d||[]}},dequeue:function(a,b){b=b||"fx";var c=f.queue(a,b),d=c.shift(),e={};d==="inprogress"&&(d=c.shift()),d&&(b==="fx"&&c.unshift("inprogress"),f._data(a,b+".run",e),d.call(a,function(){f.dequeue(a,b)},e)),c.length||(f.removeData(a,b+"queue "+b+".run",!0),n(a,b,"queue"))}}),f.fn.extend({queue:function(a,c){var d=2;typeof a!="string"&&(c=a,a="fx",d--);if(arguments.length<d)return f.queue(this[0],a);return c===b?this:this.each(function(){var b=f.queue(this,a,c);a==="fx"&&b[0]!=="inprogress"&&f.dequeue(this,a)})},dequeue:function(a){return this.each(function(){f.dequeue(this,a)})},delay:function(a,b){a=f.fx?f.fx.speeds[a]||a:a,b=b||"fx";return this.queue(b,function(b,c){var d=setTimeout(b,a);c.stop=function(){clearTimeout(d)}})},clearQueue:function(a){return this.queue(a||"fx",[])},promise:function(a,c){function m(){--h||d.resolveWith(e,[e])}typeof a!="string"&&(c=a,a=b),a=a||"fx";var d=f.Deferred(),e=this,g=e.length,h=1,i=a+"defer",j=a+"queue",k=a+"mark",l;while(g--)if(l=f.data(e[g],i,b,!0)||(f.data(e[g],j,b,!0)||f.data(e[g],k,b,!0))&&f.data(e[g],i,f.Callbacks("once memory"),!0))h++,l.add(m);m();return d.promise(c)}});var o=/[\n\t\r]/g,p=/\s+/,q=/\r/g,r=/^(?:button|input)$/i,s=/^(?:button|input|object|select|textarea)$/i,t=/^a(?:rea)?$/i,u=/^(?:autofocus|autoplay|async|checked|controls|defer|disabled|hidden|loop|multiple|open|readonly|required|scoped|selected)$/i,v=f.support.getSetAttribute,w,x,y;f.fn.extend({attr:function(a,b){return f.access(this,f.attr,a,b,arguments.length>1)},removeAttr:function(a){return this.each(function(){f.removeAttr(this,a)})},prop:function(a,b){return f.access(this,f.prop,a,b,arguments.length>1)},removeProp:function(a){a=f.propFix[a]||a;return this.each(function(){try{this[a]=b,delete this[a]}catch(c){}})},addClass:function(a){var b,c,d,e,g,h,i;if(f.isFunction(a))return this.each(function(b){f(this).addClass(a.call(this,b,this.className))});if(a&&typeof a=="string"){b=a.split(p);for(c=0,d=this.length;c<d;c++){e=this[c];if(e.nodeType===1)if(!e.className&&b.length===1)e.className=a;else{g=" "+e.className+" ";for(h=0,i=b.length;h<i;h++)~g.indexOf(" "+b[h]+" ")||(g+=b[h]+" ");e.className=f.trim(g)}}}return this},removeClass:function(a){var c,d,e,g,h,i,j;if(f.isFunction(a))return this.each(function(b){f(this).removeClass(a.call(this,b,this.className))});if(a&&typeof a=="string"||a===b){c=(a||"").split(p);for(d=0,e=this.length;d<e;d++){g=this[d];if(g.nodeType===1&&g.className)if(a){h=(" "+g.className+" ").replace(o," ");for(i=0,j=c.length;i<j;i++)h=h.replace(" "+c[i]+" "," ");g.className=f.trim(h)}else g.className=""}}return this},toggleClass:function(a,b){var c=typeof a,d=typeof b=="boolean";if(f.isFunction(a))return this.each(function(c){f(this).toggleClass(a.call(this,c,this.className,b),b)});return this.each(function(){if(c==="string"){var e,g=0,h=f(this),i=b,j=a.split(p);while(e=j[g++])i=d?i:!h.hasClass(e),h[i?"addClass":"removeClass"](e)}else if(c==="undefined"||c==="boolean")this.className&&f._data(this,"__className__",this.className),this.className=this.className||a===!1?"":f._data(this,"__className__")||""})},hasClass:function(a){var b=" "+a+" ",c=0,d=this.length;for(;c<d;c++)if(this[c].nodeType===1&&(" "+this[c].className+" ").replace(o," ").indexOf(b)>-1)return!0;return!1},val:function(a){var c,d,e,g=this[0];{if(!!arguments.length){e=f.isFunction(a);return this.each(function(d){var g=f(this),h;if(this.nodeType===1){e?h=a.call(this,d,g.val()):h=a,h==null?h="":typeof h=="number"?h+="":f.isArray(h)&&(h=f.map(h,function(a){return a==null?"":a+""})),c=f.valHooks[this.type]||f.valHooks[this.nodeName.toLowerCase()];if(!c||!("set"in c)||c.set(this,h,"value")===b)this.value=h}})}if(g){c=f.valHooks[g.type]||f.valHooks[g.nodeName.toLowerCase()];if(c&&"get"in c&&(d=c.get(g,"value"))!==b)return d;d=g.value;return typeof d=="string"?d.replace(q,""):d==null?"":d}}}}),f.extend({valHooks:{option:{get:function(a){var b=a.attributes.value;return!b||b.specified?a.value:a.text}},select:{get:function(a){var b,c,d,e,g=a.selectedIndex,h=[],i=a.options,j=a.type==="select-one";if(g<0)return null;c=j?g:0,d=j?g+1:i.length;for(;c<d;c++){e=i[c];if(e.selected&&(f.support.optDisabled?!e.disabled:e.getAttribute("disabled")===null)&&(!e.parentNode.disabled||!f.nodeName(e.parentNode,"optgroup"))){b=f(e).val();if(j)return b;h.push(b)}}if(j&&!h.length&&i.length)return f(i[g]).val();return h},set:function(a,b){var c=f.makeArray(b);f(a).find("option").each(function(){this.selected=f.inArray(f(this).val(),c)>=0}),c.length||(a.selectedIndex=-1);return c}}},attrFn:{val:!0,css:!0,html:!0,text:!0,data:!0,width:!0,height:!0,offset:!0},attr:function(a,c,d,e){var g,h,i,j=a.nodeType;if(!!a&&j!==3&&j!==8&&j!==2){if(e&&c in f.attrFn)return f(a)[c](d);if(typeof a.getAttribute=="undefined")return f.prop(a,c,d);i=j!==1||!f.isXMLDoc(a),i&&(c=c.toLowerCase(),h=f.attrHooks[c]||(u.test(c)?x:w));if(d!==b){if(d===null){f.removeAttr(a,c);return}if(h&&"set"in h&&i&&(g=h.set(a,d,c))!==b)return g;a.setAttribute(c,""+d);return d}if(h&&"get"in h&&i&&(g=h.get(a,c))!==null)return g;g=a.getAttribute(c);return g===null?b:g}},removeAttr:function(a,b){var c,d,e,g,h,i=0;if(b&&a.nodeType===1){d=b.toLowerCase().split(p),g=d.length;for(;i<g;i++)e=d[i],e&&(c=f.propFix[e]||e,h=u.test(e),h||f.attr(a,e,""),a.removeAttribute(v?e:c),h&&c in a&&(a[c]=!1))}},attrHooks:{type:{set:function(a,b){if(r.test(a.nodeName)&&a.parentNode)f.error("type property can't be changed");else if(!f.support.radioValue&&b==="radio"&&f.nodeName(a,"input")){var c=a.value;a.setAttribute("type",b),c&&(a.value=c);return b}}},value:{get:function(a,b){if(w&&f.nodeName(a,"button"))return w.get(a,b);return b in a?a.value:null},set:function(a,b,c){if(w&&f.nodeName(a,"button"))return w.set(a,b,c);a.value=b}}},propFix:{tabindex:"tabIndex",readonly:"readOnly","for":"htmlFor","class":"className",maxlength:"maxLength",cellspacing:"cellSpacing",cellpadding:"cellPadding",rowspan:"rowSpan",colspan:"colSpan",usemap:"useMap",frameborder:"frameBorder",contenteditable:"contentEditable"},prop:function(a,c,d){var e,g,h,i=a.nodeType;if(!!a&&i!==3&&i!==8&&i!==2){h=i!==1||!f.isXMLDoc(a),h&&(c=f.propFix[c]||c,g=f.propHooks[c]);return d!==b?g&&"set"in g&&(e=g.set(a,d,c))!==b?e:a[c]=d:g&&"get"in g&&(e=g.get(a,c))!==null?e:a[c]}},propHooks:{tabIndex:{get:function(a){var c=a.getAttributeNode("tabindex");return c&&c.specified?parseInt(c.value,10):s.test(a.nodeName)||t.test(a.nodeName)&&a.href?0:b}}}}),f.attrHooks.tabindex=f.propHooks.tabIndex,x={get:function(a,c){var d,e=f.prop(a,c);return e===!0||typeof e!="boolean"&&(d=a.getAttributeNode(c))&&d.nodeValue!==!1?c.toLowerCase():b},set:function(a,b,c){var d;b===!1?f.removeAttr(a,c):(d=f.propFix[c]||c,d in a&&(a[d]=!0),a.setAttribute(c,c.toLowerCase()));return c}},v||(y={name:!0,id:!0,coords:!0},w=f.valHooks.button={get:function(a,c){var d;d=a.getAttributeNode(c);return d&&(y[c]?d.nodeValue!=="":d.specified)?d.nodeValue:b},set:function(a,b,d){var e=a.getAttributeNode(d);e||(e=c.createAttribute(d),a.setAttributeNode(e));return e.nodeValue=b+""}},f.attrHooks.tabindex.set=w.set,f.each(["width","height"],function(a,b){f.attrHooks[b]=f.extend(f.attrHooks[b],{set:function(a,c){if(c===""){a.setAttribute(b,"auto");return c}}})}),f.attrHooks.contenteditable={get:w.get,set:function(a,b,c){b===""&&(b="false"),w.set(a,b,c)}}),f.support.hrefNormalized||f.each(["href","src","width","height"],function(a,c){f.attrHooks[c]=f.extend(f.attrHooks[c],{get:function(a){var d=a.getAttribute(c,2);return d===null?b:d}})}),f.support.style||(f.attrHooks.style={get:function(a){return a.style.cssText.toLowerCase()||b},set:function(a,b){return a.style.cssText=""+b}}),f.support.optSelected||(f.propHooks.selected=f.extend(f.propHooks.selected,{get:function(a){var b=a.parentNode;b&&(b.selectedIndex,b.parentNode&&b.parentNode.selectedIndex);return null}})),f.support.enctype||(f.propFix.enctype="encoding"),f.support.checkOn||f.each(["radio","checkbox"],function(){f.valHooks[this]={get:function(a){return a.getAttribute("value")===null?"on":a.value}}}),f.each(["radio","checkbox"],function(){f.valHooks[this]=f.extend(f.valHooks[this],{set:function(a,b){if(f.isArray(b))return a.checked=f.inArray(f(a).val(),b)>=0}})});var z=/^(?:textarea|input|select)$/i,A=/^([^\.]*)?(?:\.(.+))?$/,B=/(?:^|\s)hover(\.\S+)?\b/,C=/^key/,D=/^(?:mouse|contextmenu)|click/,E=/^(?:focusinfocus|focusoutblur)$/,F=/^(\w*)(?:#([\w\-]+))?(?:\.([\w\-]+))?$/,G=function(
a){var b=F.exec(a);b&&(b[1]=(b[1]||"").toLowerCase(),b[3]=b[3]&&new RegExp("(?:^|\\s)"+b[3]+"(?:\\s|$)"));return b},H=function(a,b){var c=a.attributes||{};return(!b[1]||a.nodeName.toLowerCase()===b[1])&&(!b[2]||(c.id||{}).value===b[2])&&(!b[3]||b[3].test((c["class"]||{}).value))},I=function(a){return f.event.special.hover?a:a.replace(B,"mouseenter$1 mouseleave$1")};f.event={add:function(a,c,d,e,g){var h,i,j,k,l,m,n,o,p,q,r,s;if(!(a.nodeType===3||a.nodeType===8||!c||!d||!(h=f._data(a)))){d.handler&&(p=d,d=p.handler,g=p.selector),d.guid||(d.guid=f.guid++),j=h.events,j||(h.events=j={}),i=h.handle,i||(h.handle=i=function(a){return typeof f!="undefined"&&(!a||f.event.triggered!==a.type)?f.event.dispatch.apply(i.elem,arguments):b},i.elem=a),c=f.trim(I(c)).split(" ");for(k=0;k<c.length;k++){l=A.exec(c[k])||[],m=l[1],n=(l[2]||"").split(".").sort(),s=f.event.special[m]||{},m=(g?s.delegateType:s.bindType)||m,s=f.event.special[m]||{},o=f.extend({type:m,origType:l[1],data:e,handler:d,guid:d.guid,selector:g,quick:g&&G(g),namespace:n.join(".")},p),r=j[m];if(!r){r=j[m]=[],r.delegateCount=0;if(!s.setup||s.setup.call(a,e,n,i)===!1)a.addEventListener?a.addEventListener(m,i,!1):a.attachEvent&&a.attachEvent("on"+m,i)}s.add&&(s.add.call(a,o),o.handler.guid||(o.handler.guid=d.guid)),g?r.splice(r.delegateCount++,0,o):r.push(o),f.event.global[m]=!0}a=null}},global:{},remove:function(a,b,c,d,e){var g=f.hasData(a)&&f._data(a),h,i,j,k,l,m,n,o,p,q,r,s;if(!!g&&!!(o=g.events)){b=f.trim(I(b||"")).split(" ");for(h=0;h<b.length;h++){i=A.exec(b[h])||[],j=k=i[1],l=i[2];if(!j){for(j in o)f.event.remove(a,j+b[h],c,d,!0);continue}p=f.event.special[j]||{},j=(d?p.delegateType:p.bindType)||j,r=o[j]||[],m=r.length,l=l?new RegExp("(^|\\.)"+l.split(".").sort().join("\\.(?:.*\\.)?")+"(\\.|$)"):null;for(n=0;n<r.length;n++)s=r[n],(e||k===s.origType)&&(!c||c.guid===s.guid)&&(!l||l.test(s.namespace))&&(!d||d===s.selector||d==="**"&&s.selector)&&(r.splice(n--,1),s.selector&&r.delegateCount--,p.remove&&p.remove.call(a,s));r.length===0&&m!==r.length&&((!p.teardown||p.teardown.call(a,l)===!1)&&f.removeEvent(a,j,g.handle),delete o[j])}f.isEmptyObject(o)&&(q=g.handle,q&&(q.elem=null),f.removeData(a,["events","handle"],!0))}},customEvent:{getData:!0,setData:!0,changeData:!0},trigger:function(c,d,e,g){if(!e||e.nodeType!==3&&e.nodeType!==8){var h=c.type||c,i=[],j,k,l,m,n,o,p,q,r,s;if(E.test(h+f.event.triggered))return;h.indexOf("!")>=0&&(h=h.slice(0,-1),k=!0),h.indexOf(".")>=0&&(i=h.split("."),h=i.shift(),i.sort());if((!e||f.event.customEvent[h])&&!f.event.global[h])return;c=typeof c=="object"?c[f.expando]?c:new f.Event(h,c):new f.Event(h),c.type=h,c.isTrigger=!0,c.exclusive=k,c.namespace=i.join("."),c.namespace_re=c.namespace?new RegExp("(^|\\.)"+i.join("\\.(?:.*\\.)?")+"(\\.|$)"):null,o=h.indexOf(":")<0?"on"+h:"";if(!e){j=f.cache;for(l in j)j[l].events&&j[l].events[h]&&f.event.trigger(c,d,j[l].handle.elem,!0);return}c.result=b,c.target||(c.target=e),d=d!=null?f.makeArray(d):[],d.unshift(c),p=f.event.special[h]||{};if(p.trigger&&p.trigger.apply(e,d)===!1)return;r=[[e,p.bindType||h]];if(!g&&!p.noBubble&&!f.isWindow(e)){s=p.delegateType||h,m=E.test(s+h)?e:e.parentNode,n=null;for(;m;m=m.parentNode)r.push([m,s]),n=m;n&&n===e.ownerDocument&&r.push([n.defaultView||n.parentWindow||a,s])}for(l=0;l<r.length&&!c.isPropagationStopped();l++)m=r[l][0],c.type=r[l][1],q=(f._data(m,"events")||{})[c.type]&&f._data(m,"handle"),q&&q.apply(m,d),q=o&&m[o],q&&f.acceptData(m)&&q.apply(m,d)===!1&&c.preventDefault();c.type=h,!g&&!c.isDefaultPrevented()&&(!p._default||p._default.apply(e.ownerDocument,d)===!1)&&(h!=="click"||!f.nodeName(e,"a"))&&f.acceptData(e)&&o&&e[h]&&(h!=="focus"&&h!=="blur"||c.target.offsetWidth!==0)&&!f.isWindow(e)&&(n=e[o],n&&(e[o]=null),f.event.triggered=h,e[h](),f.event.triggered=b,n&&(e[o]=n));return c.result}},dispatch:function(c){c=f.event.fix(c||a.event);var d=(f._data(this,"events")||{})[c.type]||[],e=d.delegateCount,g=[].slice.call(arguments,0),h=!c.exclusive&&!c.namespace,i=f.event.special[c.type]||{},j=[],k,l,m,n,o,p,q,r,s,t,u;g[0]=c,c.delegateTarget=this;if(!i.preDispatch||i.preDispatch.call(this,c)!==!1){if(e&&(!c.button||c.type!=="click")){n=f(this),n.context=this.ownerDocument||this;for(m=c.target;m!=this;m=m.parentNode||this)if(m.disabled!==!0){p={},r=[],n[0]=m;for(k=0;k<e;k++)s=d[k],t=s.selector,p[t]===b&&(p[t]=s.quick?H(m,s.quick):n.is(t)),p[t]&&r.push(s);r.length&&j.push({elem:m,matches:r})}}d.length>e&&j.push({elem:this,matches:d.slice(e)});for(k=0;k<j.length&&!c.isPropagationStopped();k++){q=j[k],c.currentTarget=q.elem;for(l=0;l<q.matches.length&&!c.isImmediatePropagationStopped();l++){s=q.matches[l];if(h||!c.namespace&&!s.namespace||c.namespace_re&&c.namespace_re.test(s.namespace))c.data=s.data,c.handleObj=s,o=((f.event.special[s.origType]||{}).handle||s.handler).apply(q.elem,g),o!==b&&(c.result=o,o===!1&&(c.preventDefault(),c.stopPropagation()))}}i.postDispatch&&i.postDispatch.call(this,c);return c.result}},props:"attrChange attrName relatedNode srcElement altKey bubbles cancelable ctrlKey currentTarget eventPhase metaKey relatedTarget shiftKey target timeStamp view which".split(" "),fixHooks:{},keyHooks:{props:"char charCode key keyCode".split(" "),filter:function(a,b){a.which==null&&(a.which=b.charCode!=null?b.charCode:b.keyCode);return a}},mouseHooks:{props:"button buttons clientX clientY fromElement offsetX offsetY pageX pageY screenX screenY toElement".split(" "),filter:function(a,d){var e,f,g,h=d.button,i=d.fromElement;a.pageX==null&&d.clientX!=null&&(e=a.target.ownerDocument||c,f=e.documentElement,g=e.body,a.pageX=d.clientX+(f&&f.scrollLeft||g&&g.scrollLeft||0)-(f&&f.clientLeft||g&&g.clientLeft||0),a.pageY=d.clientY+(f&&f.scrollTop||g&&g.scrollTop||0)-(f&&f.clientTop||g&&g.clientTop||0)),!a.relatedTarget&&i&&(a.relatedTarget=i===a.target?d.toElement:i),!a.which&&h!==b&&(a.which=h&1?1:h&2?3:h&4?2:0);return a}},fix:function(a){if(a[f.expando])return a;var d,e,g=a,h=f.event.fixHooks[a.type]||{},i=h.props?this.props.concat(h.props):this.props;a=f.Event(g);for(d=i.length;d;)e=i[--d],a[e]=g[e];a.target||(a.target=g.srcElement||c),a.target.nodeType===3&&(a.target=a.target.parentNode),a.metaKey===b&&(a.metaKey=a.ctrlKey);return h.filter?h.filter(a,g):a},special:{ready:{setup:f.bindReady},load:{noBubble:!0},focus:{delegateType:"focusin"},blur:{delegateType:"focusout"},beforeunload:{setup:function(a,b,c){f.isWindow(this)&&(this.onbeforeunload=c)},teardown:function(a,b){this.onbeforeunload===b&&(this.onbeforeunload=null)}}},simulate:function(a,b,c,d){var e=f.extend(new f.Event,c,{type:a,isSimulated:!0,originalEvent:{}});d?f.event.trigger(e,null,b):f.event.dispatch.call(b,e),e.isDefaultPrevented()&&c.preventDefault()}},f.event.handle=f.event.dispatch,f.removeEvent=c.removeEventListener?function(a,b,c){a.removeEventListener&&a.removeEventListener(b,c,!1)}:function(a,b,c){a.detachEvent&&a.detachEvent("on"+b,c)},f.Event=function(a,b){if(!(this instanceof f.Event))return new f.Event(a,b);a&&a.type?(this.originalEvent=a,this.type=a.type,this.isDefaultPrevented=a.defaultPrevented||a.returnValue===!1||a.getPreventDefault&&a.getPreventDefault()?K:J):this.type=a,b&&f.extend(this,b),this.timeStamp=a&&a.timeStamp||f.now(),this[f.expando]=!0},f.Event.prototype={preventDefault:function(){this.isDefaultPrevented=K;var a=this.originalEvent;!a||(a.preventDefault?a.preventDefault():a.returnValue=!1)},stopPropagation:function(){this.isPropagationStopped=K;var a=this.originalEvent;!a||(a.stopPropagation&&a.stopPropagation(),a.cancelBubble=!0)},stopImmediatePropagation:function(){this.isImmediatePropagationStopped=K,this.stopPropagation()},isDefaultPrevented:J,isPropagationStopped:J,isImmediatePropagationStopped:J},f.each({mouseenter:"mouseover",mouseleave:"mouseout"},function(a,b){f.event.special[a]={delegateType:b,bindType:b,handle:function(a){var c=this,d=a.relatedTarget,e=a.handleObj,g=e.selector,h;if(!d||d!==c&&!f.contains(c,d))a.type=e.origType,h=e.handler.apply(this,arguments),a.type=b;return h}}}),f.support.submitBubbles||(f.event.special.submit={setup:function(){if(f.nodeName(this,"form"))return!1;f.event.add(this,"click._submit keypress._submit",function(a){var c=a.target,d=f.nodeName(c,"input")||f.nodeName(c,"button")?c.form:b;d&&!d._submit_attached&&(f.event.add(d,"submit._submit",function(a){a._submit_bubble=!0}),d._submit_attached=!0)})},postDispatch:function(a){a._submit_bubble&&(delete a._submit_bubble,this.parentNode&&!a.isTrigger&&f.event.simulate("submit",this.parentNode,a,!0))},teardown:function(){if(f.nodeName(this,"form"))return!1;f.event.remove(this,"._submit")}}),f.support.changeBubbles||(f.event.special.change={setup:function(){if(z.test(this.nodeName)){if(this.type==="checkbox"||this.type==="radio")f.event.add(this,"propertychange._change",function(a){a.originalEvent.propertyName==="checked"&&(this._just_changed=!0)}),f.event.add(this,"click._change",function(a){this._just_changed&&!a.isTrigger&&(this._just_changed=!1,f.event.simulate("change",this,a,!0))});return!1}f.event.add(this,"beforeactivate._change",function(a){var b=a.target;z.test(b.nodeName)&&!b._change_attached&&(f.event.add(b,"change._change",function(a){this.parentNode&&!a.isSimulated&&!a.isTrigger&&f.event.simulate("change",this.parentNode,a,!0)}),b._change_attached=!0)})},handle:function(a){var b=a.target;if(this!==b||a.isSimulated||a.isTrigger||b.type!=="radio"&&b.type!=="checkbox")return a.handleObj.handler.apply(this,arguments)},teardown:function(){f.event.remove(this,"._change");return z.test(this.nodeName)}}),f.support.focusinBubbles||f.each({focus:"focusin",blur:"focusout"},function(a,b){var d=0,e=function(a){f.event.simulate(b,a.target,f.event.fix(a),!0)};f.event.special[b]={setup:function(){d++===0&&c.addEventListener(a,e,!0)},teardown:function(){--d===0&&c.removeEventListener(a,e,!0)}}}),f.fn.extend({on:function(a,c,d,e,g){var h,i;if(typeof a=="object"){typeof c!="string"&&(d=d||c,c=b);for(i in a)this.on(i,c,d,a[i],g);return this}d==null&&e==null?(e=c,d=c=b):e==null&&(typeof c=="string"?(e=d,d=b):(e=d,d=c,c=b));if(e===!1)e=J;else if(!e)return this;g===1&&(h=e,e=function(a){f().off(a);return h.apply(this,arguments)},e.guid=h.guid||(h.guid=f.guid++));return this.each(function(){f.event.add(this,a,e,d,c)})},one:function(a,b,c,d){return this.on(a,b,c,d,1)},off:function(a,c,d){if(a&&a.preventDefault&&a.handleObj){var e=a.handleObj;f(a.delegateTarget).off(e.namespace?e.origType+"."+e.namespace:e.origType,e.selector,e.handler);return this}if(typeof a=="object"){for(var g in a)this.off(g,c,a[g]);return this}if(c===!1||typeof c=="function")d=c,c=b;d===!1&&(d=J);return this.each(function(){f.event.remove(this,a,d,c)})},bind:function(a,b,c){return this.on(a,null,b,c)},unbind:function(a,b){return this.off(a,null,b)},live:function(a,b,c){f(this.context).on(a,this.selector,b,c);return this},die:function(a,b){f(this.context).off(a,this.selector||"**",b);return this},delegate:function(a,b,c,d){return this.on(b,a,c,d)},undelegate:function(a,b,c){return arguments.length==1?this.off(a,"**"):this.off(b,a,c)},trigger:function(a,b){return this.each(function(){f.event.trigger(a,b,this)})},triggerHandler:function(a,b){if(this[0])return f.event.trigger(a,b,this[0],!0)},toggle:function(a){var b=arguments,c=a.guid||f.guid++,d=0,e=function(c){var e=(f._data(this,"lastToggle"+a.guid)||0)%d;f._data(this,"lastToggle"+a.guid,e+1),c.preventDefault();return b[e].apply(this,arguments)||!1};e.guid=c;while(d<b.length)b[d++].guid=c;return this.click(e)},hover:function(a,b){return this.mouseenter(a).mouseleave(b||a)}}),f.each("blur focus focusin focusout load resize scroll unload click dblclick mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave change select submit keydown keypress keyup error contextmenu".split(" "),function(a,b){f.fn[b]=function(a,c){c==null&&(c=a,a=null);return arguments.length>0?this.on(b,null,a,c):this.trigger(b)},f.attrFn&&(f.attrFn[b]=!0),C.test(b)&&(f.event.fixHooks[b]=f.event.keyHooks),D.test(b)&&(f.event.fixHooks[b]=f.event.mouseHooks)}),function(){function x(a,b,c,e,f,g){for(var h=0,i=e.length;h<i;h++){var j=e[h];if(j){var k=!1;j=j[a];while(j){if(j[d]===c){k=e[j.sizset];break}if(j.nodeType===1){g||(j[d]=c,j.sizset=h);if(typeof b!="string"){if(j===b){k=!0;break}}else if(m.filter(b,[j]).length>0){k=j;break}}j=j[a]}e[h]=k}}}function w(a,b,c,e,f,g){for(var h=0,i=e.length;h<i;h++){var j=e[h];if(j){var k=!1;j=j[a];while(j){if(j[d]===c){k=e[j.sizset];break}j.nodeType===1&&!g&&(j[d]=c,j.sizset=h);if(j.nodeName.toLowerCase()===b){k=j;break}j=j[a]}e[h]=k}}}var a=/((?:\((?:\([^()]+\)|[^()]+)+\)|\[(?:\[[^\[\]]*\]|['"][^'"]*['"]|[^\[\]'"]+)+\]|\\.|[^ >+~,(\[\\]+)+|[>+~])(\s*,\s*)?((?:.|\r|\n)*)/g,d="sizcache"+(Math.random()+"").replace(".",""),e=0,g=Object.prototype.toString,h=!1,i=!0,j=/\\/g,k=/\r\n/g,l=/\W/;[0,0].sort(function(){i=!1;return 0});var m=function(b,d,e,f){e=e||[],d=d||c;var h=d;if(d.nodeType!==1&&d.nodeType!==9)return[];if(!b||typeof b!="string")return e;var i,j,k,l,n,q,r,t,u=!0,v=m.isXML(d),w=[],x=b;do{a.exec(""),i=a.exec(x);if(i){x=i[3],w.push(i[1]);if(i[2]){l=i[3];break}}}while(i);if(w.length>1&&p.exec(b))if(w.length===2&&o.relative[w[0]])j=y(w[0]+w[1],d,f);else{j=o.relative[w[0]]?[d]:m(w.shift(),d);while(w.length)b=w.shift(),o.relative[b]&&(b+=w.shift()),j=y(b,j,f)}else{!f&&w.length>1&&d.nodeType===9&&!v&&o.match.ID.test(w[0])&&!o.match.ID.test(w[w.length-1])&&(n=m.find(w.shift(),d,v),d=n.expr?m.filter(n.expr,n.set)[0]:n.set[0]);if(d){n=f?{expr:w.pop(),set:s(f)}:m.find(w.pop(),w.length===1&&(w[0]==="~"||w[0]==="+")&&d.parentNode?d.parentNode:d,v),j=n.expr?m.filter(n.expr,n.set):n.set,w.length>0?k=s(j):u=!1;while(w.length)q=w.pop(),r=q,o.relative[q]?r=w.pop():q="",r==null&&(r=d),o.relative[q](k,r,v)}else k=w=[]}k||(k=j),k||m.error(q||b);if(g.call(k)==="[object Array]")if(!u)e.push.apply(e,k);else if(d&&d.nodeType===1)for(t=0;k[t]!=null;t++)k[t]&&(k[t]===!0||k[t].nodeType===1&&m.contains(d,k[t]))&&e.push(j[t]);else for(t=0;k[t]!=null;t++)k[t]&&k[t].nodeType===1&&e.push(j[t]);else s(k,e);l&&(m(l,h,e,f),m.uniqueSort(e));return e};m.uniqueSort=function(a){if(u){h=i,a.sort(u);if(h)for(var b=1;b<a.length;b++)a[b]===a[b-1]&&a.splice(b--,1)}return a},m.matches=function(a,b){return m(a,null,null,b)},m.matchesSelector=function(a,b){return m(b,null,null,[a]).length>0},m.find=function(a,b,c){var d,e,f,g,h,i;if(!a)return[];for(e=0,f=o.order.length;e<f;e++){h=o.order[e];if(g=o.leftMatch[h].exec(a)){i=g[1],g.splice(1,1);if(i.substr(i.length-1)!=="\\"){g[1]=(g[1]||"").replace(j,""),d=o.find[h](g,b,c);if(d!=null){a=a.replace(o.match[h],"");break}}}}d||(d=typeof b.getElementsByTagName!="undefined"?b.getElementsByTagName("*"):[]);return{set:d,expr:a}},m.filter=function(a,c,d,e){var f,g,h,i,j,k,l,n,p,q=a,r=[],s=c,t=c&&c[0]&&m.isXML(c[0]);while(a&&c.length){for(h in o.filter)if((f=o.leftMatch[h].exec(a))!=null&&f[2]){k=o.filter[h],l=f[1],g=!1,f.splice(1,1);if(l.substr(l.length-1)==="\\")continue;s===r&&(r=[]);if(o.preFilter[h]){f=o.preFilter[h](f,s,d,r,e,t);if(!f)g=i=!0;else if(f===!0)continue}if(f)for(n=0;(j=s[n])!=null;n++)j&&(i=k(j,f,n,s),p=e^i,d&&i!=null?p?g=!0:s[n]=!1:p&&(r.push(j),g=!0));if(i!==b){d||(s=r),a=a.replace(o.match[h],"");if(!g)return[];break}}if(a===q)if(g==null)m.error(a);else break;q=a}return s},m.error=function(a){throw new Error("Syntax error, unrecognized expression: "+a)};var n=m.getText=function(a){var b,c,d=a.nodeType,e="";if(d){if(d===1||d===9||d===11){if(typeof a.textContent=="string")return a.textContent;if(typeof a.innerText=="string")return a.innerText.replace(k,"");for(a=a.firstChild;a;a=a.nextSibling)e+=n(a)}else if(d===3||d===4)return a.nodeValue}else for(b=0;c=a[b];b++)c.nodeType!==8&&(e+=n(c));return e},o=m.selectors={order:["ID","NAME","TAG"],match:{ID:/#((?:[\w\u00c0-\uFFFF\-]|\\.)+)/,CLASS:/\.((?:[\w\u00c0-\uFFFF\-]|\\.)+)/,NAME:/\[name=['"]*((?:[\w\u00c0-\uFFFF\-]|\\.)+)['"]*\]/,ATTR:/\[\s*((?:[\w\u00c0-\uFFFF\-]|\\.)+)\s*(?:(\S?=)\s*(?:(['"])(.*?)\3|(#?(?:[\w\u00c0-\uFFFF\-]|\\.)*)|)|)\s*\]/,TAG:/^((?:[\w\u00c0-\uFFFF\*\-]|\\.)+)/,CHILD:/:(only|nth|last|first)-child(?:\(\s*(even|odd|(?:[+\-]?\d+|(?:[+\-]?\d*)?n\s*(?:[+\-]\s*\d+)?))\s*\))?/,POS:/:(nth|eq|gt|lt|first|last|even|odd)(?:\((\d*)\))?(?=[^\-]|$)/,PSEUDO:/:((?:[\w\u00c0-\uFFFF\-]|\\.)+)(?:\((['"]?)((?:\([^\)]+\)|[^\(\)]*)+)\2\))?/},leftMatch:{},attrMap:{"class":"className","for":"htmlFor"},attrHandle:{href:function(a){return a.getAttribute("href")},type:function(a){return a.getAttribute("type")}},relative:{"+":function(a,b){var c=typeof b=="string",d=c&&!l.test(b),e=c&&!d;d&&(b=b.toLowerCase());for(var f=0,g=a.length,h;f<g;f++)if(h=a[f]){while((h=h.previousSibling)&&h.nodeType!==1);a[f]=e||h&&h.nodeName.toLowerCase()===b?h||!1:h===b}e&&m.filter(b,a,!0)},">":function(a,b){var c,d=typeof b=="string",e=0,f=a.length;if(d&&!l.test(b)){b=b.toLowerCase();for(;e<f;e++){c=a[e];if(c){var g=c.parentNode;a[e]=g.nodeName.toLowerCase()===b?g:!1}}}else{for(;e<f;e++)c=a[e],c&&(a[e]=d?c.parentNode:c.parentNode===b);d&&m.filter(b,a,!0)}},"":function(a,b,c){var d,f=e++,g=x;typeof b=="string"&&!l.test(b)&&(b=b.toLowerCase(),d=b,g=w),g("parentNode",b,f,a,d,c)},"~":function(a,b,c){var d,f=e++,g=x;typeof b=="string"&&!l.test(b)&&(b=b.toLowerCase(),d=b,g=w),g("previousSibling",b,f,a,d,c)}},find:{ID:function(a,b,c){if(typeof b.getElementById!="undefined"&&!c){var d=b.getElementById(a[1]);return d&&d.parentNode?[d]:[]}},NAME:function(a,b){if(typeof b.getElementsByName!="undefined"){var c=[],d=b.getElementsByName(a[1]);for(var e=0,f=d.length;e<f;e++)d[e].getAttribute("name")===a[1]&&c.push(d[e]);return c.length===0?null:c}},TAG:function(a,b){if(typeof b.getElementsByTagName!="undefined")return b.getElementsByTagName(a[1])}},preFilter:{CLASS:function(a,b,c,d,e,f){a=" "+a[1].replace(j,"")+" ";if(f)return a;for(var g=0,h;(h=b[g])!=null;g++)h&&(e^(h.className&&(" "+h.className+" ").replace(/[\t\n\r]/g," ").indexOf(a)>=0)?c||d.push(h):c&&(b[g]=!1));return!1},ID:function(a){return a[1].replace(j,"")},TAG:function(a,b){return a[1].replace(j,"").toLowerCase()},CHILD:function(a){if(a[1]==="nth"){a[2]||m.error(a[0]),a[2]=a[2].replace(/^\+|\s*/g,"");var b=/(-?)(\d*)(?:n([+\-]?\d*))?/.exec(a[2]==="even"&&"2n"||a[2]==="odd"&&"2n+1"||!/\D/.test(a[2])&&"0n+"+a[2]||a[2]);a[2]=b[1]+(b[2]||1)-0,a[3]=b[3]-0}else a[2]&&m.error(a[0]);a[0]=e++;return a},ATTR:function(a,b,c,d,e,f){var g=a[1]=a[1].replace(j,"");!f&&o.attrMap[g]&&(a[1]=o.attrMap[g]),a[4]=(a[4]||a[5]||"").replace(j,""),a[2]==="~="&&(a[4]=" "+a[4]+" ");return a},PSEUDO:function(b,c,d,e,f){if(b[1]==="not")if((a.exec(b[3])||"").length>1||/^\w/.test(b[3]))b[3]=m(b[3],null,null,c);else{var g=m.filter(b[3],c,d,!0^f);d||e.push.apply(e,g);return!1}else if(o.match.POS.test(b[0])||o.match.CHILD.test(b[0]))return!0;return b},POS:function(a){a.unshift(!0);return a}},filters:{enabled:function(a){return a.disabled===!1&&a.type!=="hidden"},disabled:function(a){return a.disabled===!0},checked:function(a){return a.checked===!0},selected:function(a){a.parentNode&&a.parentNode.selectedIndex;return a.selected===!0},parent:function(a){return!!a.firstChild},empty:function(a){return!a.firstChild},has:function(a,b,c){return!!m(c[3],a).length},header:function(a){return/h\d/i.test(a.nodeName)},text:function(a){var b=a.getAttribute("type"),c=a.type;return a.nodeName.toLowerCase()==="input"&&"text"===c&&(b===c||b===null)},radio:function(a){return a.nodeName.toLowerCase()==="input"&&"radio"===a.type},checkbox:function(a){return a.nodeName.toLowerCase()==="input"&&"checkbox"===a.type},file:function(a){return a.nodeName.toLowerCase()==="input"&&"file"===a.type},password:function(a){return a.nodeName.toLowerCase()==="input"&&"password"===a.type},submit:function(a){var b=a.nodeName.toLowerCase();return(b==="input"||b==="button")&&"submit"===a.type},image:function(a){return a.nodeName.toLowerCase()==="input"&&"image"===a.type},reset:function(a){var b=a.nodeName.toLowerCase();return(b==="input"||b==="button")&&"reset"===a.type},button:function(a){var b=a.nodeName.toLowerCase();return b==="input"&&"button"===a.type||b==="button"},input:function(a){return/input|select|textarea|button/i.test(a.nodeName)},focus:function(a){return a===a.ownerDocument.activeElement}},setFilters:{first:function(a,b){return b===0},last:function(a,b,c,d){return b===d.length-1},even:function(a,b){return b%2===0},odd:function(a,b){return b%2===1},lt:function(a,b,c){return b<c[3]-0},gt:function(a,b,c){return b>c[3]-0},nth:function(a,b,c){return c[3]-0===b},eq:function(a,b,c){return c[3]-0===b}},filter:{PSEUDO:function(a,b,c,d){var e=b[1],f=o.filters[e];if(f)return f(a,c,b,d);if(e==="contains")return(a.textContent||a.innerText||n([a])||"").indexOf(b[3])>=0;if(e==="not"){var g=b[3];for(var h=0,i=g.length;h<i;h++)if(g[h]===a)return!1;return!0}m.error(e)},CHILD:function(a,b){var c,e,f,g,h,i,j,k=b[1],l=a;switch(k){case"only":case"first":while(l=l.previousSibling)if(l.nodeType===1)return!1;if(k==="first")return!0;l=a;case"last":while(l=l.nextSibling)if(l.nodeType===1)return!1;return!0;case"nth":c=b[2],e=b[3];if(c===1&&e===0)return!0;f=b[0],g=a.parentNode;if(g&&(g[d]!==f||!a.nodeIndex)){i=0;for(l=g.firstChild;l;l=l.nextSibling)l.nodeType===1&&(l.nodeIndex=++i);g[d]=f}j=a.nodeIndex-e;return c===0?j===0:j%c===0&&j/c>=0}},ID:function(a,b){return a.nodeType===1&&a.getAttribute("id")===b},TAG:function(a,b){return b==="*"&&a.nodeType===1||!!a.nodeName&&a.nodeName.toLowerCase()===b},CLASS:function(a,b){return(" "+(a.className||a.getAttribute("class"))+" ").indexOf(b)>-1},ATTR:function(a,b){var c=b[1],d=m.attr?m.attr(a,c):o.attrHandle[c]?o.attrHandle[c](a):a[c]!=null?a[c]:a.getAttribute(c),e=d+"",f=b[2],g=b[4];return d==null?f==="!=":!f&&m.attr?d!=null:f==="="?e===g:f==="*="?e.indexOf(g)>=0:f==="~="?(" "+e+" ").indexOf(g)>=0:g?f==="!="?e!==g:f==="^="?e.indexOf(g)===0:f==="$="?e.substr(e.length-g.length)===g:f==="|="?e===g||e.substr(0,g.length+1)===g+"-":!1:e&&d!==!1},POS:function(a,b,c,d){var e=b[2],f=o.setFilters[e];if(f)return f(a,c,b,d)}}},p=o.match.POS,q=function(a,b){return"\\"+(b-0+1)};for(var r in o.match)o.match[r]=new RegExp(o.match[r].source+/(?![^\[]*\])(?![^\(]*\))/.source),o.leftMatch[r]=new RegExp(/(^(?:.|\r|\n)*?)/.source+o.match[r].source.replace(/\\(\d+)/g,q));o.match.globalPOS=p;var s=function(a,b){a=Array.prototype.slice.call(a,0);if(b){b.push.apply(b,a);return b}return a};try{Array.prototype.slice.call(c.documentElement.childNodes,0)[0].nodeType}catch(t){s=function(a,b){var c=0,d=b||[];if(g.call(a)==="[object Array]")Array.prototype.push.apply(d,a);else if(typeof a.length=="number")for(var e=a.length;c<e;c++)d.push(a[c]);else for(;a[c];c++)d.push(a[c]);return d}}var u,v;c.documentElement.compareDocumentPosition?u=function(a,b){if(a===b){h=!0;return 0}if(!a.compareDocumentPosition||!b.compareDocumentPosition)return a.compareDocumentPosition?-1:1;return a.compareDocumentPosition(b)&4?-1:1}:(u=function(a,b){if(a===b){h=!0;return 0}if(a.sourceIndex&&b.sourceIndex)return a.sourceIndex-b.sourceIndex;var c,d,e=[],f=[],g=a.parentNode,i=b.parentNode,j=g;if(g===i)return v(a,b);if(!g)return-1;if(!i)return 1;while(j)e.unshift(j),j=j.parentNode;j=i;while(j)f.unshift(j),j=j.parentNode;c=e.length,d=f.length;for(var k=0;k<c&&k<d;k++)if(e[k]!==f[k])return v(e[k],f[k]);return k===c?v(a,f[k],-1):v(e[k],b,1)},v=function(a,b,c){if(a===b)return c;var d=a.nextSibling;while(d){if(d===b)return-1;d=d.nextSibling}return 1}),function(){var a=c.createElement("div"),d="script"+(new Date).getTime(),e=c.documentElement;a.innerHTML="<a name='"+d+"'/>",e.insertBefore(a,e.firstChild),c.getElementById(d)&&(o.find.ID=function(a,c,d){if(typeof c.getElementById!="undefined"&&!d){var e=c.getElementById(a[1]);return e?e.id===a[1]||typeof e.getAttributeNode!="undefined"&&e.getAttributeNode("id").nodeValue===a[1]?[e]:b:[]}},o.filter.ID=function(a,b){var c=typeof a.getAttributeNode!="undefined"&&a.getAttributeNode("id");return a.nodeType===1&&c&&c.nodeValue===b}),e.removeChild(a),e=a=null}(),function(){var a=c.createElement("div");a.appendChild(c.createComment("")),a.getElementsByTagName("*").length>0&&(o.find.TAG=function(a,b){var c=b.getElementsByTagName(a[1]);if(a[1]==="*"){var d=[];for(var e=0;c[e];e++)c[e].nodeType===1&&d.push(c[e]);c=d}return c}),a.innerHTML="<a href='#'></a>",a.firstChild&&typeof a.firstChild.getAttribute!="undefined"&&a.firstChild.getAttribute("href")!=="#"&&(o.attrHandle.href=function(a){return a.getAttribute("href",2)}),a=null}(),c.querySelectorAll&&function(){var a=m,b=c.createElement("div"),d="__sizzle__";b.innerHTML="<p class='TEST'></p>";if(!b.querySelectorAll||b.querySelectorAll(".TEST").length!==0){m=function(b,e,f,g){e=e||c;if(!g&&!m.isXML(e)){var h=/^(\w+$)|^\.([\w\-]+$)|^#([\w\-]+$)/.exec(b);if(h&&(e.nodeType===1||e.nodeType===9)){if(h[1])return s(e.getElementsByTagName(b),f);if(h[2]&&o.find.CLASS&&e.getElementsByClassName)return s(e.getElementsByClassName(h[2]),f)}if(e.nodeType===9){if(b==="body"&&e.body)return s([e.body],f);if(h&&h[3]){var i=e.getElementById(h[3]);if(!i||!i.parentNode)return s([],f);if(i.id===h[3])return s([i],f)}try{return s(e.querySelectorAll(b),f)}catch(j){}}else if(e.nodeType===1&&e.nodeName.toLowerCase()!=="object"){var k=e,l=e.getAttribute("id"),n=l||d,p=e.parentNode,q=/^\s*[+~]/.test(b);l?n=n.replace(/'/g,"\\$&"):e.setAttribute("id",n),q&&p&&(e=e.parentNode);try{if(!q||p)return s(e.querySelectorAll("[id='"+n+"'] "+b),f)}catch(r){}finally{l||k.removeAttribute("id")}}}return a(b,e,f,g)};for(var e in a)m[e]=a[e];b=null}}(),function(){var a=c.documentElement,b=a.matchesSelector||a.mozMatchesSelector||a.webkitMatchesSelector||a.msMatchesSelector;if(b){var d=!b.call(c.createElement("div"),"div"),e=!1;try{b.call(c.documentElement,"[test!='']:sizzle")}catch(f){e=!0}m.matchesSelector=function(a,c){c=c.replace(/\=\s*([^'"\]]*)\s*\]/g,"='$1']");if(!m.isXML(a))try{if(e||!o.match.PSEUDO.test(c)&&!/!=/.test(c)){var f=b.call(a,c);if(f||!d||a.document&&a.document.nodeType!==11)return f}}catch(g){}return m(c,null,null,[a]).length>0}}}(),function(){var a=c.createElement("div");a.innerHTML="<div class='test e'></div><div class='test'></div>";if(!!a.getElementsByClassName&&a.getElementsByClassName("e").length!==0){a.lastChild.className="e";if(a.getElementsByClassName("e").length===1)return;o.order.splice(1,0,"CLASS"),o.find.CLASS=function(a,b,c){if(typeof b.getElementsByClassName!="undefined"&&!c)return b.getElementsByClassName(a[1])},a=null}}(),c.documentElement.contains?m.contains=function(a,b){return a!==b&&(a.contains?a.contains(b):!0)}:c.documentElement.compareDocumentPosition?m.contains=function(a,b){return!!(a.compareDocumentPosition(b)&16)}:m.contains=function(){return!1},m.isXML=function(a){var b=(a?a.ownerDocument||a:0).documentElement;return b?b.nodeName!=="HTML":!1};var y=function(a,b,c){var d,e=[],f="",g=b.nodeType?[b]:b;while(d=o.match.PSEUDO.exec(a))f+=d[0],a=a.replace(o.match.PSEUDO,"");a=o.relative[a]?a+"*":a;for(var h=0,i=g.length;h<i;h++)m(a,g[h],e,c);return m.filter(f,e)};m.attr=f.attr,m.selectors.attrMap={},f.find=m,f.expr=m.selectors,f.expr[":"]=f.expr.filters,f.unique=m.uniqueSort,f.text=m.getText,f.isXMLDoc=m.isXML,f.contains=m.contains}();var L=/Until$/,M=/^(?:parents|prevUntil|prevAll)/,N=/,/,O=/^.[^:#\[\.,]*$/,P=Array.prototype.slice,Q=f.expr.match.globalPOS,R={children:!0,contents:!0,next:!0,prev:!0};f.fn.extend({find:function(a){var b=this,c,d;if(typeof a!="string")return f(a).filter(function(){for(c=0,d=b.length;c<d;c++)if(f.contains(b[c],this))return!0});var e=this.pushStack("","find",a),g,h,i;for(c=0,d=this.length;c<d;c++){g=e.length,f.find(a,this[c],e);if(c>0)for(h=g;h<e.length;h++)for(i=0;i<g;i++)if(e[i]===e[h]){e.splice(h--,1);break}}return e},has:function(a){var b=f(a);return this.filter(function(){for(var a=0,c=b.length;a<c;a++)if(f.contains(this,b[a]))return!0})},not:function(a){return this.pushStack(T(this,a,!1),"not",a)},filter:function(a){return this.pushStack(T(this,a,!0),"filter",a)},is:function(a){return!!a&&(typeof a=="string"?Q.test(a)?f(a,this.context).index(this[0])>=0:f.filter(a,this).length>0:this.filter(a).length>0)},closest:function(a,b){var c=[],d,e,g=this[0];if(f.isArray(a)){var h=1;while(g&&g.ownerDocument&&g!==b){for(d=0;d<a.length;d++)f(g).is(a[d])&&c.push({selector:a[d],elem:g,level:h});g=g.parentNode,h++}return c}var i=Q.test(a)||typeof a!="string"?f(a,b||this.context):0;for(d=0,e=this.length;d<e;d++){g=this[d];while(g){if(i?i.index(g)>-1:f.find.matchesSelector(g,a)){c.push(g);break}g=g.parentNode;if(!g||!g.ownerDocument||g===b||g.nodeType===11)break}}c=c.length>1?f.unique(c):c;return this.pushStack(c,"closest",a)},index:function(a){if(!a)return this[0]&&this[0].parentNode?this.prevAll().length:-1;if(typeof a=="string")return f.inArray(this[0],f(a));return f.inArray(a.jquery?a[0]:a,this)},add:function(a,b){var c=typeof a=="string"?f(a,b):f.makeArray(a&&a.nodeType?[a]:a),d=f.merge(this.get(),c);return this.pushStack(S(c[0])||S(d[0])?d:f.unique(d))},andSelf:function(){return this.add(this.prevObject)}}),f.each({parent:function(a){var b=a.parentNode;return b&&b.nodeType!==11?b:null},parents:function(a){return f.dir(a,"parentNode")},parentsUntil:function(a,b,c){return f.dir(a,"parentNode",c)},next:function(a){return f.nth(a,2,"nextSibling")},prev:function(a){return f.nth(a,2,"previousSibling")},nextAll:function(a){return f.dir(a,"nextSibling")},prevAll:function(a){return f.dir(a,"previousSibling")},nextUntil:function(a,b,c){return f.dir(a,"nextSibling",c)},prevUntil:function(a,b,c){return f.dir(a,"previousSibling",c)},siblings:function(a){return f.sibling((a.parentNode||{}).firstChild,a)},children:function(a){return f.sibling(a.firstChild)},contents:function(a){return f.nodeName(a,"iframe")?a.contentDocument||a.contentWindow.document:f.makeArray(a.childNodes)}},function(a,b){f.fn[a]=function(c,d){var e=f.map(this,b,c);L.test(a)||(d=c),d&&typeof d=="string"&&(e=f.filter(d,e)),e=this.length>1&&!R[a]?f.unique(e):e,(this.length>1||N.test(d))&&M.test(a)&&(e=e.reverse());return this.pushStack(e,a,P.call(arguments).join(","))}}),f.extend({filter:function(a,b,c){c&&(a=":not("+a+")");return b.length===1?f.find.matchesSelector(b[0],a)?[b[0]]:[]:f.find.matches(a,b)},dir:function(a,c,d){var e=[],g=a[c];while(g&&g.nodeType!==9&&(d===b||g.nodeType!==1||!f(g).is(d)))g.nodeType===1&&e.push(g),g=g[c];return e},nth:function(a,b,c,d){b=b||1;var e=0;for(;a;a=a[c])if(a.nodeType===1&&++e===b)break;return a},sibling:function(a,b){var c=[];for(;a;a=a.nextSibling)a.nodeType===1&&a!==b&&c.push(a);return c}});var V="abbr|article|aside|audio|bdi|canvas|data|datalist|details|figcaption|figure|footer|header|hgroup|mark|meter|nav|output|progress|section|summary|time|video",W=/ jQuery\d+="(?:\d+|null)"/g,X=/^\s+/,Y=/<(?!area|br|col|embed|hr|img|input|link|meta|param)(([\w:]+)[^>]*)\/>/ig,Z=/<([\w:]+)/,$=/<tbody/i,_=/<|&#?\w+;/,ba=/<(?:script|style)/i,bb=/<(?:script|object|embed|option|style)/i,bc=new RegExp("<(?:"+V+")[\\s/>]","i"),bd=/checked\s*(?:[^=]|=\s*.checked.)/i,be=/\/(java|ecma)script/i,bf=/^\s*<!(?:\[CDATA\[|\-\-)/,bg={option:[1,"<select multiple='multiple'>","</select>"],legend:[1,"<fieldset>","</fieldset>"],thead:[1,"<table>","</table>"],tr:[2,"<table><tbody>","</tbody></table>"],td:[3,"<table><tbody><tr>","</tr></tbody></table>"],col:[2,"<table><tbody></tbody><colgroup>","</colgroup></table>"],area:[1,"<map>","</map>"],_default:[0,"",""]},bh=U(c);bg.optgroup=bg.option,bg.tbody=bg.tfoot=bg.colgroup=bg.caption=bg.thead,bg.th=bg.td,f.support.htmlSerialize||(bg._default=[1,"div<div>","</div>"]),f.fn.extend({text:function(a){return f.access(this,function(a){return a===b?f.text(this):this.empty().append((this[0]&&this[0].ownerDocument||c).createTextNode(a))},null,a,arguments.length)},wrapAll:function(a){if(f.isFunction(a))return this.each(function(b){f(this).wrapAll(a.call(this,b))});if(this[0]){var b=f(a,this[0].ownerDocument).eq(0).clone(!0);this[0].parentNode&&b.insertBefore(this[0]),b.map(function(){var a=this;while(a.firstChild&&a.firstChild.nodeType===1)a=a.firstChild;return a}).append(this)}return this},wrapInner:function(a){if(f.isFunction(a))return this.each(function(b){f(this).wrapInner(a.call(this,b))});return this.each(function(){var b=f(this),c=b.contents();c.length?c.wrapAll(a):b.append(a)})},wrap:function(a){var b=f.isFunction(a);return this.each(function(c){f(this).wrapAll(b?a.call(this,c):a)})},unwrap:function(){return this.parent().each(function(){f.nodeName(this,"body")||f(this).replaceWith(this.childNodes)}).end()},append:function(){return this.domManip(arguments,!0,function(a){this.nodeType===1&&this.appendChild(a)})},prepend:function(){return this.domManip(arguments,!0,function(a){this.nodeType===1&&this.insertBefore(a,this.firstChild)})},before:function(){if(this[0]&&this[0].parentNode)return this.domManip(arguments,!1,function(a){this.parentNode.insertBefore(a,this)});if(arguments.length){var a=f
.clean(arguments);a.push.apply(a,this.toArray());return this.pushStack(a,"before",arguments)}},after:function(){if(this[0]&&this[0].parentNode)return this.domManip(arguments,!1,function(a){this.parentNode.insertBefore(a,this.nextSibling)});if(arguments.length){var a=this.pushStack(this,"after",arguments);a.push.apply(a,f.clean(arguments));return a}},remove:function(a,b){for(var c=0,d;(d=this[c])!=null;c++)if(!a||f.filter(a,[d]).length)!b&&d.nodeType===1&&(f.cleanData(d.getElementsByTagName("*")),f.cleanData([d])),d.parentNode&&d.parentNode.removeChild(d);return this},empty:function(){for(var a=0,b;(b=this[a])!=null;a++){b.nodeType===1&&f.cleanData(b.getElementsByTagName("*"));while(b.firstChild)b.removeChild(b.firstChild)}return this},clone:function(a,b){a=a==null?!1:a,b=b==null?a:b;return this.map(function(){return f.clone(this,a,b)})},html:function(a){return f.access(this,function(a){var c=this[0]||{},d=0,e=this.length;if(a===b)return c.nodeType===1?c.innerHTML.replace(W,""):null;if(typeof a=="string"&&!ba.test(a)&&(f.support.leadingWhitespace||!X.test(a))&&!bg[(Z.exec(a)||["",""])[1].toLowerCase()]){a=a.replace(Y,"<$1></$2>");try{for(;d<e;d++)c=this[d]||{},c.nodeType===1&&(f.cleanData(c.getElementsByTagName("*")),c.innerHTML=a);c=0}catch(g){}}c&&this.empty().append(a)},null,a,arguments.length)},replaceWith:function(a){if(this[0]&&this[0].parentNode){if(f.isFunction(a))return this.each(function(b){var c=f(this),d=c.html();c.replaceWith(a.call(this,b,d))});typeof a!="string"&&(a=f(a).detach());return this.each(function(){var b=this.nextSibling,c=this.parentNode;f(this).remove(),b?f(b).before(a):f(c).append(a)})}return this.length?this.pushStack(f(f.isFunction(a)?a():a),"replaceWith",a):this},detach:function(a){return this.remove(a,!0)},domManip:function(a,c,d){var e,g,h,i,j=a[0],k=[];if(!f.support.checkClone&&arguments.length===3&&typeof j=="string"&&bd.test(j))return this.each(function(){f(this).domManip(a,c,d,!0)});if(f.isFunction(j))return this.each(function(e){var g=f(this);a[0]=j.call(this,e,c?g.html():b),g.domManip(a,c,d)});if(this[0]){i=j&&j.parentNode,f.support.parentNode&&i&&i.nodeType===11&&i.childNodes.length===this.length?e={fragment:i}:e=f.buildFragment(a,this,k),h=e.fragment,h.childNodes.length===1?g=h=h.firstChild:g=h.firstChild;if(g){c=c&&f.nodeName(g,"tr");for(var l=0,m=this.length,n=m-1;l<m;l++)d.call(c?bi(this[l],g):this[l],e.cacheable||m>1&&l<n?f.clone(h,!0,!0):h)}k.length&&f.each(k,function(a,b){b.src?f.ajax({type:"GET",global:!1,url:b.src,async:!1,dataType:"script"}):f.globalEval((b.text||b.textContent||b.innerHTML||"").replace(bf,"$0")),b.parentNode&&b.parentNode.removeChild(b)})}return this}}),f.buildFragment=function(a,b,d){var e,g,h,i,j=a[0];b&&b[0]&&(i=b[0].ownerDocument||b[0]),i.createDocumentFragment||(i=c),a.length===1&&typeof j=="string"&&j.length<512&&i===c&&j.charAt(0)==="<"&&!bb.test(j)&&(f.support.checkClone||!bd.test(j))&&(f.support.html5Clone||!bc.test(j))&&(g=!0,h=f.fragments[j],h&&h!==1&&(e=h)),e||(e=i.createDocumentFragment(),f.clean(a,i,e,d)),g&&(f.fragments[j]=h?e:1);return{fragment:e,cacheable:g}},f.fragments={},f.each({appendTo:"append",prependTo:"prepend",insertBefore:"before",insertAfter:"after",replaceAll:"replaceWith"},function(a,b){f.fn[a]=function(c){var d=[],e=f(c),g=this.length===1&&this[0].parentNode;if(g&&g.nodeType===11&&g.childNodes.length===1&&e.length===1){e[b](this[0]);return this}for(var h=0,i=e.length;h<i;h++){var j=(h>0?this.clone(!0):this).get();f(e[h])[b](j),d=d.concat(j)}return this.pushStack(d,a,e.selector)}}),f.extend({clone:function(a,b,c){var d,e,g,h=f.support.html5Clone||f.isXMLDoc(a)||!bc.test("<"+a.nodeName+">")?a.cloneNode(!0):bo(a);if((!f.support.noCloneEvent||!f.support.noCloneChecked)&&(a.nodeType===1||a.nodeType===11)&&!f.isXMLDoc(a)){bk(a,h),d=bl(a),e=bl(h);for(g=0;d[g];++g)e[g]&&bk(d[g],e[g])}if(b){bj(a,h);if(c){d=bl(a),e=bl(h);for(g=0;d[g];++g)bj(d[g],e[g])}}d=e=null;return h},clean:function(a,b,d,e){var g,h,i,j=[];b=b||c,typeof b.createElement=="undefined"&&(b=b.ownerDocument||b[0]&&b[0].ownerDocument||c);for(var k=0,l;(l=a[k])!=null;k++){typeof l=="number"&&(l+="");if(!l)continue;if(typeof l=="string")if(!_.test(l))l=b.createTextNode(l);else{l=l.replace(Y,"<$1></$2>");var m=(Z.exec(l)||["",""])[1].toLowerCase(),n=bg[m]||bg._default,o=n[0],p=b.createElement("div"),q=bh.childNodes,r;b===c?bh.appendChild(p):U(b).appendChild(p),p.innerHTML=n[1]+l+n[2];while(o--)p=p.lastChild;if(!f.support.tbody){var s=$.test(l),t=m==="table"&&!s?p.firstChild&&p.firstChild.childNodes:n[1]==="<table>"&&!s?p.childNodes:[];for(i=t.length-1;i>=0;--i)f.nodeName(t[i],"tbody")&&!t[i].childNodes.length&&t[i].parentNode.removeChild(t[i])}!f.support.leadingWhitespace&&X.test(l)&&p.insertBefore(b.createTextNode(X.exec(l)[0]),p.firstChild),l=p.childNodes,p&&(p.parentNode.removeChild(p),q.length>0&&(r=q[q.length-1],r&&r.parentNode&&r.parentNode.removeChild(r)))}var u;if(!f.support.appendChecked)if(l[0]&&typeof (u=l.length)=="number")for(i=0;i<u;i++)bn(l[i]);else bn(l);l.nodeType?j.push(l):j=f.merge(j,l)}if(d){g=function(a){return!a.type||be.test(a.type)};for(k=0;j[k];k++){h=j[k];if(e&&f.nodeName(h,"script")&&(!h.type||be.test(h.type)))e.push(h.parentNode?h.parentNode.removeChild(h):h);else{if(h.nodeType===1){var v=f.grep(h.getElementsByTagName("script"),g);j.splice.apply(j,[k+1,0].concat(v))}d.appendChild(h)}}}return j},cleanData:function(a){var b,c,d=f.cache,e=f.event.special,g=f.support.deleteExpando;for(var h=0,i;(i=a[h])!=null;h++){if(i.nodeName&&f.noData[i.nodeName.toLowerCase()])continue;c=i[f.expando];if(c){b=d[c];if(b&&b.events){for(var j in b.events)e[j]?f.event.remove(i,j):f.removeEvent(i,j,b.handle);b.handle&&(b.handle.elem=null)}g?delete i[f.expando]:i.removeAttribute&&i.removeAttribute(f.expando),delete d[c]}}}});var bp=/alpha\([^)]*\)/i,bq=/opacity=([^)]*)/,br=/([A-Z]|^ms)/g,bs=/^[\-+]?(?:\d*\.)?\d+$/i,bt=/^-?(?:\d*\.)?\d+(?!px)[^\d\s]+$/i,bu=/^([\-+])=([\-+.\de]+)/,bv=/^margin/,bw={position:"absolute",visibility:"hidden",display:"block"},bx=["Top","Right","Bottom","Left"],by,bz,bA;f.fn.css=function(a,c){return f.access(this,function(a,c,d){return d!==b?f.style(a,c,d):f.css(a,c)},a,c,arguments.length>1)},f.extend({cssHooks:{opacity:{get:function(a,b){if(b){var c=by(a,"opacity");return c===""?"1":c}return a.style.opacity}}},cssNumber:{fillOpacity:!0,fontWeight:!0,lineHeight:!0,opacity:!0,orphans:!0,widows:!0,zIndex:!0,zoom:!0},cssProps:{"float":f.support.cssFloat?"cssFloat":"styleFloat"},style:function(a,c,d,e){if(!!a&&a.nodeType!==3&&a.nodeType!==8&&!!a.style){var g,h,i=f.camelCase(c),j=a.style,k=f.cssHooks[i];c=f.cssProps[i]||i;if(d===b){if(k&&"get"in k&&(g=k.get(a,!1,e))!==b)return g;return j[c]}h=typeof d,h==="string"&&(g=bu.exec(d))&&(d=+(g[1]+1)*+g[2]+parseFloat(f.css(a,c)),h="number");if(d==null||h==="number"&&isNaN(d))return;h==="number"&&!f.cssNumber[i]&&(d+="px");if(!k||!("set"in k)||(d=k.set(a,d))!==b)try{j[c]=d}catch(l){}}},css:function(a,c,d){var e,g;c=f.camelCase(c),g=f.cssHooks[c],c=f.cssProps[c]||c,c==="cssFloat"&&(c="float");if(g&&"get"in g&&(e=g.get(a,!0,d))!==b)return e;if(by)return by(a,c)},swap:function(a,b,c){var d={},e,f;for(f in b)d[f]=a.style[f],a.style[f]=b[f];e=c.call(a);for(f in b)a.style[f]=d[f];return e}}),f.curCSS=f.css,c.defaultView&&c.defaultView.getComputedStyle&&(bz=function(a,b){var c,d,e,g,h=a.style;b=b.replace(br,"-$1").toLowerCase(),(d=a.ownerDocument.defaultView)&&(e=d.getComputedStyle(a,null))&&(c=e.getPropertyValue(b),c===""&&!f.contains(a.ownerDocument.documentElement,a)&&(c=f.style(a,b))),!f.support.pixelMargin&&e&&bv.test(b)&&bt.test(c)&&(g=h.width,h.width=c,c=e.width,h.width=g);return c}),c.documentElement.currentStyle&&(bA=function(a,b){var c,d,e,f=a.currentStyle&&a.currentStyle[b],g=a.style;f==null&&g&&(e=g[b])&&(f=e),bt.test(f)&&(c=g.left,d=a.runtimeStyle&&a.runtimeStyle.left,d&&(a.runtimeStyle.left=a.currentStyle.left),g.left=b==="fontSize"?"1em":f,f=g.pixelLeft+"px",g.left=c,d&&(a.runtimeStyle.left=d));return f===""?"auto":f}),by=bz||bA,f.each(["height","width"],function(a,b){f.cssHooks[b]={get:function(a,c,d){if(c)return a.offsetWidth!==0?bB(a,b,d):f.swap(a,bw,function(){return bB(a,b,d)})},set:function(a,b){return bs.test(b)?b+"px":b}}}),f.support.opacity||(f.cssHooks.opacity={get:function(a,b){return bq.test((b&&a.currentStyle?a.currentStyle.filter:a.style.filter)||"")?parseFloat(RegExp.$1)/100+"":b?"1":""},set:function(a,b){var c=a.style,d=a.currentStyle,e=f.isNumeric(b)?"alpha(opacity="+b*100+")":"",g=d&&d.filter||c.filter||"";c.zoom=1;if(b>=1&&f.trim(g.replace(bp,""))===""){c.removeAttribute("filter");if(d&&!d.filter)return}c.filter=bp.test(g)?g.replace(bp,e):g+" "+e}}),f(function(){f.support.reliableMarginRight||(f.cssHooks.marginRight={get:function(a,b){return f.swap(a,{display:"inline-block"},function(){return b?by(a,"margin-right"):a.style.marginRight})}})}),f.expr&&f.expr.filters&&(f.expr.filters.hidden=function(a){var b=a.offsetWidth,c=a.offsetHeight;return b===0&&c===0||!f.support.reliableHiddenOffsets&&(a.style&&a.style.display||f.css(a,"display"))==="none"},f.expr.filters.visible=function(a){return!f.expr.filters.hidden(a)}),f.each({margin:"",padding:"",border:"Width"},function(a,b){f.cssHooks[a+b]={expand:function(c){var d,e=typeof c=="string"?c.split(" "):[c],f={};for(d=0;d<4;d++)f[a+bx[d]+b]=e[d]||e[d-2]||e[0];return f}}});var bC=/%20/g,bD=/\[\]$/,bE=/\r?\n/g,bF=/#.*$/,bG=/^(.*?):[ \t]*([^\r\n]*)\r?$/mg,bH=/^(?:color|date|datetime|datetime-local|email|hidden|month|number|password|range|search|tel|text|time|url|week)$/i,bI=/^(?:about|app|app\-storage|.+\-extension|file|res|widget):$/,bJ=/^(?:GET|HEAD)$/,bK=/^\/\//,bL=/\?/,bM=/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,bN=/^(?:select|textarea)/i,bO=/\s+/,bP=/([?&])_=[^&]*/,bQ=/^([\w\+\.\-]+:)(?:\/\/([^\/?#:]*)(?::(\d+))?)?/,bR=f.fn.load,bS={},bT={},bU,bV,bW=["*/"]+["*"];try{bU=e.href}catch(bX){bU=c.createElement("a"),bU.href="",bU=bU.href}bV=bQ.exec(bU.toLowerCase())||[],f.fn.extend({load:function(a,c,d){if(typeof a!="string"&&bR)return bR.apply(this,arguments);if(!this.length)return this;var e=a.indexOf(" ");if(e>=0){var g=a.slice(e,a.length);a=a.slice(0,e)}var h="GET";c&&(f.isFunction(c)?(d=c,c=b):typeof c=="object"&&(c=f.param(c,f.ajaxSettings.traditional),h="POST"));var i=this;f.ajax({url:a,type:h,dataType:"html",data:c,complete:function(a,b,c){c=a.responseText,a.isResolved()&&(a.done(function(a){c=a}),i.html(g?f("<div>").append(c.replace(bM,"")).find(g):c)),d&&i.each(d,[c,b,a])}});return this},serialize:function(){return f.param(this.serializeArray())},serializeArray:function(){return this.map(function(){return this.elements?f.makeArray(this.elements):this}).filter(function(){return this.name&&!this.disabled&&(this.checked||bN.test(this.nodeName)||bH.test(this.type))}).map(function(a,b){var c=f(this).val();return c==null?null:f.isArray(c)?f.map(c,function(a,c){return{name:b.name,value:a.replace(bE,"\r\n")}}):{name:b.name,value:c.replace(bE,"\r\n")}}).get()}}),f.each("ajaxStart ajaxStop ajaxComplete ajaxError ajaxSuccess ajaxSend".split(" "),function(a,b){f.fn[b]=function(a){return this.on(b,a)}}),f.each(["get","post"],function(a,c){f[c]=function(a,d,e,g){f.isFunction(d)&&(g=g||e,e=d,d=b);return f.ajax({type:c,url:a,data:d,success:e,dataType:g})}}),f.extend({getScript:function(a,c){return f.get(a,b,c,"script")},getJSON:function(a,b,c){return f.get(a,b,c,"json")},ajaxSetup:function(a,b){b?b$(a,f.ajaxSettings):(b=a,a=f.ajaxSettings),b$(a,b);return a},ajaxSettings:{url:bU,isLocal:bI.test(bV[1]),global:!0,type:"GET",contentType:"application/x-www-form-urlencoded; charset=UTF-8",processData:!0,async:!0,accepts:{xml:"application/xml, text/xml",html:"text/html",text:"text/plain",json:"application/json, text/javascript","*":bW},contents:{xml:/xml/,html:/html/,json:/json/},responseFields:{xml:"responseXML",text:"responseText"},converters:{"* text":a.String,"text html":!0,"text json":f.parseJSON,"text xml":f.parseXML},flatOptions:{context:!0,url:!0}},ajaxPrefilter:bY(bS),ajaxTransport:bY(bT),ajax:function(a,c){function w(a,c,l,m){if(s!==2){s=2,q&&clearTimeout(q),p=b,n=m||"",v.readyState=a>0?4:0;var o,r,u,w=c,x=l?ca(d,v,l):b,y,z;if(a>=200&&a<300||a===304){if(d.ifModified){if(y=v.getResponseHeader("Last-Modified"))f.lastModified[k]=y;if(z=v.getResponseHeader("Etag"))f.etag[k]=z}if(a===304)w="notmodified",o=!0;else try{r=cb(d,x),w="success",o=!0}catch(A){w="parsererror",u=A}}else{u=w;if(!w||a)w="error",a<0&&(a=0)}v.status=a,v.statusText=""+(c||w),o?h.resolveWith(e,[r,w,v]):h.rejectWith(e,[v,w,u]),v.statusCode(j),j=b,t&&g.trigger("ajax"+(o?"Success":"Error"),[v,d,o?r:u]),i.fireWith(e,[v,w]),t&&(g.trigger("ajaxComplete",[v,d]),--f.active||f.event.trigger("ajaxStop"))}}typeof a=="object"&&(c=a,a=b),c=c||{};var d=f.ajaxSetup({},c),e=d.context||d,g=e!==d&&(e.nodeType||e instanceof f)?f(e):f.event,h=f.Deferred(),i=f.Callbacks("once memory"),j=d.statusCode||{},k,l={},m={},n,o,p,q,r,s=0,t,u,v={readyState:0,setRequestHeader:function(a,b){if(!s){var c=a.toLowerCase();a=m[c]=m[c]||a,l[a]=b}return this},getAllResponseHeaders:function(){return s===2?n:null},getResponseHeader:function(a){var c;if(s===2){if(!o){o={};while(c=bG.exec(n))o[c[1].toLowerCase()]=c[2]}c=o[a.toLowerCase()]}return c===b?null:c},overrideMimeType:function(a){s||(d.mimeType=a);return this},abort:function(a){a=a||"abort",p&&p.abort(a),w(0,a);return this}};h.promise(v),v.success=v.done,v.error=v.fail,v.complete=i.add,v.statusCode=function(a){if(a){var b;if(s<2)for(b in a)j[b]=[j[b],a[b]];else b=a[v.status],v.then(b,b)}return this},d.url=((a||d.url)+"").replace(bF,"").replace(bK,bV[1]+""),d.dataTypes=f.trim(d.dataType||"*").toLowerCase().split(bO),d.crossDomain==null&&(r=bQ.exec(d.url.toLowerCase()),d.crossDomain=!(!r||r[1]==bV[1]&&r[2]==bV[2]&&(r[3]||(r[1]==="http:"?80:443))==(bV[3]||(bV[1]==="http:"?80:443)))),d.data&&d.processData&&typeof d.data!="string"&&(d.data=f.param(d.data,d.traditional)),bZ(bS,d,c,v);if(s===2)return!1;t=d.global,d.type=d.type.toUpperCase(),d.hasContent=!bJ.test(d.type),t&&f.active++===0&&f.event.trigger("ajaxStart");if(!d.hasContent){d.data&&(d.url+=(bL.test(d.url)?"&":"?")+d.data,delete d.data),k=d.url;if(d.cache===!1){var x=f.now(),y=d.url.replace(bP,"$1_="+x);d.url=y+(y===d.url?(bL.test(d.url)?"&":"?")+"_="+x:"")}}(d.data&&d.hasContent&&d.contentType!==!1||c.contentType)&&v.setRequestHeader("Content-Type",d.contentType),d.ifModified&&(k=k||d.url,f.lastModified[k]&&v.setRequestHeader("If-Modified-Since",f.lastModified[k]),f.etag[k]&&v.setRequestHeader("If-None-Match",f.etag[k])),v.setRequestHeader("Accept",d.dataTypes[0]&&d.accepts[d.dataTypes[0]]?d.accepts[d.dataTypes[0]]+(d.dataTypes[0]!=="*"?", "+bW+"; q=0.01":""):d.accepts["*"]);for(u in d.headers)v.setRequestHeader(u,d.headers[u]);if(d.beforeSend&&(d.beforeSend.call(e,v,d)===!1||s===2)){v.abort();return!1}for(u in{success:1,error:1,complete:1})v[u](d[u]);p=bZ(bT,d,c,v);if(!p)w(-1,"No Transport");else{v.readyState=1,t&&g.trigger("ajaxSend",[v,d]),d.async&&d.timeout>0&&(q=setTimeout(function(){v.abort("timeout")},d.timeout));try{s=1,p.send(l,w)}catch(z){if(s<2)w(-1,z);else throw z}}return v},param:function(a,c){var d=[],e=function(a,b){b=f.isFunction(b)?b():b,d[d.length]=encodeURIComponent(a)+"="+encodeURIComponent(b)};c===b&&(c=f.ajaxSettings.traditional);if(f.isArray(a)||a.jquery&&!f.isPlainObject(a))f.each(a,function(){e(this.name,this.value)});else for(var g in a)b_(g,a[g],c,e);return d.join("&").replace(bC,"+")}}),f.extend({active:0,lastModified:{},etag:{}});var cc=f.now(),cd=/(\=)\?(&|$)|\?\?/i;f.ajaxSetup({jsonp:"callback",jsonpCallback:function(){return f.expando+"_"+cc++}}),f.ajaxPrefilter("json jsonp",function(b,c,d){var e=typeof b.data=="string"&&/^application\/x\-www\-form\-urlencoded/.test(b.contentType);if(b.dataTypes[0]==="jsonp"||b.jsonp!==!1&&(cd.test(b.url)||e&&cd.test(b.data))){var g,h=b.jsonpCallback=f.isFunction(b.jsonpCallback)?b.jsonpCallback():b.jsonpCallback,i=a[h],j=b.url,k=b.data,l="$1"+h+"$2";b.jsonp!==!1&&(j=j.replace(cd,l),b.url===j&&(e&&(k=k.replace(cd,l)),b.data===k&&(j+=(/\?/.test(j)?"&":"?")+b.jsonp+"="+h))),b.url=j,b.data=k,a[h]=function(a){g=[a]},d.always(function(){a[h]=i,g&&f.isFunction(i)&&a[h](g[0])}),b.converters["script json"]=function(){g||f.error(h+" was not called");return g[0]},b.dataTypes[0]="json";return"script"}}),f.ajaxSetup({accepts:{script:"text/javascript, application/javascript, application/ecmascript, application/x-ecmascript"},contents:{script:/javascript|ecmascript/},converters:{"text script":function(a){f.globalEval(a);return a}}}),f.ajaxPrefilter("script",function(a){a.cache===b&&(a.cache=!1),a.crossDomain&&(a.type="GET",a.global=!1)}),f.ajaxTransport("script",function(a){if(a.crossDomain){var d,e=c.head||c.getElementsByTagName("head")[0]||c.documentElement;return{send:function(f,g){d=c.createElement("script"),d.async="async",a.scriptCharset&&(d.charset=a.scriptCharset),d.src=a.url,d.onload=d.onreadystatechange=function(a,c){if(c||!d.readyState||/loaded|complete/.test(d.readyState))d.onload=d.onreadystatechange=null,e&&d.parentNode&&e.removeChild(d),d=b,c||g(200,"success")},e.insertBefore(d,e.firstChild)},abort:function(){d&&d.onload(0,1)}}}});var ce=a.ActiveXObject?function(){for(var a in cg)cg[a](0,1)}:!1,cf=0,cg;f.ajaxSettings.xhr=a.ActiveXObject?function(){return!this.isLocal&&ch()||ci()}:ch,function(a){f.extend(f.support,{ajax:!!a,cors:!!a&&"withCredentials"in a})}(f.ajaxSettings.xhr()),f.support.ajax&&f.ajaxTransport(function(c){if(!c.crossDomain||f.support.cors){var d;return{send:function(e,g){var h=c.xhr(),i,j;c.username?h.open(c.type,c.url,c.async,c.username,c.password):h.open(c.type,c.url,c.async);if(c.xhrFields)for(j in c.xhrFields)h[j]=c.xhrFields[j];c.mimeType&&h.overrideMimeType&&h.overrideMimeType(c.mimeType),!c.crossDomain&&!e["X-Requested-With"]&&(e["X-Requested-With"]="XMLHttpRequest");try{for(j in e)h.setRequestHeader(j,e[j])}catch(k){}h.send(c.hasContent&&c.data||null),d=function(a,e){var j,k,l,m,n;try{if(d&&(e||h.readyState===4)){d=b,i&&(h.onreadystatechange=f.noop,ce&&delete cg[i]);if(e)h.readyState!==4&&h.abort();else{j=h.status,l=h.getAllResponseHeaders(),m={},n=h.responseXML,n&&n.documentElement&&(m.xml=n);try{m.text=h.responseText}catch(a){}try{k=h.statusText}catch(o){k=""}!j&&c.isLocal&&!c.crossDomain?j=m.text?200:404:j===1223&&(j=204)}}}catch(p){e||g(-1,p)}m&&g(j,k,m,l)},!c.async||h.readyState===4?d():(i=++cf,ce&&(cg||(cg={},f(a).unload(ce)),cg[i]=d),h.onreadystatechange=d)},abort:function(){d&&d(0,1)}}}});var cj={},ck,cl,cm=/^(?:toggle|show|hide)$/,cn=/^([+\-]=)?([\d+.\-]+)([a-z%]*)$/i,co,cp=[["height","marginTop","marginBottom","paddingTop","paddingBottom"],["width","marginLeft","marginRight","paddingLeft","paddingRight"],["opacity"]],cq;f.fn.extend({show:function(a,b,c){var d,e;if(a||a===0)return this.animate(ct("show",3),a,b,c);for(var g=0,h=this.length;g<h;g++)d=this[g],d.style&&(e=d.style.display,!f._data(d,"olddisplay")&&e==="none"&&(e=d.style.display=""),(e===""&&f.css(d,"display")==="none"||!f.contains(d.ownerDocument.documentElement,d))&&f._data(d,"olddisplay",cu(d.nodeName)));for(g=0;g<h;g++){d=this[g];if(d.style){e=d.style.display;if(e===""||e==="none")d.style.display=f._data(d,"olddisplay")||""}}return this},hide:function(a,b,c){if(a||a===0)return this.animate(ct("hide",3),a,b,c);var d,e,g=0,h=this.length;for(;g<h;g++)d=this[g],d.style&&(e=f.css(d,"display"),e!=="none"&&!f._data(d,"olddisplay")&&f._data(d,"olddisplay",e));for(g=0;g<h;g++)this[g].style&&(this[g].style.display="none");return this},_toggle:f.fn.toggle,toggle:function(a,b,c){var d=typeof a=="boolean";f.isFunction(a)&&f.isFunction(b)?this._toggle.apply(this,arguments):a==null||d?this.each(function(){var b=d?a:f(this).is(":hidden");f(this)[b?"show":"hide"]()}):this.animate(ct("toggle",3),a,b,c);return this},fadeTo:function(a,b,c,d){return this.filter(":hidden").css("opacity",0).show().end().animate({opacity:b},a,c,d)},animate:function(a,b,c,d){function g(){e.queue===!1&&f._mark(this);var b=f.extend({},e),c=this.nodeType===1,d=c&&f(this).is(":hidden"),g,h,i,j,k,l,m,n,o,p,q;b.animatedProperties={};for(i in a){g=f.camelCase(i),i!==g&&(a[g]=a[i],delete a[i]);if((k=f.cssHooks[g])&&"expand"in k){l=k.expand(a[g]),delete a[g];for(i in l)i in a||(a[i]=l[i])}}for(g in a){h=a[g],f.isArray(h)?(b.animatedProperties[g]=h[1],h=a[g]=h[0]):b.animatedProperties[g]=b.specialEasing&&b.specialEasing[g]||b.easing||"swing";if(h==="hide"&&d||h==="show"&&!d)return b.complete.call(this);c&&(g==="height"||g==="width")&&(b.overflow=[this.style.overflow,this.style.overflowX,this.style.overflowY],f.css(this,"display")==="inline"&&f.css(this,"float")==="none"&&(!f.support.inlineBlockNeedsLayout||cu(this.nodeName)==="inline"?this.style.display="inline-block":this.style.zoom=1))}b.overflow!=null&&(this.style.overflow="hidden");for(i in a)j=new f.fx(this,b,i),h=a[i],cm.test(h)?(q=f._data(this,"toggle"+i)||(h==="toggle"?d?"show":"hide":0),q?(f._data(this,"toggle"+i,q==="show"?"hide":"show"),j[q]()):j[h]()):(m=cn.exec(h),n=j.cur(),m?(o=parseFloat(m[2]),p=m[3]||(f.cssNumber[i]?"":"px"),p!=="px"&&(f.style(this,i,(o||1)+p),n=(o||1)/j.cur()*n,f.style(this,i,n+p)),m[1]&&(o=(m[1]==="-="?-1:1)*o+n),j.custom(n,o,p)):j.custom(n,h,""));return!0}var e=f.speed(b,c,d);if(f.isEmptyObject(a))return this.each(e.complete,[!1]);a=f.extend({},a);return e.queue===!1?this.each(g):this.queue(e.queue,g)},stop:function(a,c,d){typeof a!="string"&&(d=c,c=a,a=b),c&&a!==!1&&this.queue(a||"fx",[]);return this.each(function(){function h(a,b,c){var e=b[c];f.removeData(a,c,!0),e.stop(d)}var b,c=!1,e=f.timers,g=f._data(this);d||f._unmark(!0,this);if(a==null)for(b in g)g[b]&&g[b].stop&&b.indexOf(".run")===b.length-4&&h(this,g,b);else g[b=a+".run"]&&g[b].stop&&h(this,g,b);for(b=e.length;b--;)e[b].elem===this&&(a==null||e[b].queue===a)&&(d?e[b](!0):e[b].saveState(),c=!0,e.splice(b,1));(!d||!c)&&f.dequeue(this,a)})}}),f.each({slideDown:ct("show",1),slideUp:ct("hide",1),slideToggle:ct("toggle",1),fadeIn:{opacity:"show"},fadeOut:{opacity:"hide"},fadeToggle:{opacity:"toggle"}},function(a,b){f.fn[a]=function(a,c,d){return this.animate(b,a,c,d)}}),f.extend({speed:function(a,b,c){var d=a&&typeof a=="object"?f.extend({},a):{complete:c||!c&&b||f.isFunction(a)&&a,duration:a,easing:c&&b||b&&!f.isFunction(b)&&b};d.duration=f.fx.off?0:typeof d.duration=="number"?d.duration:d.duration in f.fx.speeds?f.fx.speeds[d.duration]:f.fx.speeds._default;if(d.queue==null||d.queue===!0)d.queue="fx";d.old=d.complete,d.complete=function(a){f.isFunction(d.old)&&d.old.call(this),d.queue?f.dequeue(this,d.queue):a!==!1&&f._unmark(this)};return d},easing:{linear:function(a){return a},swing:function(a){return-Math.cos(a*Math.PI)/2+.5}},timers:[],fx:function(a,b,c){this.options=b,this.elem=a,this.prop=c,b.orig=b.orig||{}}}),f.fx.prototype={update:function(){this.options.step&&this.options.step.call(this.elem,this.now,this),(f.fx.step[this.prop]||f.fx.step._default)(this)},cur:function(){if(this.elem[this.prop]!=null&&(!this.elem.style||this.elem.style[this.prop]==null))return this.elem[this.prop];var a,b=f.css(this.elem,this.prop);return isNaN(a=parseFloat(b))?!b||b==="auto"?0:b:a},custom:function(a,c,d){function h(a){return e.step(a)}var e=this,g=f.fx;this.startTime=cq||cr(),this.end=c,this.now=this.start=a,this.pos=this.state=0,this.unit=d||this.unit||(f.cssNumber[this.prop]?"":"px"),h.queue=this.options.queue,h.elem=this.elem,h.saveState=function(){f._data(e.elem,"fxshow"+e.prop)===b&&(e.options.hide?f._data(e.elem,"fxshow"+e.prop,e.start):e.options.show&&f._data(e.elem,"fxshow"+e.prop,e.end))},h()&&f.timers.push(h)&&!co&&(co=setInterval(g.tick,g.interval))},show:function(){var a=f._data(this.elem,"fxshow"+this.prop);this.options.orig[this.prop]=a||f.style(this.elem,this.prop),this.options.show=!0,a!==b?this.custom(this.cur(),a):this.custom(this.prop==="width"||this.prop==="height"?1:0,this.cur()),f(this.elem).show()},hide:function(){this.options.orig[this.prop]=f._data(this.elem,"fxshow"+this.prop)||f.style(this.elem,this.prop),this.options.hide=!0,this.custom(this.cur(),0)},step:function(a){var b,c,d,e=cq||cr(),g=!0,h=this.elem,i=this.options;if(a||e>=i.duration+this.startTime){this.now=this.end,this.pos=this.state=1,this.update(),i.animatedProperties[this.prop]=!0;for(b in i.animatedProperties)i.animatedProperties[b]!==!0&&(g=!1);if(g){i.overflow!=null&&!f.support.shrinkWrapBlocks&&f.each(["","X","Y"],function(a,b){h.style["overflow"+b]=i.overflow[a]}),i.hide&&f(h).hide();if(i.hide||i.show)for(b in i.animatedProperties)f.style(h,b,i.orig[b]),f.removeData(h,"fxshow"+b,!0),f.removeData(h,"toggle"+b,!0);d=i.complete,d&&(i.complete=!1,d.call(h))}return!1}i.duration==Infinity?this.now=e:(c=e-this.startTime,this.state=c/i.duration,this.pos=f.easing[i.animatedProperties[this.prop]](this.state,c,0,1,i.duration),this.now=this.start+(this.end-this.start)*this.pos),this.update();return!0}},f.extend(f.fx,{tick:function(){var a,b=f.timers,c=0;for(;c<b.length;c++)a=b[c],!a()&&b[c]===a&&b.splice(c--,1);b.length||f.fx.stop()},interval:13,stop:function(){clearInterval(co),co=null},speeds:{slow:600,fast:200,_default:400},step:{opacity:function(a){f.style(a.elem,"opacity",a.now)},_default:function(a){a.elem.style&&a.elem.style[a.prop]!=null?a.elem.style[a.prop]=a.now+a.unit:a.elem[a.prop]=a.now}}}),f.each(cp.concat.apply([],cp),function(a,b){b.indexOf("margin")&&(f.fx.step[b]=function(a){f.style(a.elem,b,Math.max(0,a.now)+a.unit)})}),f.expr&&f.expr.filters&&(f.expr.filters.animated=function(a){return f.grep(f.timers,function(b){return a===b.elem}).length});var cv,cw=/^t(?:able|d|h)$/i,cx=/^(?:body|html)$/i;"getBoundingClientRect"in c.documentElement?cv=function(a,b,c,d){try{d=a.getBoundingClientRect()}catch(e){}if(!d||!f.contains(c,a))return d?{top:d.top,left:d.left}:{top:0,left:0};var g=b.body,h=cy(b),i=c.clientTop||g.clientTop||0,j=c.clientLeft||g.clientLeft||0,k=h.pageYOffset||f.support.boxModel&&c.scrollTop||g.scrollTop,l=h.pageXOffset||f.support.boxModel&&c.scrollLeft||g.scrollLeft,m=d.top+k-i,n=d.left+l-j;return{top:m,left:n}}:cv=function(a,b,c){var d,e=a.offsetParent,g=a,h=b.body,i=b.defaultView,j=i?i.getComputedStyle(a,null):a.currentStyle,k=a.offsetTop,l=a.offsetLeft;while((a=a.parentNode)&&a!==h&&a!==c){if(f.support.fixedPosition&&j.position==="fixed")break;d=i?i.getComputedStyle(a,null):a.currentStyle,k-=a.scrollTop,l-=a.scrollLeft,a===e&&(k+=a.offsetTop,l+=a.offsetLeft,f.support.doesNotAddBorder&&(!f.support.doesAddBorderForTableAndCells||!cw.test(a.nodeName))&&(k+=parseFloat(d.borderTopWidth)||0,l+=parseFloat(d.borderLeftWidth)||0),g=e,e=a.offsetParent),f.support.subtractsBorderForOverflowNotVisible&&d.overflow!=="visible"&&(k+=parseFloat(d.borderTopWidth)||0,l+=parseFloat(d.borderLeftWidth)||0),j=d}if(j.position==="relative"||j.position==="static")k+=h.offsetTop,l+=h.offsetLeft;f.support.fixedPosition&&j.position==="fixed"&&(k+=Math.max(c.scrollTop,h.scrollTop),l+=Math.max(c.scrollLeft,h.scrollLeft));return{top:k,left:l}},f.fn.offset=function(a){if(arguments.length)return a===b?this:this.each(function(b){f.offset.setOffset(this,a,b)});var c=this[0],d=c&&c.ownerDocument;if(!d)return null;if(c===d.body)return f.offset.bodyOffset(c);return cv(c,d,d.documentElement)},f.offset={bodyOffset:function(a){var b=a.offsetTop,c=a.offsetLeft;f.support.doesNotIncludeMarginInBodyOffset&&(b+=parseFloat(f.css(a,"marginTop"))||0,c+=parseFloat(f.css(a,"marginLeft"))||0);return{top:b,left:c}},setOffset:function(a,b,c){var d=f.css(a,"position");d==="static"&&(a.style.position="relative");var e=f(a),g=e.offset(),h=f.css(a,"top"),i=f.css(a,"left"),j=(d==="absolute"||d==="fixed")&&f.inArray("auto",[h,i])>-1,k={},l={},m,n;j?(l=e.position(),m=l.top,n=l.left):(m=parseFloat(h)||0,n=parseFloat(i)||0),f.isFunction(b)&&(b=b.call(a,c,g)),b.top!=null&&(k.top=b.top-g.top+m),b.left!=null&&(k.left=b.left-g.left+n),"using"in b?b.using.call(a,k):e.css(k)}},f.fn.extend({position:function(){if(!this[0])return null;var a=this[0],b=this.offsetParent(),c=this.offset(),d=cx.test(b[0].nodeName)?{top:0,left:0}:b.offset();c.top-=parseFloat(f.css(a,"marginTop"))||0,c.left-=parseFloat(f.css(a,"marginLeft"))||0,d.top+=parseFloat(f.css(b[0],"borderTopWidth"))||0,d.left+=parseFloat(f.css(b[0],"borderLeftWidth"))||0;return{top:c.top-d.top,left:c.left-d.left}},offsetParent:function(){return this.map(function(){var a=this.offsetParent||c.body;while(a&&!cx.test(a.nodeName)&&f.css(a,"position")==="static")a=a.offsetParent;return a})}}),f.each({scrollLeft:"pageXOffset",scrollTop:"pageYOffset"},function(a,c){var d=/Y/.test(c);f.fn[a]=function(e){return f.access(this,function(a,e,g){var h=cy(a);if(g===b)return h?c in h?h[c]:f.support.boxModel&&h.document.documentElement[e]||h.document.body[e]:a[e];h?h.scrollTo(d?f(h).scrollLeft():g,d?g:f(h).scrollTop()):a[e]=g},a,e,arguments.length,null)}}),f.each({Height:"height",Width:"width"},function(a,c){var d="client"+a,e="scroll"+a,g="offset"+a;f.fn["inner"+a]=function(){var a=this[0];return a?a.style?parseFloat(f.css(a,c,"padding")):this[c]():null},f.fn["outer"+a]=function(a){var b=this[0];return b?b.style?parseFloat(f.css(b,c,a?"margin":"border")):this[c]():null},f.fn[c]=function(a){return f.access(this,function(a,c,h){var i,j,k,l;if(f.isWindow(a)){i=a.document,j=i.documentElement[d];return f.support.boxModel&&j||i.body&&i.body[d]||j}if(a.nodeType===9){i=a.documentElement;if(i[d]>=i[e])return i[d];return Math.max(a.body[e],i[e],a.body[g],i[g])}if(h===b){k=f.css(a,c),l=parseFloat(k);return f.isNumeric(l)?l:k}f(a).css(c,h)},c,a,arguments.length,null)}}),a.jQuery=a.$=f,typeof define=="function"&&define.amd&&define.amd.jQuery&&define("jquery",[],function(){return f})})(window);
};

/*! Copyright (c) 2011 Brandon Aaron (http://brandonaaron.net)
* Licensed under the MIT License (LICENSE.txt).
*
* Thanks to: http://adomas.org/javascript-mouse-wheel/ for some pointers.
* Thanks to: Mathias Bank(http://www.mathias-bank.de) for a scope bug fix.
* Thanks to: Seamus Leahy for adding deltaX and deltaY
*
* Version: 3.0.6
*
* Requires: 1.2.2+
*/

(function($) {

var types = ['DOMMouseScroll', 'mousewheel'];

if ($.event.fixHooks) {
    for ( var i=types.length; i; ) {
        $.event.fixHooks[ types[--i] ] = $.event.mouseHooks;
    }
}

$.event.special.mousewheel = {
    setup: function() {
        if ( this.addEventListener ) {
            for ( var i=types.length; i; ) {
                this.addEventListener( types[--i], handler, false );
            }
        } else {
            this.onmousewheel = handler;
        }
    },

    teardown: function() {
        if ( this.removeEventListener ) {
            for ( var i=types.length; i; ) {
                this.removeEventListener( types[--i], handler, false );
            }
        } else {
            this.onmousewheel = null;
        }
    }
};

$.fn.extend({
    mousewheel: function(fn) {
        return fn ? this.bind("mousewheel", fn) : this.trigger("mousewheel");
    },

    unmousewheel: function(fn) {
        return this.unbind("mousewheel", fn);
    }
});


function handler(event) {
    var orgEvent = event || window.event, args = [].slice.call( arguments, 1 ), delta = 0, returnValue = true, deltaX = 0, deltaY = 0;
    event = $.event.fix(orgEvent);
    event.type = "mousewheel";

    // Old school scrollwheel delta
    if ( orgEvent.wheelDelta ) { delta = orgEvent.wheelDelta/120; }
    if ( orgEvent.detail ) { delta = -orgEvent.detail/3; }

    // New school multidimensional scroll (touchpads) deltas
    deltaY = delta;

    // Gecko
    if ( orgEvent.axis !== undefined && orgEvent.axis === orgEvent.HORIZONTAL_AXIS ) {
        deltaY = 0;
        deltaX = -1*delta;
    }

    // Webkit
    if ( orgEvent.wheelDeltaY !== undefined ) { deltaY = orgEvent.wheelDeltaY/120; }
    if ( orgEvent.wheelDeltaX !== undefined ) { deltaX = -1*orgEvent.wheelDeltaX/120; }

    // Add event and delta to the front of the arguments
    args.unshift(event, delta, deltaX, deltaY);

    return ($.event.dispatch || $.event.handle).apply(this, args);
}

})(jQuery);

//     Underscore.js 1.4.4
//     http://underscorejs.org
//     (c) 2009-2013 Jeremy Ashkenas, DocumentCloud Inc.
//     Underscore may be freely distributed under the MIT license.

(function() {

  // Baseline setup
  // --------------

  // Establish the root object, `window` in the browser, or `global` on the server.
  var root = this;

  // Save the previous value of the `_` variable.
  var previousUnderscore = root._;

  // Establish the object that gets returned to break out of a loop iteration.
  var breaker = {};

  // Save bytes in the minified (but not gzipped) version:
  var ArrayProto = Array.prototype, ObjProto = Object.prototype, FuncProto = Function.prototype;

  // Create quick reference variables for speed access to core prototypes.
  var push             = ArrayProto.push,
      slice            = ArrayProto.slice,
      concat           = ArrayProto.concat,
      toString         = ObjProto.toString,
      hasOwnProperty   = ObjProto.hasOwnProperty;

  // All **ECMAScript 5** native function implementations that we hope to use
  // are declared here.
  var
    nativeForEach      = ArrayProto.forEach,
    nativeMap          = ArrayProto.map,
    nativeReduce       = ArrayProto.reduce,
    nativeReduceRight  = ArrayProto.reduceRight,
    nativeFilter       = ArrayProto.filter,
    nativeEvery        = ArrayProto.every,
    nativeSome         = ArrayProto.some,
    nativeIndexOf      = ArrayProto.indexOf,
    nativeLastIndexOf  = ArrayProto.lastIndexOf,
    nativeIsArray      = Array.isArray,
    nativeKeys         = Object.keys,
    nativeBind         = FuncProto.bind;

  // Create a safe reference to the Underscore object for use below.
  var _ = function(obj) {
    if (obj instanceof _) return obj;
    if (!(this instanceof _)) return new _(obj);
    this._wrapped = obj;
  };

  // Export the Underscore object for **Node.js**, with
  // backwards-compatibility for the old `require()` API. If we're in
  // the browser, add `_` as a global object via a string identifier,
  // for Closure Compiler "advanced" mode.
  if (typeof exports !== 'undefined') {
    if (typeof module !== 'undefined' && module.exports) {
      exports = module.exports = _;
    }
    exports._ = _;
  } else {
    root._ = _;
  }

  // Current version.
  _.VERSION = '1.4.4';

  // Collection Functions
  // --------------------

  // The cornerstone, an `each` implementation, aka `forEach`.
  // Handles objects with the built-in `forEach`, arrays, and raw objects.
  // Delegates to **ECMAScript 5**'s native `forEach` if available.
  var each = _.each = _.forEach = function(obj, iterator, context) {
    if (obj == null) return;
    if (nativeForEach && obj.forEach === nativeForEach) {
      obj.forEach(iterator, context);
    } else if (obj.length === +obj.length) {
      for (var i = 0, l = obj.length; i < l; i++) {
        if (iterator.call(context, obj[i], i, obj) === breaker) return;
      }
    } else {
      for (var key in obj) {
        if (_.has(obj, key)) {
          if (iterator.call(context, obj[key], key, obj) === breaker) return;
        }
      }
    }
  };

  // Return the results of applying the iterator to each element.
  // Delegates to **ECMAScript 5**'s native `map` if available.
  _.map = _.collect = function(obj, iterator, context) {
    var results = [];
    if (obj == null) return results;
    if (nativeMap && obj.map === nativeMap) return obj.map(iterator, context);
    each(obj, function(value, index, list) {
      results[results.length] = iterator.call(context, value, index, list);
    });
    return results;
  };

  var reduceError = 'Reduce of empty array with no initial value';

  // **Reduce** builds up a single result from a list of values, aka `inject`,
  // or `foldl`. Delegates to **ECMAScript 5**'s native `reduce` if available.
  _.reduce = _.foldl = _.inject = function(obj, iterator, memo, context) {
    var initial = arguments.length > 2;
    if (obj == null) obj = [];
    if (nativeReduce && obj.reduce === nativeReduce) {
      if (context) iterator = _.bind(iterator, context);
      return initial ? obj.reduce(iterator, memo) : obj.reduce(iterator);
    }
    each(obj, function(value, index, list) {
      if (!initial) {
        memo = value;
        initial = true;
      } else {
        memo = iterator.call(context, memo, value, index, list);
      }
    });
    if (!initial) throw new TypeError(reduceError);
    return memo;
  };

  // The right-associative version of reduce, also known as `foldr`.
  // Delegates to **ECMAScript 5**'s native `reduceRight` if available.
  _.reduceRight = _.foldr = function(obj, iterator, memo, context) {
    var initial = arguments.length > 2;
    if (obj == null) obj = [];
    if (nativeReduceRight && obj.reduceRight === nativeReduceRight) {
      if (context) iterator = _.bind(iterator, context);
      return initial ? obj.reduceRight(iterator, memo) : obj.reduceRight(iterator);
    }
    var length = obj.length;
    if (length !== +length) {
      var keys = _.keys(obj);
      length = keys.length;
    }
    each(obj, function(value, index, list) {
      index = keys ? keys[--length] : --length;
      if (!initial) {
        memo = obj[index];
        initial = true;
      } else {
        memo = iterator.call(context, memo, obj[index], index, list);
      }
    });
    if (!initial) throw new TypeError(reduceError);
    return memo;
  };

  // Return the first value which passes a truth test. Aliased as `detect`.
  _.find = _.detect = function(obj, iterator, context) {
    var result;
    any(obj, function(value, index, list) {
      if (iterator.call(context, value, index, list)) {
        result = value;
        return true;
      }
    });
    return result;
  };

  // Return all the elements that pass a truth test.
  // Delegates to **ECMAScript 5**'s native `filter` if available.
  // Aliased as `select`.
  _.filter = _.select = function(obj, iterator, context) {
    var results = [];
    if (obj == null) return results;
    if (nativeFilter && obj.filter === nativeFilter) return obj.filter(iterator, context);
    each(obj, function(value, index, list) {
      if (iterator.call(context, value, index, list)) results[results.length] = value;
    });
    return results;
  };

  // Return all the elements for which a truth test fails.
  _.reject = function(obj, iterator, context) {
    return _.filter(obj, function(value, index, list) {
      return !iterator.call(context, value, index, list);
    }, context);
  };

  // Determine whether all of the elements match a truth test.
  // Delegates to **ECMAScript 5**'s native `every` if available.
  // Aliased as `all`.
  _.every = _.all = function(obj, iterator, context) {
    iterator || (iterator = _.identity);
    var result = true;
    if (obj == null) return result;
    if (nativeEvery && obj.every === nativeEvery) return obj.every(iterator, context);
    each(obj, function(value, index, list) {
      if (!(result = result && iterator.call(context, value, index, list))) return breaker;
    });
    return !!result;
  };

  // Determine if at least one element in the object matches a truth test.
  // Delegates to **ECMAScript 5**'s native `some` if available.
  // Aliased as `any`.
  var any = _.some = _.any = function(obj, iterator, context) {
    iterator || (iterator = _.identity);
    var result = false;
    if (obj == null) return result;
    if (nativeSome && obj.some === nativeSome) return obj.some(iterator, context);
    each(obj, function(value, index, list) {
      if (result || (result = iterator.call(context, value, index, list))) return breaker;
    });
    return !!result;
  };

  // Determine if the array or object contains a given value (using `===`).
  // Aliased as `include`.
  _.contains = _.include = function(obj, target) {
    if (obj == null) return false;
    if (nativeIndexOf && obj.indexOf === nativeIndexOf) return obj.indexOf(target) != -1;
    return any(obj, function(value) {
      return value === target;
    });
  };

  // Invoke a method (with arguments) on every item in a collection.
  _.invoke = function(obj, method) {
    var args = slice.call(arguments, 2);
    var isFunc = _.isFunction(method);
    return _.map(obj, function(value) {
      return (isFunc ? method : value[method]).apply(value, args);
    });
  };

  // Convenience version of a common use case of `map`: fetching a property.
  _.pluck = function(obj, key) {
    return _.map(obj, function(value){ return value[key]; });
  };

  // Convenience version of a common use case of `filter`: selecting only objects
  // containing specific `key:value` pairs.
  _.where = function(obj, attrs, first) {
    if (_.isEmpty(attrs)) return first ? null : [];
    return _[first ? 'find' : 'filter'](obj, function(value) {
      for (var key in attrs) {
        if (attrs[key] !== value[key]) return false;
      }
      return true;
    });
  };

  // Convenience version of a common use case of `find`: getting the first object
  // containing specific `key:value` pairs.
  _.findWhere = function(obj, attrs) {
    return _.where(obj, attrs, true);
  };

  // Return the maximum element or (element-based computation).
  // Can't optimize arrays of integers longer than 65,535 elements.
  // See: https://bugs.webkit.org/show_bug.cgi?id=80797
  _.max = function(obj, iterator, context) {
    if (!iterator && _.isArray(obj) && obj[0] === +obj[0] && obj.length < 65535) {
      return Math.max.apply(Math, obj);
    }
    if (!iterator && _.isEmpty(obj)) return -Infinity;
    var result = {computed : -Infinity, value: -Infinity};
    each(obj, function(value, index, list) {
      var computed = iterator ? iterator.call(context, value, index, list) : value;
      computed >= result.computed && (result = {value : value, computed : computed});
    });
    return result.value;
  };

  // Return the minimum element (or element-based computation).
  _.min = function(obj, iterator, context) {
    if (!iterator && _.isArray(obj) && obj[0] === +obj[0] && obj.length < 65535) {
      return Math.min.apply(Math, obj);
    }
    if (!iterator && _.isEmpty(obj)) return Infinity;
    var result = {computed : Infinity, value: Infinity};
    each(obj, function(value, index, list) {
      var computed = iterator ? iterator.call(context, value, index, list) : value;
      computed < result.computed && (result = {value : value, computed : computed});
    });
    return result.value;
  };

  // Shuffle an array.
  _.shuffle = function(obj) {
    var rand;
    var index = 0;
    var shuffled = [];
    each(obj, function(value) {
      rand = _.random(index++);
      shuffled[index - 1] = shuffled[rand];
      shuffled[rand] = value;
    });
    return shuffled;
  };

  // An internal function to generate lookup iterators.
  var lookupIterator = function(value) {
    return _.isFunction(value) ? value : function(obj){ return obj[value]; };
  };

  // Sort the object's values by a criterion produced by an iterator.
  _.sortBy = function(obj, value, context) {
    var iterator = lookupIterator(value);
    return _.pluck(_.map(obj, function(value, index, list) {
      return {
        value : value,
        index : index,
        criteria : iterator.call(context, value, index, list)
      };
    }).sort(function(left, right) {
      var a = left.criteria;
      var b = right.criteria;
      if (a !== b) {
        if (a > b || a === void 0) return 1;
        if (a < b || b === void 0) return -1;
      }
      return left.index < right.index ? -1 : 1;
    }), 'value');
  };

  // An internal function used for aggregate "group by" operations.
  var group = function(obj, value, context, behavior) {
    var result = {};
    var iterator = lookupIterator(value || _.identity);
    each(obj, function(value, index) {
      var key = iterator.call(context, value, index, obj);
      behavior(result, key, value);
    });
    return result;
  };

  // Groups the object's values by a criterion. Pass either a string attribute
  // to group by, or a function that returns the criterion.
  _.groupBy = function(obj, value, context) {
    return group(obj, value, context, function(result, key, value) {
      (_.has(result, key) ? result[key] : (result[key] = [])).push(value);
    });
  };

  // Counts instances of an object that group by a certain criterion. Pass
  // either a string attribute to count by, or a function that returns the
  // criterion.
  _.countBy = function(obj, value, context) {
    return group(obj, value, context, function(result, key) {
      if (!_.has(result, key)) result[key] = 0;
      result[key]++;
    });
  };

  // Use a comparator function to figure out the smallest index at which
  // an object should be inserted so as to maintain order. Uses binary search.
  _.sortedIndex = function(array, obj, iterator, context) {
    iterator = iterator == null ? _.identity : lookupIterator(iterator);
    var value = iterator.call(context, obj);
    var low = 0, high = array.length;
    while (low < high) {
      var mid = (low + high) >>> 1;
      iterator.call(context, array[mid]) < value ? low = mid + 1 : high = mid;
    }
    return low;
  };

  // Safely convert anything iterable into a real, live array.
  _.toArray = function(obj) {
    if (!obj) return [];
    if (_.isArray(obj)) return slice.call(obj);
    if (obj.length === +obj.length) return _.map(obj, _.identity);
    return _.values(obj);
  };

  // Return the number of elements in an object.
  _.size = function(obj) {
    if (obj == null) return 0;
    return (obj.length === +obj.length) ? obj.length : _.keys(obj).length;
  };

  // Array Functions
  // ---------------

  // Get the first element of an array. Passing **n** will return the first N
  // values in the array. Aliased as `head` and `take`. The **guard** check
  // allows it to work with `_.map`.
  _.first = _.head = _.take = function(array, n, guard) {
    if (array == null) return void 0;
    return (n != null) && !guard ? slice.call(array, 0, n) : array[0];
  };

  // Returns everything but the last entry of the array. Especially useful on
  // the arguments object. Passing **n** will return all the values in
  // the array, excluding the last N. The **guard** check allows it to work with
  // `_.map`.
  _.initial = function(array, n, guard) {
    return slice.call(array, 0, array.length - ((n == null) || guard ? 1 : n));
  };

  // Get the last element of an array. Passing **n** will return the last N
  // values in the array. The **guard** check allows it to work with `_.map`.
  _.last = function(array, n, guard) {
    if (array == null) return void 0;
    if ((n != null) && !guard) {
      return slice.call(array, Math.max(array.length - n, 0));
    } else {
      return array[array.length - 1];
    }
  };

  // Returns everything but the first entry of the array. Aliased as `tail` and `drop`.
  // Especially useful on the arguments object. Passing an **n** will return
  // the rest N values in the array. The **guard**
  // check allows it to work with `_.map`.
  _.rest = _.tail = _.drop = function(array, n, guard) {
    return slice.call(array, (n == null) || guard ? 1 : n);
  };

  // Trim out all falsy values from an array.
  _.compact = function(array) {
    return _.filter(array, _.identity);
  };

  // Internal implementation of a recursive `flatten` function.
  var flatten = function(input, shallow, output) {
    each(input, function(value) {
      if (_.isArray(value)) {
        shallow ? push.apply(output, value) : flatten(value, shallow, output);
      } else {
        output.push(value);
      }
    });
    return output;
  };

  // Return a completely flattened version of an array.
  _.flatten = function(array, shallow) {
    return flatten(array, shallow, []);
  };

  // Return a version of the array that does not contain the specified value(s).
  _.without = function(array) {
    return _.difference(array, slice.call(arguments, 1));
  };

  // Produce a duplicate-free version of the array. If the array has already
  // been sorted, you have the option of using a faster algorithm.
  // Aliased as `unique`.
  _.uniq = _.unique = function(array, isSorted, iterator, context) {
    if (_.isFunction(isSorted)) {
      context = iterator;
      iterator = isSorted;
      isSorted = false;
    }
    var initial = iterator ? _.map(array, iterator, context) : array;
    var results = [];
    var seen = [];
    each(initial, function(value, index) {
      if (isSorted ? (!index || seen[seen.length - 1] !== value) : !_.contains(seen, value)) {
        seen.push(value);
        results.push(array[index]);
      }
    });
    return results;
  };

  // Produce an array that contains the union: each distinct element from all of
  // the passed-in arrays.
  _.union = function() {
    return _.uniq(concat.apply(ArrayProto, arguments));
  };

  // Produce an array that contains every item shared between all the
  // passed-in arrays.
  _.intersection = function(array) {
    var rest = slice.call(arguments, 1);
    return _.filter(_.uniq(array), function(item) {
      return _.every(rest, function(other) {
        return _.indexOf(other, item) >= 0;
      });
    });
  };

  // Take the difference between one array and a number of other arrays.
  // Only the elements present in just the first array will remain.
  _.difference = function(array) {
    var rest = concat.apply(ArrayProto, slice.call(arguments, 1));
    return _.filter(array, function(value){ return !_.contains(rest, value); });
  };

  // Zip together multiple lists into a single array -- elements that share
  // an index go together.
  _.zip = function() {
    var args = slice.call(arguments);
    var length = _.max(_.pluck(args, 'length'));
    var results = new Array(length);
    for (var i = 0; i < length; i++) {
      results[i] = _.pluck(args, "" + i);
    }
    return results;
  };

  // Converts lists into objects. Pass either a single array of `[key, value]`
  // pairs, or two parallel arrays of the same length -- one of keys, and one of
  // the corresponding values.
  _.object = function(list, values) {
    if (list == null) return {};
    var result = {};
    for (var i = 0, l = list.length; i < l; i++) {
      if (values) {
        result[list[i]] = values[i];
      } else {
        result[list[i][0]] = list[i][1];
      }
    }
    return result;
  };

  // If the browser doesn't supply us with indexOf (I'm looking at you, **MSIE**),
  // we need this function. Return the position of the first occurrence of an
  // item in an array, or -1 if the item is not included in the array.
  // Delegates to **ECMAScript 5**'s native `indexOf` if available.
  // If the array is large and already in sort order, pass `true`
  // for **isSorted** to use binary search.
  _.indexOf = function(array, item, isSorted) {
    if (array == null) return -1;
    var i = 0, l = array.length;
    if (isSorted) {
      if (typeof isSorted == 'number') {
        i = (isSorted < 0 ? Math.max(0, l + isSorted) : isSorted);
      } else {
        i = _.sortedIndex(array, item);
        return array[i] === item ? i : -1;
      }
    }
    if (nativeIndexOf && array.indexOf === nativeIndexOf) return array.indexOf(item, isSorted);
    for (; i < l; i++) if (array[i] === item) return i;
    return -1;
  };

  // Delegates to **ECMAScript 5**'s native `lastIndexOf` if available.
  _.lastIndexOf = function(array, item, from) {
    if (array == null) return -1;
    var hasIndex = from != null;
    if (nativeLastIndexOf && array.lastIndexOf === nativeLastIndexOf) {
      return hasIndex ? array.lastIndexOf(item, from) : array.lastIndexOf(item);
    }
    var i = (hasIndex ? from : array.length);
    while (i--) if (array[i] === item) return i;
    return -1;
  };

  // Generate an integer Array containing an arithmetic progression. A port of
  // the native Python `range()` function. See
  // [the Python documentation](http://docs.python.org/library/functions.html#range).
  _.range = function(start, stop, step) {
    if (arguments.length <= 1) {
      stop = start || 0;
      start = 0;
    }
    step = arguments[2] || 1;

    var len = Math.max(Math.ceil((stop - start) / step), 0);
    var idx = 0;
    var range = new Array(len);

    while(idx < len) {
      range[idx++] = start;
      start += step;
    }

    return range;
  };

  // Function (ahem) Functions
  // ------------------

  // Create a function bound to a given object (assigning `this`, and arguments,
  // optionally). Delegates to **ECMAScript 5**'s native `Function.bind` if
  // available.
  _.bind = function(func, context) {
    if (func.bind === nativeBind && nativeBind) return nativeBind.apply(func, slice.call(arguments, 1));
    var args = slice.call(arguments, 2);
    return function() {
      return func.apply(context, args.concat(slice.call(arguments)));
    };
  };

  // Partially apply a function by creating a version that has had some of its
  // arguments pre-filled, without changing its dynamic `this` context.
  _.partial = function(func) {
    var args = slice.call(arguments, 1);
    return function() {
      return func.apply(this, args.concat(slice.call(arguments)));
    };
  };

  // Bind all of an object's methods to that object. Useful for ensuring that
  // all callbacks defined on an object belong to it.
  _.bindAll = function(obj) {
    var funcs = slice.call(arguments, 1);
    if (funcs.length === 0) funcs = _.functions(obj);
    each(funcs, function(f) { obj[f] = _.bind(obj[f], obj); });
    return obj;
  };

  // Memoize an expensive function by storing its results.
  _.memoize = function(func, hasher) {
    var memo = {};
    hasher || (hasher = _.identity);
    return function() {
      var key = hasher.apply(this, arguments);
      return _.has(memo, key) ? memo[key] : (memo[key] = func.apply(this, arguments));
    };
  };

  // Delays a function for the given number of milliseconds, and then calls
  // it with the arguments supplied.
  _.delay = function(func, wait) {
    var args = slice.call(arguments, 2);
    return setTimeout(function(){ return func.apply(null, args); }, wait);
  };

  // Defers a function, scheduling it to run after the current call stack has
  // cleared.
  _.defer = function(func) {
    return _.delay.apply(_, [func, 1].concat(slice.call(arguments, 1)));
  };

  // Returns a function, that, when invoked, will only be triggered at most once
  // during a given window of time.
  _.throttle = function(func, wait) {
    var context, args, timeout, result;
    var previous = 0;
    var later = function() {
      previous = new Date;
      timeout = null;
      result = func.apply(context, args);
    };
    return function() {
      var now = new Date;
      var remaining = wait - (now - previous);
      context = this;
      args = arguments;
      if (remaining <= 0) {
        clearTimeout(timeout);
        timeout = null;
        previous = now;
        result = func.apply(context, args);
      } else if (!timeout) {
        timeout = setTimeout(later, remaining);
      }
      return result;
    };
  };

  // Returns a function, that, as long as it continues to be invoked, will not
  // be triggered. The function will be called after it stops being called for
  // N milliseconds. If `immediate` is passed, trigger the function on the
  // leading edge, instead of the trailing.
  _.debounce = function(func, wait, immediate) {
    var timeout, result;
    return function() {
      var context = this, args = arguments;
      var later = function() {
        timeout = null;
        if (!immediate) result = func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) result = func.apply(context, args);
      return result;
    };
  };

  // Returns a function that will be executed at most one time, no matter how
  // often you call it. Useful for lazy initialization.
  _.once = function(func) {
    var ran = false, memo;
    return function() {
      if (ran) return memo;
      ran = true;
      memo = func.apply(this, arguments);
      func = null;
      return memo;
    };
  };

  // Returns the first function passed as an argument to the second,
  // allowing you to adjust arguments, run code before and after, and
  // conditionally execute the original function.
  _.wrap = function(func, wrapper) {
    return function() {
      var args = [func];
      push.apply(args, arguments);
      return wrapper.apply(this, args);
    };
  };

  // Returns a function that is the composition of a list of functions, each
  // consuming the return value of the function that follows.
  _.compose = function() {
    var funcs = arguments;
    return function() {
      var args = arguments;
      for (var i = funcs.length - 1; i >= 0; i--) {
        args = [funcs[i].apply(this, args)];
      }
      return args[0];
    };
  };

  // Returns a function that will only be executed after being called N times.
  _.after = function(times, func) {
    if (times <= 0) return func();
    return function() {
      if (--times < 1) {
        return func.apply(this, arguments);
      }
    };
  };

  // Object Functions
  // ----------------

  // Retrieve the names of an object's properties.
  // Delegates to **ECMAScript 5**'s native `Object.keys`
  _.keys = nativeKeys || function(obj) {
    if (obj !== Object(obj)) throw new TypeError('Invalid object');
    var keys = [];
    for (var key in obj) if (_.has(obj, key)) keys[keys.length] = key;
    return keys;
  };

  // Retrieve the values of an object's properties.
  _.values = function(obj) {
    var values = [];
    for (var key in obj) if (_.has(obj, key)) values.push(obj[key]);
    return values;
  };

  // Convert an object into a list of `[key, value]` pairs.
  _.pairs = function(obj) {
    var pairs = [];
    for (var key in obj) if (_.has(obj, key)) pairs.push([key, obj[key]]);
    return pairs;
  };

  // Invert the keys and values of an object. The values must be serializable.
  _.invert = function(obj) {
    var result = {};
    for (var key in obj) if (_.has(obj, key)) result[obj[key]] = key;
    return result;
  };

  // Return a sorted list of the function names available on the object.
  // Aliased as `methods`
  _.functions = _.methods = function(obj) {
    var names = [];
    for (var key in obj) {
      if (_.isFunction(obj[key])) names.push(key);
    }
    return names.sort();
  };

  // Extend a given object with all the properties in passed-in object(s).
  _.extend = function(obj) {
    each(slice.call(arguments, 1), function(source) {
      if (source) {
        for (var prop in source) {
          obj[prop] = source[prop];
        }
      }
    });
    return obj;
  };

  // Return a copy of the object only containing the whitelisted properties.
  _.pick = function(obj) {
    var copy = {};
    var keys = concat.apply(ArrayProto, slice.call(arguments, 1));
    each(keys, function(key) {
      if (key in obj) copy[key] = obj[key];
    });
    return copy;
  };

   // Return a copy of the object without the blacklisted properties.
  _.omit = function(obj) {
    var copy = {};
    var keys = concat.apply(ArrayProto, slice.call(arguments, 1));
    for (var key in obj) {
      if (!_.contains(keys, key)) copy[key] = obj[key];
    }
    return copy;
  };

  // Fill in a given object with default properties.
  _.defaults = function(obj) {
    each(slice.call(arguments, 1), function(source) {
      if (source) {
        for (var prop in source) {
          if (obj[prop] == null) obj[prop] = source[prop];
        }
      }
    });
    return obj;
  };

  // Create a (shallow-cloned) duplicate of an object.
  _.clone = function(obj) {
    if (!_.isObject(obj)) return obj;
    return _.isArray(obj) ? obj.slice() : _.extend({}, obj);
  };

  // Invokes interceptor with the obj, and then returns obj.
  // The primary purpose of this method is to "tap into" a method chain, in
  // order to perform operations on intermediate results within the chain.
  _.tap = function(obj, interceptor) {
    interceptor(obj);
    return obj;
  };

  // Internal recursive comparison function for `isEqual`.
  var eq = function(a, b, aStack, bStack) {
    // Identical objects are equal. `0 === -0`, but they aren't identical.
    // See the Harmony `egal` proposal: http://wiki.ecmascript.org/doku.php?id=harmony:egal.
    if (a === b) return a !== 0 || 1 / a == 1 / b;
    // A strict comparison is necessary because `null == undefined`.
    if (a == null || b == null) return a === b;
    // Unwrap any wrapped objects.
    if (a instanceof _) a = a._wrapped;
    if (b instanceof _) b = b._wrapped;
    // Compare `[[Class]]` names.
    var className = toString.call(a);
    if (className != toString.call(b)) return false;
    switch (className) {
      // Strings, numbers, dates, and booleans are compared by value.
      case '[object String]':
        // Primitives and their corresponding object wrappers are equivalent; thus, `"5"` is
        // equivalent to `new String("5")`.
        return a == String(b);
      case '[object Number]':
        // `NaN`s are equivalent, but non-reflexive. An `egal` comparison is performed for
        // other numeric values.
        return a != +a ? b != +b : (a == 0 ? 1 / a == 1 / b : a == +b);
      case '[object Date]':
      case '[object Boolean]':
        // Coerce dates and booleans to numeric primitive values. Dates are compared by their
        // millisecond representations. Note that invalid dates with millisecond representations
        // of `NaN` are not equivalent.
        return +a == +b;
      // RegExps are compared by their source patterns and flags.
      case '[object RegExp]':
        return a.source == b.source &&
               a.global == b.global &&
               a.multiline == b.multiline &&
               a.ignoreCase == b.ignoreCase;
    }
    if (typeof a != 'object' || typeof b != 'object') return false;
    // Assume equality for cyclic structures. The algorithm for detecting cyclic
    // structures is adapted from ES 5.1 section 15.12.3, abstract operation `JO`.
    var length = aStack.length;
    while (length--) {
      // Linear search. Performance is inversely proportional to the number of
      // unique nested structures.
      if (aStack[length] == a) return bStack[length] == b;
    }
    // Add the first object to the stack of traversed objects.
    aStack.push(a);
    bStack.push(b);
    var size = 0, result = true;
    // Recursively compare objects and arrays.
    if (className == '[object Array]') {
      // Compare array lengths to determine if a deep comparison is necessary.
      size = a.length;
      result = size == b.length;
      if (result) {
        // Deep compare the contents, ignoring non-numeric properties.
        while (size--) {
          if (!(result = eq(a[size], b[size], aStack, bStack))) break;
        }
      }
    } else {
      // Objects with different constructors are not equivalent, but `Object`s
      // from different frames are.
      var aCtor = a.constructor, bCtor = b.constructor;
      if (aCtor !== bCtor && !(_.isFunction(aCtor) && (aCtor instanceof aCtor) &&
                               _.isFunction(bCtor) && (bCtor instanceof bCtor))) {
        return false;
      }
      // Deep compare objects.
      for (var key in a) {
        if (_.has(a, key)) {
          // Count the expected number of properties.
          size++;
          // Deep compare each member.
          if (!(result = _.has(b, key) && eq(a[key], b[key], aStack, bStack))) break;
        }
      }
      // Ensure that both objects contain the same number of properties.
      if (result) {
        for (key in b) {
          if (_.has(b, key) && !(size--)) break;
        }
        result = !size;
      }
    }
    // Remove the first object from the stack of traversed objects.
    aStack.pop();
    bStack.pop();
    return result;
  };

  // Perform a deep comparison to check if two objects are equal.
  _.isEqual = function(a, b) {
    return eq(a, b, [], []);
  };

  // Is a given array, string, or object empty?
  // An "empty" object has no enumerable own-properties.
  _.isEmpty = function(obj) {
    if (obj == null) return true;
    if (_.isArray(obj) || _.isString(obj)) return obj.length === 0;
    for (var key in obj) if (_.has(obj, key)) return false;
    return true;
  };

  // Is a given value a DOM element?
  _.isElement = function(obj) {
    return !!(obj && obj.nodeType === 1);
  };

  // Is a given value an array?
  // Delegates to ECMA5's native Array.isArray
  _.isArray = nativeIsArray || function(obj) {
    return toString.call(obj) == '[object Array]';
  };

  // Is a given variable an object?
  _.isObject = function(obj) {
    return obj === Object(obj);
  };

  // Add some isType methods: isArguments, isFunction, isString, isNumber, isDate, isRegExp.
  each(['Arguments', 'Function', 'String', 'Number', 'Date', 'RegExp'], function(name) {
    _['is' + name] = function(obj) {
      return toString.call(obj) == '[object ' + name + ']';
    };
  });

  // Define a fallback version of the method in browsers (ahem, IE), where
  // there isn't any inspectable "Arguments" type.
  if (!_.isArguments(arguments)) {
    _.isArguments = function(obj) {
      return !!(obj && _.has(obj, 'callee'));
    };
  }

  // Optimize `isFunction` if appropriate.
  if (typeof (/./) !== 'function') {
    _.isFunction = function(obj) {
      return typeof obj === 'function';
    };
  }

  // Is a given object a finite number?
  _.isFinite = function(obj) {
    return isFinite(obj) && !isNaN(parseFloat(obj));
  };

  // Is the given value `NaN`? (NaN is the only number which does not equal itself).
  _.isNaN = function(obj) {
    return _.isNumber(obj) && obj != +obj;
  };

  // Is a given value a boolean?
  _.isBoolean = function(obj) {
    return obj === true || obj === false || toString.call(obj) == '[object Boolean]';
  };

  // Is a given value equal to null?
  _.isNull = function(obj) {
    return obj === null;
  };

  // Is a given variable undefined?
  _.isUndefined = function(obj) {
    return obj === void 0;
  };

  // Shortcut function for checking if an object has a given property directly
  // on itself (in other words, not on a prototype).
  _.has = function(obj, key) {
    return hasOwnProperty.call(obj, key);
  };

  // Utility Functions
  // -----------------

  // Run Underscore.js in *noConflict* mode, returning the `_` variable to its
  // previous owner. Returns a reference to the Underscore object.
  _.noConflict = function() {
    root._ = previousUnderscore;
    return this;
  };

  // Keep the identity function around for default iterators.
  _.identity = function(value) {
    return value;
  };

  // Run a function **n** times.
  _.times = function(n, iterator, context) {
    var accum = Array(n);
    for (var i = 0; i < n; i++) accum[i] = iterator.call(context, i);
    return accum;
  };

  // Return a random integer between min and max (inclusive).
  _.random = function(min, max) {
    if (max == null) {
      max = min;
      min = 0;
    }
    return min + Math.floor(Math.random() * (max - min + 1));
  };

  // List of HTML entities for escaping.
  var entityMap = {
    escape: {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#x27;',
      '/': '&#x2F;'
    }
  };
  entityMap.unescape = _.invert(entityMap.escape);

  // Regexes containing the keys and values listed immediately above.
  var entityRegexes = {
    escape:   new RegExp('[' + _.keys(entityMap.escape).join('') + ']', 'g'),
    unescape: new RegExp('(' + _.keys(entityMap.unescape).join('|') + ')', 'g')
  };

  // Functions for escaping and unescaping strings to/from HTML interpolation.
  _.each(['escape', 'unescape'], function(method) {
    _[method] = function(string) {
      if (string == null) return '';
      return ('' + string).replace(entityRegexes[method], function(match) {
        return entityMap[method][match];
      });
    };
  });

  // If the value of the named property is a function then invoke it;
  // otherwise, return it.
  _.result = function(object, property) {
    if (object == null) return null;
    var value = object[property];
    return _.isFunction(value) ? value.call(object) : value;
  };

  // Add your own custom functions to the Underscore object.
  _.mixin = function(obj) {
    each(_.functions(obj), function(name){
      var func = _[name] = obj[name];
      _.prototype[name] = function() {
        var args = [this._wrapped];
        push.apply(args, arguments);
        return result.call(this, func.apply(_, args));
      };
    });
  };

  // Generate a unique integer id (unique within the entire client session).
  // Useful for temporary DOM ids.
  var idCounter = 0;
  _.uniqueId = function(prefix) {
    var id = ++idCounter + '';
    return prefix ? prefix + id : id;
  };

  // By default, Underscore uses ERB-style template delimiters, change the
  // following template settings to use alternative delimiters.
  _.templateSettings = {
    evaluate    : /<%([\s\S]+?)%>/g,
    interpolate : /<%=([\s\S]+?)%>/g,
    escape      : /<%-([\s\S]+?)%>/g
  };

  // When customizing `templateSettings`, if you don't want to define an
  // interpolation, evaluation or escaping regex, we need one that is
  // guaranteed not to match.
  var noMatch = /(.)^/;

  // Certain characters need to be escaped so that they can be put into a
  // string literal.
  var escapes = {
    "'":      "'",
    '\\':     '\\',
    '\r':     'r',
    '\n':     'n',
    '\t':     't',
    '\u2028': 'u2028',
    '\u2029': 'u2029'
  };

  var escaper = /\\|'|\r|\n|\t|\u2028|\u2029/g;

  // JavaScript micro-templating, similar to John Resig's implementation.
  // Underscore templating handles arbitrary delimiters, preserves whitespace,
  // and correctly escapes quotes within interpolated code.
  _.template = function(text, data, settings) {
    var render;
    settings = _.defaults({}, settings, _.templateSettings);

    // Combine delimiters into one regular expression via alternation.
    var matcher = new RegExp([
      (settings.escape || noMatch).source,
      (settings.interpolate || noMatch).source,
      (settings.evaluate || noMatch).source
    ].join('|') + '|$', 'g');

    // Compile the template source, escaping string literals appropriately.
    var index = 0;
    var source = "__p+='";
    text.replace(matcher, function(match, escape, interpolate, evaluate, offset) {
      source += text.slice(index, offset)
        .replace(escaper, function(match) { return '\\' + escapes[match]; });

      if (escape) {
        source += "'+\n((__t=(" + escape + "))==null?'':_.escape(__t))+\n'";
      }
      if (interpolate) {
        source += "'+\n((__t=(" + interpolate + "))==null?'':__t)+\n'";
      }
      if (evaluate) {
        source += "';\n" + evaluate + "\n__p+='";
      }
      index = offset + match.length;
      return match;
    });
    source += "';\n";

    // If a variable is not specified, place data values in local scope.
    if (!settings.variable) source = 'with(obj||{}){\n' + source + '}\n';

    source = "var __t,__p='',__j=Array.prototype.join," +
      "print=function(){__p+=__j.call(arguments,'');};\n" +
      source + "return __p;\n";

    try {
      render = new Function(settings.variable || 'obj', '_', source);
    } catch (e) {
      e.source = source;
      throw e;
    }

    if (data) return render(data, _);
    var template = function(data) {
      return render.call(this, data, _);
    };

    // Provide the compiled function source as a convenience for precompilation.
    template.source = 'function(' + (settings.variable || 'obj') + '){\n' + source + '}';

    return template;
  };

  // Add a "chain" function, which will delegate to the wrapper.
  _.chain = function(obj) {
    return _(obj).chain();
  };

  // OOP
  // ---------------
  // If Underscore is called as a function, it returns a wrapped object that
  // can be used OO-style. This wrapper holds altered versions of all the
  // underscore functions. Wrapped objects may be chained.

  // Helper function to continue chaining intermediate results.
  var result = function(obj) {
    return this._chain ? _(obj).chain() : obj;
  };

  // Add all of the Underscore functions to the wrapper object.
  _.mixin(_);

  // Add all mutator Array functions to the wrapper.
  each(['pop', 'push', 'reverse', 'shift', 'sort', 'splice', 'unshift'], function(name) {
    var method = ArrayProto[name];
    _.prototype[name] = function() {
      var obj = this._wrapped;
      method.apply(obj, arguments);
      if ((name == 'shift' || name == 'splice') && obj.length === 0) delete obj[0];
      return result.call(this, obj);
    };
  });

  // Add all accessor Array functions to the wrapper.
  each(['concat', 'join', 'slice'], function(name) {
    var method = ArrayProto[name];
    _.prototype[name] = function() {
      return result.call(this, method.apply(this._wrapped, arguments));
    };
  });

  _.extend(_.prototype, {

    // Start chaining a wrapped Underscore object.
    chain: function() {
      this._chain = true;
      return this;
    },

    // Extracts the result from a wrapped and chained object.
    value: function() {
      return this._wrapped;
    }

  });

}).call(this);

//     Backbone.js 0.9.10

//     (c) 2010-2012 Jeremy Ashkenas, DocumentCloud Inc.
//     Backbone may be freely distributed under the MIT license.
//     For all details and documentation:
//     http://backbonejs.org

(function(){

  // Initial Setup
  // -------------

  // Save a reference to the global object (`window` in the browser, `exports`
  // on the server).
  var root = this;

  // Save the previous value of the `Backbone` variable, so that it can be
  // restored later on, if `noConflict` is used.
  var previousBackbone = root.Backbone;

  // Create a local reference to array methods.
  var array = [];
  var push = array.push;
  var slice = array.slice;
  var splice = array.splice;

  // The top-level namespace. All public Backbone classes and modules will
  // be attached to this. Exported for both CommonJS and the browser.
  var Backbone;
  if (typeof exports !== 'undefined') {
    Backbone = exports;
  } else {
    Backbone = root.Backbone = {};
  }

  // Current version of the library. Keep in sync with `package.json`.
  Backbone.VERSION = '0.9.10';

  // Require Underscore, if we're on the server, and it's not already present.
  var _ = root._;
  if (!_ && (typeof require !== 'undefined')) _ = require('underscore');

  // For Backbone's purposes, jQuery, Zepto, or Ender owns the `$` variable.
  Backbone.$ = root.jQuery || root.Zepto || root.ender;

  // Runs Backbone.js in *noConflict* mode, returning the `Backbone` variable
  // to its previous owner. Returns a reference to this Backbone object.
  Backbone.noConflict = function() {
    root.Backbone = previousBackbone;
    return this;
  };

  // Turn on `emulateHTTP` to support legacy HTTP servers. Setting this option
  // will fake `"PUT"` and `"DELETE"` requests via the `_method` parameter and
  // set a `X-Http-Method-Override` header.
  Backbone.emulateHTTP = false;

  // Turn on `emulateJSON` to support legacy servers that can't deal with direct
  // `application/json` requests ... will encode the body as
  // `application/x-www-form-urlencoded` instead and will send the model in a
  // form param named `model`.
  Backbone.emulateJSON = false;

  // Backbone.Events
  // ---------------

  // Regular expression used to split event strings.
  var eventSplitter = /\s+/;

  // Implement fancy features of the Events API such as multiple event
  // names `"change blur"` and jQuery-style event maps `{change: action}`
  // in terms of the existing API.
  var eventsApi = function(obj, action, name, rest) {
    if (!name) return true;
    if (typeof name === 'object') {
      for (var key in name) {
        obj[action].apply(obj, [key, name[key]].concat(rest));
      }
    } else if (eventSplitter.test(name)) {
      var names = name.split(eventSplitter);
      for (var i = 0, l = names.length; i < l; i++) {
        obj[action].apply(obj, [names[i]].concat(rest));
      }
    } else {
      return true;
    }
  };

  // Optimized internal dispatch function for triggering events. Tries to
  // keep the usual cases speedy (most Backbone events have 3 arguments).
  var triggerEvents = function(events, args) {
    var ev, i = -1, l = events.length;
    switch (args.length) {
    case 0: while (++i < l) (ev = events[i]).callback.call(ev.ctx);
    return;
    case 1: while (++i < l) (ev = events[i]).callback.call(ev.ctx, args[0]);
    return;
    case 2: while (++i < l) (ev = events[i]).callback.call(ev.ctx, args[0], args[1]);
    return;
    case 3: while (++i < l) (ev = events[i]).callback.call(ev.ctx, args[0], args[1], args[2]);
    return;
    default: while (++i < l) (ev = events[i]).callback.apply(ev.ctx, args);
    }
  };

  // A module that can be mixed in to *any object* in order to provide it with
  // custom events. You may bind with `on` or remove with `off` callback
  // functions to an event; `trigger`-ing an event fires all callbacks in
  // succession.
  //
  //     var object = {};
  //     _.extend(object, Backbone.Events);
  //     object.on('expand', function(){ alert('expanded'); });
  //     object.trigger('expand');
  //
  var Events = Backbone.Events = {

    // Bind one or more space separated events, or an events map,
    // to a `callback` function. Passing `"all"` will bind the callback to
    // all events fired.
    on: function(name, callback, context) {
      if (!(eventsApi(this, 'on', name, [callback, context]) && callback)) return this;
      this._events || (this._events = {});
      var list = this._events[name] || (this._events[name] = []);
      list.push({callback: callback, context: context, ctx: context || this});
      return this;
    },

    // Bind events to only be triggered a single time. After the first time
    // the callback is invoked, it will be removed.
    once: function(name, callback, context) {
      if (!(eventsApi(this, 'once', name, [callback, context]) && callback)) return this;
      var self = this;
      var once = _.once(function() {
        self.off(name, once);
        callback.apply(this, arguments);
      });
      once._callback = callback;
      this.on(name, once, context);
      return this;
    },

    // Remove one or many callbacks. If `context` is null, removes all
    // callbacks with that function. If `callback` is null, removes all
    // callbacks for the event. If `name` is null, removes all bound
    // callbacks for all events.
    off: function(name, callback, context) {
      var list, ev, events, names, i, l, j, k;
      if (!this._events || !eventsApi(this, 'off', name, [callback, context])) return this;
      if (!name && !callback && !context) {
        this._events = {};
        return this;
      }

      names = name ? [name] : _.keys(this._events);
      for (i = 0, l = names.length; i < l; i++) {
        name = names[i];
        if (list = this._events[name]) {
          events = [];
          if (callback || context) {
            for (j = 0, k = list.length; j < k; j++) {
              ev = list[j];
              if ((callback && callback !== ev.callback &&
                               callback !== ev.callback._callback) ||
                  (context && context !== ev.context)) {
                events.push(ev);
              }
            }
          }
          this._events[name] = events;
        }
      }

      return this;
    },

    // Trigger one or many events, firing all bound callbacks. Callbacks are
    // passed the same arguments as `trigger` is, apart from the event name
    // (unless you're listening on `"all"`, which will cause your callback to
    // receive the true name of the event as the first argument).
    trigger: function(name) {
      if (!this._events) return this;
      var args = slice.call(arguments, 1);
      if (!eventsApi(this, 'trigger', name, args)) return this;
      var events = this._events[name];
      var allEvents = this._events.all;
      if (events) triggerEvents(events, args);
      if (allEvents) triggerEvents(allEvents, arguments);
      return this;
    },

    // An inversion-of-control version of `on`. Tell *this* object to listen to
    // an event in another object ... keeping track of what it's listening to.
    listenTo: function(obj, name, callback) {
      var listeners = this._listeners || (this._listeners = {});
      var id = obj._listenerId || (obj._listenerId = _.uniqueId('l'));
      listeners[id] = obj;
      obj.on(name, typeof name === 'object' ? this : callback, this);
      return this;
    },

    // Tell this object to stop listening to either specific events ... or
    // to every object it's currently listening to.
    stopListening: function(obj, name, callback) {
      var listeners = this._listeners;
      if (!listeners) return;
      if (obj) {
        obj.off(name, typeof name === 'object' ? this : callback, this);
        if (!name && !callback) delete listeners[obj._listenerId];
      } else {
        if (typeof name === 'object') callback = this;
        for (var id in listeners) {
          listeners[id].off(name, callback, this);
        }
        this._listeners = {};
      }
      return this;
    }
  };

  // Aliases for backwards compatibility.
  Events.bind   = Events.on;
  Events.unbind = Events.off;

  // Allow the `Backbone` object to serve as a global event bus, for folks who
  // want global "pubsub" in a convenient place.
  _.extend(Backbone, Events);

  // Backbone.Model
  // --------------

  // Create a new model, with defined attributes. A client id (`cid`)
  // is automatically generated and assigned for you.
  var Model = Backbone.Model = function(attributes, options) {
    var defaults;
    var attrs = attributes || {};
    this.cid = _.uniqueId('c');
    this.attributes = {};
    if (options && options.collection) this.collection = options.collection;
    if (options && options.parse) attrs = this.parse(attrs, options) || {};
    if (defaults = _.result(this, 'defaults')) {
      attrs = _.defaults({}, attrs, defaults);
    }
    this.set(attrs, options);
    this.changed = {};
    this.initialize.apply(this, arguments);
  };

  // Attach all inheritable methods to the Model prototype.
  _.extend(Model.prototype, Events, {

    // A hash of attributes whose current and previous value differ.
    changed: null,

    // The default name for the JSON `id` attribute is `"id"`. MongoDB and
    // CouchDB users may want to set this to `"_id"`.
    idAttribute: 'id',

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize: function(){},

    // Return a copy of the model's `attributes` object.
    toJSON: function(options) {
      return _.clone(this.attributes);
    },

    // Proxy `Backbone.sync` by default.
    sync: function() {
      return Backbone.sync.apply(this, arguments);
    },

    // Get the value of an attribute.
    get: function(attr) {
      return this.attributes[attr];
    },

    // Get the HTML-escaped value of an attribute.
    escape: function(attr) {
      return _.escape(this.get(attr));
    },

    // Returns `true` if the attribute contains a value that is not null
    // or undefined.
    has: function(attr) {
      return this.get(attr) != null;
    },

    // ----------------------------------------------------------------------

    // Set a hash of model attributes on the object, firing `"change"` unless
    // you choose to silence it.
    set: function(key, val, options) {
      var attr, attrs, unset, changes, silent, changing, prev, current;
      if (key == null) return this;

      // Handle both `"key", value` and `{key: value}` -style arguments.
      if (typeof key === 'object') {
        attrs = key;
        options = val;
      } else {
        (attrs = {})[key] = val;
      }

      options || (options = {});

      // Run validation.
      if (!this._validate(attrs, options)) return false;

      // Extract attributes and options.
      unset           = options.unset;
      silent          = options.silent;
      changes         = [];
      changing        = this._changing;
      this._changing  = true;

      if (!changing) {
        this._previousAttributes = _.clone(this.attributes);
        this.changed = {};
      }
      current = this.attributes, prev = this._previousAttributes;

      // Check for changes of `id`.
      if (this.idAttribute in attrs) this.id = attrs[this.idAttribute];

      // For each `set` attribute, update or delete the current value.
      for (attr in attrs) {
        val = attrs[attr];
        if (!_.isEqual(current[attr], val)) changes.push(attr);
        if (!_.isEqual(prev[attr], val)) {
          this.changed[attr] = val;
        } else {
          delete this.changed[attr];
        }
        unset ? delete current[attr] : current[attr] = val;
      }

      // Trigger all relevant attribute changes.
      if (!silent) {
        if (changes.length) this._pending = true;
        for (var i = 0, l = changes.length; i < l; i++) {
          this.trigger('change:' + changes[i], this, current[changes[i]], options);
        }
      }

      if (changing) return this;
      if (!silent) {
        while (this._pending) {
          this._pending = false;
          this.trigger('change', this, options);
        }
      }
      this._pending = false;
      this._changing = false;
      return this;
    },

    // Remove an attribute from the model, firing `"change"` unless you choose
    // to silence it. `unset` is a noop if the attribute doesn't exist.
    unset: function(attr, options) {
      return this.set(attr, void 0, _.extend({}, options, {unset: true}));
    },

    // Clear all attributes on the model, firing `"change"` unless you choose
    // to silence it.
    clear: function(options) {
      var attrs = {};
      for (var key in this.attributes) attrs[key] = void 0;
      return this.set(attrs, _.extend({}, options, {unset: true}));
    },

    // Determine if the model has changed since the last `"change"` event.
    // If you specify an attribute name, determine if that attribute has changed.
    hasChanged: function(attr) {
      if (attr == null) return !_.isEmpty(this.changed);
      return _.has(this.changed, attr);
    },

    // Return an object containing all the attributes that have changed, or
    // false if there are no changed attributes. Useful for determining what
    // parts of a view need to be updated and/or what attributes need to be
    // persisted to the server. Unset attributes will be set to undefined.
    // You can also pass an attributes object to diff against the model,
    // determining if there *would be* a change.
    changedAttributes: function(diff) {
      if (!diff) return this.hasChanged() ? _.clone(this.changed) : false;
      var val, changed = false;
      var old = this._changing ? this._previousAttributes : this.attributes;
      for (var attr in diff) {
        if (_.isEqual(old[attr], (val = diff[attr]))) continue;
        (changed || (changed = {}))[attr] = val;
      }
      return changed;
    },

    // Get the previous value of an attribute, recorded at the time the last
    // `"change"` event was fired.
    previous: function(attr) {
      if (attr == null || !this._previousAttributes) return null;
      return this._previousAttributes[attr];
    },

    // Get all of the attributes of the model at the time of the previous
    // `"change"` event.
    previousAttributes: function() {
      return _.clone(this._previousAttributes);
    },

    // ---------------------------------------------------------------------

    // Fetch the model from the server. If the server's representation of the
    // model differs from its current attributes, they will be overriden,
    // triggering a `"change"` event.
    fetch: function(options) {
      options = options ? _.clone(options) : {};
      if (options.parse === void 0) options.parse = true;
      var success = options.success;
      options.success = function(model, resp, options) {
        if (!model.set(model.parse(resp, options), options)) return false;
        if (success) success(model, resp, options);
      };
      return this.sync('read', this, options);
    },

    // Set a hash of model attributes, and sync the model to the server.
    // If the server returns an attributes hash that differs, the model's
    // state will be `set` again.
    save: function(key, val, options) {
      var attrs, success, method, xhr, attributes = this.attributes;

      // Handle both `"key", value` and `{key: value}` -style arguments.
      if (key == null || typeof key === 'object') {
        attrs = key;
        options = val;
      } else {
        (attrs = {})[key] = val;
      }

      // If we're not waiting and attributes exist, save acts as `set(attr).save(null, opts)`.
      if (attrs && (!options || !options.wait) && !this.set(attrs, options)) return false;

      options = _.extend({validate: true}, options);

      // Do not persist invalid models.
      if (!this._validate(attrs, options)) return false;

      // Set temporary attributes if `{wait: true}`.
      if (attrs && options.wait) {
        this.attributes = _.extend({}, attributes, attrs);
      }

      // After a successful server-side save, the client is (optionally)
      // updated with the server-side state.
      if (options.parse === void 0) options.parse = true;
      success = options.success;
      options.success = function(model, resp, options) {
        // Ensure attributes are restored during synchronous saves.
        model.attributes = attributes;
        var serverAttrs = model.parse(resp, options);
        if (options.wait) serverAttrs = _.extend(attrs || {}, serverAttrs);
        if (_.isObject(serverAttrs) && !model.set(serverAttrs, options)) {
          return false;
        }
        if (success) success(model, resp, options);
      };

      // Finish configuring and sending the Ajax request.
      method = this.isNew() ? 'create' : (options.patch ? 'patch' : 'update');
      if (method === 'patch') options.attrs = attrs;
      xhr = this.sync(method, this, options);

      // Restore attributes.
      if (attrs && options.wait) this.attributes = attributes;

      return xhr;
    },

    // Destroy this model on the server if it was already persisted.
    // Optimistically removes the model from its collection, if it has one.
    // If `wait: true` is passed, waits for the server to respond before removal.
    destroy: function(options) {
      options = options ? _.clone(options) : {};
      var model = this;
      var success = options.success;

      var destroy = function() {
        model.trigger('destroy', model, model.collection, options);
      };

      options.success = function(model, resp, options) {
        if (options.wait || model.isNew()) destroy();
        if (success) success(model, resp, options);
      };

      if (this.isNew()) {
        options.success(this, null, options);
        return false;
      }

      var xhr = this.sync('delete', this, options);
      if (!options.wait) destroy();
      return xhr;
    },

    // Default URL for the model's representation on the server -- if you're
    // using Backbone's restful methods, override this to change the endpoint
    // that will be called.
    url: function() {
      var base = _.result(this, 'urlRoot') || _.result(this.collection, 'url') || urlError();
      if (this.isNew()) return base;
      return base + (base.charAt(base.length - 1) === '/' ? '' : '/') + encodeURIComponent(this.id);
    },

    // **parse** converts a response into the hash of attributes to be `set` on
    // the model. The default implementation is just to pass the response along.
    parse: function(resp, options) {
      return resp;
    },

    // Create a new model with identical attributes to this one.
    clone: function() {
      return new this.constructor(this.attributes);
    },

    // A model is new if it has never been saved to the server, and lacks an id.
    isNew: function() {
      return this.id == null;
    },

    // Check if the model is currently in a valid state.
    isValid: function(options) {
      return !this.validate || !this.validate(this.attributes, options);
    },

    // Run validation against the next complete set of model attributes,
    // returning `true` if all is well. Otherwise, fire a general
    // `"error"` event and call the error callback, if specified.
    _validate: function(attrs, options) {
      if (!options.validate || !this.validate) return true;
      attrs = _.extend({}, this.attributes, attrs);
      var error = this.validationError = this.validate(attrs, options) || null;
      if (!error) return true;
      this.trigger('invalid', this, error, options || {});
      return false;
    }

  });

  // Backbone.Collection
  // -------------------

  // Provides a standard collection class for our sets of models, ordered
  // or unordered. If a `comparator` is specified, the Collection will maintain
  // its models in sort order, as they're added and removed.
  var Collection = Backbone.Collection = function(models, options) {
    options || (options = {});
    if (options.model) this.model = options.model;
    if (options.comparator !== void 0) this.comparator = options.comparator;
    this.models = [];
    this._reset();
    this.initialize.apply(this, arguments);
    if (models) this.reset(models, _.extend({silent: true}, options));
  };

  // Define the Collection's inheritable methods.
  _.extend(Collection.prototype, Events, {

    // The default model for a collection is just a **Backbone.Model**.
    // This should be overridden in most cases.
    model: Model,

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize: function(){},

    // The JSON representation of a Collection is an array of the
    // models' attributes.
    toJSON: function(options) {
      return this.map(function(model){ return model.toJSON(options); });
    },

    // Proxy `Backbone.sync` by default.
    sync: function() {
      return Backbone.sync.apply(this, arguments);
    },

    // Add a model, or list of models to the set.
    add: function(models, options) {
      models = _.isArray(models) ? models.slice() : [models];
      options || (options = {});
      var i, l, model, attrs, existing, doSort, add, at, sort, sortAttr;
      add = [];
      at = options.at;
      sort = this.comparator && (at == null) && options.sort != false;
      sortAttr = _.isString(this.comparator) ? this.comparator : null;

      // Turn bare objects into model references, and prevent invalid models
      // from being added.
      for (i = 0, l = models.length; i < l; i++) {
        if (!(model = this._prepareModel(attrs = models[i], options))) {
          this.trigger('invalid', this, attrs, options);
          continue;
        }

        // If a duplicate is found, prevent it from being added and
        // optionally merge it into the existing model.
        if (existing = this.get(model)) {
          if (options.merge) {
            existing.set(attrs === model ? model.attributes : attrs, options);
            if (sort && !doSort && existing.hasChanged(sortAttr)) doSort = true;
          }
          continue;
        }

        // This is a new model, push it to the `add` list.
        add.push(model);

        // Listen to added models' events, and index models for lookup by
        // `id` and by `cid`.
        model.on('all', this._onModelEvent, this);
        this._byId[model.cid] = model;
        if (model.id != null) this._byId[model.id] = model;
      }

      // See if sorting is needed, update `length` and splice in new models.
      if (add.length) {
        if (sort) doSort = true;
        this.length += add.length;
        if (at != null) {
          splice.apply(this.models, [at, 0].concat(add));
        } else {
          push.apply(this.models, add);
        }
      }

      // Silently sort the collection if appropriate.
      if (doSort) this.sort({silent: true});

      if (options.silent) return this;

      // Trigger `add` events.
      for (i = 0, l = add.length; i < l; i++) {
        (model = add[i]).trigger('add', model, this, options);
      }

      // Trigger `sort` if the collection was sorted.
      if (doSort) this.trigger('sort', this, options);

      return this;
    },

    // Remove a model, or a list of models from the set.
    remove: function(models, options) {
      models = _.isArray(models) ? models.slice() : [models];
      options || (options = {});
      var i, l, index, model;
      for (i = 0, l = models.length; i < l; i++) {
        model = this.get(models[i]);
        if (!model) continue;
        delete this._byId[model.id];
        delete this._byId[model.cid];
        index = this.indexOf(model);
        this.models.splice(index, 1);
        this.length--;
        if (!options.silent) {
          options.index = index;
          model.trigger('remove', model, this, options);
        }
        this._removeReference(model);
      }
      return this;
    },

    // Add a model to the end of the collection.
    push: function(model, options) {
      model = this._prepareModel(model, options);
      this.add(model, _.extend({at: this.length}, options));
      return model;
    },

    // Remove a model from the end of the collection.
    pop: function(options) {
      var model = this.at(this.length - 1);
      this.remove(model, options);
      return model;
    },

    // Add a model to the beginning of the collection.
    unshift: function(model, options) {
      model = this._prepareModel(model, options);
      this.add(model, _.extend({at: 0}, options));
      return model;
    },

    // Remove a model from the beginning of the collection.
    shift: function(options) {
      var model = this.at(0);
      this.remove(model, options);
      return model;
    },

    // Slice out a sub-array of models from the collection.
    slice: function(begin, end) {
      return this.models.slice(begin, end);
    },

    // Get a model from the set by id.
    get: function(obj) {
      if (obj == null) return void 0;
      this._idAttr || (this._idAttr = this.model.prototype.idAttribute);
      return this._byId[obj.id || obj.cid || obj[this._idAttr] || obj];
    },

    // Get the model at the given index.
    at: function(index) {
      return this.models[index];
    },

    // Return models with matching attributes. Useful for simple cases of `filter`.
    where: function(attrs) {
      if (_.isEmpty(attrs)) return [];
      return this.filter(function(model) {
        for (var key in attrs) {
          if (attrs[key] !== model.get(key)) return false;
        }
        return true;
      });
    },

    // Force the collection to re-sort itself. You don't need to call this under
    // normal circumstances, as the set will maintain sort order as each item
    // is added.
    sort: function(options) {
      if (!this.comparator) {
        throw new Error('Cannot sort a set without a comparator');
      }
      options || (options = {});

      // Run sort based on type of `comparator`.
      if (_.isString(this.comparator) || this.comparator.length === 1) {
        this.models = this.sortBy(this.comparator, this);
      } else {
        this.models.sort(_.bind(this.comparator, this));
      }

      if (!options.silent) this.trigger('sort', this, options);
      return this;
    },

    // Pluck an attribute from each model in the collection.
    pluck: function(attr) {
      return _.invoke(this.models, 'get', attr);
    },

    // Smartly update a collection with a change set of models, adding,
    // removing, and merging as necessary.
    update: function(models, options) {
      options = _.extend({add: true, merge: true, remove: true}, options);
      if (options.parse) models = this.parse(models, options);
      var model, i, l, existing;
      var add = [], remove = [], modelMap = {};

      // Allow a single model (or no argument) to be passed.
      if (!_.isArray(models)) models = models ? [models] : [];

      // Proxy to `add` for this case, no need to iterate...
      if (options.add && !options.remove) return this.add(models, options);

      // Determine which models to add and merge, and which to remove.
      for (i = 0, l = models.length; i < l; i++) {
        model = models[i];
        existing = this.get(model);
        if (options.remove && existing) modelMap[existing.cid] = true;
        if ((options.add && !existing) || (options.merge && existing)) {
          add.push(model);
        }
      }
      if (options.remove) {
        for (i = 0, l = this.models.length; i < l; i++) {
          model = this.models[i];
          if (!modelMap[model.cid]) remove.push(model);
        }
      }

      // Remove models (if applicable) before we add and merge the rest.
      if (remove.length) this.remove(remove, options);
      if (add.length) this.add(add, options);
      return this;
    },

    // When you have more items than you want to add or remove individually,
    // you can reset the entire set with a new list of models, without firing
    // any `add` or `remove` events. Fires `reset` when finished.
    reset: function(models, options) {
      options || (options = {});
      if (options.parse) models = this.parse(models, options);
      for (var i = 0, l = this.models.length; i < l; i++) {
        this._removeReference(this.models[i]);
      }
      options.previousModels = this.models.slice();
      this._reset();
      if (models) this.add(models, _.extend({silent: true}, options));
      if (!options.silent) this.trigger('reset', this, options);
      return this;
    },

    // Fetch the default set of models for this collection, resetting the
    // collection when they arrive. If `update: true` is passed, the response
    // data will be passed through the `update` method instead of `reset`.
    fetch: function(options) {
      options = options ? _.clone(options) : {};
      if (options.parse === void 0) options.parse = true;
      var success = options.success;
      options.success = function(collection, resp, options) {
        var method = options.update ? 'update' : 'reset';
        collection[method](resp, options);
        if (success) success(collection, resp, options);
      };
      return this.sync('read', this, options);
    },

    // Create a new instance of a model in this collection. Add the model to the
    // collection immediately, unless `wait: true` is passed, in which case we
    // wait for the server to agree.
    create: function(model, options) {
      options = options ? _.clone(options) : {};
      if (!(model = this._prepareModel(model, options))) return false;
      if (!options.wait) this.add(model, options);
      var collection = this;
      var success = options.success;
      options.success = function(model, resp, options) {
        if (options.wait) collection.add(model, options);
        if (success) success(model, resp, options);
      };
      model.save(null, options);
      return model;
    },

    // **parse** converts a response into a list of models to be added to the
    // collection. The default implementation is just to pass it through.
    parse: function(resp, options) {
      return resp;
    },

    // Create a new collection with an identical list of models as this one.
    clone: function() {
      return new this.constructor(this.models);
    },

    // Reset all internal state. Called when the collection is reset.
    _reset: function() {
      this.length = 0;
      this.models.length = 0;
      this._byId  = {};
    },

    // Prepare a model or hash of attributes to be added to this collection.
    _prepareModel: function(attrs, options) {
      if (attrs instanceof Model) {
        if (!attrs.collection) attrs.collection = this;
        return attrs;
      }
      options || (options = {});
      options.collection = this;
      var model = new this.model(attrs, options);
      if (!model._validate(attrs, options)) return false;
      return model;
    },

    // Internal method to remove a model's ties to a collection.
    _removeReference: function(model) {
      if (this === model.collection) delete model.collection;
      model.off('all', this._onModelEvent, this);
    },

    // Internal method called every time a model in the set fires an event.
    // Sets need to update their indexes when models change ids. All other
    // events simply proxy through. "add" and "remove" events that originate
    // in other collections are ignored.
    _onModelEvent: function(event, model, collection, options) {
      if ((event === 'add' || event === 'remove') && collection !== this) return;
      if (event === 'destroy') this.remove(model, options);
      if (model && event === 'change:' + model.idAttribute) {
        delete this._byId[model.previous(model.idAttribute)];
        if (model.id != null) this._byId[model.id] = model;
      }
      this.trigger.apply(this, arguments);
    },

    sortedIndex: function (model, value, context) {
      value || (value = this.comparator);
      var iterator = _.isFunction(value) ? value : function(model) {
        return model.get(value);
      };
      return _.sortedIndex(this.models, model, iterator, context);
    }

  });

  // Underscore methods that we want to implement on the Collection.
  var methods = ['forEach', 'each', 'map', 'collect', 'reduce', 'foldl',
    'inject', 'reduceRight', 'foldr', 'find', 'detect', 'filter', 'select',
    'reject', 'every', 'all', 'some', 'any', 'include', 'contains', 'invoke',
    'max', 'min', 'toArray', 'size', 'first', 'head', 'take', 'initial', 'rest',
    'tail', 'drop', 'last', 'without', 'indexOf', 'shuffle', 'lastIndexOf',
    'isEmpty', 'chain'];

  // Mix in each Underscore method as a proxy to `Collection#models`.
  _.each(methods, function(method) {
    Collection.prototype[method] = function() {
      var args = slice.call(arguments);
      args.unshift(this.models);
      return _[method].apply(_, args);
    };
  });

  // Underscore methods that take a property name as an argument.
  var attributeMethods = ['groupBy', 'countBy', 'sortBy'];

  // Use attributes instead of properties.
  _.each(attributeMethods, function(method) {
    Collection.prototype[method] = function(value, context) {
      var iterator = _.isFunction(value) ? value : function(model) {
        return model.get(value);
      };
      return _[method](this.models, iterator, context);
    };
  });

  // Backbone.Router
  // ---------------

  // Routers map faux-URLs to actions, and fire events when routes are
  // matched. Creating a new one sets its `routes` hash, if not set statically.
  var Router = Backbone.Router = function(options) {
    options || (options = {});
    if (options.routes) this.routes = options.routes;
    this._bindRoutes();
    this.initialize.apply(this, arguments);
  };

  // Cached regular expressions for matching named param parts and splatted
  // parts of route strings.
  var optionalParam = /\((.*?)\)/g;
  var namedParam    = /(\(\?)?:\w+/g;
  var splatParam    = /\*\w+/g;
  var escapeRegExp  = /[\-{}\[\]+?.,\\\^$|#\s]/g;

  // Set up all inheritable **Backbone.Router** properties and methods.
  _.extend(Router.prototype, Events, {

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize: function(){},

    // Manually bind a single named route to a callback. For example:
    //
    //     this.route('search/:query/p:num', 'search', function(query, num) {
    //       ...
    //     });
    //
    route: function(route, name, callback) {
      if (!_.isRegExp(route)) route = this._routeToRegExp(route);
      if (!callback) callback = this[name];
      Backbone.history.route(route, _.bind(function(fragment) {
        var args = this._extractParameters(route, fragment);
        callback && callback.apply(this, args);
        this.trigger.apply(this, ['route:' + name].concat(args));
        this.trigger('route', name, args);
        Backbone.history.trigger('route', this, name, args);
      }, this));
      return this;
    },

    // Simple proxy to `Backbone.history` to save a fragment into the history.
    navigate: function(fragment, options) {
      Backbone.history.navigate(fragment, options);
      return this;
    },

    // Bind all defined routes to `Backbone.history`. We have to reverse the
    // order of the routes here to support behavior where the most general
    // routes can be defined at the bottom of the route map.
    _bindRoutes: function() {
      if (!this.routes) return;
      var route, routes = _.keys(this.routes);
      while ((route = routes.pop()) != null) {
        this.route(route, this.routes[route]);
      }
    },

    // Convert a route string into a regular expression, suitable for matching
    // against the current location hash.
    _routeToRegExp: function(route) {
      route = route.replace(escapeRegExp, '\\$&')
                   .replace(optionalParam, '(?:$1)?')
                   .replace(namedParam, function(match, optional){
                     return optional ? match : '([^\/]+)';
                   })
                   .replace(splatParam, '(.*?)');
      return new RegExp('^' + route + '$');
    },

    // Given a route, and a URL fragment that it matches, return the array of
    // extracted parameters.
    _extractParameters: function(route, fragment) {
      return route.exec(fragment).slice(1);
    }

  });

  // Backbone.History
  // ----------------

  // Handles cross-browser history management, based on URL fragments. If the
  // browser does not support `onhashchange`, falls back to polling.
  var History = Backbone.History = function() {
    this.handlers = [];
    _.bindAll(this, 'checkUrl');

    // Ensure that `History` can be used outside of the browser.
    if (typeof window !== 'undefined') {
      this.location = window.location;
      this.history = window.history;
    }
  };

  // Cached regex for stripping a leading hash/slash and trailing space.
  var routeStripper = /^[#\/]|\s+$/g;

  // Cached regex for stripping leading and trailing slashes.
  var rootStripper = /^\/+|\/+$/g;

  // Cached regex for detecting MSIE.
  var isExplorer = /msie [\w.]+/;

  // Cached regex for removing a trailing slash.
  var trailingSlash = /\/$/;

  // Has the history handling already been started?
  History.started = false;

  // Set up all inheritable **Backbone.History** properties and methods.
  _.extend(History.prototype, Events, {

    // The default interval to poll for hash changes, if necessary, is
    // twenty times a second.
    interval: 50,

    // Gets the true hash value. Cannot use location.hash directly due to bug
    // in Firefox where location.hash will always be decoded.
    getHash: function(window) {
      var match = (window || this).location.href.match(/#(.*)$/);
      return match ? match[1] : '';
    },

    // Get the cross-browser normalized URL fragment, either from the URL,
    // the hash, or the override.
    getFragment: function(fragment, forcePushState) {
      if (fragment == null) {
        if (this._hasPushState || !this._wantsHashChange || forcePushState) {
          fragment = this.location.pathname;
          var root = this.root.replace(trailingSlash, '');
          if (!fragment.indexOf(root)) fragment = fragment.substr(root.length);
        } else {
          fragment = this.getHash();
        }
      }
      return fragment.replace(routeStripper, '');
    },

    // Start the hash change handling, returning `true` if the current URL matches
    // an existing route, and `false` otherwise.
    start: function(options) {
      if (History.started) throw new Error("Backbone.history has already been started");
      History.started = true;

      // Figure out the initial configuration. Do we need an iframe?
      // Is pushState desired ... is it available?
      this.options          = _.extend({}, {root: '/'}, this.options, options);
      this.root             = this.options.root;
      this._wantsHashChange = this.options.hashChange !== false;
      this._wantsPushState  = !!this.options.pushState;
      this._hasPushState    = !!(this.options.pushState && this.history && this.history.pushState);
      var fragment          = this.getFragment();
      var docMode           = document.documentMode;
      var oldIE             = (isExplorer.exec(navigator.userAgent.toLowerCase()) && (!docMode || docMode <= 7));

      // Normalize root to always include a leading and trailing slash.
      this.root = ('/' + this.root + '/').replace(rootStripper, '/');

      if (oldIE && this._wantsHashChange) {
        this.iframe = Backbone.$('<iframe src="javascript:0" tabindex="-1" />').hide().appendTo('body')[0].contentWindow;
        this.navigate(fragment);
      }

      // Depending on whether we're using pushState or hashes, and whether
      // 'onhashchange' is supported, determine how we check the URL state.
      if (this._hasPushState) {
        Backbone.$(window).on('popstate', this.checkUrl);
      } else if (this._wantsHashChange && ('onhashchange' in window) && !oldIE) {
        Backbone.$(window).on('hashchange', this.checkUrl);
      } else if (this._wantsHashChange) {
        this._checkUrlInterval = setInterval(this.checkUrl, this.interval);
      }

      // Determine if we need to change the base url, for a pushState link
      // opened by a non-pushState browser.
      this.fragment = fragment;
      var loc = this.location;
      var atRoot = loc.pathname.replace(/[^\/]$/, '$&/') === this.root;

      // If we've started off with a route from a `pushState`-enabled browser,
      // but we're currently in a browser that doesn't support it...
      if (this._wantsHashChange && this._wantsPushState && !this._hasPushState && !atRoot) {
        this.fragment = this.getFragment(null, true);
        this.location.replace(this.root + this.location.search + '#' + this.fragment);
        // Return immediately as browser will do redirect to new url
        return true;

      // Or if we've started out with a hash-based route, but we're currently
      // in a browser where it could be `pushState`-based instead...
      } else if (this._wantsPushState && this._hasPushState && atRoot && loc.hash) {
        this.fragment = this.getHash().replace(routeStripper, '');
        this.history.replaceState({}, document.title, this.root + this.fragment + loc.search);
      }

      if (!this.options.silent) return this.loadUrl();
    },

    // Disable Backbone.history, perhaps temporarily. Not useful in a real app,
    // but possibly useful for unit testing Routers.
    stop: function() {
      Backbone.$(window).off('popstate', this.checkUrl).off('hashchange', this.checkUrl);
      clearInterval(this._checkUrlInterval);
      History.started = false;
    },

    // Add a route to be tested when the fragment changes. Routes added later
    // may override previous routes.
    route: function(route, callback) {
      this.handlers.unshift({route: route, callback: callback});
    },

    // Checks the current URL to see if it has changed, and if it has,
    // calls `loadUrl`, normalizing across the hidden iframe.
    checkUrl: function(e) {
      var current = this.getFragment();
      if (current === this.fragment && this.iframe) {
        current = this.getFragment(this.getHash(this.iframe));
      }
      if (current === this.fragment) return false;
      if (this.iframe) this.navigate(current);
      this.loadUrl() || this.loadUrl(this.getHash());
    },

    // Attempt to load the current URL fragment. If a route succeeds with a
    // match, returns `true`. If no defined routes matches the fragment,
    // returns `false`.
    loadUrl: function(fragmentOverride) {
      var fragment = this.fragment = this.getFragment(fragmentOverride);
      var matched = _.any(this.handlers, function(handler) {
        if (handler.route.test(fragment)) {
          handler.callback(fragment);
          return true;
        }
      });
      return matched;
    },

    // Save a fragment into the hash history, or replace the URL state if the
    // 'replace' option is passed. You are responsible for properly URL-encoding
    // the fragment in advance.
    //
    // The options object can contain `trigger: true` if you wish to have the
    // route callback be fired (not usually desirable), or `replace: true`, if
    // you wish to modify the current URL without adding an entry to the history.
    navigate: function(fragment, options) {
      if (!History.started) return false;
      if (!options || options === true) options = {trigger: options};
      fragment = this.getFragment(fragment || '');
      if (this.fragment === fragment) return;
      this.fragment = fragment;
      var url = this.root + fragment;

      // If pushState is available, we use it to set the fragment as a real URL.
      if (this._hasPushState) {
        this.history[options.replace ? 'replaceState' : 'pushState']({}, document.title, url);

      // If hash changes haven't been explicitly disabled, update the hash
      // fragment to store history.
      } else if (this._wantsHashChange) {
        this._updateHash(this.location, fragment, options.replace);
        if (this.iframe && (fragment !== this.getFragment(this.getHash(this.iframe)))) {
          // Opening and closing the iframe tricks IE7 and earlier to push a
          // history entry on hash-tag change.  When replace is true, we don't
          // want this.
          if(!options.replace) this.iframe.document.open().close();
          this._updateHash(this.iframe.location, fragment, options.replace);
        }

      // If you've told us that you explicitly don't want fallback hashchange-
      // based history, then `navigate` becomes a page refresh.
      } else {
        return this.location.assign(url);
      }
      if (options.trigger) this.loadUrl(fragment);
    },

    // Update the hash location, either replacing the current entry, or adding
    // a new one to the browser history.
    _updateHash: function(location, fragment, replace) {
      if (replace) {
        var href = location.href.replace(/(javascript:|#).*$/, '');
        location.replace(href + '#' + fragment);
      } else {
        // Some browsers require that `hash` contains a leading #.
        location.hash = '#' + fragment;
      }
    }

  });

  // Create the default Backbone.history.
  Backbone.history = new History;

  // Backbone.View
  // -------------

  // Creating a Backbone.View creates its initial element outside of the DOM,
  // if an existing element is not provided...
  var View = Backbone.View = function(options) {
    this.cid = _.uniqueId('view');
    this._configure(options || {});
    this._ensureElement();
    this.initialize.apply(this, arguments);
    this.delegateEvents();
  };

  // Cached regex to split keys for `delegate`.
  var delegateEventSplitter = /^(\S+)\s*(.*)$/;

  // List of view options to be merged as properties.
  var viewOptions = ['model', 'collection', 'el', 'id', 'attributes', 'className', 'tagName', 'events'];

  // Set up all inheritable **Backbone.View** properties and methods.
  _.extend(View.prototype, Events, {

    // The default `tagName` of a View's element is `"div"`.
    tagName: 'div',

    // jQuery delegate for element lookup, scoped to DOM elements within the
    // current view. This should be prefered to global lookups where possible.
    $: function(selector) {
      return this.$el.find(selector);
    },

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize: function(){},

    // **render** is the core function that your view should override, in order
    // to populate its element (`this.el`), with the appropriate HTML. The
    // convention is for **render** to always return `this`.
    render: function() {
      return this;
    },

    // Remove this view by taking the element out of the DOM, and removing any
    // applicable Backbone.Events listeners.
    remove: function() {
      this.$el.remove();
      this.stopListening();
      return this;
    },

    // Change the view's element (`this.el` property), including event
    // re-delegation.
    setElement: function(element, delegate) {
      if (this.$el) this.undelegateEvents();
      this.$el = element instanceof Backbone.$ ? element : Backbone.$(element);
      this.el = this.$el[0];
      if (delegate !== false) this.delegateEvents();
      return this;
    },

    // Set callbacks, where `this.events` is a hash of
    //
    // *{"event selector": "callback"}*
    //
    //     {
    //       'mousedown .title':  'edit',
    //       'click .button':     'save'
    //       'click .open':       function(e) { ... }
    //     }
    //
    // pairs. Callbacks will be bound to the view, with `this` set properly.
    // Uses event delegation for efficiency.
    // Omitting the selector binds the event to `this.el`.
    // This only works for delegate-able events: not `focus`, `blur`, and
    // not `change`, `submit`, and `reset` in Internet Explorer.
    delegateEvents: function(events) {
      if (!(events || (events = _.result(this, 'events')))) return;
      this.undelegateEvents();
      for (var key in events) {
        var method = events[key];
        if (!_.isFunction(method)) method = this[events[key]];
        if (!method) throw new Error('Method "' + events[key] + '" does not exist');
        var match = key.match(delegateEventSplitter);
        var eventName = match[1], selector = match[2];
        method = _.bind(method, this);
        eventName += '.delegateEvents' + this.cid;
        if (selector === '') {
          this.$el.on(eventName, method);
        } else {
          this.$el.on(eventName, selector, method);
        }
      }
    },

    // Clears all callbacks previously bound to the view with `delegateEvents`.
    // You usually don't need to use this, but may wish to if you have multiple
    // Backbone views attached to the same DOM element.
    undelegateEvents: function() {
      this.$el.off('.delegateEvents' + this.cid);
    },

    // Performs the initial configuration of a View with a set of options.
    // Keys with special meaning *(model, collection, id, className)*, are
    // attached directly to the view.
    _configure: function(options) {
      if (this.options) options = _.extend({}, _.result(this, 'options'), options);
      _.extend(this, _.pick(options, viewOptions));
      this.options = options;
    },

    // Ensure that the View has a DOM element to render into.
    // If `this.el` is a string, pass it through `$()`, take the first
    // matching element, and re-assign it to `el`. Otherwise, create
    // an element from the `id`, `className` and `tagName` properties.
    _ensureElement: function() {
      if (!this.el) {
        var attrs = _.extend({}, _.result(this, 'attributes'));
        if (this.id) attrs.id = _.result(this, 'id');
        if (this.className) attrs['class'] = _.result(this, 'className');
        var $el = Backbone.$('<' + _.result(this, 'tagName') + '>').attr(attrs);
        this.setElement($el, false);
      } else {
        this.setElement(_.result(this, 'el'), false);
      }
    }

  });

  // Backbone.sync
  // -------------

  // Map from CRUD to HTTP for our default `Backbone.sync` implementation.
  var methodMap = {
    'create': 'POST',
    'update': 'PUT',
    'patch':  'PATCH',
    'delete': 'DELETE',
    'read':   'GET'
  };

  // Override this function to change the manner in which Backbone persists
  // models to the server. You will be passed the type of request, and the
  // model in question. By default, makes a RESTful Ajax request
  // to the model's `url()`. Some possible customizations could be:
  //
  // * Use `setTimeout` to batch rapid-fire updates into a single request.
  // * Send up the models as XML instead of JSON.
  // * Persist models via WebSockets instead of Ajax.
  //
  // Turn on `Backbone.emulateHTTP` in order to send `PUT` and `DELETE` requests
  // as `POST`, with a `_method` parameter containing the true HTTP method,
  // as well as all requests with the body as `application/x-www-form-urlencoded`
  // instead of `application/json` with the model in a param named `model`.
  // Useful when interfacing with server-side languages like **PHP** that make
  // it difficult to read the body of `PUT` requests.
  Backbone.sync = function(method, model, options) {
    var type = methodMap[method];

    // Default options, unless specified.
    _.defaults(options || (options = {}), {
      emulateHTTP: Backbone.emulateHTTP,
      emulateJSON: Backbone.emulateJSON
    });

    // Default JSON-request options.
    var params = {type: type, dataType: 'json'};

    // Ensure that we have a URL.
    if (!options.url) {
      params.url = _.result(model, 'url') || urlError();
    }
    // Ensure that we have the appropriate request data.
    if (options.data == null && model && (method === 'create' || method === 'update' || method === 'patch')) {
      params.contentType = 'application/json';
      params.data = JSON.stringify(options.attrs || model.toJSON(options));
    }

    // For older servers, emulate JSON by encoding the request into an HTML-form.
    if (options.emulateJSON) {
      params.contentType = 'application/x-www-form-urlencoded';
      params.data = params.data ? {model: params.data} : {};
    }

    // For older servers, emulate HTTP by mimicking the HTTP method with `_method`
    // And an `X-HTTP-Method-Override` header.
    if (options.emulateHTTP && (type === 'PUT' || type === 'DELETE' || type === 'PATCH')) {
      params.type = 'POST';
      if (options.emulateJSON) params.data._method = type;
      var beforeSend = options.beforeSend;
      options.beforeSend = function(xhr) {
        xhr.setRequestHeader('X-HTTP-Method-Override', type);
        if (beforeSend) return beforeSend.apply(this, arguments);
      };
    }

    // Don't process data on a non-GET request.
    if (params.type !== 'GET' && !options.emulateJSON) {
      params.processData = false;
    }

    var success = options.success;
    options.success = function(resp) {
      if (success) success(model, resp, options);
      model.trigger('sync', model, resp, options);
    };

    var error = options.error;
    options.error = function(xhr) {
      if (error) error(model, xhr, options);
      model.trigger('error', model, xhr, options);
    };

    // Make the request, allowing the user to override any Ajax options.
    var xhr = options.xhr = Backbone.ajax(_.extend(params, options));
    model.trigger('request', model, xhr, options);
    return xhr;
  };

  // Set the default implementation of `Backbone.ajax` to proxy through to `$`.
  Backbone.ajax = function() {
    return Backbone.$.ajax.apply(Backbone.$, arguments);
  };

  // Helpers
  // -------

  // Helper function to correctly set up the prototype chain, for subclasses.
  // Similar to `goog.inherits`, but uses a hash of prototype properties and
  // class properties to be extended.
  var extend = function(protoProps, staticProps) {
    var parent = this;
    var child;

    // The constructor function for the new subclass is either defined by you
    // (the "constructor" property in your `extend` definition), or defaulted
    // by us to simply call the parent's constructor.
    if (protoProps && _.has(protoProps, 'constructor')) {
      child = protoProps.constructor;
    } else {
      child = function(){ return parent.apply(this, arguments); };
    }

    // Add static properties to the constructor function, if supplied.
    _.extend(child, parent, staticProps);

    // Set the prototype chain to inherit from `parent`, without calling
    // `parent`'s constructor function.
    var Surrogate = function(){ this.constructor = child; };
    Surrogate.prototype = parent.prototype;
    child.prototype = new Surrogate;

    // Add prototype properties (instance properties) to the subclass,
    // if supplied.
    if (protoProps) _.extend(child.prototype, protoProps);

    // Set a convenience property in case the parent's prototype is needed
    // later.
    child.__super__ = parent.prototype;

    return child;
  };

  // Set up inheritance for the model, collection, router, view and history.
  Model.extend = Collection.extend = Router.extend = View.extend = History.extend = extend;

  // Throw an error when a URL is needed, and none is supplied.
  var urlError = function() {
    throw new Error('A "url" property or function must be specified');
  };

}).call(this);

// Copyright 2012 Mauricio Santos. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
//
// Some documentation is borrowed from the official Java API
// as it serves the same porpose.

/**
 * @namespace Top level namespace for Buckets, a JavaScript data structure library.
 */
var buckets = {};

/**
 * Default function to compare element order.
 * @function
 * @private
 */
buckets.defaultCompare = function(a, b) {
    if (a < b) {
        return - 1;
    } else if (a === b) {
        return 0;
    } else {
        return 1;
    }
};
/**
 * Default function to test equality.
 * @function
 * @private
 */
buckets.defaultEquals = function(a, b) {
    return a === b;
};

/**
 * Default function to convert an object to a string.
 * @function
 * @private
 */
buckets.defaultToString = function(item) {
    if (item === null) {
        return 'BUCKETS_NULL';
    } else if (buckets.isUndefined(item)) {
        return 'BUCKETS_UNDEFINED';
    } else if (buckets.isString(item)) {
        return item;
    } else {
        return item.toString();
    }
};

/**
 * Checks if the given argument is a function.
 * @function
 * @private
 */
buckets.isFunction = function(func) {
    return (typeof func) === 'function';
};

/**
 * Checks if the given argument is undefined.
 * @function
 * @private
 */
buckets.isUndefined = function(obj) {
    return (typeof obj) === 'undefined';
};

/**
 * Checks if the given argument is a string.
 * @function
 * @private
 */
buckets.isString = function(obj) {
    return Object.prototype.toString.call(obj) === '[object String]';
};

/**
 * Reverses a compare function.
 * @function
 * @private
 */
buckets.reverseCompareFunction = function(compareFunction) {
    if (!buckets.isFunction(compareFunction)) {
        return function(a, b) {
            if (a < b) {
                return 1;
            } else if (a === b) {
                return 0;
            } else {
                return - 1;
            }
        };
    } else {
        return function(d, v) {
            return compareFunction(d, v) * -1;
        };
    }
};

/**
 * Returns an equal function given a compare function.
 * @function
 * @private
 */
buckets.compareToEquals = function(compareFunction) {
    return function(a, b) {
        return compareFunction(a, b) === 0;
    };
};

/**
 * @namespace Contains various functions for manipulating arrays.
 */
buckets.arrays = {};

/**
 * Returns the position of the first occurrence of the specified item
 * within the specified array.
 * @param {*} array the array in which to search the element.
 * @param {Object} item the element to search.
 * @param {function(Object,Object):boolean=} equalsFunction optional function used to 
 * check equality between 2 elements.
 * @return {number} the position of the first occurrence of the specified element
 * within the specified array, or -1 if not found.
 */
buckets.arrays.indexOf = function(array, item, equalsFunction) {
    var equals = equalsFunction || buckets.defaultEquals;
    var length = array.length;
    for (var i = 0; i < length; i++) {
        if (equals(array[i], item)) {
            return i;
        }
    }
    return - 1;
};

/**
 * Returns the position of the last occurrence of the specified element
 * within the specified array.
 * @param {*} array the array in which to search the element.
 * @param {Object} item the element to search.
 * @param {function(Object,Object):boolean=} equalsFunction optional function used to 
 * check equality between 2 elements.
 * @return {number} the position of the last occurrence of the specified element
 * within the specified array or -1 if not found.
 */
buckets.arrays.lastIndexOf = function(array, item, equalsFunction) {
    var equals = equalsFunction || buckets.defaultEquals;
    var length = array.length;
    for (var i = length - 1; i >= 0; i--) {
        if (equals(array[i], item)) {
            return i;
        }
    }
    return - 1;
};

/**
 * Returns true if the specified array contains the specified element.
 * @param {*} array the array in which to search the element.
 * @param {Object} item the element to search.
 * @param {function(Object,Object):boolean=} equalsFunction optional function to 
 * check equality between 2 elements.
 * @return {boolean} true if the specified array contains the specified element.
 */
buckets.arrays.contains = function(array, item, equalsFunction) {
    return buckets.arrays.indexOf(array, item, equalsFunction) >= 0;
};


/**
 * Removes the first ocurrence of the specified element from the specified array.
 * @param {*} array the array in which to search element.
 * @param {Object} item the element to search.
 * @param {function(Object,Object):boolean=} equalsFunction optional function to 
 * check equality between 2 elements.
 * @return {boolean} true if the array changed after this call.
 */
buckets.arrays.remove = function(array, item, equalsFunction) {
    var index = buckets.arrays.indexOf(array, item, equalsFunction);
    if (index < 0) {
        return false;
    }
    array.splice(index, 1);
    return true;
};

/**
 * Returns the number of elements in the specified array equal
 * to the specified object.
 * @param {Array} array the array in which to determine the frequency of the element.
 * @param {Object} item the element whose frequency is to be determined.
 * @param {function(Object,Object):boolean=} equalsFunction optional function used to 
 * check equality between 2 elements.
 * @return {number} the number of elements in the specified array 
 * equal to the specified object.
 */
buckets.arrays.frequency = function(array, item, equalsFunction) {
    var equals = equalsFunction || buckets.defaultEquals;
    var length = array.length;
    var freq = 0;
    for (var i = 0; i < length; i++) {
        if (equals(array[i], item)) {
            freq++;
        }
    }
    return freq;
};

/**
 * Returns true if the two specified arrays are equal to one another.
 * Two arrays are considered equal if both arrays contain the same number
 * of elements, and all corresponding pairs of elements in the two 
 * arrays are equal and are in the same order. 
 * @param {Array} array1 one array to be tested for equality.
 * @param {Array} array2 the other array to be tested for equality.
 * @param {function(Object,Object):boolean=} equalsFunction optional function used to 
 * check equality between elemements in the arrays.
 * @return {boolean} true if the two arrays are equal
 */
buckets.arrays.equals = function(array1, array2, equalsFunction) {
    var equals = equalsFunction || buckets.defaultEquals;

    if (array1.length !== array2.length) {
        return false;
    }
    var length = array1.length;
    for (var i = 0; i < length; i++) {
        if (!equals(array1[i], array2[i])) {
            return false;
        }
    }
    return true;
};

/**
 * Returns shallow a copy of the specified array.
 * @param {*} array the array to copy.
 * @return {Array} a copy of the specified array
 */
buckets.arrays.copy = function(array) {
    return array.concat();
};

/**
 * Swaps the elements at the specified positions in the specified array.
 * @param {Array} array The array in which to swap elements.
 * @param {number} i the index of one element to be swapped.
 * @param {number} j the index of the other element to be swapped.
 * @return {boolean} true if the array is defined and the indexes are valid.
 */
buckets.arrays.swap = function(array, i, j) {
    if (i < 0 || i >= array.length || j < 0 || j >= array.length) {
        return false;
    }
    var temp = array[i];
    array[i] = array[j];
    array[j] = temp;
    return true;
};

/**
 * Executes the provided function once for each element present in this array 
 * starting from index 0 to length - 1.
 * @param {Array} array The array in which to iterate.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.arrays.forEach = function(array, callback) {
   var lenght = array.length;
   for (var i=0; i < lenght; i++) {
   		if(callback(array[i])===false){
			return;
		}
   }	 
};

/**
 * Creates an empty Linked List.
 * @class A linked list is a data structure consisting of a group of nodes
 * which together represent a sequence.
 * @constructor
 */
buckets.LinkedList = function() {

    /**
     * First node in the list
     * @type {Object}
     * @private
     */
    this.firstNode = null;

    /**
     * Last node in the list
     * @type {Object}
     * @private
     */
    this.lastNode = null;

    /**
     * Number of elements in the list
     * @type {number}
     * @private
     */
    this.nElements = 0;
};


/**
 * Adds an element to this list.
 * @param {Object} item element to be added.
 * @param {number=} index optional index to add the element. If no index is specified
 * the element is added to the end of this list.
 * @return {boolean} true if the element was added or false if the index is invalid
 * or if the element is undefined.
 */
buckets.LinkedList.prototype.add = function(item, index) {

    if (buckets.isUndefined(index)) {
        index = this.nElements;
    }
    if (index < 0 || index > this.nElements || buckets.isUndefined(item)) {
        return false;
    }
    var newNode = this.createNode(item);
    if (this.nElements === 0) {
        // First node in the list.
        this.firstNode = newNode;
        this.lastNode = newNode;
    } else if (index === this.nElements) {
        // Insert at the end.
        this.lastNode.next = newNode;
        this.lastNode = newNode;
    } else if (index === 0) {
        // Change first node.
        newNode.next = this.firstNode;
        this.firstNode = newNode;
    } else {
        var prev = this.nodeAtIndex(index - 1);
        newNode.next = prev.next;
        prev.next = newNode;
    }
    this.nElements++;
    return true;
};


/**
 * Returns the first element in this list.
 * @return {*} the first element of the list or undefined if the list is
 * empty.
 */
buckets.LinkedList.prototype.first = function() {

    if (this.firstNode !== null) {
        return this.firstNode.element;
    }
    return undefined;
};

/**
 * Returns the last element in this list.
 * @return {*} the last element in the list or undefined if the list is
 * empty.
 */
buckets.LinkedList.prototype.last = function() {

    if (this.lastNode !== null) {
        return this.lastNode.element;
    }
    return undefined;
};


/**
 * Returns the element at the specified position in this list.
 * @param {number} index desired index.
 * @return {*} the element at the given index or undefined if the index is
 * out of bounds.
 */
buckets.LinkedList.prototype.elementAtIndex = function(index) {

    var node = this.nodeAtIndex(index);
    if (node === null) {
        return undefined;
    }
    return node.element;
};

/**
 * Returns the index in this list of the first occurrence of the
 * specified element, or -1 if the List does not contain this element.
 * <p>If the elements inside this list are
 * not comparable with the === operator a custom equals function should be
 * provided to perform searches, the function must receive two arguments and
 * return true if they are equal, false otherwise. Example:</p>
 *
 * <pre>
 * var petsAreEqualByName = function(pet1, pet2) {
 *  return pet1.name === pet2.name;
 * }
 * </pre>
 * @param {Object} item element to search for.
 * @param {function(Object,Object):boolean=} equalsFunction Optional
 * function used to check if two elements are equal.
 * @return {number} the index in this list of the first occurrence
 * of the specified element, or -1 if this list does not contain the
 * element.
 */
buckets.LinkedList.prototype.indexOf = function(item, equalsFunction) {

    var equalsF = equalsFunction || buckets.defaultEquals;
    if (buckets.isUndefined(item)) {
        return - 1;
    }
    var currentNode = this.firstNode;
    var index = 0;
    while (currentNode !== null) {
        if (equalsF(currentNode.element, item)) {
            return index;
        }
        index++;
        currentNode = currentNode.next;
    }
    return - 1;
};

/**
 * Returns true if this list contains the specified element.
 * <p>If the elements inside the list are
 * not comparable with the === operator a custom equals function should be
 * provided to perform searches, the function must receive two arguments and
 * return true if they are equal, false otherwise. Example:</p>
 *
 * <pre>
 * var petsAreEqualByName = function(pet1, pet2) {
 *  return pet1.name === pet2.name;
 * }
 * </pre>
 * @param {Object} item element to search for.
 * @param {function(Object,Object):boolean=} equalsFunction Optional
 * function used to check if two elements are equal.
 * @return {boolean} true if this list contains the specified element, false
 * otherwise.
 */
buckets.LinkedList.prototype.contains = function(item, equalsFunction) {
    return (this.indexOf(item, equalsFunction) >= 0);
};

/**
 * Removes the first occurrence of the specified element in this list.
 * <p>If the elements inside the list are
 * not comparable with the === operator a custom equals function should be
 * provided to perform searches, the function must receive two arguments and
 * return true if they are equal, false otherwise. Example:</p>
 *
 * <pre>
 * var petsAreEqualByName = function(pet1, pet2) {
 *  return pet1.name === pet2.name;
 * }
 * </pre>
 * @param {Object} item element to be removed from this list, if present.
 * @return {boolean} true if the list contained the specified element.
 */
buckets.LinkedList.prototype.remove = function(item, equalsFunction) {
    var equalsF = equalsFunction || buckets.defaultEquals;
    if (this.nElements < 1 || buckets.isUndefined(item)) {
        return false;
    }
    var previous = null;
    var currentNode = this.firstNode;
    while (currentNode !== null) {

        if (equalsF(currentNode.element, item)) {

            if (currentNode === this.firstNode) {
                this.firstNode = this.firstNode.next;
                if (currentNode === this.lastNode) {
                    this.lastNode = null;
                }
            } else if (currentNode === this.lastNode) {
                this.lastNode = previous;
                previous.next = currentNode.next;
                currentNode.next = null;
            } else {
                previous.next = currentNode.next;
                currentNode.next = null;
            }
            this.nElements--;
            return true;
        }
        previous = currentNode;
        currentNode = currentNode.next;
    }
    return false;
};

/**
 * Removes all of the elements from this list.
 */
buckets.LinkedList.prototype.clear = function() {
    this.firstNode = null;
    this.lastNode = null;
    this.nElements = 0;
};

/**
 * Returns true if this list is equal to the given list.
 * Two lists are equal if they have the same elements in the same order.
 * @param {buckets.LinkedList} other the other list.
 * @param {function(Object,Object):boolean=} equalsFunction optional
 * function used to check if two elements are equal. If the elements in the lists
 * are custom objects you should provide a function, otherwise the
 * the === operator is used to check equality between elements.
 * @return {boolean} true if this list is equal to the given list.
 */
buckets.LinkedList.prototype.equals = function(other, equalsFunction) {
    var eqF = equalsFunction || buckets.defaultEquals;
    if (! (other instanceof buckets.LinkedList)) {
        return false;
    }
    if (this.size() !== other.size()) {
        return false;
    }
    return this.equalsAux(this.firstNode, other.firstNode, eqF);
};

/**
 * @private
 */
buckets.LinkedList.prototype.equalsAux = function(n1, n2, eqF) {
    while (n1 !== null) {
        if (!eqF(n1.element, n2.element)) {
            return false;
        }
        n1 = n1.next;
        n2 = n2.next;
    }
    return true;
};

/**
 * Removes the element at the specified position in this list.
 * @param {number} index given index.
 * @return {*} removed element or undefined if the index is out of bounds.
 */
buckets.LinkedList.prototype.removeElementAtIndex = function(index) {

    if (index < 0 || index >= this.nElements) {
        return undefined;
    }
    var element;
    if (this.nElements === 1) {
        //First node in the list.
        element = this.firstNode.element;
        this.firstNode = null;
        this.lastNode = null;
    } else {
        var previous = this.nodeAtIndex(index - 1);
        if (previous === null) {
            element = this.firstNode.element;
            this.firstNode = this.firstNode.next;
        } else if (previous.next === this.lastNode) {
            element = this.lastNode.element;
            this.lastNode = previous;
        }
        if (previous !== null) {
            element = previous.next.element;
            previous.next = previous.next.next;
        }
    }
    this.nElements--;
    return element;
};

/**
 * Executes the provided function once for each element present in this list in order.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.LinkedList.prototype.forEach = function(callback) {
    var currentNode = this.firstNode;
    while (currentNode !== null) {
        if (callback(currentNode.element) === false) {
            break;
        }
        currentNode = currentNode.next;
    }
};

/**
 * Reverses the order of the elements in this linked list (makes the last 
 * element first, and the first element last).
 */
buckets.LinkedList.prototype.reverse = function() {
    var previous = null;
    var current = this.firstNode;
    var temp = null;
    while (current !== null) {
        temp = current.next;
        current.next = previous;
        previous = current;
        current = temp;
    }
    temp = this.firstNode;
    this.firstNode = this.lastNode;
    this.lastNode = temp;
};


/**
 * Returns an array containing all of the elements in this list in proper
 * sequence.
 * @return {Array.<*>} an array containing all of the elements in this list,
 * in proper sequence.
 */
buckets.LinkedList.prototype.toArray = function() {
    var array = [];
    var currentNode = this.firstNode;
    while (currentNode !== null) {
        array.push(currentNode.element);
        currentNode = currentNode.next;
    }
    return array;
};
/**
 * Returns the number of elements in this list.
 * @return {number} the number of elements in this list.
 */
buckets.LinkedList.prototype.size = function() {
    return this.nElements;
};

/**
 * Returns true if this list contains no elements.
 * @return {boolean} true if this list contains no elements.
 */
buckets.LinkedList.prototype.isEmpty = function() {
    return this.nElements <= 0;
};

/**
 * @private
 */
buckets.LinkedList.prototype.nodeAtIndex = function(index) {

    if (index < 0 || index >= this.nElements) {
        return null;
    }
    if (index === (this.nElements - 1)) {
        return this.lastNode;
    }
    var node = this.firstNode;
    for (var i = 0; i < index; i++) {
        node = node.next;
    }
    return node;
};
/**
 * @private
 */
buckets.LinkedList.prototype.createNode = function(item) {
    return {
        element: item,
        next: null
    };
};


/**
 * Creates an empty dictionary. 
 * @class <p>Dictionaries map keys to values; each key can map to at most one value.
 * This implementation accepts any kind of objects as keys.</p>
 *
 * <p>If the keys are custom objects a function which converts keys to unique
 * strings must be provided. Example:</p>
 * <pre>
 * function petToString(pet) {
 *  return pet.name;
 * }
 * </pre>
 * @constructor
 * @param {function(Object):string=} toStrFunction optional function used
 * to convert keys to strings. If the keys aren't strings or if toString()
 * is not appropriate, a custom function which receives a key and returns a
 * unique string must be provided.
 */
buckets.Dictionary = function(toStrFunction) {

    /**
     * Object holding the key-value pairs.
     * @type {Object}
     * @private
     */
    this.table = {};

    /**
     * Number of elements in the list.
     * @type {number}
     * @private
     */
    this.nElements = 0;

    /**
     * Function used to convert keys to strings.
     * @type {function(Object):string}
     * @private
     */
    this.toStr = toStrFunction || buckets.defaultToString;
};

/**
 * Returns the value to which this dictionary maps the specified key.
 * Returns undefined if this dictionary contains no mapping for this key.
 * @param {Object} key key whose associated value is to be returned.
 * @return {*} the value to which this dictionary maps the specified key or
 * undefined if the map contains no mapping for this key.
 */
buckets.Dictionary.prototype.get = function(key) {

    var pair = this.table[this.toStr(key)];
    if (buckets.isUndefined(pair)) {
        return undefined;
    }
    return pair.value;
};
/**
 * Associates the specified value with the specified key in this dictionary.
 * If the dictionary previously contained a mapping for this key, the old
 * value is replaced by the specified value.
 * @param {Object} key key with which the specified value is to be
 * associated.
 * @param {Object} value value to be associated with the specified key.
 * @return {*} previous value associated with the specified key, or undefined if
 * there was no mapping for the key or if the key/value are undefined.
 */
buckets.Dictionary.prototype.set = function(key, value) {

    if (buckets.isUndefined(key) || buckets.isUndefined(value)) {
        return undefined;
    }

    var ret;
    var k = this.toStr(key);
    var previousElement = this.table[k];
    if (buckets.isUndefined(previousElement)) {
        this.nElements++;
        ret = undefined;
    } else {
        ret = previousElement.value;
    }
    this.table[k] = {
        key: key,
        value: value
    };
    return ret;
};
/**
 * Removes the mapping for this key from this dictionary if it is present.
 * @param {Object} key key whose mapping is to be removed from the
 * dictionary.
 * @return {*} previous value associated with specified key, or undefined if
 * there was no mapping for key.
 */
buckets.Dictionary.prototype.remove = function(key) {
    var k = this.toStr(key);
    var previousElement = this.table[k];
    if (!buckets.isUndefined(previousElement)) {
        delete this.table[k];
        this.nElements--;
        return previousElement.value;
    }
    return undefined;
};
/**
 * Returns an array containing all of the keys in this dictionary.
 * @return {Array} an array containing all of the keys in this dictionary.
 */
buckets.Dictionary.prototype.keys = function() {
    var array = [];
    for (var name in this.table) {
        if (this.table.hasOwnProperty(name)) {
            array.push(this.table[name].key);
        }
    }
    return array;
};
/**
 * Returns an array containing all of the values in this dictionary.
 * @return {Array} an array containing all of the values in this dictionary.
 */
buckets.Dictionary.prototype.values = function() {
    var array = [];
    for (var name in this.table) {
        if (this.table.hasOwnProperty(name)) {
            array.push(this.table[name].value);
        }
    }
    return array;
};

/**
 * Executes the provided function once for each key-value pair 
 * present in this dictionary.
 * @param {function(Object,Object):*} callback function to execute, it is
 * invoked with two arguments: key and value. To break the iteration you can 
 * optionally return false.
 */
buckets.Dictionary.prototype.forEach = function(callback) {
    for (var name in this.table) {
        if (this.table.hasOwnProperty(name)) {
            var pair = this.table[name];
            var ret = callback(pair.key, pair.value);
            if (ret === false) {
                return;
            }
        }
    }
};

/**
 * Returns true if this dictionary contains a mapping for the specified key.
 * @param {Object} key key whose presence in this dictionary is to be
 * tested.
 * @return {boolean} true if this dictionary contains a mapping for the
 * specified key.
 */
buckets.Dictionary.prototype.containsKey = function(key) {
    return ! buckets.isUndefined(this.get(key));
};
/**
 * Removes all mappings from this dictionary.
 * @this {buckets.Dictionary}
 */
buckets.Dictionary.prototype.clear = function() {

    this.table = {};
    this.nElements = 0;
};
/**
 * Returns the number of keys in this dictionary.
 * @return {number} the number of key-value mappings in this dictionary.
 */
buckets.Dictionary.prototype.size = function() {
    return this.nElements;
};

/**
 * Returns true if this dictionary contains no mappings.
 * @return {boolean} true if this dictionary contains no mappings.
 */
buckets.Dictionary.prototype.isEmpty = function() {
    return this.nElements <= 0;
};

// /**
//  * Returns true if this dictionary is equal to the given dictionary.
//  * Two dictionaries are equal if they contain the same mappings.
//  * @param {buckets.Dictionary} other the other dictionary.
//  * @param {function(Object,Object):boolean=} valuesEqualFunction optional
//  * function used to check if two values are equal.
//  * @return {boolean} true if this dictionary is equal to the given dictionary.
//  */
// buckets.Dictionary.prototype.equals = function(other,valuesEqualFunction) {
// 	var eqF = valuesEqualFunction || buckets.defaultEquals;
// 	if(!(other instanceof buckets.Dictionary)){
// 		return false;
// 	}
// 	if(this.size() !== other.size()){
// 		return false;
// 	}
// 	return this.equalsAux(this.firstNode,other.firstNode,eqF);
// };
/**
 * Creates an empty multi dictionary. 
 * @class <p>A multi dictionary is a special kind of dictionary that holds
 * multiple values against each key. Setting a value into the dictionary will 
 * add the value to an array at that key. Getting a key will return an array,
 * holding all the values set to that key.
 * This implementation accepts any kind of objects as keys.</p>
 *
 * <p>If the keys are custom objects a function which converts keys to strings must be
 * provided. Example:</p>
 *
 * <pre>
 * function petToString(pet) {
 *  return pet.name;
 * }
 * </pre>
 * <p>If the values are custom objects a function to check equality between values
 * must be provided. Example:</p>
 *
 * <pre>
 * function petsAreEqualByAge(pet1,pet2) {
 *  return pet1.age===pet2.age;
 * }
 * </pre>
 * @constructor
 * @param {function(Object):string=} toStrFunction optional function
 * to convert keys to strings. If the keys aren't strings or if toString()
 * is not appropriate, a custom function which receives a key and returns a
 * unique string must be provided.
 * @param {function(Object,Object):boolean=} valuesEqualsFunction optional
 * function to check if two values are equal.
 * 
 */
buckets.MultiDictionary = function(toStrFunction, valuesEqualsFunction) {
    // Call the parent's constructor
    this.parent = new buckets.Dictionary(toStrFunction);
    this.equalsF = valuesEqualsFunction || buckets.defaultEquals;
};

/**
 * Returns an array holding the values to which this dictionary maps
 * the specified key.
 * Returns an empty array if this dictionary contains no mappings for this key.
 * @param {Object} key key whose associated values are to be returned.
 * @return {Array} an array holding the values to which this dictionary maps
 * the specified key.
 */
buckets.MultiDictionary.prototype.get = function(key) {
    var values = this.parent.get(key);
    if (buckets.isUndefined(values)) {
        return [];
    }
    return buckets.arrays.copy(values);
};

/**
 * Adds the value to the array associated with the specified key, if 
 * it is not already present.
 * @param {Object} key key with which the specified value is to be
 * associated.
 * @param {Object} value the value to add to the array at the key
 * @return {boolean} true if the value was not already associated with that key.
 */
buckets.MultiDictionary.prototype.set = function(key, value) {

    if (buckets.isUndefined(key) || buckets.isUndefined(value)) {
        return false;
    }
    if (!this.containsKey(key)) {
        this.parent.set(key, [value]);
        return true;
    }
    var array = this.parent.get(key);
    if (buckets.arrays.contains(array, value, this.equalsF)) {
        return false;
    }
    array.push(value);
    return true;
};

/**
 * Removes the specified values from the array of values associated with the
 * specified key. If a value isn't given, all values associated with the specified 
 * key are removed.
 * @param {Object} key key whose mapping is to be removed from the
 * dictionary.
 * @param {Object=} value optional argument to specify the value to remove 
 * from the array associated with the specified key.
 * @return {*} true if the dictionary changed, false if the key doesn't exist or 
 * if the specified value isn't associated with the specified key.
 */
buckets.MultiDictionary.prototype.remove = function(key, value) {
    if (buckets.isUndefined(value)) {
        var v = this.parent.remove(key);
        if (buckets.isUndefined(v)) {
            return false;
        }
        return true;
    }
    var array = this.parent.get(key);
    if (buckets.arrays.remove(array, value, this.equalsF)) {
        if (array.length === 0) {
            this.parent.remove(key);
        }
        return true;
    }
    return false;
};

/**
 * Returns an array containing all of the keys in this dictionary.
 * @return {Array} an array containing all of the keys in this dictionary.
 */
buckets.MultiDictionary.prototype.keys = function() {
    return this.parent.keys();
};

/**
 * Returns an array containing all of the values in this dictionary.
 * @return {Array} an array containing all of the values in this dictionary.
 */
buckets.MultiDictionary.prototype.values = function() {
    var values = this.parent.values();
    var array = [];
    for (var i = 0; i < values.length; i++) {
        var v = values[i];
        for (var j = 0; j < v.length; j++) {
            array.push(v[j]);
        }
    }
    return array;
};

/**
 * Returns true if this dictionary at least one value associatted the specified key.
 * @param {Object} key key whose presence in this dictionary is to be
 * tested.
 * @return {boolean} true if this dictionary at least one value associatted 
 * the specified key.
 */
buckets.MultiDictionary.prototype.containsKey = function(key) {
    return this.parent.containsKey(key);
};

/**
 * Removes all mappings from this dictionary.
 */
buckets.MultiDictionary.prototype.clear = function() {
    return this.parent.clear();
};

/**
 * Returns the number of keys in this dictionary.
 * @return {number} the number of key-value mappings in this dictionary.
 */
buckets.MultiDictionary.prototype.size = function() {
    return this.parent.size();
};

/**
 * Returns true if this dictionary contains no mappings.
 * @return {boolean} true if this dictionary contains no mappings.
 */
buckets.MultiDictionary.prototype.isEmpty = function() {
    return this.parent.isEmpty();
};

/**
 * Creates an empty Heap.
 * @class 
 * <p>A heap is a binary tree, where the nodes maintain the heap property: 
 * each node is smaller than each of its children. 
 * This implementation uses an array to store elements.</p>
 * <p>If the inserted elements are custom objects a compare function must be provided, 
 *  at construction time, otherwise the <=, === and >= operators are 
 * used to compare elements. Example:</p>
 *
 * <pre>
 * function compare(a, b) {
 *  if (a is less than b by some ordering criterion) {
 *     return -1;
 *  } if (a is greater than b by the ordering criterion) {
 *     return 1;
 *  } 
 *  // a must be equal to b
 *  return 0;
 * }
 * </pre>
 *
 * <p>If a Max-Heap is wanted (greater elements on top) you can a provide a
 * reverse compare function to accomplish that behavior. Example:</p>
 *
 * <pre>
 * function reverseCompare(a, b) {
 *  if (a is less than b by some ordering criterion) {
 *     return 1;
 *  } if (a is greater than b by the ordering criterion) {
 *     return -1;
 *  } 
 *  // a must be equal to b
 *  return 0;
 * }
 * </pre>
 *
 * @constructor
 * @param {function(Object,Object):number=} compareFunction optional
 * function used to compare two elements. Must return a negative integer,
 * zero, or a positive integer as the first argument is less than, equal to,
 * or greater than the second.
 */
buckets.Heap = function(compareFunction) {

    /**
     * Array used to store the elements od the heap.
     * @type {Array.<Object>}
     * @private
     */
    this.data = [];

    /**
     * Function used to compare elements.
     * @type {function(Object,Object):number}
     * @private
     */
    this.compare = compareFunction || buckets.defaultCompare;
};
/**
 * Returns the index of the left child of the node at the given index.
 * @param {number} nodeIndex The index of the node to get the left child
 * for.
 * @return {number} The index of the left child.
 * @private
 */
buckets.Heap.prototype.leftChildIndex = function(nodeIndex) {
    return (2 * nodeIndex) + 1;
};
/**
 * Returns the index of the right child of the node at the given index.
 * @param {number} nodeIndex The index of the node to get the right child
 * for.
 * @return {number} The index of the right child.
 * @private
 */
buckets.Heap.prototype.rightChildIndex = function(nodeIndex) {
    return (2 * nodeIndex) + 2;
};
/**
 * Returns the index of the parent of the node at the given index.
 * @param {number} nodeIndex The index of the node to get the parent for.
 * @return {number} The index of the parent.
 * @private
 */
buckets.Heap.prototype.parentIndex = function(nodeIndex) {
    return Math.floor((nodeIndex - 1) / 2);
};
/**
 * Returns the index of the smaller child node (if it exists).
 * @param {number} leftChild left child index.
 * @param {number} rightChild right child index.
 * @return {number} the index with the minimum value or -1 if it doesn't
 * exists.
 * @private
 */
buckets.Heap.prototype.minIndex = function(leftChild, rightChild) {

    if (rightChild >= this.data.length) {
        if (leftChild >= this.data.length) {
            return - 1;
        } else {
            return leftChild;
        }
    } else {
        if (this.compare(this.data[leftChild], this.data[rightChild]) <= 0) {
            return leftChild;
        } else {
            return rightChild;
        }
    }
};
/**
 * Moves the node at the given index up to its proper place in the heap.
 * @param {number} index The index of the node to move up.
 * @private
 */
buckets.Heap.prototype.siftUp = function(index) {

    var parent = this.parentIndex(index);
    while (index > 0 && this.compare(this.data[parent], this.data[index]) > 0) {
        buckets.arrays.swap(this.data, parent, index);
        index = parent;
        parent = this.parentIndex(index);
    }
};
/**
 * Moves the node at the given index down to its proper place in the heap.
 * @param {number} nodeIndex The index of the node to move down.
 * @private
 */
buckets.Heap.prototype.siftDown = function(nodeIndex) {

    //smaller child index
    var min = this.minIndex(this.leftChildIndex(nodeIndex),
    this.rightChildIndex(nodeIndex));

    while (min >= 0 && this.compare(this.data[nodeIndex],
    this.data[min]) > 0) {
        buckets.arrays.swap(this.data, min, nodeIndex);
        nodeIndex = min;
        min = this.minIndex(this.leftChildIndex(nodeIndex),
        this.rightChildIndex(nodeIndex));
    }
};
/**
 * Retrieves but does not remove the root element of this heap.
 * @return {*} The value at the root of the heap. Returns undefined if the
 * heap is empty.
 */
buckets.Heap.prototype.peek = function() {

    if (this.data.length > 0) {
        return this.data[0];
    } else {
        return undefined;
    }
};
/**
 * Adds the given element into the heap.
 * @param {*} element the element.
 * @return true if the element was added or fals if it is undefined.
 */
buckets.Heap.prototype.add = function(element) {
    if (buckets.isUndefined(element)) {
        return undefined;
    }
    this.data.push(element);
    this.siftUp(this.data.length - 1);
    return true;
};

/**
 * Retrieves and removes the root element of this heap.
 * @return {*} The value removed from the root of the heap. Returns
 * undefined if the heap is empty.
 */
buckets.Heap.prototype.removeRoot = function() {

    if (this.data.length > 0) {
        var obj = this.data[0];
        this.data[0] = this.data[this.data.length - 1];
        this.data.splice(this.data.length - 1, 1);
        if (this.data.length > 0) {
            this.siftDown(0);
        }
        return obj;
    }
    return undefined;
};
/**
 * Returns true if this heap contains the specified element.
 * @param {Object} element element to search for.
 * @return {boolean} true if this Heap contains the specified element, false
 * otherwise.
 */
buckets.Heap.prototype.contains = function(element) {
    var equF = buckets.compareToEquals(this.compare);
    return buckets.arrays.contains(this.data, element, equF);
};
/**
 * Returns the number of elements in this heap.
 * @return {number} the number of elements in this heap.
 */
buckets.Heap.prototype.size = function() {
    return this.data.length;
};
/**
 * Checks if this heap is empty.
 * @return {boolean} true if and only if this heap contains no items; false
 * otherwise.
 */
buckets.Heap.prototype.isEmpty = function() {
    return this.data.length <= 0;
};
/**
 * Removes all of the elements from this heap.
 */
buckets.Heap.prototype.clear = function() {
    this.data.length = 0;
};

/**
 * Executes the provided function once for each element present in this heap in 
 * no particular order.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.Heap.prototype.forEach = function(callback) {
   buckets.arrays.forEach(this.data,callback);
};

/**
 * Creates an empty Stack.
 * @class A Stack is a Last-In-First-Out (LIFO) data structure, the last
 * element added to the stack will be the first one to be removed. This
 * implementation uses a linked list as a container.
 * @constructor
 */
buckets.Stack = function() {

    /**
     * List containing the elements.
     * @type buckets.LinkedList
     * @private
     */
    this.list = new buckets.LinkedList();
};
/**
 * Pushes an item onto the top of this stack.
 * @param {Object} elem the element to be pushed onto this stack.
 * @return {boolean} true if the element was pushed or false if it is undefined.
 */
buckets.Stack.prototype.push = function(elem) {
    return this.list.add(elem, 0);
};
/**
 * Pushes an item onto the top of this stack.
 * @param {Object} elem the element to be pushed onto this stack.
 * @return {boolean} true if the element was pushed or false if it is undefined.
 */
buckets.Stack.prototype.add = function(elem) {
    return this.list.add(elem, 0);
};
/**
 * Removes the object at the top of this stack and returns that object.
 * @return {*} the object at the top of this stack or undefined if the
 * stack is empty.
 */
buckets.Stack.prototype.pop = function() {
    return this.list.removeElementAtIndex(0);
};
/**
 * Looks at the object at the top of this stack without removing it from the
 * stack.
 * @return {*} the object at the top of this stack or undefined if the
 * stack is empty.
 */
buckets.Stack.prototype.peek = function() {
    return this.list.first();
};
/**
 * Returns the number of elements in this stack.
 * @return {number} the number of elements in this stack.
 */
buckets.Stack.prototype.size = function() {
    return this.list.size();
};

/**
 * Returns true if this stack contains the specified element.
 * <p>If the elements inside this stack are
 * not comparable with the === operator, a custom equals function should be
 * provided to perform searches, the function must receive two arguments and
 * return true if they are equal, false otherwise. Example:</p>
 *
 * <pre>
 * var petsAreEqualByName = function(pet1, pet2) {
 *  return pet1.name === pet2.name;
 * }
 * </pre>
 * @param {Object} elem element to search for.
 * @param {function(Object,Object):boolean=} equalsFunction optional
 * function to check if two elements are equal.
 * @return {boolean} true if this stack contains the specified element,
 * false otherwise.
 */
buckets.Stack.prototype.contains = function(elem, equalsFunction) {
    return this.list.contains(elem, equalsFunction);
};
/**
 * Checks if this stack is empty.
 * @return {boolean} true if and only if this stack contains no items; false
 * otherwise.
 */
buckets.Stack.prototype.isEmpty = function() {
    return this.list.isEmpty();
};
/**
 * Removes all of the elements from this stack.
 */
buckets.Stack.prototype.clear = function() {
    this.list.clear();
};

/**
 * Executes the provided function once for each element present in this stack in 
 * LIFO order.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.Stack.prototype.forEach = function(callback) {
   this.list.forEach(callback);
};

/**
 * Creates an empty queue.
 * @class A queue is a First-In-First-Out (FIFO) data structure, the first
 * element added to the queue will be the first one to be removed. This
 * implementation uses a linked list as a container.
 * @constructor
 */
buckets.Queue = function() {

    /**
     * List containing the elements.
     * @type buckets.LinkedList
     * @private
     */
    this.list = new buckets.LinkedList();
};
/**
 * Inserts the specified element into the end of this queue.
 * @param {Object} elem the element to insert.
 * @return {boolean} true if the element was inserted, or false if it is undefined.
 */
buckets.Queue.prototype.enqueue = function(elem) {
    return this.list.add(elem);
};
/**
 * Inserts the specified element into the end of this queue.
 * @param {Object} elem the element to insert.
 * @return {boolean} true if the element was inserted, or false if it is undefined.
 */
buckets.Queue.prototype.add = function(elem) {
    return this.list.add(elem);
};
/**
 * Retrieves and removes the head of this queue.
 * @return {*} the head of this queue, or undefined if this queue is empty.
 */
buckets.Queue.prototype.dequeue = function() {
    if (this.list.size() !== 0) {
        var el = this.list.first();
        this.list.removeElementAtIndex(0);
        return el;
    }
    return undefined;
};
/**
 * Retrieves, but does not remove, the head of this queue.
 * @return {*} the head of this queue, or undefined if this queue is empty.
 */
buckets.Queue.prototype.peek = function() {

    if (this.list.size() !== 0) {
        return this.list.first();
    }
    return undefined;
};

/**
 * Returns the number of elements in this queue.
 * @return {number} the number of elements in this queue.
 */
buckets.Queue.prototype.size = function() {
    return this.list.size();
};

/**
 * Returns true if this queue contains the specified element.
 * <p>If the elements inside this stack are
 * not comparable with the === operator, a custom equals function should be
 * provided to perform searches, the function must receive two arguments and
 * return true if they are equal, false otherwise. Example:</p>
 *
 * <pre>
 * var petsAreEqualByName = function(pet1, pet2) {
 *  return pet1.name === pet2.name;
 * }
 * </pre>
 * @param {Object} elem element to search for.
 * @param {function(Object,Object):boolean=} equalsFunction optional
 * function to check if two elements are equal.
 * @return {boolean} true if this queue contains the specified element,
 * false otherwise.
 */
buckets.Queue.prototype.contains = function(elem, equalsFunction) {
    return this.list.contains(elem, equalsFunction);
};

/**
 * Checks if this queue is empty.
 * @return {boolean} true if and only if this queue contains no items; false
 * otherwise.
 */
buckets.Queue.prototype.isEmpty = function() {
    return this.list.size() <= 0;
};

/**
 * Removes all of the elements from this queue.
 */
buckets.Queue.prototype.clear = function() {
    this.list.clear();
};

/**
 * Executes the provided function once for each element present in this queue in 
 * FIFO order.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.Queue.prototype.forEach = function(callback) {
   this.list.forEach(callback);
};

/**
 * Creates an empty priority queue.
 * @class <p>In a priority queue each element is associated with a "priority",
 * elements are dequeued in highest-priority-first order (the elements with the 
 * highest priority are dequeued first). Priority Queues are implemented as heaps. 
 * If the inserted elements are custom objects a compare function must be provided, 
 * otherwise the <=, === and >= operators are used to compare object priority.</p>
 * <pre>
 * function compare(a, b) {
 *  if (a is less than b by some ordering criterion) {
 *     return -1;
 *  } if (a is greater than b by the ordering criterion) {
 *     return 1;
 *  } 
 *  // a must be equal to b
 *  return 0;
 * }
 * </pre>
 * @constructor
 * @param {function(Object,Object):number=} compareFunction optional
 * function used to compare two element priorities. Must return a negative integer,
 * zero, or a positive integer as the first argument is less than, equal to,
 * or greater than the second.
 */
buckets.PriorityQueue = function(compareFunction) {
    this.heap = new buckets.Heap(buckets.reverseCompareFunction(compareFunction));
};

/**
 * Inserts the specified element into this priority queue.
 * @param {Object} element the element to insert.
 * @return {boolean} true if the element was inserted, or false if it is undefined.
 */
buckets.PriorityQueue.prototype.enqueue = function(element) {
    return this.heap.add(element);
};

/**
 * Inserts the specified element into this priority queue.
 * @param {Object} element the element to insert.
 * @return {boolean} true if the element was inserted, or false if it is undefined.
 */
buckets.PriorityQueue.prototype.add = function(element) {
    return this.heap.add(element);
};

/**
 * Retrieves and removes the highest priority element of this queue.
 * @return {*} the the highest priority element of this queue, 
or undefined if this queue is empty.
 */
buckets.PriorityQueue.prototype.dequeue = function() {
    if (this.heap.size() !== 0) {
        var el = this.heap.peek();
        this.heap.removeRoot();
        return el;
    }
    return undefined;
};

/**
 * Retrieves, but does not remove, the highest priority element of this queue.
 * @return {*} the highest priority element of this queue, or undefined if this queue is empty.
 */
buckets.PriorityQueue.prototype.peek = function() {
    return this.heap.peek();
};

/**
 * Returns true if this priority queue contains the specified element.
 * @param {Object} element element to search for.
 * @return {boolean} true if this priority queue contains the specified element,
 * false otherwise.
 */
buckets.PriorityQueue.prototype.contains = function(element) {
    return this.heap.contains(element);
};

/**
 * Checks if this priority queue is empty.
 * @return {boolean} true if and only if this priority queue contains no items; false
 * otherwise.
 */
buckets.PriorityQueue.prototype.isEmpty = function() {
    return this.heap.isEmpty();
};

/**
 * Returns the number of elements in this priority queue.
 * @return {number} the number of elements in this priority queue.
 */
buckets.PriorityQueue.prototype.size = function() {
    return this.heap.size();
};

/**
 * Removes all of the elements from this priority queue.
 */
buckets.PriorityQueue.prototype.clear = function() {
    this.heap.clear();
};

/**
 * Executes the provided function once for each element present in this queue in 
 * no particular order.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.PriorityQueue.prototype.forEach = function(callback) {
   buckets.heap.forEach(callback);
};


/**
 * Creates an empty set.
 * @class <p>A set is a data structure that contains no duplicate items.</p>
 * <p>If the inserted elements are custom objects a function 
 * which converts elements to strings must be provided. Example:</p>
 *
 * <pre>
 * function petToString(pet) {
 *  return pet.name;
 * }
 * </pre>
 *
 * @constructor
 * @param {function(Object):string=} toStringFunction optional function used
 * to convert elements to strings. If the elements aren't strings or if toString()
 * is not appropriate, a custom function which receives a onject and returns a
 * unique string must be provided.
 */
buckets.Set = function(toStringFunction) {
    this.dictionary = new buckets.Dictionary(toStringFunction);
};

/**
 * Returns true if this set contains the specified element.
 * @param {Object} element element to search for.
 * @return {boolean} true if this set contains the specified element,
 * false otherwise.
 */
buckets.Set.prototype.contains = function(element) {
    return this.dictionary.containsKey(element);
};

/**
 * Adds the specified element to this set if it is not already present.
 * @param {Object} element the element to insert.
 * @return {boolean} true if this set did not already contain the specified element.
 */
buckets.Set.prototype.add = function(element) {
    if (this.contains(element) || buckets.isUndefined(element)) {
        return false;
    } else {
        this.dictionary.set(element, element);
        return true;
    }
};

/**
 * Performs an intersecion between this an another set.
 * Removes all values that are not present this set and the given set.
 * @param {buckets.Set} otherSet other set.
 */
buckets.Set.prototype.intersection = function(otherSet) {
    var set = this;
    this.forEach(function(element) {
        if (!otherSet.contains(element)) {
            set.remove(element);
        }
    });
};

/**
 * Performs a union between this an another set.
 * Adds all values from the given set to this set.
 * @param {buckets.Set} otherSet other set.
 */
buckets.Set.prototype.union = function(otherSet) {
    var set = this;
    otherSet.forEach(function(element) {
        set.add(element);
    });
};

/**
 * Performs a difference between this an another set.
 * Removes from this set all the values that are present in the given set.
 * @param {buckets.Set} otherSet other set.
 */
buckets.Set.prototype.difference = function(otherSet) {
    var set = this;
    otherSet.forEach(function(element) {
        set.remove(element);
    });
};

/**
 * Checks whether the given set contains all the elements in this set.
 * @param {buckets.Set} otherSet other set.
 * @return {boolean} true if this set is a subset of the given set.
 */
buckets.Set.prototype.isSubsetOf = function(otherSet) {
    if (this.size() > otherSet.size()) {
        return false;
    }

    this.forEach(function(element) {
        if (!otherSet.contains(element)) {
            return false;
        }
    });
    return true;
};

/**
 * Removes the specified element from this set if it is present.
 * @return {boolean} true if this set contained the specified element.
 */
buckets.Set.prototype.remove = function(element) {
    if (!this.contains(element)) {
        return false;
    } else {
        this.dictionary.remove(element);
        return true;
    }
};

/**
 * Executes the provided function once for each element 
 * present in this set.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one arguments: the element. To break the iteration you can 
 * optionally return false.
 */
buckets.Set.prototype.forEach = function(callback) {
    this.dictionary.forEach(function(k, v) {
        return callback(v);
    });
};

/**
 * Returns an array containing all of the elements in this set in arbitrary order.
 * @return {Array} an array containing all of the elements in this set.
 */
buckets.Set.prototype.toArray = function() {
    return this.dictionary.values();
};

/**
 * Returns true if this set contains no elements.
 * @return {boolean} true if this set contains no elements.
 */
buckets.Set.prototype.isEmpty = function() {
    return this.dictionary.isEmpty();
};

/**
 * Returns the number of elements in this set.
 * @return {number} the number of elements in this set.
 */
buckets.Set.prototype.size = function() {
    return this.dictionary.size();
};

/**
 * Removes all of the elements from this set.
 */
buckets.Set.prototype.clear = function() {
    this.dictionary.clear();
};

/**
 * Creates an empty bag.
 * @class <p>A bag is a special kind of set in which members are 
 * allowed to appear more than once.</p>
 * <p>If the inserted elements are custom objects a function 
 * which converts elements to unique strings must be provided. Example:</p>
 *
 * <pre>
 * function petToString(pet) {
 *  return pet.name;
 * }
 * </pre>
 *
 * @constructor
 * @param {function(Object):string=} toStringFunction optional function used
 * to convert elements to strings. If the elements aren't strings or if toString()
 * is not appropriate, a custom function which receives an object and returns a
 * unique string must be provided.
 */
buckets.Bag = function(toStrFunction) {
    this.toStrF = toStrFunction || buckets.defaultToString;
    this.dictionary = new buckets.Dictionary(this.toStrF);
    this.nElements = 0;
};

/**
* Adds nCopies of the specified object to this bag.
* @param {Object} element element to add.
* @param {number=} nCopies the number of copies to add, if this argument is
* undefined 1 copy is added.
* @return {boolean} true unless element is undefined.
*/
buckets.Bag.prototype.add = function(element, nCopies) {

    if (isNaN(nCopies) || buckets.isUndefined(nCopies)) {
        nCopies = 1;
    }
    if (buckets.isUndefined(element) || nCopies <= 0) {
        return false;
    }

    if (!this.contains(element)) {
        var node = {
            value: element,
            copies: nCopies
        };
        this.dictionary.set(element, node);
    } else {
        this.dictionary.get(element).copies += nCopies;
    }
    this.nElements += nCopies;
    return true;
};

/**
* Counts the number of copies of the specified object in this bag.
* @param {Object} element the object to search for..
* @return {number} the number of copies of the object, 0 if not found
*/
buckets.Bag.prototype.count = function(element) {

    if (!this.contains(element)) {
        return 0;
    } else {
        return this.dictionary.get(element).copies;
    }
};

/**
 * Returns true if this bag contains the specified element.
 * @param {Object} element element to search for.
 * @return {boolean} true if this bag contains the specified element,
 * false otherwise.
 */
buckets.Bag.prototype.contains = function(element) {
    return this.dictionary.containsKey(element);
};

/**
* Removes nCopies of the specified object to this bag.
* If the number of copies to remove is greater than the actual number 
* of copies in the Bag, all copies are removed. 
* @param {Object} element element to remove.
* @param {number=} nCopies the number of copies to remove, if this argument is
* undefined 1 copy is removed.
* @return {boolean} true if at least 1 element was removed.
*/
buckets.Bag.prototype.remove = function(element, nCopies) {

    if (isNaN(nCopies) || buckets.isUndefined(nCopies)) {
        nCopies = 1;
    }
    if (buckets.isUndefined(element) || nCopies <= 0) {
        return false;
    }

    if (!this.contains(element)) {
        return false;
    } else {
        var node = this.dictionary.get(element);
        if (nCopies > node.copies) {
            this.nElements -= node.copies;
        } else {
            this.nElements -= nCopies;
        }
        node.copies -= nCopies;
        if (node.copies <= 0) {
            this.dictionary.remove(element);
        }
        return true;
    }
};

/**
 * Returns an array containing all of the elements in this big in arbitrary order, 
 * including multiple copies.
 * @return {Array} an array containing all of the elements in this bag.
 */
buckets.Bag.prototype.toArray = function() {
    var a = [];
    var values = this.dictionary.values();
    var vl = values.length;
    for (var i = 0; i < vl; i++) {
        var node = values[i];
        var element = node.value;
        var copies = node.copies;
        for (var j = 0; j < copies; j++) {
            a.push(element);
        }
    }
    return a;
};

/**
 * Returns a set of unique elements in this bag. 
 * @return {buckets.Set} a set of unique elements in this bag.
 */
buckets.Bag.prototype.toSet = function() {
    var set = new buckets.Set(this.toStrF);
    var elements = this.dictionary.values();
    var l = elements.length;
    for (var i = 0; i < l; i++) {
        var value = elements[i].value;
        set.add(value);
    }
    return set;
};

/**
 * Executes the provided function once for each element 
 * present in this bag, including multiple copies.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element. To break the iteration you can 
 * optionally return false.
 */
buckets.Bag.prototype.forEach = function(callback) {
    this.dictionary.forEach(function(k, v) {
        var value = v.value;
        var copies = v.copies;
        for (var i = 0; i < copies; i++) {
            if (callback(value) === false) {
                return false;
            }
        }
        return true;
    });
};
/**
 * Returns the number of elements in this bag.
 * @return {number} the number of elements in this bag.
 */
buckets.Bag.prototype.size = function() {
    return this.nElements;
};

/**
 * Returns true if this bag contains no elements.
 * @return {boolean} true if this bag contains no elements.
 */
buckets.Bag.prototype.isEmpty = function() {
    return this.nElements === 0;
};

/**
 * Removes all of the elements from this bag.
 */
buckets.Bag.prototype.clear = function() {
    this.nElements = 0;
    this.dictionary.clear();
};



/**
 * Creates an empty binary search tree.
 * @class <p>A binary search tree is a binary tree in which each 
 * internal node stores an element such that the elements stored in the 
 * left subtree are less than it and the elements 
 * stored in the right subtree are greater.</p>
 * <p>Formally, a binary search tree is a node-based binary tree data structure which 
 * has the following properties:</p>
 * <ul>
 * <li>The left subtree of a node contains only nodes with elements less 
 * than the node's element</li>
 * <li>The right subtree of a node contains only nodes with elements greater 
 * than the node's element</li>
 * <li>Both the left and right subtrees must also be binary search trees.</li>
 * </ul>
 * <p>If the inserted elements are custom objects a compare function must 
 * be provided at construction time, otherwise the <=, === and >= operators are 
 * used to compare elements. Example:</p>
 * <pre>
 * function compare(a, b) {
 *  if (a is less than b by some ordering criterion) {
 *     return -1;
 *  } if (a is greater than b by the ordering criterion) {
 *     return 1;
 *  } 
 *  // a must be equal to b
 *  return 0;
 * }
 * </pre>
 * @constructor
 * @param {function(Object,Object):number=} compareFunction optional
 * function used to compare two elements. Must return a negative integer,
 * zero, or a positive integer as the first argument is less than, equal to,
 * or greater than the second.
 */
buckets.BSTree = function(compareFunction) {
    this.root = null;
    this.compare = compareFunction || buckets.defaultCompare;
    this.nElements = 0;
};


/**
 * Adds the specified element to this tree if it is not already present.
 * @param {Object} element the element to insert.
 * @return {boolean} true if this tree did not already contain the specified element.
 */
buckets.BSTree.prototype.add = function(element) {
    if (buckets.isUndefined(element)) {
        return false;
    }

    if (this.insertNode(this.createNode(element)) !== null) {
        this.nElements++;
        return true;
    }
    return false;
};

/**
 * Removes all of the elements from this tree.
 */
buckets.BSTree.prototype.clear = function() {
    this.root = null;
    this.nElements = 0;
};

/**
 * Returns true if this tree contains no elements.
 * @return {boolean} true if this tree contains no elements.
 */
buckets.BSTree.prototype.isEmpty = function() {
    return this.nElements === 0;
};

/**
 * Returns the number of elements in this tree.
 * @return {number} the number of elements in this tree.
 */
buckets.BSTree.prototype.size = function() {
    return this.nElements;
};

/**
 * Returns true if this tree contains the specified element.
 * @param {Object} element element to search for.
 * @return {boolean} true if this tree contains the specified element,
 * false otherwise.
 */
buckets.BSTree.prototype.contains = function(element) {
    if (buckets.isUndefined(element)) {
        return false;
    }
    return this.searchNode(this.root, element) !== null;
};

/**
 * Removes the specified element from this tree if it is present.
 * @return {boolean} true if this tree contained the specified element.
 */
buckets.BSTree.prototype.remove = function(element) {
    var node = this.searchNode(this.root, element);
    if (node === null) {
        return false;
    }
    this.removeNode(node);
    this.nElements--;
    return true;
};

/**
 * Executes the provided function once for each element present in this tree in 
 * in-order.
 * @param {function(Object):*} callback function to execute, it is invoked with one 
 * argument: the element value, to break the iteration you can optionally return false.
 */
buckets.BSTree.prototype.inorderTraversal = function(callback) {
    this.inorderTraversalAux(this.root, callback, {
        stop: false
    });
};

/**
 * Executes the provided function once for each element present in this tree in pre-order.
 * @param {function(Object):*} callback function to execute, it is invoked with one 
 * argument: the element value, to break the iteration you can optionally return false.
 */
buckets.BSTree.prototype.preorderTraversal = function(callback) {
    this.preorderTraversalAux(this.root, callback, {
        stop: false
    });
};

/**
 * Executes the provided function once for each element present in this tree in post-order.
 * @param {function(Object):*} callback function to execute, it is invoked with one 
 * argument: the element value, to break the iteration you can optionally return false.
 */
buckets.BSTree.prototype.postorderTraversal = function(callback) {
    this.postorderTraversalAux(this.root, callback, {
        stop: false
    });
};

/**
 * Executes the provided function once for each element present in this tree in 
 * level-order.
 * @param {function(Object):*} callback function to execute, it is invoked with one 
 * argument: the element value, to break the iteration you can optionally return false.
 */
buckets.BSTree.prototype.levelTraversal = function(callback) {
    this.levelTraversalAux(this.root, callback);
};

/**
 * Returns the minimum element of this tree.
 * @return {*} the minimum element of this tree or undefined if this tree is
 * is empty.
 */
buckets.BSTree.prototype.minimum = function() {
    if (this.isEmpty()) {
        return undefined;
    }
    return this.minimumAux(this.root).element;
};

/**
 * Returns the maximum element of this tree.
 * @return {*} the maximum element of this tree or undefined if this tree is
 * is empty.
 */
buckets.BSTree.prototype.maximum = function() {
    if (this.isEmpty()) {
        return undefined;
    }
    return this.maximumAux(this.root).element;
};

/**
 * Executes the provided function once for each element present in this tree in inorder.
 * Equivalent to inorderTraversal.
 * @param {function(Object):*} callback function to execute, it is
 * invoked with one argument: the element value, to break the iteration you can 
 * optionally return false.
 */
buckets.BSTree.prototype.forEach = function(callback) {
    this.inorderTraversal(callback);
};

/**
 * Returns an array containing all of the elements in this tree in in-order.
 * @return {Array} an array containing all of the elements in this tree in in-order.
 */
buckets.BSTree.prototype.toArray = function() {
    var array = [];
    this.inorderTraversal(function(element) {
        array.push(element);
    });
    return array;
};

/**
 * Returns the height of this tree.
 * @return {number} the height of this tree or -1 if is empty.
 */
buckets.BSTree.prototype.height = function() {
    return this.heightAux(this.root);
};

/**
* @private
*/
buckets.BSTree.prototype.searchNode = function(node, element) {
    var cmp = null;
    while (node !== null && cmp !== 0) {
        cmp = this.compare(element, node.element);
        if (cmp < 0) {
            node = node.leftCh;
        } else if (cmp > 0) {
            node = node.rightCh;
        }
    }
    return node;
};


/**
* @private
*/
buckets.BSTree.prototype.transplant = function(n1, n2) {
    if (n1.parent === null) {
        this.root = n2;
    } else if (n1 === n1.parent.leftCh) {
        n1.parent.leftCh = n2;
    } else {
        n1.parent.rightCh = n2;
    }
    if (n2 !== null) {
        n2.parent = n1.parent;
    }
};


/**
* @private
*/
buckets.BSTree.prototype.removeNode = function(node) {
    if (node.leftCh === null) {
        this.transplant(node, node.rightCh);
    } else if (node.rightCh === null) {
        this.transplant(node, node.leftCh);
    } else {
        var y = this.minimumAux(node.rightCh);
        if (y.parent !== node) {
            this.transplant(y, y.rightCh);
            y.rightCh = node.rightCh;
            y.rightCh.parent = y;
        }
        this.transplant(node, y);
        y.leftCh = node.leftCh;
        y.leftCh.parent = y;
    }
};
/**
* @private
*/
buckets.BSTree.prototype.inorderTraversalAux = function(node, callback, signal) {
    if (node === null || signal.stop) {
        return;
    }
    this.inorderTraversalAux(node.leftCh, callback, signal);
    if (signal.stop) {
        return;
    }
    signal.stop = callback(node.element) === false;
    if (signal.stop) {
        return;
    }
    this.inorderTraversalAux(node.rightCh, callback, signal);
};

/**
* @private
*/
buckets.BSTree.prototype.levelTraversalAux = function(node, callback) {
    var queue = new buckets.Queue();
    if (node !== null) {
        queue.enqueue(node);
    }
    while (!queue.isEmpty()) {
        node = queue.dequeue();
        if (callback(node.element) === false) {
            return;
        }
        if (node.leftCh !== null) {
            queue.enqueue(node.leftCh);
        }
        if (node.rightCh !== null) {
            queue.enqueue(node.rightCh);
        }
    }
};

/**
* @private
*/
buckets.BSTree.prototype.preorderTraversalAux = function(node, callback, signal) {
    if (node === null || signal.stop) {
        return;
    }
    signal.stop = callback(node.element) === false;
    if (signal.stop) {
        return;
    }
    this.preorderTraversalAux(node.leftCh, callback, signal);
    if (signal.stop) {
        return;
    }
    this.preorderTraversalAux(node.rightCh, callback, signal);
};
/**
* @private
*/
buckets.BSTree.prototype.postorderTraversalAux = function(node, callback, signal) {
    if (node === null || signal.stop) {
        return;
    }
    this.postorderTraversalAux(node.leftCh, callback, signal);
    if (signal.stop) {
        return;
    }
    this.postorderTraversalAux(node.rightCh, callback, signal);
    if (signal.stop) {
        return;
    }
    signal.stop = callback(node.element) === false;
};

/**
* @private
*/
buckets.BSTree.prototype.minimumAux = function(node) {
    while (node.leftCh !== null) {
        node = node.leftCh;
    }
    return node;
};

/**
* @private
*/
buckets.BSTree.prototype.maximumAux = function(node) {
    while (node.rightCh !== null) {
        node = node.rightCh;
    }
    return node;
};

/**
* @private
*/
buckets.BSTree.prototype.successorNode = function(node) {
    if (node.rightCh !== null) {
        return this.minimumAux(node.rightCh);
    }
    var successor = node.parent;
    while (successor !== null && node === successor.rightCh) {
        node = successor;
        successor = node.parent;
    }
    return successor;
};

/**
* @private
*/
buckets.BSTree.prototype.heightAux = function(node) {
    if (node === null) {
        return - 1;
    }
    return Math.max(this.heightAux(node.leftCh), this.heightAux(node.rightCh)) + 1;
};

/*
* @private
*/
buckets.BSTree.prototype.insertNode = function(node) {

    var parent = null;
    var position = this.root;
    var cmp = null;
    while (position !== null) {
        cmp = this.compare(node.element, position.element);
        if (cmp === 0) {
            return null;
        } else if (cmp < 0) {
            parent = position;
            position = position.leftCh;
        } else {
            parent = position;
            position = position.rightCh;
        }
    }
    node.parent = parent;
    if (parent === null) {
        // tree is empty
        this.root = node;
    } else if (this.compare(node.element, parent.element) < 0) {
        parent.leftCh = node;
    } else {
        parent.rightCh = node;
    }
    return node;
};

/**
* @private
*/
buckets.BSTree.prototype.createNode = function(element) {
    return {
        element: element,
        leftCh: null,
        rightCh: null,
        parent: null
    };
};
//customizations to libraries
(function () {
_.uniqueId = function (prefix) {
    //from ipython project
    // http://www.ietf.org/rfc/rfc4122.txt
    var s = [];
    var hexDigits = "0123456789ABCDEF";
    for (var i = 0; i < 32; i++) {
        s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
    }
    s[12] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
    s[16] = hexDigits.substr((s[16] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01

    var uuid = s.join("");
    if (prefix){
        return prefix + "-" + uuid;
    }else{
        return uuid;
    }
};

_.isNullOrUndefined = function(x){
    return _.isNull(x) || _.isUndefined(x);
};

_.setdefault = function(obj, key, value){
    if (_.has(obj, key)){
        return obj[key]}
    else{
        obj[key] = value
        return value
    }
};
}).call(this);


(function(/*! Stitch !*/) {
  if (!this.require) {
    var modules = {}, cache = {}, require = function(name, root) {
      var path = expand(root, name), indexPath = expand(path, './index'), module, fn;
      module   = cache[path] || cache[indexPath]
      if (module) {
        return module.exports;
      } else if (fn = modules[path] || modules[path = indexPath]) {
        module = {id: path, exports: {}};
        try {
          cache[path] = module;
          fn(module.exports, function(name) {
            return require(name, dirname(path));
          }, module);
          return module.exports;
        } catch (err) {
          delete cache[path];
          throw err;
        }
      } else {
        throw 'module \'' + name + '\' not found';
      }
    }, expand = function(root, name) {
      var results = [], parts, part;
      if (/^\.\.?(\/|$)/.test(name)) {
        parts = [root, name].join('/').split('/');
      } else {
        parts = name.split('/');
      }
      for (var i = 0, length = parts.length; i < length; i++) {
        part = parts[i];
        if (part == '..') {
          results.pop();
        } else if (part != '.' && part != '') {
          results.push(part);
        }
      }
      return results.join('/');
    }, dirname = function(path) {
      return path.split('/').slice(0, -1).join('/');
    };
    this.require = function(name) {
      return require(name, '');
    }
    this.require.define = function(bundle) {
      for (var key in bundle)
        modules[key] = bundle[key];
    };
    this.require.modules = modules;
    this.require.cache   = cache;
  }
  return this.require.define;
}).call(this)({
  "serverutils": function(exports, require, module) {(function() {
  var Collections, Config, Deferreds, HasProperties, Promises, WebSocketWrapper, base, container, load_models, submodels, utility;

  Deferreds = {};

  Promises = {};

  Deferreds._doc_loaded = $.Deferred();

  Deferreds._doc_requested = $.Deferred();

  Promises.doc_loaded = Deferreds._doc_loaded.promise();

  Promises.doc_requested = Deferreds._doc_requested.promise();

  base = require("./base");

  Collections = base.Collections;

  container = require("./container");

  HasProperties = base.HasProperties;

  load_models = base.load_models;

  submodels = base.submodels;

  WebSocketWrapper = base.WebSocketWrapper;

  Config = base.Config;

  exports.wswrapper = null;

  exports.plotcontext = null;

  exports.plotcontextview = null;

  exports.Promises = Promises;

  HasProperties.prototype.sync = Backbone.sync;

  utility = {
    load_user: function() {
      var response;
      response = $.get('/bokeh/userinfo/', {});
      return response;
    },
    load_doc: function(docid) {
      var response;
      response = $.get(Config.prefix + ("/bokeh/bokehinfo/" + docid + "/"), {}).done(function(data) {
        var all_models, apikey;
        all_models = data['all_models'];
        load_models(all_models);
        apikey = data['apikey'];
        return submodels(exports.wswrapper, "bokehplot:" + docid, apikey);
      });
      return response;
    },
    make_websocket: function() {
      var wswrapper;
      wswrapper = new WebSocketWrapper(Config.ws_conn_string);
      exports.wswrapper = wswrapper;
      return wswrapper;
    },
    render_plots: function(plot_context_ref, viewclass, viewoptions) {
      var options, plotcontext, plotcontextview;
      if (viewclass == null) {
        viewclass = null;
      }
      if (viewoptions == null) {
        viewoptions = {};
      }
      plotcontext = Collections(plot_context_ref.type).get(plot_context_ref.id);
      if (!viewclass) {
        viewclass = plotcontext.default_view;
      }
      options = _.extend(viewoptions, {
        model: plotcontext
      });
      plotcontextview = new viewclass(options);
      plotcontext = plotcontext;
      plotcontextview = plotcontextview;
      plotcontextview.render();
      exports.plotcontext = plotcontext;
      return exports.plotcontextview = plotcontextview;
    },
    bokeh_connection: function(host, docid, protocol) {
      if (_.isUndefined(protocol)) {
        protocol = "https";
      }
      if (Promises.doc_requested.state() === "pending") {
        Deferreds._doc_requested.resolve();
        return $.get("" + protocol + "://" + host + "/bokeh/publicbokehinfo/" + docid, {}, function(data) {
          console.log('instatiate_doc_single, docid', docid);
          data = JSON.parse(data);
          load_models(data['all_models']);
          return Deferreds._doc_loaded.resolve(data);
        });
      }
    },
    instantiate_doc_single_plot: function(docid, view_model_id, target_el, host) {
      if (target_el == null) {
        target_el = "#PlotPane";
      }
      if (host == null) {
        host = "www.wakari.io";
      }
      utility.bokeh_connection(host, docid, "https");
      return Deferreds._doc_loaded.done(function(data) {
        utility.render_plots(data.plot_context_ref, container.SinglePlotContextView, {
          target_model_id: view_model_id
        });
        return $(target_el).empty().append(exports.plotcontextview.el);
      });
    }
  };

  exports.utility = utility;

}).call(this);
}, "usercontext/wrappertemplate": function(exports, require, module) {module.exports = function(__obj) {
  if (!__obj) __obj = {};
  var __out = [], __capture = function(callback) {
    var out = __out, result;
    __out = [];
    callback.call(this);
    result = __out.join('');
    __out = out;
    return __safe(result);
  }, __sanitize = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else if (typeof value !== 'undefined' && value != null) {
      return __escape(value);
    } else {
      return '';
    }
  }, __safe, __objSafe = __obj.safe, __escape = __obj.escape;
  __safe = __obj.safe = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else {
      if (!(typeof value !== 'undefined' && value != null)) value = '';
      var result = new String(value);
      result.ecoSafe = true;
      return result;
    }
  };
  if (!__escape) {
    __escape = __obj.escape = function(value) {
      return ('' + value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    };
  }
  (function() {
    (function() {
    
      __out.push('<div class="accordion-heading bokehdocheading">\n  <a class="accordion-toggle bokehdoclabel" data-toggle="collapse" \n     href="#');
    
      __out.push(__sanitize(this.bodyid));
    
      __out.push('">\n    Document: ');
    
      __out.push(__sanitize(this.model.get('title')));
    
      __out.push('\n    <i class="bokehdelete icon-trash"></i>\n  </a>\n</div>\n<div id="');
    
      __out.push(__sanitize(this.bodyid));
    
      __out.push('" class="accordion-body collapse">\n  <div class="accordion-inner">\n  </div>\n</div>\n\n\n');
    
    }).call(this);
    
  }).call(__obj);
  __obj.safe = __objSafe, __obj.escape = __escape;
  return __out.join('');
}}, "usercontext/documentationtemplate": function(exports, require, module) {module.exports = function(__obj) {
  if (!__obj) __obj = {};
  var __out = [], __capture = function(callback) {
    var out = __out, result;
    __out = [];
    callback.call(this);
    result = __out.join('');
    __out = out;
    return __safe(result);
  }, __sanitize = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else if (typeof value !== 'undefined' && value != null) {
      return __escape(value);
    } else {
      return '';
    }
  }, __safe, __objSafe = __obj.safe, __escape = __obj.escape;
  __safe = __obj.safe = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else {
      if (!(typeof value !== 'undefined' && value != null)) value = '';
      var result = new String(value);
      result.ecoSafe = true;
      return result;
    }
  };
  if (!__escape) {
    __escape = __obj.escape = function(value) {
      return ('' + value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    };
  }
  (function() {
    (function() {
    
      __out.push('<p>\n  <b>\n    You have no Plots.  Follow the intsructions\n    below to create some\n  </b>\n</p>\n');
    
    }).call(this);
    
  }).call(__obj);
  __obj.safe = __objSafe, __obj.escape = __escape;
  return __out.join('');
}}, "usercontext/usercontext": function(exports, require, module) {(function() {
  var ContinuumView, HasParent, HasProperties, PlotContextWrapper, UserDoc, UserDocs, UserDocsView, base, build_views, documentationtemplate, load_models, template, userdocstemplate, utility,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("../base");

  ContinuumView = base.ContinuumView;

  HasParent = base.HasParent;

  HasProperties = base.HasProperties;

  load_models = base.load_models;

  template = require("./wrappertemplate");

  userdocstemplate = require("./userdocstemplate");

  documentationtemplate = require("./documentationtemplate");

  utility = require("../serverutils").utility;

  build_views = base.build_views;

  PlotContextWrapper = (function(_super) {

    __extends(PlotContextWrapper, _super);

    function PlotContextWrapper() {
      return PlotContextWrapper.__super__.constructor.apply(this, arguments);
    }

    PlotContextWrapper.prototype.events = {
      "click .bokehdoclabel": "loaddoc",
      "click .bokehdelete": "deldoc"
    };

    PlotContextWrapper.prototype.deldoc = function(e) {
      console.log('foo');
      e.preventDefault();
      this.model.destroy();
      return false;
    };

    PlotContextWrapper.prototype.loaddoc = function() {
      return this.model.load();
    };

    PlotContextWrapper.prototype.initialize = function(options) {
      PlotContextWrapper.__super__.initialize.call(this, options);
      return this.render_init();
    };

    PlotContextWrapper.prototype.delegateEvents = function(events) {
      PlotContextWrapper.__super__.delegateEvents.call(this, events);
      return this.listenTo(this.model, 'loaded', this.render);
    };

    PlotContextWrapper.prototype.render_init = function() {
      var html;
      html = template({
        model: this.model,
        bodyid: _.uniqueId()
      });
      this.$el.html(html);
      return this.$el.addClass('accordion-group');
    };

    PlotContextWrapper.prototype.render = function() {
      var plot_context;
      plot_context = this.model.get_obj('plot_context');
      this.plot_context_view = new plot_context.default_view({
        model: plot_context
      });
      this.$el.find('.accordion-inner').append(this.plot_context_view.el);
      return true;
    };

    return PlotContextWrapper;

  })(ContinuumView);

  UserDocsView = (function(_super) {

    __extends(UserDocsView, _super);

    function UserDocsView() {
      return UserDocsView.__super__.constructor.apply(this, arguments);
    }

    UserDocsView.prototype.initialize = function(options) {
      this.docs = options.docs;
      this.collection = options.collection;
      this.views = {};
      UserDocsView.__super__.initialize.call(this, options);
      return this.render();
    };

    UserDocsView.prototype.attributes = {
      "class": 'usercontext'
    };

    UserDocsView.prototype.events = {
      'click .bokehrefresh': function() {
        return this.collection.fetch({
          update: true
        });
      }
    };

    UserDocsView.prototype.delegateEvents = function(events) {
      var _this = this;
      UserDocsView.__super__.delegateEvents.call(this, events);
      this.listenTo(this.collection, 'add', this.render);
      this.listenTo(this.collection, 'remove', this.render);
      this.listenTo(this.collection, 'add', function(model, collection, options) {
        return _this.listenTo(model, 'loaded', function() {
          return _this.listenTo(model.get_obj('plot_context'), 'change', function() {
            return _this.trigger('show');
          });
        });
      });
      return this.listenTo(this.collection, 'remove', function(model, collection, options) {
        return _this.stopListening(model);
      });
    };

    UserDocsView.prototype.render_docs = function() {
      this.$el.html(documentationtemplate());
      return this.$el.append(this.docs);
    };

    UserDocsView.prototype.render = function() {
      var html, model, models, _i, _len;
      if (this.collection.models.length === 0 && this.docs) {
        return this.render_docs();
      }
      html = userdocstemplate();
      _.map(_.values(this.views), function(view) {
        return view.$el.detach();
      });
      models = this.collection.models.slice().reverse();
      build_views(this.views, models, {});
      this.$el.html(html);
      for (_i = 0, _len = models.length; _i < _len; _i++) {
        model = models[_i];
        this.$el.find(".accordion").append(this.views[model.id].el);
      }
      return this;
    };

    return UserDocsView;

  })(ContinuumView);

  UserDoc = (function(_super) {

    __extends(UserDoc, _super);

    function UserDoc() {
      return UserDoc.__super__.constructor.apply(this, arguments);
    }

    UserDoc.prototype.default_view = PlotContextWrapper;

    UserDoc.prototype.idAttribute = 'docid';

    UserDoc.prototype.defaults = {
      docid: null,
      title: null,
      plot_context: null,
      apikey: null
    };

    UserDoc.prototype.sync = function() {};

    UserDoc.prototype.destroy = function(options) {
      UserDoc.__super__.destroy.call(this, options);
      return $.ajax({
        url: "/bokeh/doc/" + (this.get('docid')) + "/",
        type: 'delete'
      });
    };

    UserDoc.prototype.load = function() {
      var docid, resp,
        _this = this;
      if (this.loaded) {
        return;
      }
      docid = this.get('docid');
      resp = utility.load_doc(docid);
      return resp.done(function(data) {
        _this.set('apikey', data['apikey']);
        _this.set('plot_context', data['plot_context_ref']);
        _this.trigger('loaded');
        return _this.loaded = true;
      });
    };

    return UserDoc;

  })(HasParent);

  UserDocs = (function(_super) {

    __extends(UserDocs, _super);

    function UserDocs() {
      return UserDocs.__super__.constructor.apply(this, arguments);
    }

    UserDocs.prototype.model = UserDoc;

    UserDocs.prototype.subscribe = function(wswrapper, username) {
      wswrapper.subscribe("bokehuser:" + username, null);
      return this.listenTo(wswrapper, "msg:bokehuser:" + username, function(msg) {
        msg = JSON.parse(msg);
        if (msg['msgtype'] === 'docchange') {
          return this.fetch({
            update: true
          });
        }
      });
    };

    UserDocs.prototype.fetch = function(options) {
      var resp, response,
        _this = this;
      if (_.isUndefined(options)) {
        options = {};
      }
      resp = response = $.get('/bokeh/userinfo/', {});
      resp.done(function(data) {
        var docs;
        docs = data['docs'];
        if (options.update) {
          return _this.update(docs, options);
        } else {
          return _this.reset(docs, options);
        }
      });
      return resp;
    };

    return UserDocs;

  })(Backbone.Collection);

  exports.UserDocs = UserDocs;

  exports.UserDocsView = UserDocsView;

}).call(this);
}, "usercontext/userdocstemplate": function(exports, require, module) {module.exports = function(__obj) {
  if (!__obj) __obj = {};
  var __out = [], __capture = function(callback) {
    var out = __out, result;
    __out = [];
    callback.call(this);
    result = __out.join('');
    __out = out;
    return __safe(result);
  }, __sanitize = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else if (typeof value !== 'undefined' && value != null) {
      return __escape(value);
    } else {
      return '';
    }
  }, __safe, __objSafe = __obj.safe, __escape = __obj.escape;
  __safe = __obj.safe = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else {
      if (!(typeof value !== 'undefined' && value != null)) value = '';
      var result = new String(value);
      result.ecoSafe = true;
      return result;
    }
  };
  if (!__escape) {
    __escape = __obj.escape = function(value) {
      return ('' + value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    };
  }
  (function() {
    (function() {
    
      __out.push('<div class="accordion">\n</div>\n');
    
    }).call(this);
    
  }).call(__obj);
  __obj.safe = __objSafe, __obj.escape = __escape;
  return __out.join('');
}}, "serverrun": function(exports, require, module) {(function() {
  var Config, Promises, base, container, usercontext, utility, utils;

  utils = require("./serverutils");

  base = require("./base");

  container = require("./container");

  Config = base.Config;

  utility = utils.utility;

  Promises = utils.Promises;

  Config.ws_conn_string = "ws://" + window.location.host + "/bokeh/sub";

  usercontext = require("usercontext/usercontext");

  $(function() {
    var load, userdocs, wswrapper;
    wswrapper = utility.make_websocket();
    userdocs = new usercontext.UserDocs();
    window.userdocs = userdocs;
    load = userdocs.fetch();
    return load.done(function() {
      var userdocsview;
      userdocsview = new usercontext.UserDocsView({
        collection: userdocs
      });
      return $('#PlotPane').append(userdocsview.el);
    });
  });

}).call(this);
}, "guides": function(exports, require, module) {(function() {
  var HasParent, Legend, LegendRendererView, Legends, LinearAxes, LinearAxis, LinearAxisView, LinearDateAxes, LinearDateAxis, LinearDateAxisView, LinearMapper, PlotWidget, base, mapper, safebind, ticks,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  ticks = require("./ticks");

  safebind = base.safebind;

  HasParent = base.HasParent;

  PlotWidget = base.PlotWidget;

  mapper = require("./mapper");

  LinearMapper = mapper.LinearMapper;

  LinearAxisView = (function(_super) {

    __extends(LinearAxisView, _super);

    function LinearAxisView() {
      return LinearAxisView.__super__.constructor.apply(this, arguments);
    }

    LinearAxisView.prototype.initialize = function(options) {
      LinearAxisView.__super__.initialize.call(this, options);
      this.plot_view = options.plot_view;
      if (this.mget('orientation') === 'top' || this.mget('orientation') === 'bottom') {
        this.screendim = 'width';
      } else {
        this.screendim = 'height';
      }
      return this.set_mapper();
    };

    LinearAxisView.prototype.bind_bokeh_events = function() {
      safebind(this, this.plot_model, 'change', this.request_render);
      safebind(this, this.model, 'change', this.request_render);
      safebind(this, this.model, 'change:data_range', this.set_mapper);
      return safebind(this, this.mget_obj('data_range'), 'change', this.request_render);
    };

    LinearAxisView.prototype.set_mapper = function() {
      this.mapper = new LinearMapper({}, {
        data_range: this.mget_obj('data_range'),
        viewstate: this.plot_view.viewstate,
        screendim: this.screendim
      });
      return this.request_render();
    };

    LinearAxisView.prototype.tagName = 'div';

    LinearAxisView.prototype.get_offsets = function(orientation) {
      var offsets;
      offsets = {
        x: 0,
        y: 0
      };
      if (orientation === 'bottom') {
        offsets['y'] += this.plot_view.viewstate.get('height');
      }
      return offsets;
    };

    LinearAxisView.prototype.get_tick_size = function(orientation) {
      if (!_.isNull(this.mget('tickSize'))) {
        return this.mget('tickSize');
      } else {
        if (orientation === 'bottom') {
          return -this.plot_view.viewstate.get('height');
        } else {
          return -this.plot_view.viewstate.get('width');
        }
      }
    };

    LinearAxisView.prototype.render = function() {
      var unselected_color, _ref;
      LinearAxisView.__super__.render.call(this);
      unselected_color = "#ccc";
      this.plot_view.ctx.fillStyle = unselected_color;
      this.plot_view.ctx.strokeStyle = unselected_color;
      if ((_ref = this.mget('orientation')) === 'bottom' || _ref === 'top') {
        this.render_x();
        this.render_end();
        return;
      }
      this.render_y();
      this.render_end();
    };

    LinearAxisView.prototype.tick_label = function(tick) {
      return tick.toString();
    };

    LinearAxisView.prototype.render_x = function() {
      var can_ctx, current_tick, data_range, first_tick, interval, last_tick, last_tick_end, range, text_width, txtpos, x, x_scale, x_ticks, _ref;
      can_ctx = this.plot_view.x_can_ctx;
      data_range = this.mapper.data_range;
      interval = ticks.auto_interval(data_range.get('start'), data_range.get('end'));
      range = data_range.get('end') - data_range.get('start');
      x_scale = this.mapper.get('scalestate')[0];
      last_tick_end = 10000;
      _ref = ticks.auto_bounds(data_range.get('start'), data_range.get('end'), interval), first_tick = _ref[0], last_tick = _ref[1];
      current_tick = first_tick;
      x_ticks = [];
      last_tick_end = 0;
      can_ctx.clearRect(0, 0, this.plot_view.viewstate.get('width'), this.plot_view.viewstate.get('height'));
      while (current_tick <= last_tick) {
        x_ticks.push(current_tick);
        text_width = can_ctx.measureText(this.tick_label(current_tick)).width;
        x = this.plot_view.viewstate.xpos(this.mapper.map_screen(current_tick));
        txtpos = x - (text_width / 2);
        if (txtpos > last_tick_end) {
          can_ctx.fillText(this.tick_label(current_tick), txtpos, 20);
          last_tick_end = (txtpos + text_width) + 10;
        }
        this.plot_view.ctx.beginPath();
        this.plot_view.ctx.moveTo(x, 0);
        this.plot_view.ctx.lineTo(x, this.plot_view.viewstate.get('height'));
        this.plot_view.ctx.stroke();
        current_tick += interval;
      }
      can_ctx.stroke();
      return this.render_end();
    };

    LinearAxisView.prototype.DEFAULT_TEXT_HEIGHT = 8;

    LinearAxisView.prototype.render_y = function() {
      var can_ctx, current_tick, data_range, first_tick, interval, last_tick, last_tick_end, range, txtpos, y, y_scale, y_ticks, _ref;
      can_ctx = this.plot_view.y_can_ctx;
      data_range = this.mapper.data_range;
      interval = ticks.auto_interval(data_range.get('start'), data_range.get('end'));
      range = data_range.get('end') - data_range.get('start');
      y_scale = this.mapper.get('scalestate')[0];
      _ref = ticks.auto_bounds(data_range.get('start'), data_range.get('end'), interval), first_tick = _ref[0], last_tick = _ref[1];
      current_tick = first_tick;
      y_ticks = [];
      last_tick_end = 10000;
      can_ctx.clearRect(0, 0, this.plot_view.viewstate.get('width'), this.plot_view.viewstate.get('height'));
      while (current_tick <= last_tick) {
        y_ticks.push(current_tick);
        y = this.plot_view.viewstate.ypos(this.mapper.map_screen(current_tick));
        txtpos = y + (this.DEFAULT_TEXT_HEIGHT / 2);
        if (y < last_tick_end) {
          can_ctx.fillText(this.tick_label(current_tick), 0, y);
          last_tick_end = (y + this.DEFAULT_TEXT_HEIGHT) + 10;
        }
        this.plot_view.ctx.beginPath();
        this.plot_view.ctx.moveTo(0, y);
        this.plot_view.ctx.lineTo(this.plot_view.viewstate.get('width'), y);
        this.plot_view.ctx.stroke();
        current_tick += interval;
      }
      can_ctx.stroke();
      return this.render_end();
    };

    return LinearAxisView;

  })(PlotWidget);

  LinearDateAxisView = (function(_super) {

    __extends(LinearDateAxisView, _super);

    function LinearDateAxisView() {
      return LinearDateAxisView.__super__.constructor.apply(this, arguments);
    }

    LinearDateAxisView.prototype.tick_label = function(tick) {
      var end, one_day, start;
      start = this.mget_obj('data_range').get('start');
      end = this.mget_obj('data_range').get('end');
      one_day = 3600 * 24 * 1000;
      tick = new Date(tick);
      if ((Math.abs(end - start)) > (one_day * 2)) {
        return tick.toLocaleDateString();
      } else {
        return tick.toLocaleTimeString();
      }
    };

    return LinearDateAxisView;

  })(LinearAxisView);

  LegendRendererView = (function(_super) {

    __extends(LegendRendererView, _super);

    function LegendRendererView() {
      return LegendRendererView.__super__.constructor.apply(this, arguments);
    }

    LegendRendererView.prototype.render = function() {
      var can_ctx, coords, l, legend_height, legend_offset_x, legend_offset_y, legend_width, start_x, start_y, text_height, x, y, _i, _len, _ref;
      LegendRendererView.__super__.render.call(this);
      can_ctx = this.plot_view.ctx;
      coords = this.model.get('coords');
      x = coords[0], y = coords[1];
      if (x < 0) {
        start_x = this.plot_view.viewstate.get('width') + x;
      } else {
        start_x = x;
      }
      if (y < 0) {
        start_y = this.plot_view.viewstate.get('height') + y;
      } else {
        start_y = y;
      }
      text_height = 20;
      legend_height = text_height * this.model.get('legends').length;
      legend_width = 100;
      legend_offset_x = start_x;
      legend_offset_y = start_y;
      can_ctx.strokeStyle = 'black';
      can_ctx.strokeRect(legend_offset_x, legend_offset_y, legend_width, legend_height);
      can_ctx.fillStyle = 'white';
      can_ctx.fillRect(legend_offset_x, legend_offset_y, legend_width, legend_height);
      can_ctx.strokeStyle = 'black';
      can_ctx.fillStyle = 'black';
      legend_offset_x += 5;
      legend_offset_y += 10;
      _ref = this.model.get('legends');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        l = _ref[_i];
        console.log("l.name", l.name, l, legend_offset_x, legend_offset_y);
        can_ctx.strokeStyle = l.color;
        can_ctx.fillStyle = l.color;
        can_ctx.fillText(l.name, legend_offset_x, legend_offset_y);
        legend_offset_y += text_height;
      }
      can_ctx.stroke();
      this.render_end();
      return null;
    };

    return LegendRendererView;

  })(PlotWidget);

  LinearAxis = (function(_super) {

    __extends(LinearAxis, _super);

    function LinearAxis() {
      return LinearAxis.__super__.constructor.apply(this, arguments);
    }

    LinearAxis.prototype.type = 'LinearAxis';

    LinearAxis.prototype.default_view = LinearAxisView;

    LinearAxis.prototype.display_defaults = {
      tick_color: '#fff'
    };

    return LinearAxis;

  })(HasParent);

  LinearAxis.prototype.defaults = _.clone(LinearAxis.prototype.defaults);

  _.extend(LinearAxis.prototype.defaults, {
    data_range: null,
    orientation: 'bottom',
    ticks: 10,
    ticksSubdivide: 1,
    tickSize: null,
    tickPadding: 3
  });

  LinearAxes = (function(_super) {

    __extends(LinearAxes, _super);

    function LinearAxes() {
      return LinearAxes.__super__.constructor.apply(this, arguments);
    }

    LinearAxes.prototype.model = LinearAxis;

    return LinearAxes;

  })(Backbone.Collection);

  LinearDateAxis = (function(_super) {

    __extends(LinearDateAxis, _super);

    function LinearDateAxis() {
      return LinearDateAxis.__super__.constructor.apply(this, arguments);
    }

    LinearDateAxis.prototype.type = "LinearDateAxis";

    LinearDateAxis.prototype.default_view = LinearDateAxisView;

    return LinearDateAxis;

  })(LinearAxis);

  LinearDateAxes = (function(_super) {

    __extends(LinearDateAxes, _super);

    function LinearDateAxes() {
      return LinearDateAxes.__super__.constructor.apply(this, arguments);
    }

    LinearDateAxes.prototype.model = LinearDateAxis;

    return LinearDateAxes;

  })(Backbone.Collection);

  Legend = (function(_super) {

    __extends(Legend, _super);

    function Legend() {
      return Legend.__super__.constructor.apply(this, arguments);
    }

    Legend.prototype.type = "Legend";

    Legend.prototype.default_view = LegendRendererView;

    Legend.prototype.defaults = {
      renderers: [],
      unselected_color: "#ccc",
      positions: {
        top_left: [20, 20],
        top_right: [-80, 20],
        bottom_left: [20, -60],
        bottom_right: [-80, -60]
      },
      position: "top_left"
    };

    Legend.prototype.initialize = function(options) {
      var ptype;
      Legend.__super__.initialize.call(this, options);
      console.log("options", options);
      ptype = typeof options.position;
      if (ptype === "string") {
        return this.set('coords', this.defaults.positions[options.position]);
      } else if (ptype === "object") {
        return this.set('coords', options.position);
      }
    };

    return Legend;

  })(HasParent);

  Legends = (function(_super) {

    __extends(Legends, _super);

    function Legends() {
      return Legends.__super__.constructor.apply(this, arguments);
    }

    Legends.prototype.model = Legend;

    return Legends;

  })(Backbone.Collection);

  exports.linearaxes = new LinearAxes;

  exports.lineardateaxes = new LinearDateAxes;

  exports.legends = new Legends;

  exports.LinearAxisView = LinearAxisView;

  exports.LinearDateAxisView = LinearDateAxisView;

  exports.LegendRendererView = LegendRendererView;

}).call(this);
}, "renderers/glyph": function(exports, require, module) {(function() {
  var Collections, Glyph, GlyphView, Glyphs, HasParent, LinearMapper, PlotWidget, base, mapper, safebind,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require('../base');

  Collections = base.Collections;

  HasParent = base.HasParent;

  PlotWidget = base.PlotWidget;

  safebind = base.safebind;

  mapper = require('../mapper');

  LinearMapper = mapper.LinearMapper;

  GlyphView = (function(_super) {

    __extends(GlyphView, _super);

    function GlyphView() {
      return GlyphView.__super__.constructor.apply(this, arguments);
    }

    GlyphView.prototype.initialize = function(options) {
      GlyphView.__super__.initialize.call(this, options);
      this.set_xmapper();
      return this.set_ymapper();
    };

    GlyphView.prototype.render = function() {
      var data, source;
      source = this.mget_obj('data_source');
      if (source.type === 'ObjectArrayDataSource') {
        data = source.get('data');
      } else if (source.type === 'ColumnDataSource') {
        data = source.datapoints();
      } else {
        console.log('Unknown data source type: ' + source.type);
      }
      return this._render(data);
    };

    GlyphView.prototype.bind_bokeh_events = function() {
      safebind(this, this.model, 'change', this.request_render);
      safebind(this, this.plot_view.viewstate, 'change', this.request_render);
      safebind(this, this.mget_obj('data_source'), 'change', this.request_render);
      safebind(this, this.model, 'change:xdata_range', this.set_xmapper);
      safebind(this, this.model, 'change:ydata_range', this.set_ymapper);
      safebind(this, this.mget_obj('xdata_range'), 'change', this.request_render);
      return safebind(this, this.mget_obj('ydata_range'), 'change', this.request_render);
    };

    GlyphView.prototype.set_xmapper = function() {
      this.xmapper = new LinearMapper({}, {
        data_range: this.mget_obj('xdata_range'),
        viewstate: this.plot_view.viewstate,
        screendim: 'width'
      });
      return this.request_render();
    };

    GlyphView.prototype.set_ymapper = function() {
      this.ymapper = new LinearMapper({}, {
        data_range: this.mget_obj('ydata_range'),
        viewstate: this.plot_view.viewstate,
        screendim: 'height'
      });
      return this.request_render();
    };

    GlyphView.prototype.distance = function(data, pt, span, position) {
      var d, halfspan, i, pt0, pt1, pt_units, ptc, span_units, spt0, spt1, x;
      pt_units = this.glyph_props[pt].units;
      span_units = this.glyph_props[span].units;
      if (pt === 'x') {
        mapper = this.xmapper;
      } else if (pt === 'y') {
        mapper = this.ymapper;
      }
      span = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          x = data[_i];
          _results.push(this.glyph_props.select(span, x));
        }
        return _results;
      }).call(this);
      if (span_units === 'screen') {
        return span;
      }
      if (position === 'center') {
        halfspan = (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = span.length; _i < _len; _i++) {
            d = span[_i];
            _results.push(d / 2);
          }
          return _results;
        })();
        ptc = (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = data.length; _i < _len; _i++) {
            x = data[_i];
            _results.push(this.glyph_props.select(pt, x));
          }
          return _results;
        }).call(this);
        if (pt_units === 'screen') {
          ptc = mapper.v_map_data(ptc);
        }
        pt0 = (function() {
          var _i, _ref, _results;
          _results = [];
          for (i = _i = 0, _ref = ptc.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
            _results.push(ptc[i] - halfspan[i]);
          }
          return _results;
        })();
        pt1 = (function() {
          var _i, _ref, _results;
          _results = [];
          for (i = _i = 0, _ref = ptc.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
            _results.push(ptc[i] + halfspan[i]);
          }
          return _results;
        })();
      } else {
        pt0 = (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = data.length; _i < _len; _i++) {
            x = data[_i];
            _results.push(this.glyph_props.select(pt, x));
          }
          return _results;
        }).call(this);
        if (pt_units === 'screen') {
          pt0 = mapper.v_map_data(pt0);
        }
        pt1 = (function() {
          var _i, _ref, _results;
          _results = [];
          for (i = _i = 0, _ref = pt0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
            _results.push(pt0[i] + span[i]);
          }
          return _results;
        })();
      }
      spt0 = mapper.v_map_screen(pt0);
      spt1 = mapper.v_map_screen(pt1);
      return (function() {
        var _i, _ref, _results;
        _results = [];
        for (i = _i = 0, _ref = spt0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          _results.push(spt1[i] - spt0[i]);
        }
        return _results;
      })();
    };

    GlyphView.prototype.map_to_screen = function(x, x_units, y, y_units) {
      var sx, sy;
      sx = new Array(x.length);
      sy = new Array(y.length);
      if (x_units === 'screen') {
        sx = x;
      } else {
        sx = this.xmapper.v_map_screen(x);
        sx = this.plot_view.viewstate.v_xpos(sx);
      }
      if (y_units === 'screen') {
        sy = y;
      } else {
        sy = this.ymapper.v_map_screen(y);
        sy = this.plot_view.viewstate.v_ypos(sy);
      }
      return [sx, sy];
    };

    return GlyphView;

  })(PlotWidget);

  Glyph = (function(_super) {

    __extends(Glyph, _super);

    function Glyph() {
      return Glyph.__super__.constructor.apply(this, arguments);
    }

    return Glyph;

  })(HasParent);

  Glyph.prototype.defaults = _.clone(Glyph.prototype.defaults);

  _.extend(Glyph.prototype.defaults, {
    data_source: null
  });

  Glyph.prototype.display_defaults = _.clone(Glyph.prototype.display_defaults);

  _.extend(Glyph.prototype.display_defaults, {
    radius_units: 'screen',
    length_units: 'screen',
    angle_units: 'deg',
    start_angle_units: 'deg',
    end_angle_units: 'deg'
  });

  Glyphs = (function(_super) {

    __extends(Glyphs, _super);

    function Glyphs() {
      return Glyphs.__super__.constructor.apply(this, arguments);
    }

    Glyphs.prototype.model = Glyph;

    return Glyphs;

  })(Backbone.Collection);

  exports.glyphs = new Glyphs;

  exports.GlyphView = GlyphView;

  exports.Glyph = Glyph;

}).call(this);
}, "renderers/oval": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Oval, OvalView, Ovals, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  OvalView = (function(_super) {

    __extends(OvalView, _super);

    function OvalView() {
      return OvalView.__super__.constructor.apply(this, arguments);
    }

    OvalView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'width', 'height', 'angle'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return OvalView.__super__.initialize.call(this, options);
    };

    OvalView.prototype._render = function(data) {
      var ctx, glyph_props, obj, x, y, _ref;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.sw = this.distance(data, 'x', 'width', 'center');
      this.sh = this.distance(data, 'y', 'height', 'center');
      this.angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('angle', obj));
        }
        return _results;
      })();
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    OvalView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _j, _ref, _ref1;
      if (this.do_fill) {
        glyph_props.fill_properties.set(ctx, glyph);
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
            continue;
          }
          ctx.translate(this.sx[i], this.sy[i]);
          ctx.rotate(this.angle[i]);
          ctx.beginPath();
          ctx.moveTo(0, -this.sh[i] / 2);
          ctx.bezierCurveTo(this.sw[i] / 2, -this.sh[i] / 2, this.sw[i] / 2, this.sh[i] / 2, 0, this.sh[i] / 2);
          ctx.bezierCurveTo(-this.sw[i] / 2, this.sh[i] / 2, -this.sw[i] / 2, -this.sh[i] / 2, 0, -this.sh[i] / 2);
          ctx.closePath();
          ctx.fill();
          ctx.rotate(-this.angle[i]);
          ctx.translate(-this.sx[i], -this.sy[i]);
        }
      }
      if (this.do_fill) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _j = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
          if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
            continue;
          }
          ctx.translate(this.sx[i], this.sy[i]);
          ctx.rotate(this.angle[i]);
          ctx.moveTo(0, -this.sh[i] / 2);
          ctx.bezierCurveTo(this.sw[i] / 2, -this.sh[i] / 2, this.sw[i] / 2, this.sh[i] / 2, 0, this.sh[i] / 2);
          ctx.bezierCurveTo(-this.sw[i] / 2, this.sh[i] / 2, -this.sw[i] / 2, -this.sh[i] / 2, 0, -this.sh[i] / 2);
          ctx.rotate(-this.angle[i]);
          ctx.translate(-this.sx[i], -this.sy[i]);
        }
        return ctx.stroke();
      }
    };

    OvalView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
          continue;
        }
        ctx.translate(this.sx[i], this.sy[i]);
        ctx.rotate(this.angle[i]);
        ctx.beginPath();
        ctx.moveTo(0, -this.sh[i] / 2);
        ctx.bezierCurveTo(this.sw[i] / 2, -this.sh[i] / 2, this.sw[i] / 2, this.sh[i] / 2, 0, this.sh[i] / 2);
        ctx.bezierCurveTo(-this.sw[i] / 2, this.sh[i] / 2, -this.sw[i] / 2, -this.sh[i] / 2, 0, -this.sh[i] / 2);
        ctx.closePath();
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, data[i]);
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, data[i]);
          ctx.stroke();
        }
        ctx.rotate(-this.angle[i]);
        _results.push(ctx.translate(-this.sx[i], -this.sy[i]));
      }
      return _results;
    };

    return OvalView;

  })(GlyphView);

  Oval = (function(_super) {

    __extends(Oval, _super);

    function Oval() {
      return Oval.__super__.constructor.apply(this, arguments);
    }

    Oval.prototype.default_view = OvalView;

    Oval.prototype.type = 'GlyphRenderer';

    return Oval;

  })(Glyph);

  Oval.prototype.display_defaults = _.clone(Oval.prototype.display_defaults);

  _.extend(Oval.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0,
    angle: 0.0
  });

  Ovals = (function(_super) {

    __extends(Ovals, _super);

    function Ovals() {
      return Ovals.__super__.constructor.apply(this, arguments);
    }

    Ovals.prototype.model = Oval;

    return Ovals;

  })(Backbone.Collection);

  exports.ovals = new Ovals;

  exports.Oval = Oval;

  exports.OvalView = OvalView;

}).call(this);
}, "renderers/ray": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Ray, RayView, Rays, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  RayView = (function(_super) {

    __extends(RayView, _super);

    function RayView() {
      return RayView.__super__.constructor.apply(this, arguments);
    }

    RayView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'angle', 'length'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return RayView.__super__.initialize.call(this, options);
    };

    RayView.prototype._render = function(data) {
      var ctx, glyph_props, height, i, inf_len, obj, width, x, y, _i, _ref, _ref1;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      width = this.plot_view.viewstate.get('width');
      height = this.plot_view.viewstate.get('height');
      inf_len = 2 * (width + height);
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('angle', obj));
        }
        return _results;
      })();
      this.length = glyph_props.v_select('length', data);
      for (i = _i = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _i <= _ref1 : _i >= _ref1; i = 0 <= _ref1 ? ++_i : --_i) {
        if (this.length[i] === 0) {
          this.length[i] = inf_len;
        }
      }
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    RayView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.angle[i] + this.length[i])) {
            continue;
          }
          ctx.translate(this.sx[i], this.sy[i]);
          ctx.rotate(this.angle[i]);
          ctx.moveTo(0, 0);
          ctx.lineTo(this.length[i], 0);
          ctx.rotate(-this.angle[i]);
          ctx.translate(-this.sx[i], -this.sy[i]);
        }
        return ctx.stroke();
      }
    };

    RayView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        _results = [];
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.angle[i] + this.length[i])) {
            continue;
          }
          ctx.translate(this.sx[i], this.sy[i]);
          ctx.rotate(this.angle[i]);
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(this.length[i], 0);
          glyph_props.line_properties.set(ctx, data[i]);
          ctx.stroke();
          ctx.rotate(-this.angle[i]);
          _results.push(ctx.translate(-this.sx[i], -this.sy[i]));
        }
        return _results;
      }
    };

    return RayView;

  })(GlyphView);

  Ray = (function(_super) {

    __extends(Ray, _super);

    function Ray() {
      return Ray.__super__.constructor.apply(this, arguments);
    }

    Ray.prototype.default_view = RayView;

    Ray.prototype.type = 'GlyphRenderer';

    return Ray;

  })(Glyph);

  Ray.prototype.display_defaults = _.clone(Ray.prototype.display_defaults);

  _.extend(Ray.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Rays = (function(_super) {

    __extends(Rays, _super);

    function Rays() {
      return Rays.__super__.constructor.apply(this, arguments);
    }

    Rays.prototype.model = Ray;

    return Rays;

  })(Backbone.Collection);

  exports.rays = new Rays;

  exports.Ray = Ray;

  exports.RayView = RayView;

}).call(this);
}, "renderers/bezier": function(exports, require, module) {(function() {
  var Bezier, BezierView, Beziers, Glyph, GlyphView, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  BezierView = (function(_super) {

    __extends(BezierView, _super);

    function BezierView() {
      return BezierView.__super__.constructor.apply(this, arguments);
    }

    BezierView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x0', 'y0', 'x1', 'y1', 'cx0', 'cy0', 'cx1', 'cy1'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return BezierView.__super__.initialize.call(this, options);
    };

    BezierView.prototype._render = function(data) {
      var ctx, cx0, cx1, cy0, cy1, glyph_props, x0, x1, y0, y1, _ref, _ref1, _ref2, _ref3;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x0 = glyph_props.v_select('x0', data);
      y0 = glyph_props.v_select('y0', data);
      _ref = this.map_to_screen(x0, glyph_props.x0.units, y0, glyph_props.y0.units), this.sx0 = _ref[0], this.sy0 = _ref[1];
      x1 = glyph_props.v_select('x1', data);
      y1 = glyph_props.v_select('y1', data);
      _ref1 = this.map_to_screen(x1, glyph_props.x1.units, y1, glyph_props.y1.units), this.sx1 = _ref1[0], this.sy1 = _ref1[1];
      cx0 = glyph_props.v_select('cx0', data);
      cy0 = glyph_props.v_select('cy0', data);
      _ref2 = this.map_to_screen(cx0, glyph_props.cx0.units, cy0, glyph_props.cy0.units), this.scx0 = _ref2[0], this.scy0 = _ref2[1];
      cx1 = glyph_props.v_select('cx1', data);
      cy1 = glyph_props.v_select('cy1', data);
      _ref3 = this.map_to_screen(cx1, glyph_props.cx1.units, cy1, glyph_props.cy1.units), this.scx1 = _ref3[0], this.scy1 = _ref3[1];
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    BezierView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i] + this.scx0[i] + this.scy0[i] + this.scx1[i] + this.scy1[i])) {
            continue;
          }
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.bezierCurveTo(this.scx0[i], this.scy0[i], this.scx1[i], this.scy1[i], this.sx1[i], this.sy1[i]);
        }
        return ctx.stroke();
      }
    };

    BezierView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        _results = [];
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i] + this.scx0[i] + this.scy0[i] + this.scx1[i] + this.scy1[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.bezierCurveTo(this.scx0[i], this.scy0[i], this.scx1[i], this.scy1[i], this.sx1[i], this.sy1[i]);
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    return BezierView;

  })(GlyphView);

  Bezier = (function(_super) {

    __extends(Bezier, _super);

    function Bezier() {
      return Bezier.__super__.constructor.apply(this, arguments);
    }

    Bezier.prototype.default_view = BezierView;

    Bezier.prototype.type = 'GlyphRenderer';

    return Bezier;

  })(Glyph);

  Bezier.prototype.display_defaults = _.clone(Bezier.prototype.display_defaults);

  _.extend(Bezier.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Beziers = (function(_super) {

    __extends(Beziers, _super);

    function Beziers() {
      return Beziers.__super__.constructor.apply(this, arguments);
    }

    Beziers.prototype.model = Bezier;

    return Beziers;

  })(Backbone.Collection);

  exports.beziers = new Beziers;

  exports.Bezier = Bezier;

  exports.BezierView = BezierView;

}).call(this);
}, "renderers/glyph_renderer": function(exports, require, module) {(function() {
  var Collections, GlyphRenderers, HasParent, base, prim,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require('../base');

  Collections = base.Collections;

  HasParent = base.HasParent;

  prim = require('./primitives');

  GlyphRenderers = (function(_super) {

    __extends(GlyphRenderers, _super);

    function GlyphRenderers() {
      return GlyphRenderers.__super__.constructor.apply(this, arguments);
    }

    GlyphRenderers.prototype.model = function(attrs, options) {
      var model, type, _ref;
      if (!(((_ref = attrs.glyphspec) != null ? _ref.type : void 0) != null)) {
        console.log("missing type");
        return;
      }
      type = attrs.glyphspec.type;
      if (!(type in prim)) {
        console.log("Unknown type '" + attrs.type + "'");
        return;
      }
      model = prim[type];
      return new model(attrs, options);
    };

    return GlyphRenderers;

  })(Backbone.Collection);

  exports.glyphrenderers = new GlyphRenderers;

}).call(this);
}, "renderers/quad": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Quad, QuadView, Quads, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  QuadView = (function(_super) {

    __extends(QuadView, _super);

    function QuadView() {
      return QuadView.__super__.constructor.apply(this, arguments);
    }

    QuadView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['right', 'left', 'bottom', 'top'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return QuadView.__super__.initialize.call(this, options);
    };

    QuadView.prototype._render = function(data) {
      var bottom, ctx, glyph_props, left, right, top, _ref, _ref1;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      left = glyph_props.v_select('left', data);
      top = glyph_props.v_select('top', data);
      _ref = this.map_to_screen(left, glyph_props.left.units, top, glyph_props.top.units), this.sx0 = _ref[0], this.sy0 = _ref[1];
      right = glyph_props.v_select('right', data);
      bottom = glyph_props.v_select('bottom', data);
      _ref1 = this.map_to_screen(right, glyph_props.right.units, bottom, glyph_props.bottom.units), this.sx1 = _ref1[0], this.sy1 = _ref1[1];
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    QuadView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _j, _ref, _ref1;
      if (this.do_fill) {
        glyph_props.fill_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i])) {
            continue;
          }
          ctx.rect(this.sx0[i], this.sy0[i], this.sx1[i] - this.sx0[i], this.sy1[i] - this.sy0[i]);
        }
        ctx.fill();
      }
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _j = 0, _ref1 = this.sx0.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i])) {
            continue;
          }
          ctx.rect(this.sx0[i], this.sy0[i], this.sx1[i] - this.sx0[i], this.sy1[i] - this.sy0[i]);
        }
        return ctx.stroke();
      }
    };

    QuadView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i])) {
          continue;
        }
        ctx.beginPath();
        ctx.rect(this.sx0[i], this.sy0[i], this.sx1[i] - this.sx0[i], this.sy1[i] - this.sy0[i]);
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, data[i]);
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    return QuadView;

  })(GlyphView);

  Quad = (function(_super) {

    __extends(Quad, _super);

    function Quad() {
      return Quad.__super__.constructor.apply(this, arguments);
    }

    Quad.prototype.default_view = QuadView;

    Quad.prototype.type = 'GlyphRenderer';

    return Quad;

  })(Glyph);

  Quad.prototype.display_defaults = _.clone(Quad.prototype.display_defaults);

  _.extend(Quad.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Quads = (function(_super) {

    __extends(Quads, _super);

    function Quads() {
      return Quads.__super__.constructor.apply(this, arguments);
    }

    Quads.prototype.model = Quad;

    return Quads;

  })(Backbone.Collection);

  exports.quads = new Quads;

  exports.Quad = Quad;

  exports.QuadView = QuadView;

}).call(this);
}, "renderers/circle": function(exports, require, module) {(function() {
  var Circle, CircleView, Circles, Glyph, GlyphView, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  CircleView = (function(_super) {

    __extends(CircleView, _super);

    function CircleView() {
      return CircleView.__super__.constructor.apply(this, arguments);
    }

    CircleView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'radius'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return CircleView.__super__.initialize.call(this, options);
    };

    CircleView.prototype._render = function(data) {
      var ctx, glyph_props, x, y, _ref;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.radius = this.distance(data, 'x', 'radius', 'edge');
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    CircleView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _j, _ref, _ref1, _results;
      if (this.do_fill) {
        glyph_props.fill_properties.set(ctx, glyph);
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], 0, 2 * Math.PI * 2, false);
          ctx.fill();
        }
      }
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        _results = [];
        for (i = _j = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], 0, 2 * Math.PI * 2, false);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    CircleView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.radius[i])) {
          continue;
        }
        ctx.beginPath();
        ctx.arc(this.sx[i], this.sy[i], this.radius[i], 0, 2 * Math.PI * 2, false);
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, data[i]);
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    return CircleView;

  })(GlyphView);

  Circle = (function(_super) {

    __extends(Circle, _super);

    function Circle() {
      return Circle.__super__.constructor.apply(this, arguments);
    }

    Circle.prototype.default_view = CircleView;

    Circle.prototype.type = 'GlyphRenderer';

    return Circle;

  })(Glyph);

  Circle.prototype.display_defaults = _.clone(Circle.prototype.display_defaults);

  _.extend(Circle.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Circles = (function(_super) {

    __extends(Circles, _super);

    function Circles() {
      return Circles.__super__.constructor.apply(this, arguments);
    }

    Circles.prototype.model = Circle;

    return Circles;

  })(Backbone.Collection);

  exports.circles = new Circles;

  exports.Circle = Circle;

  exports.CircleView = CircleView;

}).call(this);
}, "renderers/text": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Text, TextView, Texts, glyph, glyph_properties, properties, text_properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  text_properties = properties.text_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  TextView = (function(_super) {

    __extends(TextView, _super);

    function TextView() {
      return TextView.__super__.constructor.apply(this, arguments);
    }

    TextView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'angle', 'text:string'], [new text_properties(this, glyphspec)]);
      return TextView.__super__.initialize.call(this, options);
    };

    TextView.prototype._render = function(data) {
      var ctx, glyph_props, obj, x, y, _ref;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select("angle", obj));
        }
        return _results;
      })();
      this.text = glyph_props.v_select("text", data);
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    TextView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref, _results;
      glyph_props.text_properties.set(ctx, glyph);
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.angle[i])) {
          continue;
        }
        if (angle[i]) {
          ctx.translate(this.sx[i], this.sy[i]);
          ctx.rotate(this.angle[i]);
          ctx.fillText(this.text[i], 0, 0);
          ctx.rotate(-this.angle[i]);
          _results.push(ctx.translate(-this.sx[i], -this.sy[i]));
        } else {
          _results.push(ctx.fillText(text[i], this.sx[i], this.sy[i]));
        }
      }
      return _results;
    };

    TextView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.angle[i])) {
          continue;
        }
        ctx.translate(this.sx[i], this.sy[i]);
        ctx.rotate(this.angle[i]);
        glyph_props.text_properties.set(ctx, data[i]);
        ctx.fillText(this.text[i], 0, 0);
        ctx.rotate(-this.angle[i]);
        _results.push(ctx.translate(-this.sx[i], -this.sy[i]));
      }
      return _results;
    };

    return TextView;

  })(GlyphView);

  Text = (function(_super) {

    __extends(Text, _super);

    function Text() {
      return Text.__super__.constructor.apply(this, arguments);
    }

    Text.prototype.default_view = TextView;

    Text.prototype.type = 'GlyphRenderer';

    return Text;

  })(Glyph);

  Text.prototype.display_defaults = _.clone(Text.prototype.display_defaults);

  _.extend(Text.prototype.display_defaults, {
    text_font: "helvetica",
    text_font_size: "1em",
    text_font_style: "normal",
    text_color: "#444444",
    text_alpha: 1.0,
    text_align: "left",
    text_baseline: "bottom"
  });

  Texts = (function(_super) {

    __extends(Texts, _super);

    function Texts() {
      return Texts.__super__.constructor.apply(this, arguments);
    }

    Texts.prototype.model = Text;

    return Texts;

  })(Backbone.Collection);

  exports.texts = new Texts;

  exports.Text = Text;

  exports.TextView = TextView;

}).call(this);
}, "renderers/primitives": function(exports, require, module) {(function() {
  var arc, area, bezier, circle, image, line, oval, quad, quadcurve, ray, rect, segment, text, wedge;

  arc = require("./arc");

  area = require("./area");

  bezier = require("./bezier");

  circle = require("./circle");

  image = require("./image");

  line = require("./line");

  oval = require("./oval");

  quad = require("./quad");

  quadcurve = require("./quadcurve");

  ray = require("./ray");

  rect = require("./rect");

  segment = require("./segment");

  text = require("./text");

  wedge = require("./wedge");

  exports.arc = arc.Arc;

  exports.area = area.Area;

  exports.bezier = bezier.Bezier;

  exports.circle = circle.Circle;

  exports.image = image.Image;

  exports.line = line.Line;

  exports.oval = oval.Oval;

  exports.quad = quad.Quad;

  exports.quadcurve = quadcurve.Quadcurve;

  exports.ray = ray.Ray;

  exports.rect = rect.Rect;

  exports.segment = segment.Segment;

  exports.text = text.Text;

  exports.wedge = wedge.Wedge;

}).call(this);
}, "renderers/image": function(exports, require, module) {(function() {
  var Glyph, GlyphView, ImageGlyph, ImageView, Images, glyph, glyph_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  ImageView = (function(_super) {

    __extends(ImageView, _super);

    function ImageView() {
      return ImageView.__super__.constructor.apply(this, arguments);
    }

    ImageView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['image:string', 'x', 'y', 'angle'], []);
      return ImageView.__super__.initialize.call(this, options);
    };

    ImageView.prototype._render = function(data) {
      var ctx, glyph_props, i, img, obj, x, y, _i, _ref, _ref1,
        _this = this;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.image = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('image', obj));
        }
        return _results;
      })();
      this.angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('angle', obj));
        }
        return _results;
      })();
      for (i = _i = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _i <= _ref1 : _i >= _ref1; i = 0 <= _ref1 ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.angle[i])) {
          continue;
        }
        img = new Image();
        img.onload = (function(img, i) {
          return function() {
            if (_this.angle[i]) {
              ctx.translate(_this.sx[i], _this.sy[i]);
              ctx.rotate(_this.angle[i]);
              ctx.drawImage(img, 0, 0);
              ctx.rotate(-_this.angle[i]);
              return ctx.translate(-_this.sx[i], -_this.sy[i]);
            } else {
              return ctx.drawImage(img, _this.sx[i], _this.sy[i]);
            }
          };
        })(img, i);
        img.src = this.image[i];
      }
      return ctx.restore();
    };

    return ImageView;

  })(GlyphView);

  ImageGlyph = (function(_super) {

    __extends(ImageGlyph, _super);

    function ImageGlyph() {
      return ImageGlyph.__super__.constructor.apply(this, arguments);
    }

    ImageGlyph.prototype.default_view = ImageView;

    ImageGlyph.prototype.type = 'GlyphRenderer';

    return ImageGlyph;

  })(Glyph);

  ImageGlyph.prototype.display_defaults = _.clone(ImageGlyph.prototype.display_defaults);

  _.extend(ImageGlyph.prototype.display_defaults, {});

  Images = (function(_super) {

    __extends(Images, _super);

    function Images() {
      return Images.__super__.constructor.apply(this, arguments);
    }

    Images.prototype.model = ImageGlyph;

    return Images;

  })(Backbone.Collection);

  exports.images = new Images;

  exports.Image = ImageGlyph;

  exports.ImageView = ImageView;

}).call(this);
}, "renderers/area": function(exports, require, module) {(function() {
  var Area, AreaView, Areas, Glyph, GlyphView, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  AreaView = (function(_super) {

    __extends(AreaView, _super);

    function AreaView() {
      return AreaView.__super__.constructor.apply(this, arguments);
    }

    AreaView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['xs:array', 'ys:array'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return AreaView.__super__.initialize.call(this, options);
    };

    AreaView.prototype._render = function(data) {
      var ctx, glyph_props, i, pt, sx, sy, x, y, _i, _j, _k, _len, _ref, _ref1, _ref2;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      for (_i = 0, _len = data.length; _i < _len; _i++) {
        pt = data[_i];
        x = glyph_props.select('xs', pt);
        y = glyph_props.select('ys', pt);
        _ref = this.map_to_screen(x, glyph_props.xs.units, y, glyph_props.ys.units), sx = _ref[0], sy = _ref[1];
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, pt);
          for (i = _j = 0, _ref1 = sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
            if (i === 0) {
              ctx.beginPath();
              ctx.moveTo(sx[i], sy[i]);
              continue;
            } else if (isNaN(sx[i] + sy[i])) {
              ctx.closePath();
              ctx.fill();
              ctx.beginPath();
              continue;
            } else {
              ctx.lineTo(sx[i], sy[i]);
            }
          }
          ctx.closePath();
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, pt);
          for (i = _k = 0, _ref2 = sx.length - 1; 0 <= _ref2 ? _k <= _ref2 : _k >= _ref2; i = 0 <= _ref2 ? ++_k : --_k) {
            if (i === 0) {
              ctx.beginPath();
              ctx.moveTo(sx[i], sy[i]);
              continue;
            } else if (isNaN(sx[i] + sy[i])) {
              ctx.closePath();
              ctx.stroke();
              ctx.beginPath();
              continue;
            } else {
              ctx.lineTo(sx[i], sy[i]);
            }
          }
          ctx.closePath();
          ctx.stroke();
        }
      }
      return ctx.restore();
    };

    return AreaView;

  })(GlyphView);

  Area = (function(_super) {

    __extends(Area, _super);

    function Area() {
      return Area.__super__.constructor.apply(this, arguments);
    }

    Area.prototype.default_view = AreaView;

    Area.prototype.type = 'GlyphRenderer';

    return Area;

  })(Glyph);

  Area.prototype.display_defaults = _.clone(Area.prototype.display_defaults);

  _.extend(Area.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Areas = (function(_super) {

    __extends(Areas, _super);

    function Areas() {
      return Areas.__super__.constructor.apply(this, arguments);
    }

    Areas.prototype.model = Area;

    return Areas;

  })(Backbone.Collection);

  exports.areas = new Areas;

  exports.Area = Area;

  exports.AreaView = AreaView;

}).call(this);
}, "renderers/segment": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Segment, SegmentView, Segments, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  SegmentView = (function(_super) {

    __extends(SegmentView, _super);

    function SegmentView() {
      return SegmentView.__super__.constructor.apply(this, arguments);
    }

    SegmentView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x0', 'y0', 'x1', 'y1'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return SegmentView.__super__.initialize.call(this, options);
    };

    SegmentView.prototype._render = function(data) {
      var ctx, glyph_props, x0, x1, y0, y1, _ref, _ref1;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x0 = glyph_props.v_select('x0', data);
      y0 = glyph_props.v_select('y0', data);
      _ref = this.map_to_screen(x0, glyph_props.x0.units, y0, glyph_props.y0.units), this.sx0 = _ref[0], this.sy0 = _ref[1];
      x1 = glyph_props.v_select('x1', data);
      y1 = glyph_props.v_select('y1', data);
      _ref1 = this.map_to_screen(x1, glyph_props.x1.units, y1, glyph_props.y1.units), this.sx1 = _ref1[0], this.sy1 = _ref1[1];
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    SegmentView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i])) {
            continue;
          }
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.lineTo(this.sx1[i], this.sy1[i]);
        }
        return ctx.stroke();
      }
    };

    SegmentView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        _results = [];
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.lineTo(this.sx1[i], this.sy1[i]);
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    return SegmentView;

  })(GlyphView);

  Segment = (function(_super) {

    __extends(Segment, _super);

    function Segment() {
      return Segment.__super__.constructor.apply(this, arguments);
    }

    Segment.prototype.default_view = SegmentView;

    Segment.prototype.type = 'GlyphRenderer';

    return Segment;

  })(Glyph);

  Segment.prototype.display_defaults = _.clone(Segment.prototype.display_defaults);

  _.extend(Segment.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Segments = (function(_super) {

    __extends(Segments, _super);

    function Segments() {
      return Segments.__super__.constructor.apply(this, arguments);
    }

    Segments.prototype.model = Segment;

    return Segments;

  })(Backbone.Collection);

  exports.segments = new Segments;

  exports.Segment = Segment;

  exports.SegmentView = SegmentView;

}).call(this);
}, "renderers/wedge": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Wedge, WedgeView, Wedges, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  WedgeView = (function(_super) {

    __extends(WedgeView, _super);

    function WedgeView() {
      return WedgeView.__super__.constructor.apply(this, arguments);
    }

    WedgeView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'radius', 'start_angle', 'end_angle'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return WedgeView.__super__.initialize.call(this, options);
    };

    WedgeView.prototype._render = function(data) {
      var ctx, glyph_props, obj, x, y, _ref;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, this.glyph_props.x.units, y, this.glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.radius = this.distance(data, 'x', 'radius', 'edge');
      this.start_angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(this.glyph_props.select('start_angle', obj));
        }
        return _results;
      }).call(this);
      this.end_angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(this.glyph_props.select('end_angle', obj));
        }
        return _results;
      }).call(this);
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    WedgeView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _j, _ref, _ref1, _results;
      if (this.do_fill) {
        glyph_props.fill_properties.set(ctx, glyph);
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i] + this.start_angle[i] + this.end_angle[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], this.start_angle[i], this.end_angle[i], false);
          ctx.lineTo(this.sx[i], this.sy[i]);
          ctx.closePath();
          ctx.fill();
        }
      }
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        _results = [];
        for (i = _j = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i] + this.start_angle[i] + this.end_angle[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], this.start_angle[i], this.end_angle[i], false);
          ctx.lineTo(this.sx[i], this.sy[i]);
          ctx.closePath();
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    WedgeView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.radius[i] + this.start_angle[i] + this.end_angle[i])) {
          continue;
        }
        ctx.beginPath();
        ctx.arc(this.sx[i], this.sy[i], this.radius[i], this.start_angle[i], this.end_angle[i], false);
        ctx.lineTo(this.sx[i], this.sy[i]);
        ctx.closePath();
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, data[i]);
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        } else {
          _results.push(void 0);
        }
      }
      return _results;
    };

    return WedgeView;

  })(GlyphView);

  Wedge = (function(_super) {

    __extends(Wedge, _super);

    function Wedge() {
      return Wedge.__super__.constructor.apply(this, arguments);
    }

    Wedge.prototype.default_view = WedgeView;

    Wedge.prototype.type = 'GlyphRenderer';

    return Wedge;

  })(Glyph);

  Wedge.prototype.display_defaults = _.clone(Wedge.prototype.display_defaults);

  _.extend(Wedge.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Wedges = (function(_super) {

    __extends(Wedges, _super);

    function Wedges() {
      return Wedges.__super__.constructor.apply(this, arguments);
    }

    Wedges.prototype.model = Wedge;

    return Wedges;

  })(Backbone.Collection);

  exports.wedges = new Wedges;

  exports.Wedge = Wedge;

  exports.WedgeView = WedgeView;

}).call(this);
}, "renderers/quadcurve": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Quadcurve, QuadcurveView, Quadcurves, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  QuadcurveView = (function(_super) {

    __extends(QuadcurveView, _super);

    function QuadcurveView() {
      return QuadcurveView.__super__.constructor.apply(this, arguments);
    }

    QuadcurveView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x0', 'y0', 'x1', 'y1', 'cx', 'cy'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return QuadcurveView.__super__.initialize.call(this, options);
    };

    QuadcurveView.prototype._render = function(data) {
      var ctx, cx, cy, glyph_props, x0, x1, y0, y1, _ref, _ref1, _ref2;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x0 = glyph_props.v_select('x0', data);
      y0 = glyph_props.v_select('y0', data);
      _ref = this.map_to_screen(x0, glyph_props.x0.units, y0, glyph_props.y0.units), this.sx0 = _ref[0], this.sy0 = _ref[1];
      x1 = glyph_props.v_select('x1', data);
      y1 = glyph_props.v_select('y1', data);
      _ref1 = this.map_to_screen(x1, glyph_props.x1.units, y1, glyph_props.y1.units), this.sx1 = _ref1[0], this.sy1 = _ref1[1];
      cx = glyph_props.v_select('cx', data);
      cy = glyph_props.v_select('cy', data);
      _ref2 = this.map_to_screen(cx, glyph_props.cx.units, cy, glyph_props.cy.units), this.scx = _ref2[0], this.scy = _ref2[1];
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    QuadcurveView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i] + this.scx[i] + this.scy[i])) {
            continue;
          }
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.quadraticCurveTo(this.scx[i], this.scy[i], this.sx1[i], this.sy1[i]);
        }
        return ctx.stroke();
      }
    };

    QuadcurveView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        _results = [];
        for (i = _i = 0, _ref = this.sx0.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx0[i] + this.sy0[i] + this.sx1[i] + this.sy1[i] + this.scx[i] + this.scy[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.moveTo(this.sx0[i], this.sy0[i]);
          ctx.quadraticCurveTo(this.scx[i], this.scy[i], this.sx1[i], this.sy1[i]);
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    return QuadcurveView;

  })(GlyphView);

  Quadcurve = (function(_super) {

    __extends(Quadcurve, _super);

    function Quadcurve() {
      return Quadcurve.__super__.constructor.apply(this, arguments);
    }

    Quadcurve.prototype.default_view = QuadcurveView;

    Quadcurve.prototype.type = 'GlyphRenderer';

    return Quadcurve;

  })(Glyph);

  Quadcurve.prototype.display_defaults = _.clone(Quadcurve.prototype.display_defaults);

  _.extend(Quadcurve.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Quadcurves = (function(_super) {

    __extends(Quadcurves, _super);

    function Quadcurves() {
      return Quadcurves.__super__.constructor.apply(this, arguments);
    }

    Quadcurves.prototype.model = Quadcurve;

    return Quadcurves;

  })(Backbone.Collection);

  exports.quadcurves = new Quadcurves;

  exports.Quadcurve = Quadcurve;

  exports.QuadcurveView = QuadcurveView;

}).call(this);
}, "renderers/properties": function(exports, require, module) {(function() {
  var fill_properties, glyph_properties, line_properties, properties, text_properties,
    __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = (function() {

    function properties() {}

    properties.prototype.string = function(styleprovider, glyphspec, attrname) {
      var default_value, glyph_value;
      default_value = styleprovider.mget(attrname);
      if (!(attrname in glyphspec)) {
        if (_.isString(default_value)) {
          this[attrname] = {
            "default": default_value
          };
        } else {
          console.log(("string property '" + attrname + "' given invalid default value: ") + default_value);
        }
        return;
      }
      glyph_value = glyphspec[attrname];
      if (_.isString(glyph_value)) {
        return this[attrname] = {
          "default": glyph_value
        };
      } else if (_.isObject(glyph_value)) {
        this[attrname] = glyph_value;
        if (!(this[attrname]["default"] != null)) {
          this[attrname]["default"] = default_value;
        }
        return console.log(this[attrname]);
      } else {
        return console.log(("string property '" + attrname + "' given invalid glyph value: ") + glyph_value);
      }
    };

    properties.prototype.number = function(styleprovider, glyphspec, attrname) {
      var default_units, default_value, glyph_value, _ref;
      default_value = styleprovider.mget(attrname);
      default_units = (_ref = styleprovider.mget(attrname + '_units')) != null ? _ref : 'data';
      if (attrname + '_units' in glyphspec) {
        default_units = glyphspec[attrname + '_units'];
      }
      if (!(attrname in glyphspec)) {
        if (_.isNumber(default_value)) {
          this[attrname] = {
            "default": default_value,
            units: default_units
          };
        } else {
          console.log(("number property '" + attrname + "' given invalid default value: ") + default_value);
        }
        return;
      }
      glyph_value = glyphspec[attrname];
      if (_.isString(glyph_value)) {
        return this[attrname] = {
          field: glyph_value,
          "default": default_value,
          units: default_units
        };
      } else if (_.isNumber(glyph_value)) {
        return this[attrname] = {
          "default": glyph_value,
          units: default_units
        };
      } else if (_.isObject(glyph_value)) {
        this[attrname] = glyph_value;
        if (!(this[attrname]["default"] != null)) {
          this[attrname]["default"] = default_value;
        }
        if (!(this[attrname].units != null)) {
          return this[attrname].units = default_units;
        }
      } else {
        return console.log(("number property '" + attrname + "' given invalid glyph value: ") + glyph_value);
      }
    };

    properties.prototype.color = function(styleprovider, glyphspec, attrname) {
      var default_value, glyph_value;
      default_value = styleprovider.mget(attrname);
      if (!(attrname in glyphspec)) {
        if (_.isString(default_value) || _.isNull(default_value)) {
          this[attrname] = {
            "default": default_value
          };
        } else {
          console.log(("color property '" + attrname + "' given invalid default value: ") + default_value);
        }
        return;
      }
      glyph_value = glyphspec[attrname];
      if (_.isString(glyph_value) || _.isNull(glyph_value)) {
        return this[attrname] = {
          "default": glyph_value
        };
      } else if (_.isObject(glyph_value)) {
        this[attrname] = glyph_value;
        if (!(this[attrname]["default"] != null)) {
          return this[attrname]["default"] = default_value;
        }
      } else {
        return console.log(("color property '" + attrname + "' given invalid glyph value: ") + glyph_value);
      }
    };

    properties.prototype.array = function(styleprovider, glyphspec, attrname) {
      var default_units, default_value, glyph_value, _ref;
      default_value = styleprovider.mget(attrname);
      default_units = (_ref = styleprovider.mget(attrname + "_units")) != null ? _ref : 'data';
      if (attrname + '_units' in glyphspec) {
        default_units = glyphspec[attrname + 'units'];
      }
      if (!(attrname in glyphspec)) {
        if (_.isArray(default_value)) {
          this[attrname] = {
            "default": default_value,
            units: default_units
          };
        } else {
          console.log(("array property '" + attrname + "' given invalid default value: ") + default_value);
        }
        return;
      }
      glyph_value = glyphspec[attrname];
      if (_.isString(glyph_value)) {
        return this[attrname] = {
          field: glyph_value,
          "default": default_value,
          units: default_units
        };
      } else if (_.isArray(glyph_value)) {
        return this[attrname] = {
          "default": glyph_value,
          units: default_units
        };
      } else if (_.isObject(glyph_value)) {
        this[attrname] = glyph_value;
        if (!(this[attrname]["default"] != null)) {
          return this[attrname]["default"] = default_value;
        }
      } else {
        return console.log(("array property '" + attrname + "' given invalid glyph value: ") + glyph_value);
      }
    };

    properties.prototype["enum"] = function(styleprovider, glyphspec, attrname, vals) {
      var default_value, glyph_value, levels_value;
      default_value = styleprovider.mget(attrname);
      levels_value = vals.split(" ");
      if (!(attrname in glyphspec)) {
        if (_.isString(default_value) && __indexOf.call(levels_value, default_value) >= 0) {
          this[attrname] = {
            "default": default_value
          };
        } else {
          console.log(("enum property '" + attrname + "' given invalid default value: ") + default_value);
          console.log("    acceptable values:" + levels_value);
        }
        return;
      }
      glyph_value = glyphspec[attrname];
      if (_.isString(glyph_value)) {
        if (__indexOf.call(levels_value, glyph_value) >= 0) {
          return this[attrname] = {
            "default": glyph_value
          };
        } else {
          return this[attrname] = {
            field: glyph_value,
            "default": default_value
          };
        }
      } else if (_.isObject(glyph_value)) {
        this[attrname] = glyph_value;
        if (!(this[attrname]["default"] != null)) {
          return this[attrname]["default"] = default_value;
        }
      } else {
        console.log(("enum property '" + attrname + "' given invalid glyph value: ") + glyph_value);
        return console.log("    acceptable values:" + levels_value);
      }
    };

    properties.prototype.setattr = function(styleprovider, glyphspec, attrname, attrtype) {
      var values, _ref;
      values = null;
      if (attrtype.indexOf(":") > -1) {
        _ref = attrtype.split(":"), attrtype = _ref[0], values = _ref[1];
      }
      if (attrtype === "string") {
        return this.string(styleprovider, glyphspec, attrname);
      } else if (attrtype === "number") {
        return this.number(styleprovider, glyphspec, attrname);
      } else if (attrtype === "color") {
        return this.color(styleprovider, glyphspec, attrname);
      } else if (attrtype === "array") {
        return this.array(styleprovider, glyphspec, attrname);
      } else if (attrtype === "enum" && values) {
        return this["enum"](styleprovider, glyphspec, attrname, values);
      } else {
        return console.log(("Unknown type '" + attrtype + "' for glyph property: ") + attrname);
      }
    };

    properties.prototype.select = function(attrname, obj) {
      if (!(attrname in this)) {
        console.log(("requested unknown property '" + attrname + " on object: ") + obj);
        return;
      }
      if (this[attrname].field != null) {
        if (this[attrname].field in obj) {
          return obj[this[attrname].field];
        }
      }
      if (obj[attrname]) {
        return obj[attrname];
      }
      if (this[attrname]["default"] != null) {
        return this[attrname]["default"];
      } else {
        return console.log("selection for attribute '" + attrname + " failed on object: " + obj);
      }
    };

    properties.prototype.v_select = function(attrname, objs) {
      var i, obj, result, _i, _ref;
      if (!(attrname in this)) {
        console.log("requested unknown property '" + attrname + " on objects");
        return;
      }
      result = new Array(objs.length);
      for (i = _i = 0, _ref = objs.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        obj = objs[i];
        if (this[attrname].field != null) {
          if (this[attrname].field in obj) {
            result[i] = obj[this[attrname].field];
          }
        } else if (obj[attrname]) {
          result[i] = obj[attrname];
        } else if (this[attrname]["default"] != null) {
          result[i] = this[attrname]["default"];
        } else {
          console.log("vector selection for attribute '" + attrname + " failed on object: " + obj);
          return;
        }
      }
      return result;
    };

    return properties;

  })();

  line_properties = (function(_super) {

    __extends(line_properties, _super);

    function line_properties(styleprovider, glyphspec, prefix) {
      if (prefix == null) {
        prefix = "";
      }
      this.line_color_name = "" + prefix + "line_color";
      this.line_width_name = "" + prefix + "line_width";
      this.line_alpha_name = "" + prefix + "line_alpha";
      this.line_join_name = "" + prefix + "line_join";
      this.line_cap_name = "" + prefix + "line_cap";
      this.line_dash_name = "" + prefix + "line_dash";
      this.line_dash_offset_name = "" + prefix + "line_dash_offset";
      this.color(styleprovider, glyphspec, this.line_color_name);
      this.number(styleprovider, glyphspec, this.line_width_name);
      this.number(styleprovider, glyphspec, this.line_alpha_name);
      this["enum"](styleprovider, glyphspec, this.line_join_name, "miter round bevel");
      this["enum"](styleprovider, glyphspec, this.line_cap_name, "butt round square");
      this.array(styleprovider, glyphspec, this.line_dash_name);
      this.number(styleprovider, glyphspec, this.line_dash_offset_name);
      this.do_stroke = !(this.line_color["default"] === null);
    }

    line_properties.prototype.set = function(ctx, obj) {
      ctx.strokeStyle = this.select(this.line_color_name, obj);
      ctx.globalAlpha = this.select(this.line_alpha_name, obj);
      ctx.lineWidth = this.select(this.line_width_name, obj);
      ctx.lineJoin = this.select(this.line_join_name, obj);
      ctx.lineCap = this.select(this.line_cap_name, obj);
      ctx.setLineDash(this.select(this.line_dash_name, obj));
      return ctx.setLineDashOffset(this.select(this.line_dash_offset_name, obj));
    };

    return line_properties;

  })(properties);

  fill_properties = (function(_super) {

    __extends(fill_properties, _super);

    function fill_properties(styleprovider, glyphspec, prefix) {
      if (prefix == null) {
        prefix = "";
      }
      this.fill_name = "" + prefix + "fill";
      this.fill_alpha_name = "" + prefix + "fill_alpha";
      this.color(styleprovider, glyphspec, this.fill_name);
      this.number(styleprovider, glyphspec, this.fill_alpha_name);
      this.do_fill = !(this.fill["default"] === null);
    }

    fill_properties.prototype.set = function(ctx, obj) {
      ctx.fillStyle = this.select(this.fill_name, obj);
      return ctx.globalAlpha = this.select(this.fill_alpha_name, obj);
    };

    return fill_properties;

  })(properties);

  text_properties = (function(_super) {

    __extends(text_properties, _super);

    function text_properties(styleprovider, glyphspec, prefix) {
      if (prefix == null) {
        prefix = "";
      }
      this.text_font_name = "" + prefix + "text_font";
      this.text_font_size_name = "" + prefix + "text_font_size";
      this.text_font_style_name = "" + prefix + "text_font_style";
      this.text_color_name = "" + prefix + "text_color";
      this.text_alpha_name = "" + prefix + "text_alpha";
      this.text_align_name = "" + prefix + "text_align";
      this.text_baseline_name = "" + prefix + "text_baseline";
      this.string(styleprovider, glyphspec, this.text_font_name);
      this.string(styleprovider, glyphspec, this.text_font_size_name);
      this.string(styleprovider, glyphspec, this.text_font_style_name);
      this.color(styleprovider, glyphspec, this.text_color_name);
      this.number(styleprovider, glyphspec, this.text_alpha_name);
      this["enum"](styleprovider, glyphspec, this.text_align_name, "left right center");
      this["enum"](styleprovider, glyphspec, this.text_baseline_name, "top middle bottom");
    }

    text_properties.prototype.set = function(ctx, obj) {
      var font, font_size, font_style;
      font = this.select(this.text_font_name, obj);
      font_size = this.select(this.text_font_size_name, obj);
      font_style = this.select(this.text_font_style_name, obj);
      ctx.font = font_style + " " + font_size + " " + font;
      ctx.fillStyle = this.select(this.text_color_name, obj);
      ctx.globalAlpha = this.select(this.text_alpha_name, obj);
      ctx.textAlign = this.select(this.text_align_name, obj);
      return ctx.textBaseline = this.select(this.text_baseline_name, obj);
    };

    return text_properties;

  })(properties);

  glyph_properties = (function(_super) {

    __extends(glyph_properties, _super);

    function glyph_properties(styleprovider, glyphspec, attrnames, properties) {
      var attrname, attrtype, prop, _i, _j, _len, _len1, _ref;
      for (_i = 0, _len = attrnames.length; _i < _len; _i++) {
        attrname = attrnames[_i];
        attrtype = "number";
        if (attrname.indexOf(":") > -1) {
          _ref = attrname.split(":"), attrname = _ref[0], attrtype = _ref[1];
        }
        this.setattr(styleprovider, glyphspec, attrname, attrtype);
      }
      for (_j = 0, _len1 = properties.length; _j < _len1; _j++) {
        prop = properties[_j];
        this[prop.constructor.name] = prop;
      }
      this.fast_path = false;
      if ('fast_path' in glyphspec) {
        this.fast_path = glyphspec.fast_path;
      }
    }

    return glyph_properties;

  })(properties);

  exports.glyph_properties = glyph_properties;

  exports.fill_properties = fill_properties;

  exports.line_properties = line_properties;

  exports.text_properties = text_properties;

}).call(this);
}, "renderers/rect": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Rect, RectView, Rects, fill_properties, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  fill_properties = properties.fill_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  RectView = (function(_super) {

    __extends(RectView, _super);

    function RectView() {
      return RectView.__super__.constructor.apply(this, arguments);
    }

    RectView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'width', 'height', 'angle'], [new fill_properties(this, glyphspec), new line_properties(this, glyphspec)]);
      this.do_fill = this.glyph_props.fill_properties.do_fill;
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return RectView.__super__.initialize.call(this, options);
    };

    RectView.prototype._render = function(data) {
      var ctx, glyph_props, obj, x, y, _ref;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.sw = this.distance(data, 'x', 'width', 'center');
      this.sh = this.distance(data, 'y', 'height', 'center');
      this.angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('angle', obj));
        }
        return _results;
      })();
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    RectView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _j, _ref, _ref1;
      if (this.do_fill) {
        glyph_props.fill_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
            continue;
          }
          if (this.angle[i]) {
            ctx.translate(this.sx[i], this.sy[i]);
            ctx.rotate(this.angle[i]);
            ctx.rect(-this.sw[i] / 2, -this.sh[i] / 2, this.sw[i], this.sh[i]);
            ctx.rotate(-this.angle[i]);
            ctx.translate(-this.sx[i], -this.sy[i]);
          } else {
            ctx.rect(this.sx[i] - this.sw[i] / 2, this.sy[i] - this.sh[i] / 2, this.sw[i], this.sh[i]);
          }
        }
        ctx.fill();
      }
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        ctx.beginPath();
        for (i = _j = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
          if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
            continue;
          }
          if (this.angle[i]) {
            ctx.translate(this.sx[i], this.sy[i]);
            ctx.rotate(this.angle[i]);
            ctx.rect(-this.sw[i] / 2, -this.sh[i] / 2, this.sw[i], this.sh[i]);
            ctx.rotate(-this.angle[i]);
            ctx.translate(-this.sx[i], -this.sy[i]);
          } else {
            ctx.rect(this.sx[i] - this.sw[i] / 2, this.sy[i] - this.sh[i] / 2, this.sw[i], this.sh[i]);
          }
        }
        return ctx.stroke();
      }
    };

    RectView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      _results = [];
      for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        if (isNaN(this.sx[i] + this.sy[i] + this.sw[i] + this.sh[i] + this.angle[i])) {
          continue;
        }
        ctx.translate(this.sx[i], this.sy[i]);
        ctx.rotate(this.angle[i]);
        ctx.beginPath();
        ctx.rect(-this.sw[i] / 2, -this.sh[i] / 2, this.sw[i], this.sh[i]);
        if (this.do_fill) {
          glyph_props.fill_properties.set(ctx, data[i]);
          ctx.fill();
        }
        if (this.do_stroke) {
          glyph_props.line_properties.set(ctx, data[i]);
          ctx.stroke();
        }
        ctx.rotate(-this.angle[i]);
        _results.push(ctx.translate(-this.sx[i], -this.sy[i]));
      }
      return _results;
    };

    return RectView;

  })(GlyphView);

  Rect = (function(_super) {

    __extends(Rect, _super);

    function Rect() {
      return Rect.__super__.constructor.apply(this, arguments);
    }

    Rect.prototype.default_view = RectView;

    Rect.prototype.type = 'GlyphRenderer';

    return Rect;

  })(Glyph);

  Rect.prototype.display_defaults = _.clone(Rect.prototype.display_defaults);

  _.extend(Rect.prototype.display_defaults, {
    fill: 'gray',
    fill_alpha: 1.0,
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0,
    angle: 0.0
  });

  Rects = (function(_super) {

    __extends(Rects, _super);

    function Rects() {
      return Rects.__super__.constructor.apply(this, arguments);
    }

    Rects.prototype.model = Rect;

    return Rects;

  })(Backbone.Collection);

  exports.rects = new Rects;

  exports.Rect = Rect;

  exports.RectView = RectView;

}).call(this);
}, "renderers/line": function(exports, require, module) {(function() {
  var Glyph, GlyphView, Line, LineView, Lines, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  LineView = (function(_super) {

    __extends(LineView, _super);

    function LineView() {
      return LineView.__super__.constructor.apply(this, arguments);
    }

    LineView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['xs:array', 'ys:array'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return LineView.__super__.initialize.call(this, options);
    };

    LineView.prototype._render = function(data) {
      var ctx, glyph_props;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    LineView.prototype._fast_path = function(ctx, glyph_props) {
      var i, pt, sx, sy, x, y, _i, _j, _len, _ref, _ref1, _results;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph);
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          pt = data[_i];
          x = glyph_props.select('xs', pt);
          y = glyph_props.select('ys', pt);
          _ref = this.map_to_screen(x, glyph_props.xs.units, y, glyph_props.ys.units), sx = _ref[0], sy = _ref[1];
          for (i = _j = 0, _ref1 = sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
            if (i === 0) {
              ctx.beginPath();
              ctx.moveTo(sx[i], sy[i]);
              continue;
            } else if (isNaN(sx[i]) || isNaN(sy[i])) {
              ctx.stroke();
              ctx.beginPath();
              continue;
            } else {
              ctx.lineTo(sx[i], sy[i]);
            }
          }
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    LineView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, pt, sx, sy, x, y, _i, _j, _len, _ref, _ref1, _results;
      if (this.do_stroke) {
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          pt = data[_i];
          x = glyph_props.select('xs', pt);
          y = glyph_props.select('ys', pt);
          _ref = this.map_to_screen(x, glyph_props.xs.units, y, glyph_props.ys.units), sx = _ref[0], sy = _ref[1];
          glyph_props.line_properties.set(ctx, pt);
          for (i = _j = 0, _ref1 = sx.length - 1; 0 <= _ref1 ? _j <= _ref1 : _j >= _ref1; i = 0 <= _ref1 ? ++_j : --_j) {
            if (i === 0) {
              ctx.beginPath();
              ctx.moveTo(sx[i], sy[i]);
              continue;
            } else if (isNaN(sx[i]) || isNaN(sy[i])) {
              ctx.stroke();
              ctx.beginPath();
              continue;
            } else {
              ctx.lineTo(sx[i], sy[i]);
            }
          }
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    return LineView;

  })(GlyphView);

  Line = (function(_super) {

    __extends(Line, _super);

    function Line() {
      return Line.__super__.constructor.apply(this, arguments);
    }

    Line.prototype.default_view = LineView;

    Line.prototype.type = 'GlyphRenderer';

    return Line;

  })(Glyph);

  Line.prototype.display_defaults = _.clone(Line.prototype.display_defaults);

  _.extend(Line.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Lines = (function(_super) {

    __extends(Lines, _super);

    function Lines() {
      return Lines.__super__.constructor.apply(this, arguments);
    }

    Lines.prototype.model = Line;

    return Lines;

  })(Backbone.Collection);

  exports.lines = new Lines;

  exports.Line = Line;

  exports.LineView = LineView;

}).call(this);
}, "renderers/arc": function(exports, require, module) {(function() {
  var Arc, ArcView, Arcs, Glyph, GlyphView, glyph, glyph_properties, line_properties, properties,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  properties = require('./properties');

  glyph_properties = properties.glyph_properties;

  line_properties = properties.line_properties;

  glyph = require('./glyph');

  Glyph = glyph.Glyph;

  GlyphView = glyph.GlyphView;

  ArcView = (function(_super) {

    __extends(ArcView, _super);

    function ArcView() {
      return ArcView.__super__.constructor.apply(this, arguments);
    }

    ArcView.prototype.initialize = function(options) {
      var glyphspec;
      glyphspec = this.mget('glyphspec');
      this.glyph_props = new glyph_properties(this, glyphspec, ['x', 'y', 'radius', 'start_angle', 'end_angle', 'direction:string'], [new line_properties(this, glyphspec)]);
      this.do_stroke = this.glyph_props.line_properties.do_stroke;
      return ArcView.__super__.initialize.call(this, options);
    };

    ArcView.prototype._render = function(data) {
      var ctx, dir, glyph_props, i, obj, x, y, _i, _ref, _ref1;
      ctx = this.plot_view.ctx;
      glyph_props = this.glyph_props;
      ctx.save();
      x = glyph_props.v_select('x', data);
      y = glyph_props.v_select('y', data);
      _ref = this.map_to_screen(x, glyph_props.x.units, y, glyph_props.y.units), this.sx = _ref[0], this.sy = _ref[1];
      this.radius = this.distance(data, 'x', 'radius', 'edge');
      this.start_angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('start_angle', obj));
        }
        return _results;
      })();
      this.end_angle = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          obj = data[_i];
          _results.push(glyph_props.select('end_angle', obj));
        }
        return _results;
      })();
      this.direction = new Array(this.sx.length);
      for (i = _i = 0, _ref1 = this.sx.length - 1; 0 <= _ref1 ? _i <= _ref1 : _i >= _ref1; i = 0 <= _ref1 ? ++_i : --_i) {
        dir = glyph_props.select('direction', data[i]);
        if (dir === 'clock') {
          this.direction[i] = false;
        } else if (dir === 'anticlock') {
          this.direction[i] = true;
        } else {
          this.direction[i] = NaN;
        }
      }
      if (this.glyph_props.fast_path) {
        this._fast_path(ctx, glyph_props);
      } else {
        this._full_path(ctx, glyph_props, data);
      }
      return ctx.restore();
    };

    ArcView.prototype._fast_path = function(ctx, glyph_props) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        glyph_props.line_properties.set(ctx, glyph_props);
        _results = [];
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i] + this.start_angle[i] + this.end_angle[i] + this.direction[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], this.start_angle[i], this.end_angle[i], this.direction[i]);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    ArcView.prototype._full_path = function(ctx, glyph_props, data) {
      var i, _i, _ref, _results;
      if (this.do_stroke) {
        _results = [];
        for (i = _i = 0, _ref = this.sx.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
          if (isNaN(this.sx[i] + this.sy[i] + this.radius[i] + this.start_angle[i] + this.end_angle[i] + this.direction[i])) {
            continue;
          }
          ctx.beginPath();
          ctx.arc(this.sx[i], this.sy[i], this.radius[i], this.start_angle[i], this.end_angle[i], this.direction[i]);
          glyph_props.line_properties.set(ctx, data[i]);
          _results.push(ctx.stroke());
        }
        return _results;
      }
    };

    return ArcView;

  })(GlyphView);

  Arc = (function(_super) {

    __extends(Arc, _super);

    function Arc() {
      return Arc.__super__.constructor.apply(this, arguments);
    }

    Arc.prototype.default_view = ArcView;

    Arc.prototype.type = 'GlyphRenderer';

    return Arc;

  })(Glyph);

  Arc.prototype.display_defaults = _.clone(Arc.prototype.display_defaults);

  _.extend(Arc.prototype.display_defaults, {
    line_color: 'red',
    line_width: 1,
    line_alpha: 1.0,
    line_join: 'miter',
    line_cap: 'butt',
    line_dash: [],
    line_dash_offset: 0
  });

  Arcs = (function(_super) {

    __extends(Arcs, _super);

    function Arcs() {
      return Arcs.__super__.constructor.apply(this, arguments);
    }

    Arcs.prototype.model = Arc;

    return Arcs;

  })(Backbone.Collection);

  exports.arcs = new Arcs;

  exports.Arc = Arc;

  exports.ArcView = ArcView;

}).call(this);
}, "ticks": function(exports, require, module) {(function() {
  " Tick generator classes and helper functions for calculating axis\ntick-related values (i.e., bounds and intervals).\n";

  var AbstractTickGenerator, DefaultTickGenerator, ShowAllTickGenerator, arange, argsort, arr_div, arr_div2, arr_div3, arr_pow2, auto_bounds, auto_interval, auto_ticks, calc_bound, divmod, float, heckbert_interval, is_base2, log10, log2, tick_intervals, _nice,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  AbstractTickGenerator = (function() {
    " Abstract class for tick generators.";

    function AbstractTickGenerator() {}

    AbstractTickGenerator.prototype.get_ticks = function(data_low, data_high, bounds_low, bounds_high, interval, use_endpoints, scale) {
      if (use_endpoints == null) {
        use_endpoints = False;
      }
      if (scale == null) {
        scale = 'linear';
      }
      return " Returns a list of ticks points in data space.\n\nParameters\n----------\ndata_low, data_high : float\n    The actual minimum and maximum of index values of the entire\n    dataset.\nbounds_low, bounds_high : \"auto\", \"fit\", float\n    The range for which ticks should be generated.\ninterval : \"auto\", float\n    If the value is a positive number, it specifies the length\n    of the tick interval; a negative integer specifies the\n    number of tick intervals; 'auto' specifies that the number and\n    length of the tick intervals are automatically calculated, based\n    on the range of the axis.\nuse_endpoints : Boolean\n    If True, the lower and upper bounds of the data are used as the\n    lower and upper end points of the axis. If False, the end points\n    might not fall exactly on the bounds.\nscale : 'linear' or 'log'\n    The type of scale the ticks are for.\n\nReturns\n-------\ntick_list : array of floats\n    Where ticks are to be placed.\n\n\nExample\n-------\nIf the range of x-values in a line plot span from -15.0 to +15.0, but\nthe plot is currently displaying only the region from 3.1 to 6.83, and\nthe user wants the interval to be automatically computed to be some\nnice value, then call get_ticks() thusly::\n\n    get_ticks(-15.0, 15.0, 3.1, 6.83, \"auto\")\n\nA reasonable return value in this case would be::\n\n    [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]";
    };

    return AbstractTickGenerator;

  })();

  DefaultTickGenerator = (function(_super) {

    __extends(DefaultTickGenerator, _super);

    " An implementation of AbstractTickGenerator that simply uses the\nauto_ticks() and log_auto_ticks() functions.";


    function DefaultTickGenerator() {
      return DefaultTickGenerator.__super__.constructor.apply(this, arguments);
    }

    DefaultTickGenerator.prototype.get_ticks = function(data_low, data_high, bounds_low, bounds_high, interval, use_endpoints, scale) {
      if (use_endpoints == null) {
        use_endpoints = False;
      }
      if (scale == null) {
        scale = 'linear';
      }
      if (scale === 'linear') {
        "";

      }
      return elif(scale === {
        'log': ""
      });
    };

    return DefaultTickGenerator;

  })(AbstractTickGenerator);

  ShowAllTickGenerator = (function(_super) {

    __extends(ShowAllTickGenerator, _super);

    " Uses the abstract interface, but returns all \"positions\" instead\nof decimating the ticks.\n\nYou must provide a sequence of values as a *positions* keyword argument\nto the constructor.";


    function ShowAllTickGenerator() {
      return ShowAllTickGenerator.__super__.constructor.apply(this, arguments);
    }

    ShowAllTickGenerator.prototype.get_ticks = function(data_low, data_high, bounds_low, bounds_high, interval, use_endpoints, scale) {
      if (use_endpoints == null) {
        use_endpoints = False;
      }
      if (scale == null) {
        scale = 'linear';
      }
      return " Returns an array based on **positions**.";
    };

    return ShowAllTickGenerator;

  })(AbstractTickGenerator);

  auto_ticks = function(data_low, data_high, bound_low, bound_high, tick_interval, use_endpoints) {
    var auto_lower, auto_upper, delta, end, intervals, is_auto_high, is_auto_low, lower, rng, start, tick, ticks, upper, _ref;
    if (use_endpoints == null) {
      use_endpoints = true;
    }
    " Finds locations for axis tick marks.\n\nCalculates the locations for tick marks on an axis. The *bound_low*,\n*bound_high*, and *tick_interval* parameters specify how the axis end\npoints and tick interval are calculated.\n\nParameters\n----------\n\ndata_low, data_high : number\n    The minimum and maximum values of the data along this axis.\n    If any of the bound settings are 'auto' or 'fit', the axis\n    traits are calculated automatically from these values.\nbound_low, bound_high : 'auto', 'fit', or a number.\n    The lower and upper bounds of the axis. If the value is a number,\n    that value is used for the corresponding end point. If the value is\n    'auto', then the end point is calculated automatically. If the\n    value is 'fit', then the axis bound is set to the corresponding\n    *data_low* or *data_high* value.\ntick_interval : can be 'auto' or a number\n    If the value is a positive number, it specifies the length\n    of the tick interval; a negative integer specifies the\n    number of tick intervals; 'auto' specifies that the number and\n    length of the tick intervals are automatically calculated, based\n    on the range of the axis.\nuse_endpoints : Boolean\n    If True, the lower and upper bounds of the data are used as the\n    lower and upper end points of the axis. If False, the end points\n    might not fall exactly on the bounds.\n\nReturns\n-------\nAn array of tick mark locations. The first and last tick entries are the\naxis end points.";

    is_auto_low = bound_low === 'auto';
    is_auto_high = bound_high === 'auto';
    if (typeof bound_low === "string") {
      lower = data_low;
    } else {
      lower = bound_low;
    }
    if (typeof bound_high === "string") {
      upper = data_high;
    } else {
      upper = bound_high;
    }
    if ((tick_interval === 'auto') || (tick_interval === 0.0)) {
      rng = Math.abs(upper - lower);
      if (rng === 0.0) {
        tick_interval = 0.5;
        lower = data_low - 0.5;
        upper = data_high + 0.5;
      } else if (is_base2(rng) && is_base2(upper) && rng > 4) {
        if (rng === 2) {
          tick_interval = 1;
        } else if (rng === 4) {
          tick_interval = 4;
        } else {
          tick_interval = rng / 4;
        }
      } else {
        tick_interval = auto_interval(lower, upper);
      }
    } else if (tick_interval < 0) {
      intervals = -tick_interval;
      tick_interval = tick_intervals(lower, upper, intervals);
      if (is_auto_low && is_auto_high) {
        is_auto_low = is_auto_high = false;
        lower = tick_interval * floor(lower / tick_interval);
        while ((Math.abs(lower) >= tick_interval) && ((lower + tick_interval * (intervals - 1)) >= upper)) {
          lower -= tick_interval;
        }
        upper = lower + tick_interval * intervals;
      }
    }
    if (is_auto_low || is_auto_high) {
      delta = 0.01 * tick_interval * (data_low === data_high);
      _ref = auto_bounds(data_low - delta, data_high + delta, tick_interval), auto_lower = _ref[0], auto_upper = _ref[1];
      if (is_auto_low) {
        lower = auto_lower;
      }
      if (is_auto_high) {
        upper = auto_upper;
      }
    }
    start = floor(lower / tick_interval) * tick_interval;
    end = floor(upper / tick_interval) * tick_interval;
    if (start === end) {
      lower = start = start - tick_interval;
      upper = end = start - tick_interval;
    }
    if (upper > end) {
      end += tick_interval;
    }
    ticks = arange(start, end + (tick_interval / 2.0), tick_interval);
    if (len(ticks) < 2) {
      "";

    }
    if ((!is_auto_low) && use_endpoints) {
      ticks[0] = lower;
    }
    if ((!is_auto_high) && use_endpoints) {
      ticks[-1] = upper;
    }
    return [
      (function() {
        var _i, _len, _results;
        if (tick >= bound_low && tick <= bound_high) {
          _results = [];
          for (_i = 0, _len = ticks.length; _i < _len; _i++) {
            tick = ticks[_i];
            _results.push(tick);
          }
          return _results;
        }
      })()
    ];
  };

  is_base2 = function(range) {
    " Returns True if *range* is a positive base-2 number (2, 4, 8, 16, ...).";

    var lg;
    if (range <= 0.0) {
      return false;
    } else {
      lg = log2(range);
      return (lg === Math.floor(lg)) && (lg > 0.0);
    }
  };

  log10 = function(num) {
    if (num === 0.0) {
      num += 1.0e-16;
    }
    return Math.log(num) / Math.log(10);
  };

  log2 = function(num) {
    " Returns the base 2 logarithm of a number (or array).\n";
    if (num === 0.0) {
      num += 1.0e-16;
    }
    return Math.log(num);
  };

  heckbert_interval = function(data_low, data_high, numticks) {
    var d, graphmax, graphmin, range;
    if (numticks == null) {
      numticks = 8;
    }
    "Returns a \"nice\" range and interval for a given data range and a preferred\nnumber of ticks.  From Paul Heckbert's algorithm in Graphics Gems.";

    range = _nice(data_high - data_low);
    d = _nice(range / (numticks - 1), true);
    graphmin = Math.floor(data_low / d) * d;
    graphmax = Math.ceil(data_high / d) * d;
    return [graphmin, graphmax, d];
  };

  _nice = function(x, round) {
    var expv, f, nf;
    if (round == null) {
      round = false;
    }
    " if round is false, then use Math.ceil(range) ";

    expv = Math.floor(log10(x));
    f = x / Math.pow(10, expv);
    if (round) {
      if (f < 1.5) {
        nf = 1.0;
      } else if (f < 3.0) {
        nf = 2.0;
      } else if (f < 7.0) {
        nf = 5.0;
      } else {
        nf = 10.0;
      }
    } else {
      if (f <= 1.0) {
        nf = 1.0;
      } else if (f <= 2.0) {
        nf = 2.0;
      } else if (f <= 5.0) {
        nf = 5.0;
      } else {
        nf = 10.0;
      }
    }
    return nf * Math.pow(10, expv);
  };

  arange = function(start, end, step) {
    var i, ret_arr;
    if (end == null) {
      end = false;
    }
    if (step == null) {
      step = false;
    }
    if (!end) {
      end = start;
      start = 0;
    }
    if (start > end) {
      if (step === false) {
        step = -1;
      } else if (step > 0) {
        "the loop will never terminate";

        1 / 0;
      }
    } else if (step < 0) {
      "the loop will never terminate";

      1 / 0;
    }
    if (!step) {
      step = 1;
    }
    ret_arr = [];
    i = start;
    if (start < end) {
      while (i < end) {
        ret_arr.push(i);
        i += step;
      }
    } else {
      while (i > end) {
        ret_arr.push(i);
        i += step;
      }
    }
    return ret_arr;
  };

  arr_div = function(numerators, denominator) {
    var output_arr, val, _i, _len;
    output_arr = [];
    for (_i = 0, _len = numerators.length; _i < _len; _i++) {
      val = numerators[_i];
      output_arr.push(val / denominator);
    }
    return output_arr;
  };

  arr_div2 = function(numerator, denominators) {
    var output_arr, val, _i, _len;
    output_arr = [];
    for (_i = 0, _len = denominators.length; _i < _len; _i++) {
      val = denominators[_i];
      output_arr.push(numerator / val);
    }
    return output_arr;
  };

  arr_div3 = function(numerators, denominators) {
    var i, output_arr, val, _i, _len;
    output_arr = [];
    for (i = _i = 0, _len = denominators.length; _i < _len; i = ++_i) {
      val = denominators[i];
      output_arr.push(numerators[i] / val);
    }
    return output_arr;
  };

  arr_pow2 = function(base, exponents) {
    var output_arr, val, _i, _len;
    output_arr = [];
    for (_i = 0, _len = exponents.length; _i < _len; _i++) {
      val = exponents[_i];
      output_arr.push(Math.pow(base, val));
    }
    return output_arr;
  };

  _.sorted = function(arr) {
    return _.sortBy(arr, _.identity);
  };

  argsort = function(arr) {
    var i, ret_arr, sorted_arr, y, _i, _len;
    sorted_arr = _.sortBy(arr, _.identity);
    ret_arr = [];
    for (i = _i = 0, _len = sorted_arr.length; _i < _len; i = ++_i) {
      y = sorted_arr[i];
      ret_arr[i] = arr.indexOf(y);
    }
    return ret_arr;
  };

  exports.argsort = argsort;

  auto_interval = function(data_low, data_high) {
    " Calculates the tick interval for a range.\n\nThe boundaries for the data to be plotted on the axis are::\n\n    data_bounds = (data_low,data_high)\n\nThe function chooses the number of tick marks, which can be between\n3 and 9 marks (including end points), and chooses tick intervals at\n1, 2, 2.5, 5, 10, 20, ...\n\nReturns\n-------\ninterval : float\n    tick mark interval for axis";

    var best_magics, best_mantissas, candidate_intervals, diff_arr, divisions, interval, ma, magic_index, magic_intervals, magnitude, magnitudes, mantissa_index, mantissas, mi, range, result, _i, _j, _len, _len1;
    range = float(data_high) - float(data_low);
    divisions = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0];
    candidate_intervals = arr_div2(range, divisions);
    magnitudes = candidate_intervals.map(function(candidate) {
      return Math.pow(10.0, Math.floor(log10(candidate)));
    });
    mantissas = arr_div3(candidate_intervals, magnitudes);
    magic_intervals = [1.0, 2.0, 2.5, 5.0, 10.0];
    best_mantissas = [];
    best_magics = [];
    for (_i = 0, _len = magic_intervals.length; _i < _len; _i++) {
      mi = magic_intervals[_i];
      diff_arr = mantissas.map(function(x) {
        return Math.abs(mi - x);
      });
      best_magics.push(_.min(diff_arr));
    }
    for (_j = 0, _len1 = mantissas.length; _j < _len1; _j++) {
      ma = mantissas[_j];
      diff_arr = magic_intervals.map(function(x) {
        return Math.abs(ma - x);
      });
      best_mantissas.push(_.min(diff_arr));
    }
    magic_index = argsort(best_magics)[0];
    mantissa_index = argsort(best_mantissas)[0];
    interval = magic_intervals[magic_index];
    magnitude = magnitudes[mantissa_index];
    result = interval * magnitude;
    return result;
  };

  exports.auto_interval = auto_interval;

  float = function(x) {
    return x + 0.0;
  };

  exports.float = float;

  tick_intervals = function(data_low, data_high, intervals) {
    " Computes the best tick interval length to achieve a specified number of\ntick intervals.\n\nParameters\n----------\ndata_low, data_high : number\n    The minimum and maximum values of the data along this axis.\n    If any of the bound settings are 'auto' or 'fit', the axis\n    traits are calculated automatically from these values.\nintervals : number\n    The desired number of intervals\n\nReturns\n-------\nReturns a float indicating the tick interval length.";

    var exp_, factor, index, interval, range, result;
    range = float(data_high - data_low);
    if (range === 0.0) {
      range = 1.0;
    }
    interval = range / intervals;
    exp_ = Math.floor(log10(interval));
    factor = Math.pow(10, exp_);
    console.log("exp_ " + exp_ + "  pre_factor " + factor + " pre_interval " + interval);
    interval = interval / factor;
    console.log(" factor " + factor + " initial_interval " + interval);
    if (interval < 2.0) {
      interval = 2.0;
      index = 0;
    } else if (interval < 2.5) {
      interval = 2.5;
      index = 1;
    } else if (interval < 5.0) {
      interval = 5.0;
      index = 2;
    } else {
      interval = 10.0;
      index = 3;
    }
    while (true) {
      result = interval * factor;
      console.log("result " + result + " index " + index + " interval " + interval);
      if ((Math.floor(data_low / result) * result) + (intervals * result) >= data_high) {
        return result;
      }
      index = (index + 1) % 4;
      interval = interval * [2.0, 1.25, 2.0, 2.0]([index]);
    }
  };

  exports.tick_intervals = tick_intervals;

  "I'll worry about this after getting linear ticks working\nlog_auto_ticks = (data_low, data_high,\n                   bound_low, bound_high,\n                   tick_interval, use_endpoints=true) ->\n    #Like auto_ticks(), but for log scales.\n    tick_goal = 15\n    magic_numbers = [1, 2, 5]\n    explicit_ticks = false\n\n    if data_low <= 0.0\n        return []\n\n    if tick_interval != 'auto'\n        if tick_interval < 0\n            tick_goal = -tick_interval\n        else\n            magic_numbers = [tick_interval]\n            explicit_ticks = true\n\n    if data_low>data_high\n        [data_low, data_high] = data_high, data_low\n\n    log_low = log10(data_low)\n    log_high = log10(data_high)\n    log_interval = log_high-log_low\n\n    if log_interval < 1.0\n        # If less than a factor of 10 separates the data, just use the normal\n        # linear approach\n        return auto_ticks(data_low, data_high,\n                          bound_low, bound_high,\n                          tick_interval,\n                          use_endpoints = false)\n\n    else if log_interval < (tick_goal+1)/2 or explicit_ticks\n        # If there's enough space, try to put lines at the magic number multipliers\n        # inside each power of ten\n\n        # Try each interval to see how many ticks we get\n        for interval in magic_numbers\n            ticklist = []\n            for exp in [Math.floor(log_low).,Math.ceil(log_high)]\n                for multiplier in linspace(interval, 10.0, round(10.0/interval),\n                                           endpoint=1)\n                    tick = Math.exp(10, exp*multiplier)\n                    if tick >= data_low and tick <= data_high:\n                        ticklist.append(tick)\n            if len(ticklist)<tick_goal+3 or explicit_ticks:\n                return ticklist\n    else:\n        # We put lines at every power of ten or less\n        startlog = Math.ceil(log_low)\n        endlog = Math.floor(log_high)\n        interval = Math.ceil((endlog-startlog)/9.0)\n        expticks = arange(startlog, endlog, interval)\n        # There's no function that is like arange but inclusive, so\n        # we have to check whether the endpoint should be included.\n        if (endlog-startlog) % interval == 0.0:\n            expticks = concatenate([expticks, [endlog]])\n        return 10**expticks";


  auto_bounds = function(data_low, data_high, tick_interval) {
    " Calculates appropriate upper and lower bounds for the axis from\nthe data bounds and the given axis interval.\n\nThe boundaries  hit either exactly on the lower and upper values\nor on the tick mark just beyond the lower and upper values.";
    return [calc_bound(data_low, tick_interval, false), calc_bound(data_high, tick_interval, true)];
  };

  exports.auto_bounds = auto_bounds;

  divmod = function(x, y) {
    var quot, rem;
    quot = Math.floor(x / y);
    rem = x % y;
    return [quot, rem];
  };

  exports.divmod = divmod;

  calc_bound = function(end_point, tick_interval, is_upper) {
    " Finds an axis end point that includes the value *end_point*.\n\nIf the tick mark interval results in a tick mark hitting directly on the\nend point, *end_point* is returned.  Otherwise, the location of the tick\nmark just past *end_point* is returned. The *is_upper* parameter\nspecifies whether *end_point* is at the upper (True) or lower (false)\nend of the axis.";

    var c1, c2, quotient, rem_p, remainder, tick_p, _ref;
    _ref = divmod(end_point, tick_interval), quotient = _ref[0], remainder = _ref[1];
    rem_p = remainder === 0.0;
    tick_p = ((tick_interval - remainder) / tick_interval) < 0.00001;
    if (rem_p || tick_p) {
      return end_point;
    }
    c1 = (quotient + 1.0) * tick_interval;
    c2 = quotient * tick_interval;
    if (is_upper) {
      return Math.max(c1, c2);
    }
    return Math.min(c1, c2);
  };

  exports.calc_bound = calc_bound;

}).call(this);
}, "adhoc/speed_test": function(exports, require, module) {(function() {

  test('linetest', function() {
    var a, b, c, data, line, maxval, path, scale1, scale2, temp, x, y, _i, _len, _ref;
    expect(0);
    maxval = 6000;
    x = _.range(maxval);
    y = _.range(maxval);
    data = (function() {
      var _i, _len, _ref, _results;
      _ref = _.zip(x, y);
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        temp = _ref[_i];
        _results.push({
          'x': temp[0],
          'y': temp[1]
        });
      }
      return _results;
    })();
    window.data = data;
    scale1 = d3.scale.linear().domain([0, maxval]).range([0, 300]);
    scale2 = d3.scale.linear().domain([0, maxval]).range([300, 0]);
    $('body').append("<div><svg id='chart'></svg></div>");
    d3.select('#chart').attr('width', 300).attr('height', 300);
    a = new Date();
    _ref = _.range(1);
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      c = _ref[_i];
      console.log('drawing line');
      line = d3.svg.line().x(function(d) {
        return scale1(d['x']);
      }).y(function(d) {
        return scale2(d['y']);
      });
      path = d3.select('#chart').selectAll('path').data([data]).attr('d', line);
      path = d3.select('#chart').selectAll('path').data([data]);
      path.attr('d', line);
      path.attr('stroke', '#000').attr('fill', 'none');
      path = path.enter().append('path');
      path.attr('d', line);
      path.attr('stroke', '#000').attr('fill', 'none');
    }
    b = new Date();
    return console.log(b - a);
  });

  test('scatter', function() {
    var a, b, c, data, maxval, node, scale1, scale2, temp, x, y, _i, _len, _ref;
    expect(0);
    maxval = 1560;
    x = _.range(maxval);
    y = _.range(maxval);
    data = (function() {
      var _i, _len, _ref, _results;
      _ref = _.zip(x, y);
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        temp = _ref[_i];
        _results.push({
          'x': temp[0],
          'y': temp[1]
        });
      }
      return _results;
    })();
    window.data = data;
    scale1 = d3.scale.linear().domain([0, maxval]).range([0, 300]);
    scale2 = d3.scale.linear().domain([0, maxval]).range([300, 0]);
    $('body').append("<div><svg id='chart'></svg></div>");
    d3.select('#chart').attr('width', 300).attr('height', 300);
    a = new Date();
    node = d3.select('#chart').selectAll('circle').data(data).enter().append('circle');
    b = new Date();
    console.log('getmarks', b - a);
    a = new Date();
    _ref = _.range(1);
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      c = _ref[_i];
      console.log('drawing scatter');
      node.attr('cx', (function(d) {
        return scale1(d['x']);
      })).attr('cy', (function(d) {
        return scale2(d['x']);
      })).attr('r', 5).attr('fill', '#000');
    }
    b = new Date();
    return console.log(b - a);
  });

}).call(this);
}, "base": function(exports, require, module) {(function() {
  var Collections, Config, ContinuumView, HasParent, HasProperties, PlotWidget, WebSocketWrapper, build_views, load_models, locations, safebind, submodels,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  Config = {
    prefix: ''
  };

  safebind = function(binder, target, event, callback) {
    var _this = this;
    if (!_.has(binder, 'eventers')) {
      binder['eventers'] = {};
    }
    try {
      binder['eventers'][target.id] = target;
    } catch (error) {

    }
    if (target != null) {
      target.on(event, callback, binder);
      target.on('destroy remove', function() {
        return delete binder['eventers'][target];
      }, binder);
    } else {
      console.log("error with binder", binder, event);
    }
    return null;
  };

  load_models = function(modelspecs) {
    var attrs, coll, coll_attrs, model, newspecs, oldspecs, _i, _j, _k, _l, _len, _len1, _len2, _len3, _len4, _m;
    newspecs = [];
    oldspecs = [];
    for (_i = 0, _len = modelspecs.length; _i < _len; _i++) {
      model = modelspecs[_i];
      coll = Collections(model['type']);
      attrs = model['attributes'];
      if (coll && coll.get(attrs['id'])) {
        oldspecs.push([coll, attrs]);
      } else {
        newspecs.push([coll, attrs]);
      }
    }
    for (_j = 0, _len1 = newspecs.length; _j < _len1; _j++) {
      coll_attrs = newspecs[_j];
      coll = coll_attrs[0], attrs = coll_attrs[1];
      if (coll) {
        coll.add(attrs, {
          'silent': true
        });
      }
    }
    for (_k = 0, _len2 = newspecs.length; _k < _len2; _k++) {
      coll_attrs = newspecs[_k];
      coll = coll_attrs[0], attrs = coll_attrs[1];
      if (coll) {
        coll.get(attrs['id']).dinitialize(attrs);
      }
    }
    for (_l = 0, _len3 = newspecs.length; _l < _len3; _l++) {
      coll_attrs = newspecs[_l];
      coll = coll_attrs[0], attrs = coll_attrs[1];
      if (coll) {
        model = coll.get(attrs.id);
        model.trigger('add', model, coll, {});
      }
    }
    for (_m = 0, _len4 = oldspecs.length; _m < _len4; _m++) {
      coll_attrs = oldspecs[_m];
      coll = coll_attrs[0], attrs = coll_attrs[1];
      if (coll) {
        coll.get(attrs['id']).set(attrs);
      }
    }
    return null;
  };

  WebSocketWrapper = (function() {

    _.extend(WebSocketWrapper.prototype, Backbone.Events);

    function WebSocketWrapper(ws_conn_string) {
      this.onmessage = __bind(this.onmessage, this);

      var _this = this;
      this.auth = {};
      this.ws_conn_string = ws_conn_string;
      this._connected = $.Deferred();
      this.connected = this._connected.promise();
      try {
        this.s = new WebSocket(ws_conn_string);
      } catch (error) {
        this.s = new MozWebSocket(ws_conn_string);
      }
      this.s.onopen = function() {
        return _this._connected.resolve();
      };
      this.s.onmessage = this.onmessage;
    }

    WebSocketWrapper.prototype.onmessage = function(msg) {
      var data, index, topic;
      data = msg.data;
      index = data.indexOf(":");
      index = data.indexOf(":", index + 1);
      topic = data.substring(0, index);
      data = data.substring(index + 1);
      this.trigger("msg:" + topic, data);
      return null;
    };

    WebSocketWrapper.prototype.send = function(msg) {
      var _this = this;
      return $.when(this.connected).done(function() {
        return _this.s.send(msg);
      });
    };

    WebSocketWrapper.prototype.subscribe = function(topic, auth) {
      var msg;
      this.auth[topic] = auth;
      msg = JSON.stringify({
        msgtype: 'subscribe',
        topic: topic,
        auth: auth
      });
      return this.send(msg);
    };

    return WebSocketWrapper;

  })();

  submodels = function(wswrapper, topic, apikey) {
    wswrapper.subscribe(topic, apikey);
    return wswrapper.on("msg:" + topic, function(msg) {
      var clientid, model, msgobj, ref, _i, _len, _ref;
      msgobj = JSON.parse(msg);
      if (msgobj['msgtype'] === 'modelpush') {
        load_models(msgobj['modelspecs']);
      } else if (msgobj['msgtype'] === 'modeldel') {
        _ref = msgobj['modelspecs'];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          ref = _ref[_i];
          model = resolve_ref(ref['type'], ref['id']);
          if (model) {
            model.destroy({
              'local': true
            });
          }
        }
      } else if (msgobj['msgtype'] === 'status' && msgobj['status'][0] === 'subscribesuccess') {
        clientid = msgobj['status'][2];
        Config.clientid = clientid;
        $.ajaxSetup({
          'headers': {
            'Continuum-Clientid': clientid
          }
        });
      } else {
        console.log(msgobj);
      }
      return null;
    });
  };

  HasProperties = (function(_super) {

    __extends(HasProperties, _super);

    function HasProperties() {
      this.get_obj = __bind(this.get_obj, this);

      this.resolve_ref = __bind(this.resolve_ref, this);

      this.convert_to_ref = __bind(this.convert_to_ref, this);
      return HasProperties.__super__.constructor.apply(this, arguments);
    }

    HasProperties.prototype.destroy = function(options) {
      var target, val, _ref, _results;
      HasProperties.__super__.destroy.call(this, options);
      if (_.has(this, 'eventers')) {
        _ref = this.eventers;
        _results = [];
        for (target in _ref) {
          if (!__hasProp.call(_ref, target)) continue;
          val = _ref[target];
          _results.push(val.off(null, null, this));
        }
        return _results;
      }
    };

    HasProperties.prototype.isNew = function() {
      return !this.get('created');
    };

    HasProperties.prototype.initialize = function(attrs, options) {
      var _this = this;
      if (!attrs) {
        attrs = {};
      }
      if (!options) {
        options = {};
      }
      HasProperties.__super__.initialize.call(this, attrs, options);
      this.properties = {};
      this.property_cache = {};
      if (!_.has(attrs, this.idAttribute)) {
        this.id = _.uniqueId(this.type);
        this.attributes[this.idAttribute] = this.id;
      }
      return _.defer(function() {
        if (!_this.inited) {
          return _this.dinitialize(attrs, options);
        }
      });
    };

    HasProperties.prototype.dinitialize = function(attrs, options) {
      return this.inited = true;
    };

    HasProperties.prototype.set_obj = function(key, value, options) {
      var attrs, val;
      if (_.isObject(key) || key === null) {
        attrs = key;
        options = value;
      } else {
        attrs = {};
        attrs[key] = value;
      }
      for (key in attrs) {
        if (!__hasProp.call(attrs, key)) continue;
        val = attrs[key];
        attrs[key] = this.convert_to_ref(val);
      }
      return this.set(attrs, options);
    };

    HasProperties.prototype.set = function(key, value, options) {
      var attrs, toremove, val, _i, _len;
      if (_.isObject(key) || key === null) {
        attrs = key;
        options = value;
      } else {
        attrs = {};
        attrs[key] = value;
      }
      toremove = [];
      for (key in attrs) {
        if (!__hasProp.call(attrs, key)) continue;
        val = attrs[key];
        if (_.has(this, 'properties') && _.has(this.properties, key) && this.properties[key]['setter']) {
          this.properties[key]['setter'].call(this, val);
          toremove.push(key);
        }
      }
      for (_i = 0, _len = toremove.length; _i < _len; _i++) {
        key = toremove[_i];
        delete attrs[key];
      }
      if (!_.isEmpty(attrs)) {
        return HasProperties.__super__.set.call(this, attrs, options);
      }
    };

    HasProperties.prototype.convert_to_ref = function(value) {
      if (_.isArray(value)) {
        return _.map(value, this.convert_to_ref);
      } else {
        if (value instanceof HasProperties) {
          return value.ref();
        }
      }
    };

    HasProperties.prototype.add_dependencies = function(prop_name, object, fields) {
      var fld, prop_spec, _i, _len, _results;
      if (!_.isArray(fields)) {
        fields = [fields];
      }
      prop_spec = this.properties[prop_name];
      prop_spec.dependencies = prop_spec.dependencies.concat({
        obj: object,
        fields: fields
      });
      _results = [];
      for (_i = 0, _len = fields.length; _i < _len; _i++) {
        fld = fields[_i];
        _results.push(safebind(this, object, "change:" + fld, prop_spec['callbacks']['changedep']));
      }
      return _results;
    };

    HasProperties.prototype.register_setter = function(prop_name, setter) {
      var prop_spec;
      prop_spec = this.properties[prop_name];
      return prop_spec.setter = setter;
    };

    HasProperties.prototype.register_property = function(prop_name, getter, use_cache) {
      var changedep, prop_spec, propchange,
        _this = this;
      if (_.isUndefined(use_cache)) {
        use_cache = true;
      }
      if (_.has(this.properties, prop_name)) {
        this.remove_property(prop_name);
      }
      changedep = function() {
        return _this.trigger('changedep:' + prop_name);
      };
      propchange = function() {
        var firechange, new_val, old_val;
        firechange = true;
        if (prop_spec['use_cache']) {
          old_val = _this.get_cache(prop_name);
          _this.clear_cache(prop_name);
          new_val = _this.get(prop_name);
          firechange = new_val !== old_val;
        }
        if (firechange) {
          _this.trigger('change:' + prop_name, _this, _this.get(prop_name));
          return _this.trigger('change', _this);
        }
      };
      prop_spec = {
        'getter': getter,
        'dependencies': [],
        'use_cache': use_cache,
        'setter': null,
        'callbacks': {
          changedep: changedep,
          propchange: propchange
        }
      };
      this.properties[prop_name] = prop_spec;
      safebind(this, this, "changedep:" + prop_name, prop_spec['callbacks']['propchange']);
      return prop_spec;
    };

    HasProperties.prototype.remove_property = function(prop_name) {
      var dep, dependencies, fld, obj, prop_spec, _i, _j, _len, _len1, _ref;
      prop_spec = this.properties[prop_name];
      dependencies = prop_spec.dependencies;
      for (_i = 0, _len = dependencies.length; _i < _len; _i++) {
        dep = dependencies[_i];
        obj = dep.obj;
        _ref = dep['fields'];
        for (_j = 0, _len1 = _ref.length; _j < _len1; _j++) {
          fld = _ref[_j];
          obj.off('change:' + fld, prop_spec['callbacks']['changedep'], this);
        }
      }
      this.off("changedep:" + dep);
      delete this.properties[prop_name];
      if (prop_spec.use_cache) {
        return this.clear_cache(prop_name);
      }
    };

    HasProperties.prototype.has_cache = function(prop_name) {
      return _.has(this.property_cache, prop_name);
    };

    HasProperties.prototype.add_cache = function(prop_name, val) {
      return this.property_cache[prop_name] = val;
    };

    HasProperties.prototype.clear_cache = function(prop_name, val) {
      return delete this.property_cache[prop_name];
    };

    HasProperties.prototype.get_cache = function(prop_name) {
      return this.property_cache[prop_name];
    };

    HasProperties.prototype.get = function(prop_name) {
      var computed, getter, prop_spec;
      if (_.has(this.properties, prop_name)) {
        prop_spec = this.properties[prop_name];
        if (prop_spec.use_cache && this.has_cache(prop_name)) {
          return this.property_cache[prop_name];
        } else {
          getter = prop_spec.getter;
          computed = getter.apply(this, this);
          if (this.properties[prop_name].use_cache) {
            this.add_cache(prop_name, computed);
          }
          return computed;
        }
      } else {
        return HasProperties.__super__.get.call(this, prop_name);
      }
    };

    HasProperties.prototype.ref = function() {
      return {
        'type': this.type,
        'id': this.id
      };
    };

    HasProperties.prototype.resolve_ref = function(ref) {
      if (_.isArray(ref)) {
        return _.map(ref, this.resolve_ref);
      }
      if (!ref) {
        console.log('ERROR, null reference');
      }
      if (ref['type'] === this.type && ref['id'] === this.id) {
        return this;
      } else {
        return Collections(ref['type']).get(ref['id']);
      }
    };

    HasProperties.prototype.get_obj = function(ref_name) {
      var ref;
      ref = this.get(ref_name);
      if (ref) {
        return this.resolve_ref(ref);
      }
    };

    HasProperties.prototype.url = function() {
      var base;
      base = Config.prefix + "/bokeh/bb/" + this.get('doc') + "/" + this.type + "/";
      if (this.isNew()) {
        return base;
      }
      return base + this.get('id') + "/";
    };

    HasProperties.prototype.sync = function(method, model, options) {
      return options.success(model);
    };

    HasProperties.prototype.defaults = {};

    return HasProperties;

  })(Backbone.Model);

  HasParent = (function(_super) {

    __extends(HasParent, _super);

    function HasParent() {
      return HasParent.__super__.constructor.apply(this, arguments);
    }

    HasParent.prototype.get_fallback = function(attr) {
      var retval;
      if (this.get_obj('parent') && _.indexOf(this.get_obj('parent').parent_properties, attr) >= 0 && !_.isUndefined(this.get_obj('parent').get(attr))) {
        return this.get_obj('parent').get(attr);
      } else {
        retval = this.display_defaults[attr];
        return retval;
      }
    };

    HasParent.prototype.get = function(attr) {
      var normalval;
      normalval = HasParent.__super__.get.call(this, attr);
      if (!_.isUndefined(normalval)) {
        return normalval;
      } else if (!(attr === 'parent')) {
        return this.get_fallback(attr);
      }
    };

    HasParent.prototype.display_defaults = {};

    return HasParent;

  })(HasProperties);

  build_views = function(view_storage, view_models, options) {
    "use strict";

    var created_views, key, model, newmodels, to_remove, view_specific_option, _i, _j, _len, _len1;
    created_views = [];
    try {
      newmodels = _.filter(view_models, function(x) {
        return !_.has(view_storage, x.id);
      });
    } catch (error) {
      debugger;
      console.log(error);
      throw error;
    }
    for (_i = 0, _len = newmodels.length; _i < _len; _i++) {
      model = newmodels[_i];
      view_specific_option = _.extend({}, options, {
        'model': model
      });
      try {
        view_storage[model.id] = new model.default_view(view_specific_option);
      } catch (error) {
        console.log("error on model of", model, error);
        throw error;
      }
      created_views.push(view_storage[model.id]);
    }
    to_remove = _.difference(_.keys(view_storage), _.pluck(view_models, 'id'));
    for (_j = 0, _len1 = to_remove.length; _j < _len1; _j++) {
      key = to_remove[_j];
      view_storage[key].remove();
      delete view_storage[key];
    }
    return created_views;
  };

  ContinuumView = (function(_super) {

    __extends(ContinuumView, _super);

    function ContinuumView() {
      return ContinuumView.__super__.constructor.apply(this, arguments);
    }

    ContinuumView.prototype.initialize = function(options) {
      if (!_.has(options, 'id')) {
        return this.id = _.uniqueId('ContinuumView');
      }
    };

    ContinuumView.prototype.bind_bokeh_events = function() {
      return 'pass';
    };

    ContinuumView.prototype.delegateEvents = function(events) {
      ContinuumView.__super__.delegateEvents.call(this, events);
      return this.bind_bokeh_events();
    };

    ContinuumView.prototype.remove = function() {
      var target, val, _ref;
      if (_.has(this, 'eventers')) {
        _ref = this.eventers;
        for (target in _ref) {
          if (!__hasProp.call(_ref, target)) continue;
          val = _ref[target];
          val.off(null, null, this);
        }
      }
      this.trigger('remove');
      return ContinuumView.__super__.remove.call(this);
    };

    ContinuumView.prototype.mget = function() {
      return this.model.get.apply(this.model, arguments);
    };

    ContinuumView.prototype.mset = function() {
      return this.model.set.apply(this.model, arguments);
    };

    ContinuumView.prototype.mget_obj = function(fld) {
      return this.model.get_obj(fld);
    };

    ContinuumView.prototype.render_end = function() {
      return "pass";
    };

    return ContinuumView;

  })(Backbone.View);

  PlotWidget = (function(_super) {

    __extends(PlotWidget, _super);

    function PlotWidget() {
      return PlotWidget.__super__.constructor.apply(this, arguments);
    }

    PlotWidget.prototype.tagName = 'div';

    PlotWidget.prototype.marksize = 3;

    PlotWidget.prototype.initialize = function(options) {
      var ctx;
      this.plot_model = options.plot_model;
      this.plot_view = options.plot_view;
      ctx = this.plot_view.ctx;
      if (!ctx.setLineDash) {
        ctx.setLineDash = function(dash) {
          ctx.mozDash = dash;
          return ctx.webkitLineDash = dash;
        };
      }
      if (!ctx.getLineDash) {
        ctx.getLineDash = function() {
          return ctx.mozDash;
        };
      }
      ctx.setLineDashOffset = function(dash_offset) {
        ctx.lineDashOffset = dash_offset;
        ctx.mozDashOffset = dash_offset;
        return ctx.webkitLineDashOffset = dash_offset;
      };
      return PlotWidget.__super__.initialize.call(this, options);
    };

    PlotWidget.prototype.bind_bokeh_events = function() {
      return safebind(this, this.plot_view.viewstate, 'change', function() {
        return this.request_render();
      });
    };

    PlotWidget.prototype.addPolygon = function(x, y) {
      if (isNaN(x) || isNaN(y)) {
        return null;
      }
      return this.plot_view.ctx.fillRect(x, y, this.marksize, this.marksize);
    };

    PlotWidget.prototype.addCircle = function(x, y) {
      if (isNaN(x) || isNaN(y)) {
        return null;
      }
      this.plot_view.ctx.beginPath();
      this.plot_view.ctx.arc(x, y, this.marksize, 0, Math.PI * 2);
      this.plot_view.ctx.closePath();
      this.plot_view.ctx.fill();
      return this.plot_view.ctx.stroke();
    };

    PlotWidget.prototype.request_render = function() {
      return this.plot_view.throttled();
    };

    return PlotWidget;

  })(ContinuumView);

  locations = {
    Plot: ['./container', 'plots'],
    PanTool: ['./tools/pantool', 'pantools'],
    ZoomTool: ['./tools/zoomtool', 'zoomtools'],
    SelectionTool: ['./tools/selecttool', 'selectiontools'],
    LinearAxis: ['./guides', 'linearaxes'],
    LinearDateAxis: ['./guides', 'lineardateaxes'],
    Legend: ['./guides', 'legends'],
    GlyphRenderer: ['./renderers/glyph_renderer', 'glyphrenderers'],
    Glyph: ['./renderers/glyph', 'glyphs'],
    Arc: ['./renderers/arc', 'arcs'],
    Area: ['./renderers/area', 'areas'],
    Bezier: ['./renderers/bezier', 'beziers'],
    Circle: ['./renderers/circle', 'circles'],
    Image: ['./renderers/image', 'images'],
    Line: ['./renderers/line', 'lines'],
    Oval: ['./renderers/oval', 'ovals'],
    Quad: ['./renderers/quad', 'quads'],
    Quadcurve: ['./renderers/quadcurve', 'quadcurves'],
    Ray: ['./renderers/ray', 'rays'],
    Rect: ['./renderers/rect', 'rects'],
    Segment: ['./renderers/segment', 'segments'],
    Text: ['./renderers/text', 'texts'],
    Wedge: ['./renderers/wedge', 'wedges'],
    BoxSelectionOverlay: ['./overlays', 'boxselectionoverlays'],
    ObjectArrayDataSource: ['./datasource', 'objectarraydatasources'],
    ColumnDataSource: ['./datasource', 'columndatasources'],
    Range1d: ['./ranges', 'range1ds'],
    DataRange1d: ['./ranges', 'datarange1ds'],
    DataFactorRange: ['./ranges', 'datafactorranges'],
    Plot: ['./container', 'plots'],
    GridPlotContainer: ['./container', 'gridplotcontainers'],
    CDXPlotContext: ['./container', 'plotcontexts'],
    PlotContext: ['./container', 'plotcontexts'],
    ScatterRenderer: ['./schema_renderers', 'scatterrenderers'],
    LineRenderer: ['./schema_renderers', 'linerenderers'],
    DiscreteColorMapper: ['./mapper', 'discretecolormappers'],
    DataTable: ['./table', 'datatables'],
    PandasPivot: ['./pandas/pandas', 'pandaspivots'],
    PandasDataSource: ['./pandas/pandas', 'pandasdatasources'],
    PandasPlotSource: ['./pandas/pandas', 'pandasplotsources']
  };

  exports.locations = locations;

  Collections = function(typename) {
    var collection, modulename, _ref;
    if (!locations[typename]) {
      throw "./base: Unknown Collection " + typename;
    }
    _ref = locations[typename], modulename = _ref[0], collection = _ref[1];
    return require(modulename)[collection];
  };

  exports.Collections = Collections;

  exports.Config = Config;

  exports.safebind = safebind;

  exports.load_models = load_models;

  exports.WebSocketWrapper = WebSocketWrapper;

  exports.submodels = submodels;

  exports.HasProperties = HasProperties;

  exports.HasParent = HasParent;

  exports.build_views = build_views;

  exports.ContinuumView = ContinuumView;

  exports.PlotWidget = PlotWidget;

}).call(this);
}, "coffee_style_guide": function(exports, require, module) {(function() {
  "start of continuum CS style guide. our code does not follow this yet.";

  "2 spaces per indent\n80 characters per line";

  "underscores to separate variables names\nCamelCase for class names\nunderscores preceding functions show what we think is private\ncoffeescript makes it easy to pass instance methods as callbacks.\ntry to use that instead of writing lots of inline functions as callbacks";

  var MyBigClass, foo,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  MyBigClass = (function(_super) {

    __extends(MyBigClass, _super);

    function MyBigClass() {
      return MyBigClass.__super__.constructor.apply(this, arguments);
    }

    MyBigClass.prototype.set_my_field = function() {
      this.set('hello');
      return MyBigClass.__super__.set_my_field.call(this);
    };

    MyBigClass.prototype._dont_call_func = function() {
      return console.log('you should not be calling this');
    };

    MyBigClass.prototype.call_func = function() {
      console.log('but I can call this func, because I am in this class');
      return this._dont_call_func();
    };

    return MyBigClass;

  })(Backbone.Model);

  "coffee script looseness\nALWAYS use parentheses around function calls";


  console.log('log this statement');

  console.log('logging this message');

  foo = {
    coffee: 'black',
    cream: 'none',
    bagels: {
      cream_cheese: 'fat_free',
      toasted: 'of course'
    }
  };

  foo({
    'name': 'firstobject',
    'title': 'first'
  }, {
    'name': 'second object',
    'title': 'first'
  });

  foo({
    'name': 'second object',
    'title': 'first'
  }, {
    'name': 'second object',
    'title': 'first'
  });

  foo({
    'name': 'second object',
    'title': 'first'
  }, {
    'name': 'second object',
    'title': 'first'
  }, [1, 2, 3, 4, 5]);

  "inline functions\nwe follow the same syntax for object arrays.  4 spaces before the start of the\nfunction definition.  2 spaces before the comma separating the functions";


  foo(1, 2, 3, function() {
    var a;
    my_callback_goes_here();
    a = {
      'node': 'fast'
    };
    return a;
  }, function() {
    return second_callback_goes_here();
  });

  "return values\ncoffee script always returns the last value in a function.  don't rely on this.\nalways return something, or null";


}).call(this);
}, "overlays": function(exports, require, module) {(function() {
  var BoxSelectionOverlay, BoxSelectionOverlayView, BoxSelectionOverlays, HasParent, PlotWidget, base, safebind,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  safebind = base.safebind;

  PlotWidget = base.PlotWidget;

  HasParent = base.HasParent;

  BoxSelectionOverlayView = (function(_super) {

    __extends(BoxSelectionOverlayView, _super);

    function BoxSelectionOverlayView() {
      return BoxSelectionOverlayView.__super__.constructor.apply(this, arguments);
    }

    BoxSelectionOverlayView.prototype.bind_events = function() {};

    BoxSelectionOverlayView.prototype.initialize = function(options) {
      this.selecting = false;
      this.xrange = [null, null];
      this.yrange = [null, null];
      BoxSelectionOverlayView.__super__.initialize.call(this, options);
      this.toolview = this.plot_view.tools[this.mget('tool').id];
      return this.plot_view.$el.find('.main_can_wrapper').append(this.$el);
    };

    BoxSelectionOverlayView.prototype.boxselect = function(xrange, yrange) {
      this.xrange = xrange;
      this.yrange = yrange;
      this.request_render();
      return console.log('valchange');
    };

    BoxSelectionOverlayView.prototype.startselect = function() {
      this.selecting = true;
      this.xrange = [null, null];
      this.yrange = [null, null];
      this.request_render();
      return console.log('selecting');
    };

    BoxSelectionOverlayView.prototype.stopselect = function() {
      this.selecting = false;
      this.xrange = [null, null];
      this.yrange = [null, null];
      this.request_render();
      return console.log('not selecting');
    };

    BoxSelectionOverlayView.prototype.bind_bokeh_events = function(options) {
      safebind(this, this.toolview, 'boxselect', this.boxselect);
      safebind(this, this.toolview, 'startselect', this.startselect);
      return safebind(this, this.toolview, 'stopselect', this.stopselect);
    };

    BoxSelectionOverlayView.prototype.render = function() {
      var height, style_string, width, xpos, xrange, ypos, yrange;
      if (!this.selecting) {
        this.$el.removeClass('shading');
        return;
      }
      xrange = this.xrange;
      yrange = this.yrange;
      if (_.any(_.map(xrange, _.isNullOrUndefined)) || _.any(_.map(yrange, _.isNullOrUndefined))) {
        this.$el.removeClass('shading');
        return;
      }
      style_string = "";
      xpos = this.plot_view.viewstate.rxpos(Math.min(xrange[0], xrange[1]));
      if (xrange) {
        width = Math.abs(xrange[1] - xrange[0]);
      } else {
        width = this.plot_view.viewstate.get('width');
      }
      style_string += "; left:" + xpos + "px; width:" + width + "px; ";
      ypos = this.plot_view.viewstate.rypos(Math.max(yrange[0], yrange[1]));
      if (yrange) {
        height = yrange[1] - yrange[0];
      } else {
        height = this.plot_view.viewstate.get('height');
      }
      this.$el.addClass('shading');
      style_string += "top:" + ypos + "px; height:" + height + "px";
      return this.$el.attr('style', style_string);
    };

    return BoxSelectionOverlayView;

  })(PlotWidget);

  BoxSelectionOverlay = (function(_super) {

    __extends(BoxSelectionOverlay, _super);

    function BoxSelectionOverlay() {
      return BoxSelectionOverlay.__super__.constructor.apply(this, arguments);
    }

    BoxSelectionOverlay.prototype.type = 'BoxSelectionOverlay';

    BoxSelectionOverlay.prototype.default_view = BoxSelectionOverlayView;

    return BoxSelectionOverlay;

  })(HasParent);

  _.extend(BoxSelectionOverlay.prototype.defaults, {
    tool: null
  });

  BoxSelectionOverlays = (function(_super) {

    __extends(BoxSelectionOverlays, _super);

    function BoxSelectionOverlays() {
      return BoxSelectionOverlays.__super__.constructor.apply(this, arguments);
    }

    BoxSelectionOverlays.prototype.model = BoxSelectionOverlay;

    return BoxSelectionOverlays;

  })(Backbone.Collection);

  exports.boxselectionoverlays = new BoxSelectionOverlays;

  exports.BoxSelectionOverlayView = BoxSelectionOverlayView;

  exports.BoxSelectionOverlay = BoxSelectionOverlay;

}).call(this);
}, "testutils": function(exports, require, module) {(function() {
  var Collections, bar_plot, base, data_table, glyph_plot, line_plot, make_range_and_mapper, scatter_plot,
    __hasProp = {}.hasOwnProperty;

  base = require("./base");

  Collections = base.Collections;

  scatter_plot = function(parent, data_source, xfield, yfield, color_field, mark, colormapper, local) {
    var color_mapper, options, plot_model, source_name, xaxis, xdr, yaxis, ydr;
    if (_.isUndefined(local)) {
      local = true;
    }
    options = {
      'local': local
    };
    if (_.isUndefined(mark)) {
      mark = 'circle';
    }
    if (_.isUndefined(color_field)) {
      color_field = null;
    }
    if (_.isUndefined(color_mapper) && color_field) {
      color_mapper = Collections('DiscreteColorMapper').create({
        data_range: Collections('DataFactorRange').create({
          data_source: data_source.ref(),
          columns: ['x']
        }, options)
      }, options);
    }
    source_name = data_source.get('name');
    plot_model = Collections('Plot').create({
      data_sources: {
        source_name: data_source.ref()
      },
      parent: parent
    }, options);
    xdr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [xfield]
        }
      ]
    }, options);
    ydr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [yfield]
        }
      ]
    }, options);
    scatter_plot = Collections("ScatterRenderer").create({
      data_source: data_source.ref(),
      xdata_range: xdr.ref(),
      ydata_range: ydr.ref(),
      xfield: xfield,
      yfield: yfield,
      color_field: color_field,
      color_mapper: color_mapper,
      mark: mark,
      parent: plot_model.ref()
    }, options);
    xaxis = Collections('LinearAxis').create({
      'orientation': 'bottom',
      'parent': plot_model.ref(),
      'data_range': xdr.ref()
    }, options);
    yaxis = Collections('LinearAxis').create({
      'orientation': 'left',
      'parent': plot_model.ref(),
      'data_range': ydr.ref()
    }, options);
    plot_model.set({
      'renderers': [scatter_plot.ref()],
      'axes': [xaxis.ref(), yaxis.ref()]
    }, options);
    return plot_model;
  };

  data_table = function(parent, data_source, xfield, yfield, color_field, mark, colormapper, local) {
    var color_mapper, options, source_name, table_model, xdr, xmapper, ydr, ymapper;
    if (_.isUndefined(local)) {
      local = true;
    }
    options = {
      'local': local
    };
    if (_.isUndefined(mark)) {
      mark = 'circle';
    }
    if (_.isUndefined(color_field)) {
      color_field = null;
    }
    if (_.isUndefined(color_mapper) && color_field) {
      color_mapper = Collections('DiscreteColorMapper').create({
        data_range: Collections('DataFactorRange').create({
          data_source: data_source.ref(),
          columns: ['x']
        }, options)
      }, options);
    }
    source_name = data_source.get('name');
    table_model = Collections('Table').create({
      data_sources: {
        source_name: data_source.ref()
      },
      parent: parent
    }, options);
    xdr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [xfield]
        }
      ]
    }, options);
    ydr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [yfield]
        }
      ]
    }, options);
    xmapper = Collections('LinearMapper').create({
      data_range: xdr.ref(),
      screen_range: table_model.get('xrange')
    }, options);
    ymapper = Collections('LinearMapper').create({
      data_range: ydr.ref(),
      screen_range: table_model.get('yrange')
    }, options);
    scatter_plot = Collections("TableRenderer").create({
      data_source: data_source.ref(),
      xfield: xfield,
      yfield: yfield,
      color_field: color_field,
      color_mapper: color_mapper,
      mark: mark,
      xmapper: xmapper.ref(),
      ymapper: ymapper.ref(),
      parent: table_model.ref()
    }, options);
    return table_model.set({
      'renderers': [scatter_plot.ref()]
    }, options);
  };

  make_range_and_mapper = function(data_source, datafields, padding, screen_range, ordinal, options) {
    var mapper, range;
    if (!ordinal) {
      range = Collections('DataRange1d').create({
        sources: [
          {
            ref: data_source.ref(),
            columns: datafields
          }
        ],
        rangepadding: padding
      }, options);
      mapper = Collections('LinearMapper').create({
        data_range: range.ref(),
        screen_range: screen_range.ref()
      }, options);
    } else {
      range = Collections('DataFactorRange').create({
        data_source: data_source.ref(),
        columns: [field]
      }, options);
      mapper = Collections('FactorMapper').create({
        data_range: range.ref(),
        screen_range: screen_range.ref()
      }, options);
    }
    return [range, mapper];
  };

  bar_plot = function(parent, data_source, xfield, yfield, orientation, local) {
    var options, plot_model, xaxis, xdr, xmapper, yaxis, ydr, ymapper, _ref, _ref1;
    if (_.isUndefined(local)) {
      local = true;
    }
    options = {
      'local': local
    };
    plot_model = Collections('Plot').create({
      data_sources: {
        source_name: data_source.ref()
      },
      parent: parent
    }, options);
    _ref = make_range_and_mapper(data_source, [xfield], d3.max([1 / (data_source.get('data').length - 1), 0.1]), plot_model.get_obj('xrange'), false, options), xdr = _ref[0], xmapper = _ref[1];
    _ref1 = make_range_and_mapper(data_source, [yfield], d3.max([1 / (data_source.get('data').length - 1), 0.1]), plot_model.get_obj('yrange'), false, options), ydr = _ref1[0], ymapper = _ref1[1];
    bar_plot = Collections("BarRenderer").create({
      data_source: data_source.ref(),
      xfield: xfield,
      yfield: yfield,
      xmapper: xmapper.ref(),
      ymapper: ymapper.ref(),
      parent: plot_model.ref(),
      orientation: orientation
    }, options);
    xaxis = Collections('LinearAxis').create({
      orientation: 'bottom',
      mapper: xmapper.ref(),
      parent: plot_model.ref()
    }, options);
    yaxis = Collections('LinearAxis').create({
      orientation: 'left',
      mapper: ymapper.ref(),
      parent: plot_model.ref()
    }, options);
    return plot_model.set({
      renderers: [bar_plot.ref()],
      axes: [xaxis.ref(), yaxis.ref()]
    }, options);
  };

  line_plot = function(parent, data_source, xfield, yfield, local) {
    var options, plot_model, source_name, xaxis, xdr, yaxis, ydr;
    if (_.isUndefined(local)) {
      local = true;
    }
    options = {
      'local': local
    };
    source_name = data_source.get('name');
    plot_model = Collections('Plot').create({
      data_sources: {
        source_name: data_source.ref()
      },
      parent: parent
    }, options);
    xdr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [xfield]
        }
      ]
    }, options);
    ydr = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': [yfield]
        }
      ]
    }, options);
    line_plot = Collections("LineRenderer").create({
      data_source: data_source.ref(),
      xfield: xfield,
      yfield: yfield,
      xdata_range: xdr.ref(),
      ydata_range: ydr.ref(),
      parent: plot_model.ref()
    }, options);
    xaxis = Collections('LinearAxis').create({
      'orientation': 'bottom',
      'data_range': xdr.ref(),
      'mapper': 'linear',
      'parent': plot_model.ref()
    }, options);
    yaxis = Collections('LinearAxis').create({
      'orientation': 'left',
      'data_range': ydr.ref(),
      'mapper': 'linear',
      'parent': plot_model.ref()
    }, options);
    return plot_model.set({
      'renderers': [line_plot.ref()],
      'axes': [xaxis.ref(), yaxis.ref()]
    }, options);
  };

  glyph_plot = function(data_source, renderer, dom_element, xdatanames, ydatanames) {
    var plot_model, xaxis, xdr, yaxis, ydr;
    if (xdatanames == null) {
      xdatanames = ['x'];
    }
    if (ydatanames == null) {
      ydatanames = ['y'];
    }
    plot_model = Collections('Plot').create();
    xdr = Collections('DataRange1d').create({
      sources: [
        {
          ref: data_source.ref(),
          columns: ['x']
        }
      ]
    });
    ydr = Collections('DataRange1d').create({
      sources: [
        {
          ref: data_source.ref(),
          columns: ['y']
        }
      ]
    });
    renderer.set('xdata_range', xdr.ref());
    renderer.set('ydata_range', ydr.ref());
    xaxis = Collections('LinearAxis').create({
      orientation: 'bottom',
      parent: plot_model.ref(),
      data_range: xdr.ref()
    });
    yaxis = Collections('LinearAxis').create({
      orientation: 'left',
      parent: plot_model.ref(),
      data_range: ydr.ref()
    });
    plot_model.set({
      renderers: [renderer.ref()],
      axes: [xaxis.ref(), yaxis.ref()]
    });
    return plot_model;
  };

  window.bokehprettyprint = function(obj) {
    var key, val, _results;
    _results = [];
    for (key in obj) {
      if (!__hasProp.call(obj, key)) continue;
      val = obj[key];
      _results.push(console.log(key, val));
    }
    return _results;
  };

  exports.scatter_plot = scatter_plot;

  exports.data_table = data_table;

  exports.make_range_and_mapper = make_range_and_mapper;

  exports.bar_plot = bar_plot;

  exports.line_plot = line_plot;

  exports.glyph_plot = glyph_plot;

}).call(this);
}, "table": function(exports, require, module) {(function() {
  var ContinuumView, DataTable, DataTableView, DataTables, HasParent, base, safebind,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  ContinuumView = base.ContinuumView;

  safebind = base.safebind;

  HasParent = base.HasParent;

  DataTableView = (function(_super) {

    __extends(DataTableView, _super);

    function DataTableView() {
      return DataTableView.__super__.constructor.apply(this, arguments);
    }

    DataTableView.prototype.initialize = function(options) {
      DataTableView.__super__.initialize.call(this, options);
      safebind(this, this.model, 'destroy', this.remove);
      safebind(this, this.model, 'change', this.render);
      safebind(this, this.mget_obj('data_source'), 'change', this.render);
      return this.render();
    };

    DataTableView.prototype.className = 'div';

    DataTableView.prototype.render = function() {
      var colname, data_source, datacell, datacell_template, header, header_column, header_template, html, idx, rawdata, row, row_template, rowdata, table, table_template, toiter, _i, _j, _k, _len, _len1, _len2, _ref, _ref1;
      data_source = this.mget_obj('data_source');
      table_template = "<table class='table table-striped table-bordered table-condensed' id='tableid_na'></table>";
      header_template = "<thead></thead>";
      header_column = "<th><%= column_name %></th>";
      row_template = "<tr></tr>";
      datacell_template = "<td><%= data %></td>";
      table = $(table_template);
      header = $(header_template);
      _ref = this.mget('columns');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        colname = _ref[_i];
        html = _.template(header_column, {
          'column_name': colname
        });
        header.append($(html));
      }
      table.append(header);
      rawdata = this.mget_obj('data_source').get('data');
      if (!data_source.get('selecting')) {
        toiter = _.range(rawdata.length);
      } else {
        toiter = data_source.get('selected');
      }
      for (_j = 0, _len1 = toiter.length; _j < _len1; _j++) {
        idx = toiter[_j];
        rowdata = rawdata[idx];
        row = $(row_template);
        _ref1 = this.mget('columns');
        for (_k = 0, _len2 = _ref1.length; _k < _len2; _k++) {
          colname = _ref1[_k];
          datacell = $(_.template(datacell_template, {
            'data': rowdata[colname]
          }));
          row.append(datacell);
        }
        table.append(row);
      }
      this.$el.empty();
      this.$el.html(table);
      this.$el.height(this.mget('height'));
      this.$el.width(this.mget('width'));
      return this.$el.addClass("bokehtable");
    };

    return DataTableView;

  })(ContinuumView);

  DataTable = (function(_super) {

    __extends(DataTable, _super);

    function DataTable() {
      return DataTable.__super__.constructor.apply(this, arguments);
    }

    DataTable.prototype.type = 'DataTable';

    DataTable.prototype.initialize = function(attrs, options) {
      return DataTable.__super__.initialize.call(this, attrs, options);
    };

    DataTable.prototype.defaults = {
      data_source: null,
      columns: []
    };

    DataTable.prototype.default_view = DataTableView;

    return DataTable;

  })(HasParent);

  DataTables = (function(_super) {

    __extends(DataTables, _super);

    function DataTables() {
      return DataTables.__super__.constructor.apply(this, arguments);
    }

    DataTables.prototype.model = DataTable;

    return DataTables;

  })(Backbone.Collection);

  exports.datatables = new DataTables();

  exports.DataTable = DataTable;

  exports.DataTableView = DataTableView;

}).call(this);
}, "datasource": function(exports, require, module) {(function() {
  var ColumnDataSource, ColumnDataSources, HasProperties, ObjectArrayDataSource, ObjectArrayDataSources, base,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  HasProperties = base.HasProperties;

  ObjectArrayDataSource = (function(_super) {

    __extends(ObjectArrayDataSource, _super);

    function ObjectArrayDataSource() {
      return ObjectArrayDataSource.__super__.constructor.apply(this, arguments);
    }

    ObjectArrayDataSource.prototype.type = 'ObjectArrayDataSource';

    ObjectArrayDataSource.prototype.initialize = function(attrs, options) {
      ObjectArrayDataSource.__super__.initialize.call(this, attrs, options);
      this.cont_ranges = {};
      return this.discrete_ranges = {};
    };

    ObjectArrayDataSource.prototype.getcolumn = function(colname) {
      var x;
      return (function() {
        var _i, _len, _ref, _results;
        _ref = this.get('data');
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          _results.push(x[colname]);
        }
        return _results;
      }).call(this);
    };

    ObjectArrayDataSource.prototype.compute_cont_range = function(field) {
      var data;
      data = this.getcolumn(field);
      return [_.max(data), _.min(data)];
    };

    ObjectArrayDataSource.prototype.compute_discrete_factor = function(field) {
      var temp, uniques, val, _i, _len, _ref;
      temp = {};
      _ref = this.getcolumn(field);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        val = _ref[_i];
        temp[val] = true;
      }
      uniques = _.keys(temp);
      return uniques = _.sortBy(uniques, (function(x) {
        return x;
      }));
    };

    ObjectArrayDataSource.prototype.get_cont_range = function(field, padding) {
      var center, max, min, span, _ref, _ref1,
        _this = this;
      if (_.isUndefined(padding)) {
        padding = 1.0;
      }
      if (!_.exists(this.cont_ranges, field)) {
        _ref = this.compute_cont_range(field), min = _ref[0], max = _ref[1];
        span = (max - min) * (1 + padding);
        center = (max + min) / 2.0;
        _ref1 = [center - span / 2.0, center + span / 2.0], min = _ref1[0], max = _ref1[1];
        this.cont_ranges[field] = Collections('Range1d').create({
          start: min,
          end: max
        });
        this.on('change:data', function() {
          var _ref2;
          _ref2 = _this.compute_cont_range(field), max = _ref2[0], min = _ref2[1];
          _this.cont_ranges[field].set('start', min);
          return _this.cont_ranges[field].set('end', max);
        });
      }
      return this.cont_ranges[field];
    };

    ObjectArrayDataSource.prototype.get_discrete_range = function(field) {
      var factors,
        _this = this;
      if (!_.exists(this.discrete_ranges, field)) {
        factors = this.compute_discrete_factor(field);
        this.discrete_ranges[field] = Collections('FactorRange').create({
          values: factors
        });
        this.on('change:data', function() {
          factors = _this.compute_discrete_factor(field);
          return _this.discrete_ranges[field] = Collections('FactorRange').set('values', factors);
        });
      }
      return this.discrete_ranges[field];
    };

    ObjectArrayDataSource.prototype.select = function(fields, func) {
      var args, idx, selected, val, x, _i, _len, _ref;
      selected = [];
      _ref = this.get('data');
      for (idx = _i = 0, _len = _ref.length; _i < _len; idx = ++_i) {
        val = _ref[idx];
        args = (function() {
          var _j, _len1, _results;
          _results = [];
          for (_j = 0, _len1 = fields.length; _j < _len1; _j++) {
            x = fields[_j];
            _results.push(val[x]);
          }
          return _results;
        })();
        if (func.apply(func, args)) {
          selected.push(idx);
        }
      }
      selected.sort();
      return selected;
    };

    return ObjectArrayDataSource;

  })(HasProperties);

  ObjectArrayDataSource.prototype.defaults = _.clone(ObjectArrayDataSource.prototype.defaults);

  _.extend(ObjectArrayDataSource.prototype.defaults, {
    data: [{}],
    name: 'data',
    selected: [],
    selecting: false
  });

  ObjectArrayDataSources = (function(_super) {

    __extends(ObjectArrayDataSources, _super);

    function ObjectArrayDataSources() {
      return ObjectArrayDataSources.__super__.constructor.apply(this, arguments);
    }

    ObjectArrayDataSources.prototype.model = ObjectArrayDataSource;

    return ObjectArrayDataSources;

  })(Backbone.Collection);

  ColumnDataSource = (function(_super) {

    __extends(ColumnDataSource, _super);

    function ColumnDataSource() {
      return ColumnDataSource.__super__.constructor.apply(this, arguments);
    }

    ColumnDataSource.prototype.type = 'ColumnDataSource';

    ColumnDataSource.prototype.initialize = function(attrs, options) {
      ColumnDataSource.__super__.initialize.call(this, attrs, options);
      this.cont_ranges = {};
      return this.discrete_ranges = {};
    };

    ColumnDataSource.prototype.getcolumn = function(colname) {
      return this.get('data')[colname];
    };

    ColumnDataSource.prototype.datapoints = function() {
      var data, field, fields, i, point, points, _i, _j, _len, _ref;
      data = this.get('data');
      fields = _.keys(data);
      points = [];
      for (i = _i = 0, _ref = data[fields[0]].length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        point = {};
        for (_j = 0, _len = fields.length; _j < _len; _j++) {
          field = fields[_j];
          point[field] = data[field][i];
        }
        points.push(point);
      }
      return points;
    };

    return ColumnDataSource;

  })(ObjectArrayDataSource);

  ColumnDataSources = (function(_super) {

    __extends(ColumnDataSources, _super);

    function ColumnDataSources() {
      return ColumnDataSources.__super__.constructor.apply(this, arguments);
    }

    ColumnDataSources.prototype.model = ColumnDataSource;

    return ColumnDataSources;

  })(Backbone.Collection);

  exports.objectarraydatasources = new ObjectArrayDataSources;

  exports.columndatasources = new ColumnDataSources;

  exports.ObjectArrayDataSource = ObjectArrayDataSource;

  exports.ColumnDataSource = ColumnDataSource;

}).call(this);
}, "ranges": function(exports, require, module) {(function() {
  var DataFactorRange, DataFactorRanges, DataRange1d, DataRange1ds, FactorRange, FactorRanges, HasProperties, Range1d, Range1ds, base,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  base = require("./base");

  HasProperties = base.HasProperties;

  Range1d = (function(_super) {

    __extends(Range1d, _super);

    function Range1d() {
      return Range1d.__super__.constructor.apply(this, arguments);
    }

    Range1d.prototype.type = 'Range1d';

    return Range1d;

  })(HasProperties);

  Range1d.prototype.defaults = _.clone(Range1d.prototype.defaults);

  _.extend(Range1d.prototype.defaults, {
    start: 0,
    end: 1
  });

  Range1ds = (function(_super) {

    __extends(Range1ds, _super);

    function Range1ds() {
      return Range1ds.__super__.constructor.apply(this, arguments);
    }

    Range1ds.prototype.model = Range1d;

    return Range1ds;

  })(Backbone.Collection);

  DataRange1d = (function(_super) {

    __extends(DataRange1d, _super);

    function DataRange1d() {
      return DataRange1d.__super__.constructor.apply(this, arguments);
    }

    DataRange1d.prototype.type = 'DataRange1d';

    DataRange1d.prototype._get_minmax = function() {
      var center, colname, columns, max, min, source, sourceobj, span, _i, _j, _len, _len1, _ref, _ref1, _ref2, _ref3;
      columns = [];
      _ref = this.get('sources');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        source = _ref[_i];
        sourceobj = this.resolve_ref(source['ref']);
        _ref1 = source['columns'];
        for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
          colname = _ref1[_j];
          columns.push(sourceobj.getcolumn(colname));
        }
      }
      columns = _.reduce(columns, (function(x, y) {
        return x.concat(y);
      }), []);
      columns = _.filter(columns, function(x) {
        return typeof x !== "string";
      });
      _ref2 = [_.min(columns), _.max(columns)], min = _ref2[0], max = _ref2[1];
      span = (max - min) * (1 + this.get('rangepadding'));
      center = (max + min) / 2.0;
      _ref3 = [center - span / 2.0, center + span / 2.0], min = _ref3[0], max = _ref3[1];
      return [min, max];
    };

    DataRange1d.prototype._get_start = function() {
      if (!_.isNullOrUndefined(this.get('_start'))) {
        return this.get('_start');
      } else {
        return this.get('minmax')[0];
      }
    };

    DataRange1d.prototype._set_start = function(start) {
      return this.set('_start', start);
    };

    DataRange1d.prototype._get_end = function() {
      if (!_.isNullOrUndefined(this.get('_end'))) {
        return this.get('_end');
      } else {
        return this.get('minmax')[1];
      }
    };

    DataRange1d.prototype._set_end = function(end) {
      return this.set('_end', end);
    };

    DataRange1d.prototype.dinitialize = function(attrs, options) {
      var source, _i, _len, _ref;
      DataRange1d.__super__.dinitialize.call(this, attrs, options);
      this.register_property('minmax', this._get_minmax, true);
      this.add_dependencies('minmax', this, ['sources'], ['rangepadding']);
      _ref = this.get('sources');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        source = _ref[_i];
        source = this.resolve_ref(source.ref);
        this.add_dependencies('minmax', source, 'data');
      }
      this.register_property('start', this._get_start, true);
      this.register_setter('start', this._set_start);
      this.add_dependencies('start', this, ['minmax', '_start']);
      this.register_property('end', this._get_end, true);
      this.register_setter('end', this._set_end);
      return this.add_dependencies('end', this, ['minmax', '_end']);
    };

    return DataRange1d;

  })(Range1d);

  DataRange1d.prototype.defaults = _.clone(DataRange1d.prototype.defaults);

  _.extend(DataRange1d.prototype.defaults, {
    sources: [],
    rangepadding: 0.1
  });

  DataRange1ds = (function(_super) {

    __extends(DataRange1ds, _super);

    function DataRange1ds() {
      return DataRange1ds.__super__.constructor.apply(this, arguments);
    }

    DataRange1ds.prototype.model = DataRange1d;

    return DataRange1ds;

  })(Backbone.Collection);

  Range1ds = (function(_super) {

    __extends(Range1ds, _super);

    function Range1ds() {
      return Range1ds.__super__.constructor.apply(this, arguments);
    }

    Range1ds.prototype.model = Range1d;

    return Range1ds;

  })(Backbone.Collection);

  FactorRange = (function(_super) {

    __extends(FactorRange, _super);

    function FactorRange() {
      return FactorRange.__super__.constructor.apply(this, arguments);
    }

    FactorRange.prototype.type = 'FactorRange';

    return FactorRange;

  })(HasProperties);

  FactorRange.prototype.defaults = _.clone(FactorRange.prototype.defaults);

  _.extend(FactorRange.prototype.defaults, {
    values: []
  });

  DataFactorRange = (function(_super) {

    __extends(DataFactorRange, _super);

    function DataFactorRange() {
      this._get_values = __bind(this._get_values, this);
      return DataFactorRange.__super__.constructor.apply(this, arguments);
    }

    DataFactorRange.prototype.type = 'DataFactorRange';

    DataFactorRange.prototype._get_values = function() {
      var columns, temp, uniques, val, x, _i, _len;
      columns = (function() {
        var _i, _len, _ref, _results;
        _ref = this.get('columns');
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          _results.push(this.get_obj('data_source').getcolumn(x));
        }
        return _results;
      }).call(this);
      columns = _.reduce(columns, (function(x, y) {
        return x.concat(y);
      }), []);
      temp = {};
      for (_i = 0, _len = columns.length; _i < _len; _i++) {
        val = columns[_i];
        temp[val] = true;
      }
      uniques = _.keys(temp);
      uniques = _.sortBy(uniques, (function(x) {
        return x;
      }));
      return uniques;
    };

    DataFactorRange.prototype.dinitialize = function(attrs, options) {
      DataFactorRange.__super__.dinitialize.call(this, attrs, options);
      this.register_property;
      this.register_property('values', this._get_values, true);
      this.add_dependencies('values', this, ['data_source', 'columns']);
      return this.add_dependencies('values', this.get_obj('data_source'), ['data_source', 'columns']);
    };

    return DataFactorRange;

  })(FactorRange);

  DataFactorRange.prototype.defaults = _.clone(DataFactorRange.prototype.defaults);

  _.extend(DataFactorRange.prototype.defaults, {
    values: [],
    columns: [],
    data_source: null
  });

  DataFactorRanges = (function(_super) {

    __extends(DataFactorRanges, _super);

    function DataFactorRanges() {
      return DataFactorRanges.__super__.constructor.apply(this, arguments);
    }

    DataFactorRanges.prototype.model = DataFactorRange;

    return DataFactorRanges;

  })(Backbone.Collection);

  FactorRanges = (function(_super) {

    __extends(FactorRanges, _super);

    function FactorRanges() {
      return FactorRanges.__super__.constructor.apply(this, arguments);
    }

    FactorRanges.prototype.model = FactorRange;

    return FactorRanges;

  })(Backbone.Collection);

  exports.range1ds = new Range1ds;

  exports.datarange1ds = new DataRange1ds;

  exports.datafactorranges = new DataFactorRanges;

}).call(this);
}, "container": function(exports, require, module) {(function() {
  var ActiveToolManager, ContinuumView, GridPlotContainer, GridPlotContainerView, GridPlotContainers, GridViewState, HasParent, HasProperties, Plot, PlotContext, PlotContextView, PlotContextViewState, PlotContextViewWithMaximized, PlotContexts, PlotView, Plots, SinglePlotContextView, ViewState, base, build_views, safebind,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  HasParent = base.HasParent;

  HasProperties = base.HasProperties;

  ContinuumView = base.ContinuumView;

  safebind = base.safebind;

  build_views = base.build_views;

  ActiveToolManager = require("./tools/activetoolmanager").ActiveToolManager;

  PlotContextView = (function(_super) {

    __extends(PlotContextView, _super);

    function PlotContextView() {
      this.removeplot = __bind(this.removeplot, this);

      this.closeall = __bind(this.closeall, this);

      this.savetitle = __bind(this.savetitle, this);
      return PlotContextView.__super__.constructor.apply(this, arguments);
    }

    PlotContextView.prototype.initialize = function(options) {
      this.views = {};
      this.views_rendered = [false];
      this.child_models = [];
      PlotContextView.__super__.initialize.call(this, options);
      return this.render();
    };

    PlotContextView.prototype.delegateEvents = function() {
      safebind(this, this.model, 'destroy', this.remove);
      safebind(this, this.model, 'change', this.render);
      return PlotContextView.__super__.delegateEvents.call(this);
    };

    PlotContextView.prototype.generate_remove_child_callback = function(view) {
      var callback,
        _this = this;
      callback = function() {
        return null;
      };
      return callback;
    };

    PlotContextView.prototype.build_children = function() {
      var created_views;
      created_views = build_views(this.views, this.mget_obj('children'), {});
      window.pc_created_views = created_views;
      window.pc_views = this.views;
      return null;
    };

    PlotContextView.prototype.events = {
      'click .plotclose': 'removeplot',
      'click .closeall': 'closeall',
      'keydown .plottitle': 'savetitle'
    };

    PlotContextView.prototype.size_textarea = function(textarea) {
      var scrollHeight;
      scrollHeight = $(textarea).height(0).prop('scrollHeight');
      return $(textarea).height(scrollHeight);
    };

    PlotContextView.prototype.savetitle = function(e) {
      var plotnum, s_pc;
      if (e.keyCode === 13) {
        e.preventDefault();
        plotnum = parseInt($(e.currentTarget).parent().attr('data-plot_num'));
        s_pc = this.model.resolve_ref(this.mget('children')[plotnum]);
        s_pc.set('title', $(e.currentTarget).val());
        s_pc.save();
        $(e.currentTarget).blur();
        return false;
      }
      return this.size_textarea($(e.currentTarget));
    };

    PlotContextView.prototype.closeall = function(e) {
      this.mset('children', []);
      return this.model.save();
    };

    PlotContextView.prototype.removeplot = function(e) {
      var newchildren, plotnum, s_pc, view, x;
      plotnum = parseInt($(e.currentTarget).parent().attr('data-plot_num'));
      s_pc = this.model.resolve_ref(this.mget('children')[plotnum]);
      view = this.views[s_pc.get('id')];
      view.remove();
      newchildren = (function() {
        var _i, _len, _ref, _results;
        _ref = this.mget('children');
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          if (x.id !== view.model.id) {
            _results.push(x);
          }
        }
        return _results;
      }).call(this);
      this.mset('children', newchildren);
      this.model.save();
      return false;
    };

    PlotContextView.prototype.render = function() {
      var index, key, modelref, node, numplots, tab_names, title, to_render, val, view, _i, _len, _ref, _ref1,
        _this = this;
      PlotContextView.__super__.render.call(this);
      this.build_children();
      _ref = this.views;
      for (key in _ref) {
        if (!__hasProp.call(_ref, key)) continue;
        val = _ref[key];
        val.$el.detach();
      }
      this.$el.html('');
      numplots = _.keys(this.views).length;
      this.$el.append("<div>You have " + numplots + " plots</div>");
      this.$el.append("<div><a class='closeall' href='#'>Close All Plots</a></div>");
      this.$el.append("<br/>");
      to_render = [];
      tab_names = {};
      _ref1 = this.mget('children');
      for (index = _i = 0, _len = _ref1.length; _i < _len; index = ++_i) {
        modelref = _ref1[index];
        view = this.views[modelref.id];
        node = $("<div class='jsp' data-plot_num='" + index + "'></div>");
        this.$el.append(node);
        title = view.model.get('title');
        node.append($("<textarea class='plottitle'>" + title + "</textarea>"));
        node.append($("<a class='plotclose'>[close]</a>"));
        node.append(view.el);
      }
      _.defer(function() {
        var textarea, _j, _len1, _ref2, _results;
        _ref2 = _this.$el.find('.plottitle');
        _results = [];
        for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
          textarea = _ref2[_j];
          _results.push(_this.size_textarea($(textarea)));
        }
        return _results;
      });
      return null;
    };

    return PlotContextView;

  })(ContinuumView);

  PlotContextViewState = (function(_super) {

    __extends(PlotContextViewState, _super);

    function PlotContextViewState() {
      return PlotContextViewState.__super__.constructor.apply(this, arguments);
    }

    PlotContextViewState.prototype.defaults = {
      maxheight: 600,
      maxwidth: 600,
      selected: 0
    };

    return PlotContextViewState;

  })(HasProperties);

  PlotContextViewWithMaximized = (function(_super) {

    __extends(PlotContextViewWithMaximized, _super);

    function PlotContextViewWithMaximized() {
      return PlotContextViewWithMaximized.__super__.constructor.apply(this, arguments);
    }

    PlotContextViewWithMaximized.prototype.initialize = function(options) {
      var _this = this;
      this.selected = 0;
      this.viewstate = new PlotContextViewState({
        maxheight: options.maxheight,
        maxwidth: options.maxwidth
      });
      PlotContextViewWithMaximized.__super__.initialize.call(this, options);
      safebind(this, this.viewstate, 'change', this.render);
      return safebind(this, this.model, 'change:children', function() {
        var selected;
        selected = _this.viewstate.get('selected');
        if (selected > _this.model.get('children') - 1) {
          return _this.viewstate.set('selected', 0);
        }
      });
    };

    PlotContextViewWithMaximized.prototype.events = {
      'click .maximize': 'maximize',
      'click .plotclose': 'removeplot',
      'click .closeall': 'closeall',
      'keydown .plottitle': 'savetitle'
    };

    PlotContextViewWithMaximized.prototype.maximize = function(e) {
      var plotnum;
      plotnum = parseInt($(e.currentTarget).parent().attr('data-plot_num'));
      return this.viewstate.set('selected', plotnum);
    };

    PlotContextViewWithMaximized.prototype.render = function() {
      var index, key, main, model, modelref, node, tab_names, title, to_render, val, view, _i, _len, _ref, _ref1,
        _this = this;
      PlotContextViewWithMaximized.__super__.render.call(this);
      this.build_children();
      _ref = this.views;
      for (key in _ref) {
        if (!__hasProp.call(_ref, key)) continue;
        val = _ref[key];
        val.$el.detach();
      }
      this.$el.html('');
      main = $("<div class='plotsidebar'><div>");
      this.$el.append(main);
      this.$el.append("<div class='maxplot'>");
      main.append("<div><a class='closeall' href='#'>Close All Plots</a></div>");
      main.append("<br/>");
      to_render = [];
      tab_names = {};
      _ref1 = this.mget('children');
      for (index = _i = 0, _len = _ref1.length; _i < _len; index = ++_i) {
        modelref = _ref1[index];
        view = this.views[modelref.id];
        node = $("<div class='jsp' data-plot_num='" + index + "'></div>");
        main.append(node);
        title = view.model.get('title');
        node.append($("<textarea class='plottitle'>" + title + "</textarea>"));
        node.append($("<a class='maximize'>[max]</a>"));
        node.append($("<a class='plotclose'>[close]</a>"));
        node.append(view.el);
      }
      if (this.mget('children').length > 0) {
        modelref = this.mget('children')[this.viewstate.get('selected')];
        model = this.model.resolve_ref(modelref);
        this.maxview = new model.default_view({
          model: model
        });
        this.$el.find('.maxplot').append(this.maxview.$el);
      } else {
        this.maxview = null;
      }
      _.defer(function() {
        var height, heightratio, maxheight, maxwidth, newheight, newwidth, ratio, textarea, width, widthratio, _j, _len1, _ref2;
        _ref2 = main.find('.plottitle');
        for (_j = 0, _len1 = _ref2.length; _j < _len1; _j++) {
          textarea = _ref2[_j];
          _this.size_textarea($(textarea));
        }
        if (_this.maxview) {
          width = model.get('width');
          height = model.get('height');
          maxwidth = _this.viewstate.get('maxwidth');
          maxheight = _this.viewstate.get('maxheight');
          widthratio = maxwidth / width;
          heightratio = maxheight / height;
          ratio = _.min([widthratio, heightratio]);
          newwidth = ratio * width;
          newheight = ratio * height;
          _this.maxview.viewstate.set('height', newheight);
          return _this.maxview.viewstate.set('width', newwidth);
        }
      });
      return null;
    };

    return PlotContextViewWithMaximized;

  })(PlotContextView);

  SinglePlotContextView = (function(_super) {

    __extends(SinglePlotContextView, _super);

    function SinglePlotContextView() {
      this.removeplot = __bind(this.removeplot, this);
      return SinglePlotContextView.__super__.constructor.apply(this, arguments);
    }

    SinglePlotContextView.prototype.initialize = function(options) {
      this.views = {};
      this.views_rendered = [false];
      this.child_models = [];
      this.target_model_id = options.target_model_id;
      SinglePlotContextView.__super__.initialize.call(this, options);
      return this.render();
    };

    SinglePlotContextView.prototype.delegateEvents = function() {
      safebind(this, this.model, 'destroy', this.remove);
      safebind(this, this.model, 'change', this.render);
      return SinglePlotContextView.__super__.delegateEvents.call(this);
    };

    SinglePlotContextView.prototype.generate_remove_child_callback = function(view) {
      var callback,
        _this = this;
      callback = function() {
        return null;
      };
      return callback;
    };

    SinglePlotContextView.prototype.single_plot_children = function() {
      var _this = this;
      return _.filter(this.mget_obj('children'), function(child) {
        return child.id === _this.target_model_id;
      });
    };

    SinglePlotContextView.prototype.build_children = function() {
      var created_views;
      created_views = build_views(this.views, this.single_plot_children(), {});
      window.pc_created_views = created_views;
      window.pc_views = this.views;
      return null;
    };

    SinglePlotContextView.prototype.events = {
      'click .plotclose': 'removeplot'
    };

    SinglePlotContextView.prototype.removeplot = function(e) {
      var newchildren, plotnum, s_pc, view, x;
      plotnum = parseInt($(e.currentTarget).parent().attr('data-plot_num'));
      s_pc = this.model.resolve_ref(this.mget('children')[plotnum]);
      view = this.views[s_pc.get('id')];
      view.remove();
      newchildren = (function() {
        var _i, _len, _ref, _results;
        _ref = this.mget('children');
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          x = _ref[_i];
          if (x.id !== view.model.id) {
            _results.push(x);
          }
        }
        return _results;
      }).call(this);
      this.mset('children', newchildren);
      this.model.save();
      return false;
    };

    SinglePlotContextView.prototype.render = function() {
      var index, key, modelref, node, tab_names, title, to_render, val, view, _i, _len, _ref, _ref1;
      SinglePlotContextView.__super__.render.call(this);
      this.build_children();
      _ref = this.views;
      for (key in _ref) {
        if (!__hasProp.call(_ref, key)) continue;
        val = _ref[key];
        val.$el.detach();
      }
      this.$el.html('');
      to_render = [];
      tab_names = {};
      _ref1 = this.single_plot_children();
      for (index = _i = 0, _len = _ref1.length; _i < _len; index = ++_i) {
        modelref = _ref1[index];
        console.log("modelref.id ", modelref.id);
        view = this.views[modelref.id];
        node = $("<div class='jsp' data-plot_num='" + index + "'></div>");
        this.$el.append(node);
        title = view.model.get('title');
        node.append($("<p>" + title + "</p>"));
        node.append(view.el);
      }
      return null;
    };

    return SinglePlotContextView;

  })(ContinuumView);

  PlotView = (function(_super) {

    __extends(PlotView, _super);

    function PlotView() {
      return PlotView.__super__.constructor.apply(this, arguments);
    }

    PlotView.prototype.default_options = {
      scale: 1.0
    };

    PlotView.prototype.view_options = function() {
      return _.extend({
        plot_model: this.model,
        plot_view: this
      }, this.options);
    };

    PlotView.prototype.build_renderers = function() {
      return build_views(this.renderers, this.mget_obj('renderers'), this.view_options());
    };

    PlotView.prototype.build_axes = function() {
      return build_views(this.axes, this.mget_obj('axes'), this.view_options());
    };

    PlotView.prototype.build_tools = function() {
      return build_views(this.tools, this.mget_obj('tools'), this.view_options());
    };

    PlotView.prototype.build_overlays = function() {
      return build_views(this.overlays, this.mget_obj('overlays'), this.view_options());
    };

    PlotView.prototype.bind_overlays = function() {
      var overlayspec, _i, _len, _ref, _results;
      _ref = this.mget('overlays');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        overlayspec = _ref[_i];
        _results.push(this.overlays[overlayspec.id].bind_events(this));
      }
      return _results;
    };

    PlotView.prototype.bind_tools = function() {
      var toolspec, _i, _len, _ref, _results;
      _ref = this.mget('tools');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        toolspec = _ref[_i];
        _results.push(this.tools[toolspec.id].bind_events(this));
      }
      return _results;
    };

    PlotView.prototype.tagName = 'div';

    PlotView.prototype.events = {
      "mousemove .main_can_wrapper": "_mousemove",
      "mousedown .main_can_wrapper": "_mousedown"
    };

    PlotView.prototype._mousedown = function(e) {
      var f, _i, _len, _ref, _results;
      _ref = this.mousedownCallbacks;
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        f = _ref[_i];
        _results.push(f(e, e.layerX, e.layerY));
      }
      return _results;
    };

    PlotView.prototype._mousemove = function(e) {
      var f, _i, _len, _ref, _results;
      _ref = this.moveCallbacks;
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        f = _ref[_i];
        _results.push(f(e, e.layerX, e.layerY));
      }
      return _results;
    };

    PlotView.prototype.initialize = function(options) {
      var atm, border_space, height, offset, width;
      this.throttled = _.throttle(this.render_deferred_components, 50);
      PlotView.__super__.initialize.call(this, _.defaults(options, this.default_options));
      height = options.height ? options.height : this.mget('height');
      width = options.width ? options.width : this.mget('width');
      offset = options.offset ? options.offset : this.mget('offset');
      if (options.border_space) {
        border_space = options.border_space;
      } else {
        border_space = this.mget('border_space');
      }
      this.viewstate = new ViewState({
        height: height,
        width: width,
        offset: offset,
        border_space: border_space
      });
      this.renderers = {};
      this.axes = {};
      this.tools = {};
      this.overlays = {};
      this.eventSink = _.extend({}, Backbone.Events);
      atm = new ActiveToolManager(this.eventSink);
      this.moveCallbacks = [];
      this.mousedownCallbacks = [];
      this.keydownCallbacks = [];
      this.render_init();
      this.render();
      this.build_subviews();
      this.throttled();
      return this;
    };

    PlotView.prototype.render_init = function() {
      this.$el.append($("<div class='button_bar'/>\n<div class='all_can_wrapper'>\n\n  <div class='main_can_wrapper can_wrapper'>\n    <div class='_shader' />\n    <canvas class='main_can'></canvas>\n  </div>\n  <div class='x_can_wrapper can_wrapper'>\n      <canvas class='x_can'></canvas>\n  </div>\n  <div class='y_can_wrapper can_wrapper'>\n    <canvas class='y_can'></canvas>\n  </div>\n</div>"));
      this.$el.addClass("plot_wrap");
      this.canvas = this.$el.find('canvas.main_can');
      this.x_can = this.$el.find('canvas.x_can')[0];
      this.y_can = this.$el.find('canvas.y_can')[0];
      this.main_can_wrapper = this.$el.find('.main_can_wrapper');
      this.x_can_wrapper = this.$el.find('.x_can_wrapper');
      return this.y_can_wrapper = this.$el.find('.y_can_wrapper');
    };

    PlotView.prototype.build_subviews = function() {
      this.build_renderers();
      this.build_axes();
      this.build_tools();
      this.build_overlays();
      this.bind_tools();
      return this.bind_overlays();
    };

    PlotView.prototype.bind_bokeh_events = function() {
      var _this = this;
      safebind(this, this.viewstate, 'change', this.render);
      safebind(this, this.model, 'change:renderers', this.build_renderers);
      safebind(this, this.model, 'change:axes', this.build_axes);
      safebind(this, this.model, 'change:tools', this.build_tools);
      safebind(this, this.model, 'change', this.render);
      safebind(this, this.viewstate, 'change', this.render);
      return safebind(this, this.model, 'destroy', function() {
        return _this.remove();
      });
    };

    PlotView.prototype.render = function() {
      var bord, border_space, h, height, o_h, o_w, outerheight, outerwidth, w, wh, width, xcw;
      height = this.viewstate.get('height');
      width = this.viewstate.get('width');
      border_space = this.viewstate.get('border_space');
      outerheight = this.viewstate.get('outerheight');
      outerwidth = this.viewstate.get('outerwidth');
      PlotView.__super__.render.call(this);
      this.$el.attr("width", outerwidth).attr('height', outerheight);
      bord = border_space;
      xcw = this.x_can_wrapper;
      w = width;
      h = height;
      o_w = outerwidth;
      o_h = outerheight;
      this.main_can_wrapper.attr('style', "left:" + bord + "px; height:" + h + "px; width:" + w + "px");
      this.x_can_wrapper.attr('style', "left:" + bord + "px; top:" + h + "px; height:" + bord + "px; width:" + w + "px");
      this.y_can_wrapper.attr('style', "width:" + bord + "px; height:" + h + "px;");
      this.$el.attr("style", "height:" + o_h + "px; width:" + o_w + "px");
      wh = function(el, w, h) {
        $(el).attr('width', w);
        return $(el).attr('height', h);
      };
      wh(this.canvas, w, h);
      wh(this.x_can, w, bord);
      wh(this.y_can, bord, h);
      this.x_can_ctx = this.x_can.getContext('2d');
      this.y_can_ctx = this.y_can.getContext('2d');
      this.ctx = this.canvas[0].getContext('2d');
      return this.render_end();
    };

    PlotView.prototype.render_deferred_components = function(force) {
      var all_views, v, _i, _len, _results;
      all_views = _.flatten(_.map([this.tools, this.axes, this.renderers, this.overlays], _.values));
      this.ctx.clearRect(0, 0, this.viewstate.get('width'), this.viewstate.get('height'));
      _results = [];
      for (_i = 0, _len = all_views.length; _i < _len; _i++) {
        v = all_views[_i];
        _results.push(v.render());
      }
      return _results;
    };

    return PlotView;

  })(ContinuumView);

  GridPlotContainerView = (function(_super) {

    __extends(GridPlotContainerView, _super);

    function GridPlotContainerView() {
      return GridPlotContainerView.__super__.constructor.apply(this, arguments);
    }

    GridPlotContainerView.prototype.tagName = 'div';

    GridPlotContainerView.prototype.className = "gridplot_container";

    GridPlotContainerView.prototype.default_options = {
      scale: 1.0
    };

    GridPlotContainerView.prototype.set_child_view_states = function() {
      var row, viewstaterow, viewstates, x, _i, _len, _ref;
      viewstates = [];
      _ref = this.mget('children');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        row = _ref[_i];
        viewstaterow = (function() {
          var _j, _len1, _results;
          _results = [];
          for (_j = 0, _len1 = row.length; _j < _len1; _j++) {
            x = row[_j];
            _results.push(this.childviews[x.id].viewstate);
          }
          return _results;
        }).call(this);
        viewstates.push(viewstaterow);
      }
      return this.viewstate.set('childviewstates', viewstates);
    };

    GridPlotContainerView.prototype.initialize = function(options) {
      GridPlotContainerView.__super__.initialize.call(this, _.defaults(options, this.default_options));
      this.viewstate = new GridViewState();
      this.childviews = {};
      this.build_children();
      this.render();
      return this;
    };

    GridPlotContainerView.prototype.bind_bokeh_events = function() {
      var _this = this;
      safebind(this, this.model, 'change:children', this.build_children);
      safebind(this, this.model, 'change', this.render);
      safebind(this, this.viewstate, 'change', this.render);
      return safebind(this, this.model, 'destroy', function() {
        return _this.remove();
      });
    };

    GridPlotContainerView.prototype.b_events = {
      "change:children model": "build_children",
      "change model": "render",
      "change viewstate": "render",
      "destroy model": "remove"
    };

    GridPlotContainerView.prototype.build_children = function() {
      var childmodels, plot, row, _i, _j, _len, _len1, _ref;
      childmodels = [];
      _ref = this.mget_obj('children');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        row = _ref[_i];
        for (_j = 0, _len1 = row.length; _j < _len1; _j++) {
          plot = row[_j];
          childmodels.push(plot);
        }
      }
      build_views(this.childviews, childmodels, {});
      return this.set_child_view_states();
    };

    GridPlotContainerView.prototype.render = function() {
      var cidx, col_widths, height, last_plot, plot_divs, plot_wrapper, plotspec, ridx, row, row_heights, view, width, x_coords, xpos, y_coords, ypos, _i, _j, _k, _len, _len1, _len2, _ref, _ref1;
      GridPlotContainerView.__super__.render.call(this);
      _ref = _.values(this.childviews);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        view = _ref[_i];
        view.$el.detach();
      }
      this.$el.html('');
      row_heights = this.viewstate.get('layout_heights');
      col_widths = this.viewstate.get('layout_widths');
      y_coords = [0];
      _.reduceRight(row_heights.slice(1), function(x, y) {
        var val;
        val = x + y;
        y_coords.push(val);
        return val;
      }, 0);
      y_coords.reverse();
      x_coords = [0];
      _.reduce(col_widths.slice(0), function(x, y) {
        var val;
        val = x + y;
        x_coords.push(val);
        return val;
      }, 0);
      plot_divs = [];
      last_plot = null;
      _ref1 = this.mget('children');
      for (ridx = _j = 0, _len1 = _ref1.length; _j < _len1; ridx = ++_j) {
        row = _ref1[ridx];
        for (cidx = _k = 0, _len2 = row.length; _k < _len2; cidx = ++_k) {
          plotspec = row[cidx];
          view = this.childviews[plotspec.id];
          ypos = this.viewstate.position_child_y(view.viewstate.get('outerheight'), y_coords[ridx]);
          xpos = this.viewstate.position_child_x(view.viewstate.get('outerwidth'), x_coords[cidx]);
          plot_wrapper = $("<div class='gp_plotwrapper'></div>");
          plot_wrapper.attr('style', "left:" + xpos + "px; top:" + ypos + "px");
          plot_wrapper.append(view.$el);
          this.$el.append(plot_wrapper);
        }
      }
      height = this.viewstate.get('outerheight');
      width = this.viewstate.get('outerwidth');
      this.$el.attr('style', "height:" + height + "px;width:" + width + "px");
      return this.render_end();
    };

    return GridPlotContainerView;

  })(ContinuumView);

  GridPlotContainer = (function(_super) {

    __extends(GridPlotContainer, _super);

    function GridPlotContainer() {
      return GridPlotContainer.__super__.constructor.apply(this, arguments);
    }

    GridPlotContainer.prototype.type = 'GridPlotContainer';

    GridPlotContainer.prototype.default_view = GridPlotContainerView;

    return GridPlotContainer;

  })(HasParent);

  GridPlotContainer.prototype.defaults = _.clone(GridPlotContainer.prototype.defaults);

  _.extend(GridPlotContainer.prototype.defaults, {
    children: [[]],
    border_space: 0
  });

  GridPlotContainers = (function(_super) {

    __extends(GridPlotContainers, _super);

    function GridPlotContainers() {
      return GridPlotContainers.__super__.constructor.apply(this, arguments);
    }

    GridPlotContainers.prototype.model = GridPlotContainer;

    return GridPlotContainers;

  })(Backbone.Collection);

  Plot = (function(_super) {

    __extends(Plot, _super);

    function Plot() {
      return Plot.__super__.constructor.apply(this, arguments);
    }

    Plot.prototype.type = 'Plot';

    Plot.prototype.default_view = PlotView;

    Plot.prototype.parent_properties = ['background_color', 'foreground_color', 'width', 'height', 'border_space', 'unselected_color'];

    return Plot;

  })(HasParent);

  Plot.prototype.defaults = _.clone(Plot.prototype.defaults);

  _.extend(Plot.prototype.defaults, {
    'data_sources': {},
    'renderers': [],
    'axes': [],
    'legends': [],
    'tools': [],
    'overlays': [],
    'usedialog': false,
    'title': 'Plot'
  });

  Plot.prototype.display_defaults = _.clone(Plot.prototype.display_defaults);

  _.extend(Plot.prototype.display_defaults, {
    background_color: "#eee",
    foreground_color: "#333",
    unselected_color: "#ccc"
  });

  Plots = (function(_super) {

    __extends(Plots, _super);

    function Plots() {
      return Plots.__super__.constructor.apply(this, arguments);
    }

    Plots.prototype.model = Plot;

    return Plots;

  })(Backbone.Collection);

  PlotContext = (function(_super) {

    __extends(PlotContext, _super);

    function PlotContext() {
      return PlotContext.__super__.constructor.apply(this, arguments);
    }

    PlotContext.prototype.type = 'PlotContext';

    PlotContext.prototype.default_view = PlotContextView;

    PlotContext.prototype.url = function() {
      return PlotContext.__super__.url.call(this);
    };

    PlotContext.prototype.defaults = {
      children: [],
      render_loop: true
    };

    return PlotContext;

  })(HasParent);

  PlotContexts = (function(_super) {

    __extends(PlotContexts, _super);

    function PlotContexts() {
      return PlotContexts.__super__.constructor.apply(this, arguments);
    }

    PlotContexts.prototype.model = PlotContext;

    return PlotContexts;

  })(Backbone.Collection);

  ViewState = (function(_super) {

    __extends(ViewState, _super);

    function ViewState() {
      return ViewState.__super__.constructor.apply(this, arguments);
    }

    ViewState.prototype.initialize = function(attrs, options) {
      ViewState.__super__.initialize.call(this, attrs, options);
      this.register_property('outerwidth', function() {
        return this.get('width') + 2 * this.get('border_space');
      }, false);
      this.add_dependencies('outerwidth', this, ['width', 'border_space']);
      this.register_property('outerheight', function() {
        return this.get('height') + 2 * this.get('border_space');
      }, false);
      return this.add_dependencies('outerheight', this, ['height', 'border_space']);
    };

    ViewState.prototype.xpos = function(x) {
      return x;
    };

    ViewState.prototype.ypos = function(y) {
      return this.get('height') - y;
    };

    ViewState.prototype.v_xpos = function(xx) {
      return xx;
    };

    ViewState.prototype.v_ypos = function(yy) {
      var height, idx, y, _i, _len;
      height = this.get('height');
      for (idx = _i = 0, _len = yy.length; _i < _len; idx = ++_i) {
        y = yy[idx];
        yy[idx] = height - y;
      }
      return yy;
    };

    ViewState.prototype.rxpos = function(x) {
      return x;
    };

    ViewState.prototype.rypos = function(y) {
      return this.get('height') - y;
    };

    ViewState.prototype.position_child_x = function(childsize, offset) {
      return this.xpos(offset);
    };

    ViewState.prototype.position_child_y = function(childsize, offset) {
      return this.ypos(offset) - childsize;
    };

    ViewState.prototype.defaults = {
      parent: null
    };

    ViewState.prototype.display_defaults = {
      width: 200,
      height: 200,
      position: 0,
      offset: [0, 0],
      border_space: 30
    };

    return ViewState;

  })(HasParent);

  GridViewState = (function(_super) {

    __extends(GridViewState, _super);

    function GridViewState() {
      this.layout_widths = __bind(this.layout_widths, this);

      this.layout_heights = __bind(this.layout_heights, this);

      this.setup_layout_properties = __bind(this.setup_layout_properties, this);
      return GridViewState.__super__.constructor.apply(this, arguments);
    }

    GridViewState.prototype.setup_layout_properties = function() {
      var row, viewstate, _i, _len, _ref, _results;
      this.register_property('layout_heights', this.layout_heights, true);
      this.register_property('layout_widths', this.layout_widths, true);
      _ref = this.get('childviewstates');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        row = _ref[_i];
        _results.push((function() {
          var _j, _len1, _results1;
          _results1 = [];
          for (_j = 0, _len1 = row.length; _j < _len1; _j++) {
            viewstate = row[_j];
            this.add_dependencies('layout_heights', viewstate, 'outerheight');
            _results1.push(this.add_dependencies('layout_widths', viewstate, 'outerwidth'));
          }
          return _results1;
        }).call(this));
      }
      return _results;
    };

    GridViewState.prototype.initialize = function(attrs, options) {
      GridViewState.__super__.initialize.call(this, attrs, options);
      this.setup_layout_properties();
      safebind(this, this, 'change:childviewstates', this.setup_layout_properties);
      this.register_property('height', function() {
        return _.reduce(this.get('layout_heights'), (function(x, y) {
          return x + y;
        }), 0);
      }, true);
      this.add_dependencies('height', this, 'layout_heights');
      this.register_property('width', function() {
        return _.reduce(this.get('layout_widths'), (function(x, y) {
          return x + y;
        }), 0);
      }, true);
      return this.add_dependencies('width', this, 'layout_widths');
    };

    GridViewState.prototype.maxdim = function(dim, row) {
      if (row.length === 0) {
        return 0;
      } else {
        return _.max(_.map(row, (function(x) {
          return x.get(dim);
        })));
      }
    };

    GridViewState.prototype.layout_heights = function() {
      var row, row_heights;
      row_heights = (function() {
        var _i, _len, _ref, _results;
        _ref = this.get('childviewstates');
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          row = _ref[_i];
          _results.push(this.maxdim('outerheight', row));
        }
        return _results;
      }).call(this);
      return row_heights;
    };

    GridViewState.prototype.layout_widths = function() {
      var col, col_widths, columns, n, num_cols, row;
      num_cols = this.get('childviewstates')[0].length;
      columns = (function() {
        var _i, _len, _ref, _results;
        _ref = _.range(num_cols);
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          n = _ref[_i];
          _results.push((function() {
            var _j, _len1, _ref1, _results1;
            _ref1 = this.get('childviewstates');
            _results1 = [];
            for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
              row = _ref1[_j];
              _results1.push(row[n]);
            }
            return _results1;
          }).call(this));
        }
        return _results;
      }).call(this);
      col_widths = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = columns.length; _i < _len; _i++) {
          col = columns[_i];
          _results.push(this.maxdim('outerwidth', col));
        }
        return _results;
      }).call(this);
      return col_widths;
    };

    return GridViewState;

  })(ViewState);

  GridViewState.prototype.defaults = _.clone(GridViewState.prototype.defaults);

  _.extend(GridViewState.prototype.defaults, {
    childviewstates: [[]],
    border_space: 0
  });

  exports.gridplotcontainers = new GridPlotContainers;

  exports.plots = new Plots;

  exports.plotcontexts = new PlotContexts();

  exports.PlotContextView = PlotContextView;

  exports.PlotContextViewState = PlotContextViewState;

  exports.PlotContextViewWithMaximized = PlotContextViewWithMaximized;

  exports.SinglePlotContextView = SinglePlotContextView;

  exports.PlotView = PlotView;

  exports.GridPlotContainerView = GridPlotContainerView;

  exports.GridPlotContainer = GridPlotContainer;

  exports.Plot = Plot;

  exports.PlotContext = PlotContext;

  exports.ViewState = ViewState;

  exports.GridViewState = GridViewState;

}).call(this);
}, "tools/eventgenerators": function(exports, require, module) {(function() {
  var OnePointWheelEventGenerator, TwoPointEventGenerator;

  TwoPointEventGenerator = (function() {

    function TwoPointEventGenerator(options) {
      this.options = options;
      this.toolName = this.options.eventBasename;
      this.dragging = false;
      this.basepoint_set = false;
      this.button_activated = false;
      this.tool_active = false;
    }

    TwoPointEventGenerator.prototype.bind_events = function(plotview, eventSink) {
      var toolName,
        _this = this;
      toolName = this.toolName;
      this.plotview = plotview;
      this.eventSink = eventSink;
      this.plotview.moveCallbacks.push(function(e, x, y) {
        var offset;
        if (!_this.dragging) {
          return;
        }
        if (!_this.tool_active) {
          return;
        }
        offset = $(e.currentTarget).offset();
        e.bokehX = e.pageX - offset.left;
        e.bokehY = e.pageY - offset.top;
        if (!_this.basepoint_set) {
          _this.dragging = true;
          _this.basepoint_set = true;
          return eventSink.trigger("" + toolName + ":SetBasepoint", e);
        } else {
          eventSink.trigger("" + toolName + ":UpdatingMouseMove", e);
          e.preventDefault();
          return e.stopPropagation();
        }
      });
      $(document).bind('keydown', function(e) {
        if (e[_this.options.keyName]) {
          _this._start_drag();
        }
        if (e.keyCode === 27) {
          return eventSink.trigger("clear_active_tool");
        }
      });
      $(document).bind('keyup', function(e) {
        if (!e[_this.options.keyName]) {
          return _this._stop_drag();
        }
      });
      this.plotview.main_can_wrapper.bind('mousedown', function(e) {
        if (_this.button_activated) {
          _this._start_drag();
          return false;
        }
      });
      this.plotview.main_can_wrapper.bind('mouseup', function(e) {
        if (_this.button_activated) {
          _this._stop_drag();
          return false;
        }
      });
      this.$tool_button = $("<button class='btn btn-small'> " + this.options.buttonText + " </button>");
      this.plotview.$el.find('.button_bar').append(this.$tool_button);
      this.$tool_button.click(function() {
        if (_this.button_activated) {
          return eventSink.trigger("clear_active_tool");
        } else {
          eventSink.trigger("active_tool", toolName);
          return _this.button_activated = true;
        }
      });
      eventSink.on("" + toolName + ":deactivated", function() {
        _this.tool_active = false;
        _this.button_activated = false;
        return _this.$tool_button.removeClass('active');
      });
      eventSink.on("" + toolName + ":activated", function() {
        _this.tool_active = true;
        return _this.$tool_button.addClass('active');
      });
      return eventSink;
    };

    TwoPointEventGenerator.prototype._start_drag = function() {
      this.eventSink.trigger("active_tool", this.toolName);
      if (!this.dragging) {
        this.dragging = true;
        if (!this.button_activated) {
          return this.$tool_button.addClass('active');
        }
      }
    };

    TwoPointEventGenerator.prototype._stop_drag = function() {
      this.basepoint_set = false;
      if (this.dragging) {
        this.dragging = false;
        if (!this.button_activated) {
          this.$tool_button.removeClass('active');
        }
        return this.eventSink.trigger("" + this.options.eventBasename + ":DragEnd");
      }
    };

    return TwoPointEventGenerator;

  })();

  OnePointWheelEventGenerator = (function() {

    function OnePointWheelEventGenerator(options) {
      this.options = options;
      this.toolName = this.options.eventBasename;
      this.dragging = false;
      this.basepoint_set = false;
      this.button_activated = false;
      this.tool_active = false;
    }

    OnePointWheelEventGenerator.prototype.bind_events = function(plotview, eventSink) {
      var no_scroll, restore_scroll, toolName,
        _this = this;
      toolName = this.toolName;
      this.plotview = plotview;
      this.eventSink = eventSink;
      this.plotview.main_can_wrapper.bind("mousewheel", function(e, delta, dX, dY) {
        var offset;
        if (!_this.tool_active) {
          return;
        }
        offset = $(e.currentTarget).offset();
        e.bokehX = e.pageX - offset.left;
        e.bokehY = e.pageY - offset.top;
        e.delta = delta;
        eventSink.trigger("" + toolName + ":zoom", e);
        e.preventDefault();
        return e.stopPropagation();
      });
      $(document).bind('keydown', function(e) {
        if (e.keyCode === 27) {
          return eventSink.trigger("clear_active_tool");
        }
      });
      this.mouseover_count = 0;
      this.plotview.$el.bind("mouseout", function(e) {
        _this.mouseover_count -= 1;
        return _.delay((function() {
          if (_this.mouseover_count === 0) {
            return eventSink.trigger("clear_active_tool");
          }
        }), 500);
      });
      this.plotview.$el.bind("mouseover", function(e) {
        return _this.mouseover_count += 1;
      });
      this.$tool_button = $("<button class='btn btn-small'> " + this.options.buttonText + " </button>");
      this.plotview.$el.find('.button_bar').append(this.$tool_button);
      this.$tool_button.click(function() {
        if (_this.button_activated) {
          return eventSink.trigger("clear_active_tool");
        } else {
          eventSink.trigger("active_tool", toolName);
          return _this.button_activated = true;
        }
      });
      no_scroll = function(el) {
        el.setAttribute("old_overflow", el.style.overflow);
        el.style.overflow = "hidden";
        if (el === document.body) {

        } else {
          return no_scroll(el.parentNode);
        }
      };
      restore_scroll = function(el) {
        el.style.overflow = el.getAttribute("old_overflow");
        if (el === document.body) {

        } else {
          return restore_scroll(el.parentNode);
        }
      };
      eventSink.on("" + toolName + ":deactivated", function() {
        _this.tool_active = false;
        _this.button_activated = false;
        _this.$tool_button.removeClass('active');
        restore_scroll(_this.plotview.$el[0]);
        return document.body.style.overflow = _this.old_overflow;
      });
      eventSink.on("" + toolName + ":activated", function() {
        _this.tool_active = true;
        _this.$tool_button.addClass('active');
        return no_scroll(_this.plotview.$el[0]);
      });
      return eventSink;
    };

    return OnePointWheelEventGenerator;

  })();

  exports.TwoPointEventGenerator = TwoPointEventGenerator;

  exports.OnePointWheelEventGenerator = OnePointWheelEventGenerator;

}).call(this);
}, "tools/events": function(exports, require, module) {(function() {
  var OnePointWheelEventGenerator, TwoPointEventGenerator;

  TwoPointEventGenerator = (function() {

    function TwoPointEventGenerator(options) {
      this.options = options;
      this.toolName = this.options.eventBasename;
      this.dragging = false;
      this.basepoint_set = false;
      this.button_activated = false;
      this.tool_active = false;
    }

    TwoPointEventGenerator.prototype.bind_events = function(plotview, eventSink) {
      var toolName,
        _this = this;
      toolName = this.toolName;
      this.plotview = plotview;
      this.eventSink = eventSink;
      this.plotview.moveCallbacks.push(function(e, x, y) {
        var offset;
        if (!_this.dragging) {
          return;
        }
        if (!_this.tool_active) {
          return;
        }
        offset = $(e.currentTarget).offset();
        e.bokehX = e.pageX - offset.left;
        e.bokehY = e.pageY - offset.top;
        if (!_this.basepoint_set) {
          _this.dragging = true;
          _this.basepoint_set = true;
          return eventSink.trigger("" + toolName + ":SetBasepoint", e);
        } else {
          eventSink.trigger("" + toolName + ":UpdatingMouseMove", e);
          e.preventDefault();
          return e.stopPropagation();
        }
      });
      $(document).bind('keydown', function(e) {
        if (e[_this.options.keyName]) {
          _this._start_drag();
        }
        if (e.keyCode === 27) {
          return eventSink.trigger("clear_active_tool");
        }
      });
      $(document).bind('keyup', function(e) {
        if (!e[_this.options.keyName]) {
          return _this._stop_drag();
        }
      });
      this.plotview.main_can_wrapper.bind('mousedown', function(e) {
        if (_this.button_activated) {
          _this._start_drag();
          return false;
        }
      });
      this.plotview.main_can_wrapper.bind('mouseup', function(e) {
        if (_this.button_activated) {
          _this._stop_drag();
          return false;
        }
      });
      this.$tool_button = $("<button class='btn btn-small'> " + this.options.buttonText + " </button>");
      this.plotview.$el.find('.button_bar').append(this.$tool_button);
      this.$tool_button.click(function() {
        if (_this.button_activated) {
          return eventSink.trigger("clear_active_tool");
        } else {
          eventSink.trigger("active_tool", toolName);
          return _this.button_activated = true;
        }
      });
      eventSink.on("" + toolName + ":deactivated", function() {
        _this.tool_active = false;
        _this.button_activated = false;
        return _this.$tool_button.removeClass('active');
      });
      eventSink.on("" + toolName + ":activated", function() {
        _this.tool_active = true;
        return _this.$tool_button.addClass('active');
      });
      return eventSink;
    };

    TwoPointEventGenerator.prototype._start_drag = function() {
      this.eventSink.trigger("active_tool", this.toolName);
      if (!this.dragging) {
        this.dragging = true;
        if (!this.button_activated) {
          return this.$tool_button.addClass('active');
        }
      }
    };

    TwoPointEventGenerator.prototype._stop_drag = function() {
      this.basepoint_set = false;
      if (this.dragging) {
        this.dragging = false;
        if (!this.button_activated) {
          this.$tool_button.removeClass('active');
        }
        return this.eventSink.trigger("" + this.options.eventBasename + ":DragEnd");
      }
    };

    return TwoPointEventGenerator;

  })();

  OnePointWheelEventGenerator = (function() {

    function OnePointWheelEventGenerator(options) {
      this.options = options;
      this.toolName = this.options.eventBasename;
      this.dragging = false;
      this.basepoint_set = false;
      this.button_activated = false;
      this.tool_active = false;
    }

    OnePointWheelEventGenerator.prototype.bind_events = function(plotview, eventSink) {
      var no_scroll, restore_scroll, toolName,
        _this = this;
      toolName = this.toolName;
      this.plotview = plotview;
      this.eventSink = eventSink;
      this.plotview.main_can_wrapper.bind("mousewheel", function(e, delta, dX, dY) {
        var offset;
        if (!_this.tool_active) {
          return;
        }
        offset = $(e.currentTarget).offset();
        e.bokehX = e.pageX - offset.left;
        e.bokehY = e.pageY - offset.top;
        e.delta = delta;
        eventSink.trigger("" + toolName + ":zoom", e);
        e.preventDefault();
        return e.stopPropagation();
      });
      $(document).bind('keydown', function(e) {
        if (e.keyCode === 27) {
          return eventSink.trigger("clear_active_tool");
        }
      });
      this.mouseover_count = 0;
      this.plotview.$el.bind("mouseout", function(e) {
        _this.mouseover_count -= 1;
        return _.delay((function() {
          if (_this.mouseover_count === 0) {
            return eventSink.trigger("clear_active_tool");
          }
        }), 500);
      });
      this.plotview.$el.bind("mouseover", function(e) {
        return _this.mouseover_count += 1;
      });
      this.$tool_button = $("<button class='btn btn-small'> " + this.options.buttonText + " </button>");
      this.plotview.$el.find('.button_bar').append(this.$tool_button);
      this.$tool_button.click(function() {
        if (_this.button_activated) {
          return eventSink.trigger("clear_active_tool");
        } else {
          eventSink.trigger("active_tool", toolName);
          return _this.button_activated = true;
        }
      });
      no_scroll = function(el) {
        el.setAttribute("old_overflow", el.style.overflow);
        el.style.overflow = "hidden";
        if (el === document.body) {

        } else {
          return no_scroll(el.parentNode);
        }
      };
      restore_scroll = function(el) {
        el.style.overflow = el.getAttribute("old_overflow");
        if (el === document.body) {

        } else {
          return restore_scroll(el.parentNode);
        }
      };
      eventSink.on("" + toolName + ":deactivated", function() {
        _this.tool_active = false;
        _this.button_activated = false;
        _this.$tool_button.removeClass('active');
        restore_scroll(_this.plotview.$el[0]);
        return document.body.style.overflow = _this.old_overflow;
      });
      eventSink.on("" + toolName + ":activated", function() {
        _this.tool_active = true;
        _this.$tool_button.addClass('active');
        return no_scroll(_this.plotview.$el[0]);
      });
      return eventSink;
    };

    return OnePointWheelEventGenerator;

  })();

  exports.TwoPointEventGenerator = TwoPointEventGenerator;

  exports.OnePointWheelEventGenerator = OnePointWheelEventGenerator;

}).call(this);
}, "tools/toolview": function(exports, require, module) {(function() {
  var PlotWidget, ToolView, base,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("../base");

  PlotWidget = base.PlotWidget;

  ToolView = (function(_super) {

    __extends(ToolView, _super);

    function ToolView() {
      return ToolView.__super__.constructor.apply(this, arguments);
    }

    ToolView.prototype.initialize = function(options) {
      return ToolView.__super__.initialize.call(this, options);
    };

    ToolView.prototype.bind_events = function(plotview) {
      var eventSink, evgen, evgen_options, evgen_options2,
        _this = this;
      eventSink = plotview.eventSink;
      this.plotview = plotview;
      evgen_options = {
        eventBasename: this.cid
      };
      evgen_options2 = _.extend(evgen_options, this.evgen_options);
      evgen = new this.eventGeneratorClass(evgen_options2);
      evgen.bind_events(plotview, eventSink);
      return _.each(this.tool_events, function(handler_f, event_name) {
        var full_event_name, wrap;
        full_event_name = "" + _this.cid + ":" + event_name;
        wrap = function(e) {
          return _this[handler_f](e);
        };
        return eventSink.on(full_event_name, wrap);
      });
    };

    return ToolView;

  })(PlotWidget);

  exports.ToolView = ToolView;

}).call(this);
}, "tools/selecttool": function(exports, require, module) {(function() {
  var HasParent, LinearMapper, SelectionTool, SelectionToolView, SelectionTools, ToolView, TwoPointEventGenerator, base, eventgenerators, mapper, safebind, toolview,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  toolview = require("./toolview");

  ToolView = toolview.ToolView;

  eventgenerators = require("./eventgenerators");

  TwoPointEventGenerator = eventgenerators.TwoPointEventGenerator;

  mapper = require("../mapper");

  LinearMapper = mapper.LinearMapper;

  base = require("../base");

  safebind = base.safebind;

  HasParent = base.HasParent;

  SelectionToolView = (function(_super) {

    __extends(SelectionToolView, _super);

    function SelectionToolView() {
      return SelectionToolView.__super__.constructor.apply(this, arguments);
    }

    SelectionToolView.prototype.initialize = function(options) {
      var renderer, select_callback, _i, _len, _ref, _results,
        _this = this;
      SelectionToolView.__super__.initialize.call(this, options);
      select_callback = _.debounce((function() {
        return _this._select_data();
      }), 50);
      safebind(this, this.model, 'change', this.request_render);
      safebind(this, this.model, 'change', select_callback);
      _ref = this.mget_obj('renderers');
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        renderer = _ref[_i];
        safebind(this, renderer, 'change', this.request_render);
        safebind(this, renderer.get_obj('xdata_range'), 'change', this.request_render);
        safebind(this, renderer.get_obj('ydata_range'), 'change', this.request_render);
        safebind(this, renderer.get_obj('data_source'), 'change', this.request_render);
        safebind(this, renderer, 'change', select_callback);
        safebind(this, renderer.get_obj('xdata_range'), 'change', select_callback);
        _results.push(safebind(this, renderer.get_obj('ydata_range'), 'change', select_callback));
      }
      return _results;
    };

    SelectionToolView.prototype.eventGeneratorClass = TwoPointEventGenerator;

    SelectionToolView.prototype.evgen_options = {
      keyName: "ctrlKey",
      buttonText: "Select"
    };

    SelectionToolView.prototype.tool_events = {
      UpdatingMouseMove: "_selecting",
      SetBasepoint: "_start_selecting",
      deactivated: "_stop_selecting"
    };

    SelectionToolView.prototype.mouse_coords = function(e, x, y) {
      var _ref;
      _ref = [this.plot_view.viewstate.rxpos(x), this.plot_view.viewstate.rypos(y)], x = _ref[0], y = _ref[1];
      return [x, y];
    };

    SelectionToolView.prototype._stop_selecting = function() {
      this.trigger('stopselect');
      return this.basepoint_set = false;
    };

    SelectionToolView.prototype._start_selecting = function(e) {
      var x, y, _ref;
      this.trigger('startselect');
      _ref = this.mouse_coords(e, e.bokehX, e.bokehY), x = _ref[0], y = _ref[1];
      this.mset({
        'start_x': x,
        'start_y': y,
        'current_x': null,
        'current_y': null
      });
      return this.basepoint_set = true;
    };

    SelectionToolView.prototype._get_selection_range = function() {
      var xrange, yrange;
      xrange = [this.mget('start_x'), this.mget('current_x')];
      yrange = [this.mget('start_y'), this.mget('current_y')];
      if (this.mget('select_x')) {
        xrange = [d3.min(xrange), d3.max(xrange)];
      } else {
        xrange = null;
      }
      if (this.mget('select_y')) {
        yrange = [d3.min(yrange), d3.max(yrange)];
      } else {
        yrange = null;
      }
      return [xrange, yrange];
    };

    SelectionToolView.prototype._selecting = function(e, x_, y_) {
      var x, y, _ref, _ref1;
      _ref = this.mouse_coords(e, e.bokehX, e.bokehY), x = _ref[0], y = _ref[1];
      this.mset({
        'current_x': x,
        'current_y': y
      });
      _ref1 = this._get_selection_range(), this.xrange = _ref1[0], this.yrange = _ref1[1];
      this.trigger('boxselect', this.xrange, this.yrange);
      return null;
    };

    SelectionToolView.prototype._select_data = function() {
      var datasource, datasource_id, datasource_selections, datasources, k, renderer, selected, v, _i, _j, _len, _len1, _ref, _ref1;
      if (!this.basepoint_set) {
        return;
      }
      datasources = {};
      datasource_selections = {};
      _ref = this.mget_obj('renderers');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        renderer = _ref[_i];
        datasource = renderer.get_obj('data_source');
        datasources[datasource.id] = datasource;
      }
      _ref1 = this.mget_obj('renderers');
      for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
        renderer = _ref1[_j];
        datasource_id = renderer.get_obj('data_source').id;
        _.setdefault(datasource_selections, datasource_id, []);
        selected = this.plot_view.renderers[renderer.id].select(this.xrange, this.yrange);
        datasource_selections[datasource_id].push(selected);
      }
      for (k in datasource_selections) {
        if (!__hasProp.call(datasource_selections, k)) continue;
        v = datasource_selections[k];
        selected = _.intersection.apply(_, v);
        datasources[k].set('selected', selected);
        datasources[k].save();
      }
      return null;
    };

    return SelectionToolView;

  })(ToolView);

  SelectionTool = (function(_super) {

    __extends(SelectionTool, _super);

    function SelectionTool() {
      return SelectionTool.__super__.constructor.apply(this, arguments);
    }

    SelectionTool.prototype.type = "SelectionTool";

    SelectionTool.prototype.default_view = SelectionToolView;

    return SelectionTool;

  })(HasParent);

  SelectionTool.prototype.defaults = _.clone(SelectionTool.prototype.defaults);

  _.extend(SelectionTool.prototype.defaults, {
    renderers: [],
    select_x: true,
    select_y: true,
    data_source_options: {}
  });

  SelectionTools = (function(_super) {

    __extends(SelectionTools, _super);

    function SelectionTools() {
      return SelectionTools.__super__.constructor.apply(this, arguments);
    }

    SelectionTools.prototype.model = SelectionTool;

    return SelectionTools;

  })(Backbone.Collection);

  exports.SelectionToolView = SelectionToolView;

  exports.selectiontools = new SelectionTools;

}).call(this);
}, "tools/activetoolmanager": function(exports, require, module) {(function() {
  var ActiveToolManager;

  ActiveToolManager = (function() {
    " This makes sure that only one tool is active at a time ";

    function ActiveToolManager(eventSink) {
      this.eventSink = eventSink;
      this.eventSink.active = true;
      this.bind_events();
    }

    ActiveToolManager.prototype.bind_events = function() {
      var _this = this;
      this.eventSink.on("clear_active_tool", function() {
        _this.eventSink.trigger("" + _this.eventSink.active + ":deactivated");
        return _this.eventSink.active = true;
      });
      return this.eventSink.on("active_tool", function(toolName) {
        if (toolName !== _this.eventSink.active) {
          _this.eventSink.trigger("" + toolName + ":activated");
          _this.eventSink.trigger("" + _this.eventSink.active + ":deactivated");
          return _this.eventSink.active = toolName;
        }
      });
    };

    return ActiveToolManager;

  })();

  exports.ActiveToolManager = ActiveToolManager;

}).call(this);
}, "tools/pantool": function(exports, require, module) {(function() {
  var HasParent, LinearMapper, PanTool, PanToolView, PanTools, ToolView, TwoPointEventGenerator, base, eventgenerators, mapper, safebind, toolview,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  toolview = require("./toolview");

  ToolView = toolview.ToolView;

  eventgenerators = require("./eventgenerators");

  TwoPointEventGenerator = eventgenerators.TwoPointEventGenerator;

  mapper = require("../mapper");

  LinearMapper = mapper.LinearMapper;

  base = require("../base");

  safebind = base.safebind;

  HasParent = base.HasParent;

  PanToolView = (function(_super) {

    __extends(PanToolView, _super);

    function PanToolView() {
      this.build_mappers = __bind(this.build_mappers, this);
      return PanToolView.__super__.constructor.apply(this, arguments);
    }

    PanToolView.prototype.initialize = function(options) {
      PanToolView.__super__.initialize.call(this, options);
      return this.build_mappers();
    };

    PanToolView.prototype.bind_bokeh_events = function() {
      return safebind(this, this.model, 'change:dataranges', this.build_mappers);
    };

    PanToolView.prototype.build_mappers = function() {
      var datarange, dim, temp, _i, _len, _ref;
      this.mappers = [];
      _ref = _.zip(this.mget_obj('dataranges'), this.mget('dimensions'));
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        temp = _ref[_i];
        datarange = temp[0], dim = temp[1];
        mapper = new LinearMapper({}, {
          data_range: datarange,
          viewstate: this.plot_view.viewstate,
          screendim: dim
        });
        this.mappers.push(mapper);
      }
      return this.mappers;
    };

    PanToolView.prototype.eventGeneratorClass = TwoPointEventGenerator;

    PanToolView.prototype.evgen_options = {
      keyName: "shiftKey",
      buttonText: "Pan"
    };

    PanToolView.prototype.tool_events = {
      UpdatingMouseMove: "_drag",
      SetBasepoint: "_set_base_point"
    };

    PanToolView.prototype.mouse_coords = function(e, x, y) {
      var x_, y_, _ref;
      _ref = [this.plot_view.viewstate.rxpos(x), this.plot_view.viewstate.rypos(y)], x_ = _ref[0], y_ = _ref[1];
      return [x_, y_];
    };

    PanToolView.prototype._set_base_point = function(e) {
      var _ref;
      _ref = this.mouse_coords(e, e.bokehX, e.bokehY), this.x = _ref[0], this.y = _ref[1];
      return null;
    };

    PanToolView.prototype._drag = function(e) {
      var diff, end, screenhigh, screenlow, start, x, xdiff, y, ydiff, _i, _len, _ref, _ref1, _ref2, _ref3;
      _ref = this.mouse_coords(e, e.bokehX, e.bokehY), x = _ref[0], y = _ref[1];
      xdiff = x - this.x;
      ydiff = y - this.y;
      _ref1 = [x, y], this.x = _ref1[0], this.y = _ref1[1];
      _ref2 = this.mappers;
      for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
        mapper = _ref2[_i];
        if (mapper.screendim === 'width') {
          diff = xdiff;
        } else {
          diff = ydiff;
        }
        screenlow = 0 - diff;
        screenhigh = this.plot_view.viewstate.get(mapper.screendim) - diff;
        _ref3 = [mapper.map_data(screenlow), mapper.map_data(screenhigh)], start = _ref3[0], end = _ref3[1];
        mapper.data_range.set({
          start: start,
          end: end
        });
      }
      return null;
    };

    return PanToolView;

  })(ToolView);

  PanTool = (function(_super) {

    __extends(PanTool, _super);

    function PanTool() {
      return PanTool.__super__.constructor.apply(this, arguments);
    }

    PanTool.prototype.type = "PanTool";

    PanTool.prototype.default_view = PanToolView;

    return PanTool;

  })(HasParent);

  PanTool.prototype.defaults = _.clone(PanTool.prototype.defaults);

  _.extend(PanTool.prototype.defaults, {
    dimensions: [],
    dataranges: []
  });

  PanTools = (function(_super) {

    __extends(PanTools, _super);

    function PanTools() {
      return PanTools.__super__.constructor.apply(this, arguments);
    }

    PanTools.prototype.model = PanTool;

    return PanTools;

  })(Backbone.Collection);

  exports.PanToolView = PanToolView;

  exports.pantools = new PanTools;

}).call(this);
}, "tools/zoomtool": function(exports, require, module) {(function() {
  var HasParent, LinearMapper, OnePointWheelEventGenerator, ToolView, ZoomTool, ZoomToolView, ZoomTools, base, eventgenerators, mapper, safebind, toolview,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  toolview = require("./toolview");

  ToolView = toolview.ToolView;

  eventgenerators = require("./eventgenerators");

  OnePointWheelEventGenerator = eventgenerators.OnePointWheelEventGenerator;

  mapper = require("../mapper");

  LinearMapper = mapper.LinearMapper;

  base = require("../base");

  safebind = base.safebind;

  HasParent = base.HasParent;

  ZoomToolView = (function(_super) {

    __extends(ZoomToolView, _super);

    function ZoomToolView() {
      this.build_mappers = __bind(this.build_mappers, this);
      return ZoomToolView.__super__.constructor.apply(this, arguments);
    }

    ZoomToolView.prototype.initialize = function(options) {
      ZoomToolView.__super__.initialize.call(this, options);
      safebind(this, this.model, 'change:dataranges', this.build_mappers);
      return this.build_mappers();
    };

    ZoomToolView.prototype.eventGeneratorClass = OnePointWheelEventGenerator;

    ZoomToolView.prototype.evgen_options = {
      buttonText: "Zoom"
    };

    ZoomToolView.prototype.tool_events = {
      zoom: "_zoom"
    };

    ZoomToolView.prototype.build_mappers = function() {
      var datarange, dim, temp, _i, _len, _ref;
      this.mappers = [];
      _ref = _.zip(this.mget_obj('dataranges'), this.mget('dimensions'));
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        temp = _ref[_i];
        datarange = temp[0], dim = temp[1];
        mapper = new LinearMapper({}, {
          data_range: datarange,
          viewstate: this.plot_view.viewstate,
          screendim: dim
        });
        this.mappers.push(mapper);
      }
      return this.mappers;
    };

    ZoomToolView.prototype.mouse_coords = function(e, x, y) {
      var x_, y_, _ref;
      _ref = [this.plot_view.viewstate.rxpos(x), this.plot_view.viewstate.rypos(y)], x_ = _ref[0], y_ = _ref[1];
      return [x_, y_];
    };

    ZoomToolView.prototype._zoom = function(e) {
      var delta, end, eventpos, factor, screenX, screenY, screenhigh, screenlow, speed, start, x, y, _i, _len, _ref, _ref1, _ref2;
      delta = e.delta;
      screenX = e.bokehX;
      screenY = e.bokehY;
      _ref = this.mouse_coords(e, screenX, screenY), x = _ref[0], y = _ref[1];
      speed = this.mget('speed');
      factor = -speed * (delta * 50);
      _ref1 = this.mappers;
      for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
        mapper = _ref1[_i];
        if (mapper.screendim === 'width') {
          eventpos = x;
        } else {
          eventpos = y;
        }
        screenlow = 0;
        screenhigh = this.plot_view.viewstate.get(mapper.screendim);
        start = screenlow - (eventpos - screenlow) * factor;
        end = screenhigh + (screenhigh - eventpos) * factor;
        _ref2 = [mapper.map_data(start), mapper.map_data(end)], start = _ref2[0], end = _ref2[1];
        mapper.data_range.set({
          start: start,
          end: end
        });
      }
      return null;
    };

    return ZoomToolView;

  })(ToolView);

  ZoomTool = (function(_super) {

    __extends(ZoomTool, _super);

    function ZoomTool() {
      return ZoomTool.__super__.constructor.apply(this, arguments);
    }

    ZoomTool.prototype.type = "ZoomTool";

    ZoomTool.prototype.default_view = ZoomToolView;

    return ZoomTool;

  })(HasParent);

  ZoomTool.prototype.defaults = _.clone(ZoomTool.prototype.defaults);

  _.extend(ZoomTool.prototype.defaults, {
    dimensions: [],
    dataranges: [],
    speed: 1 / 600
  });

  ZoomTools = (function(_super) {

    __extends(ZoomTools, _super);

    function ZoomTools() {
      return ZoomTools.__super__.constructor.apply(this, arguments);
    }

    ZoomTools.prototype.model = ZoomTool;

    return ZoomTools;

  })(Backbone.Collection);

  exports.ZoomToolView = ZoomToolView;

  exports.zoomtools = new ZoomTools;

}).call(this);
}, "unittest/hasproperty_test": function(exports, require, module) {(function() {
  var Collections, ContinuumView, HasProperties, TestObject, TestObjects, base, safebind, testobjects,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("../base");

  ContinuumView = base.ContinuumView;

  safebind = base.safebind;

  Collections = base.Collections;

  HasProperties = base.HasParent;

  TestObject = (function(_super) {

    __extends(TestObject, _super);

    function TestObject() {
      return TestObject.__super__.constructor.apply(this, arguments);
    }

    TestObject.prototype.type = 'TestObject';

    return TestObject;

  })(HasProperties);

  TestObjects = (function(_super) {

    __extends(TestObjects, _super);

    function TestObjects() {
      return TestObjects.__super__.constructor.apply(this, arguments);
    }

    TestObjects.prototype.model = TestObject;

    TestObjects.prototype.url = "/";

    return TestObjects;

  })(Backbone.Collection);

  testobjects = new TestObjects();

  exports.testobjects = testobjects;

  base.locations['TestObject'] = ['./unittest/hasproperty_test', 'testobjects'];

  test('computed_properties', function() {
    var model, temp;
    testobjects.reset();
    model = Collections('TestObject').create({
      'a': 1,
      'b': 1
    });
    model.register_property('c', function() {
      return this.get('a') + this.get('b');
    });
    model.add_dependencies('c', model, ['a', 'b']);
    temp = model.get('c');
    return ok(temp === 2);
  });

  test('cached_properties_react_changes', function() {
    var model, temp;
    testobjects.reset();
    model = testobjects.create({
      'a': 1,
      'b': 1
    });
    model.register_property('c', function() {
      return this.get('a') + this.get('b');
    }, true);
    model.add_dependencies('c', model, ['a', 'b']);
    temp = model.get('c');
    ok(temp === 2);
    temp = model.get_cache('c');
    ok(!_.isUndefined(temp));
    model.set('a', 10);
    temp = model.get_cache('c');
    temp = model.get('c');
    return ok(temp === 11);
  });

  test('has_prop_manages_event_lifcycle', function() {
    var model, model2, triggered;
    testobjects.reset();
    model = testobjects.create({
      'a': 1,
      'b': 1
    });
    model2 = testobjects.create({
      'a': 1,
      'b': 1
    });
    triggered = false;
    safebind(model, model2, 'change', function() {
      return triggered = true;
    });
    model2.set({
      'a': 2
    });
    ok(triggered);
    triggered = false;
    model.destroy();
    model2.set({
      'a': 3
    });
    return ok(!triggered);
  });

  test('has_prop_manages_event_for_views', function() {
    var model, model2, triggered, view;
    testobjects.reset();
    model = testobjects.create({
      'a': 1,
      'b': 1
    });
    model2 = testobjects.create({
      'a': 1,
      'b': 1
    });
    view = new ContinuumView({
      'model': model2
    });
    triggered = false;
    safebind(view, model, 'change', function() {
      return triggered = true;
    });
    model.set({
      'a': 2
    });
    ok(triggered);
    triggered = false;
    view.remove();
    model.set({
      'a': 3
    });
    return ok(!triggered);
  });

  test('property_setters', function() {
    var model, prop, setter;
    testobjects.reset();
    model = testobjects.create({
      'a': 1,
      'b': 1
    });
    prop = function() {
      return this.get('a') + this.get('b');
    };
    setter = function(val) {
      this.set('a', val / 2, {
        silent: true
      });
      return this.set('b', val / 2);
    };
    model.register_property('c', prop, true);
    model.add_dependencies('c', model, ['a', 'b']);
    model.register_setter('c', setter);
    model.set('c', 100);
    ok(model.get('a') === 50);
    return ok(model.get('b') === 50);
  });

  test('test_vectorized_ref', function() {
    var model1, model2, model3, output;
    testobjects.reset();
    model1 = testobjects.create({
      a: 1,
      b: 1
    });
    model2 = testobjects.create({
      a: 2,
      b: 2
    });
    model3 = testobjects.create({
      a: 1,
      b: 1,
      vectordata: [model1.ref(), model2.ref()]
    });
    output = model3.get_obj('vectordata');
    ok(output[0] === model1);
    ok(output[1] === model2);
    model3.set_obj('vectordata2', [model1, model1, model2]);
    output = model3.get('vectordata2');
    ok(output[0].id === model1.ref().id);
    ok(output[1].id === model1.ref().id);
    ok(output[2].id === model2.ref().id);
    ok(!(output[0] instanceof HasProperties));
    return null;
  });

}).call(this);
}, "unittest/plot_test_simple": function(exports, require, module) {(function() {
  var Collections, base, testutils;

  base = require("../base");

  testutils = require("../testutils");

  Collections = base.Collections;

  test('test_simple_plot', function() {
    var data_source, div, myrender, plotmodel;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plotmodel = testutils.scatter_plot(null, data_source, 'x', 'y', null, 'circle');
    window.plot = plotmodel;
    div = $('<div/>');
    $('body').append(div);
    myrender = function() {
      var view;
      view = new plotmodel.default_view({
        'model': plotmodel,
        'render_loop': true
      });
      div.append(view.$el);
      return view.render();
    };
    console.log('test_simple_plot');
    return _.defer(myrender);
  });

  test('test_line_plot', function() {
    var data_source, div, myrender, plotmodel;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plotmodel = testutils.line_plot(null, data_source, 'x', 'y', null, 'circle');
    window.plot = plotmodel;
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    myrender = function() {
      var view;
      view = new plotmodel.default_view({
        'model': plotmodel,
        'render_loop': true
      });
      div.append(view.$el);
      return view.render();
    };
    console.log('test_simple_plot');
    return _.defer(myrender);
  });

  test('test_updating_plot', function() {
    var data_source, div, myrender, plotmodel;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plotmodel = testutils.scatter_plot(null, data_source, 'x', 'y', null, 'circle');
    plotmodel.set({
      'render_loop': true
    });
    window.plot = plotmodel;
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    myrender = function() {
      var view;
      view = new plotmodel.default_view({
        'model': plotmodel,
        'render_loop': true
      });
      div.append(view.$el);
      window.view = view;
      view.render();
      return view.viewstate.set({
        'width': 300,
        'height': 300
      });
    };
    return _.defer(myrender);
  });

  test('test_colors_plot', function() {
    var data_source, div, myrender, plotmodel;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plotmodel = testutils.scatter_plot(null, data_source, 'x', 'y', 'x', 'circle');
    plotmodel.set({
      'render_loop': true
    });
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    myrender = function() {
      var view;
      view = new plotmodel.default_view({
        'model': plotmodel
      });
      div.append(view.$el);
      view.render();
      return view.viewstate.set({
        'width': 300,
        'height': 300
      });
    };
    console.log("test_colors_plot");
    return _.defer(myrender);
  });

  test('rectangular_plot_test', function() {
    var data_source, div, plot1, view;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    $('body').append($('<br/>'));
    plot1 = testutils.scatter_plot(null, data_source, 'x', 'y', 'x', 'circle');
    plot1.set('width', 500);
    window.plot = container;
    window.plot1 = plot1;
    view = new plot1.default_view({
      model: plot1
    });
    window.view = view;
    return _.defer(function() {
      div.append(view.$el);
      return view.render();
    });
  });

}).call(this);
}, "unittest/plot_test_grid": function(exports, require, module) {(function() {
  var Collections, base, line_plot, scatter_plot, testutils;

  base = require("../base");

  Collections = base.Collections;

  testutils = require("../testutils");

  scatter_plot = testutils.scatter_plot;

  line_plot = testutils.line_plot;

  test('simple_grid_test', function() {
    var container, data_source, div, plot1, plot2, view;
    expect(0);
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    container = Collections('GridPlotContainer').create({
      'render_loop': true
    }, {
      'local': true
    });
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    $('body').append($('<br/>'));
    plot1 = scatter_plot(container, data_source, 'x', 'y', 'x', 'circle');
    plot2 = scatter_plot(container, data_source, 'x', 'y', 'x', 'circle');
    window.plot = container;
    window.plot1 = plot1;
    window.plot2 = plot2;
    container.set({
      'children': [[plot1.ref(), plot2.ref()]]
    });
    view = new container.default_view({
      'model': container,
      'render_loop': true
    });
    window.view = view;
    return _.defer(function() {
      div.append(view.$el);
      return view.render();
    });
  });

  test('line_plot_grid_test', function() {
    var container, data_source1, data_source2, div, plot1, plot2, plot3, plot4;
    expect(0);
    data_source1 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    data_source2 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: 2
        }, {
          x: 2,
          y: 3
        }, {
          x: 3,
          y: 1
        }, {
          x: 4,
          y: 5
        }, {
          x: 5,
          y: 6
        }
      ]
    }, {
      'local': true
    });
    container = Collections('GridPlotContainer').create({
      'render_loop': true
    }, {
      'local': true
    });
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    $('body').append($('<br/>'));
    plot1 = scatter_plot(container, data_source1, 'x', 'y', 'x', 'circle');
    plot2 = scatter_plot(container, data_source2, 'x', 'y', 'x', 'circle');
    plot3 = scatter_plot(container, data_source2, 'x', 'y', 'x', 'circle');
    plot4 = line_plot(container, data_source1, 'x', 'y');
    window.plot3 = plot3;
    container.set({
      'children': [[plot1.ref(), plot2.ref()], [plot3.ref(), plot4.ref()]]
    });
    return _.defer(function() {
      var plotstate, view, view2;
      view = new container.default_view({
        model: container
      });
      div.append(view.$el);
      view.render();
      view2 = new container.default_view({
        model: container
      });
      div.append(view2.$el);
      view2.render();
      window.view = view;
      window.view2 = view2;
      plotstate = view2.childviews[plot3.id].viewstate;
      plotstate.set('height', 300);
      window.plotstate = plotstate;
      return null;
    });
  });

}).call(this);
}, "unittest/bokeh_test": function(exports, require, module) {(function() {
  var Collections, LinearMapper, ViewState, base, container, mapper, scatter_plot, testutils;

  base = require("../base");

  Collections = base.Collections;

  container = require("../container");

  ViewState = container.ViewState;

  mapper = require("../mapper");

  LinearMapper = mapper.LinearMapper;

  testutils = require("../testutils");

  scatter_plot = testutils.scatter_plot;

  asyncTest('test_datarange1d', function() {
    var data_source, datarange;
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    });
    datarange = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': ['x', 'y']
        }
      ],
      'rangepadding': 0.0
    });
    return _.defer(function() {
      ok(datarange.get('start') === -6);
      ok(datarange.get('end') === 5);
      data_source.set('data', [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -100
        }
      ]);
      ok(datarange.get('start') === -100);
      ok(datarange.get('end') === 5);
      return start();
    });
  });

  asyncTest('test_datarange1d_multiple_sources', function() {
    var data_source, data_source2, datarange;
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    });
    data_source2 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          xx: 10,
          yy: -20
        }, {
          xx: 20,
          yy: -30
        }, {
          xx: 30,
          yy: -40
        }, {
          xx: 40,
          yy: -50
        }, {
          xx: 50,
          yy: -60
        }
      ]
    });
    datarange = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': ['x', 'y']
        }, {
          'ref': data_source2.ref(),
          'columns': ['yy']
        }
      ],
      'rangepadding': 0.0
    });
    return _.defer(function() {
      ok(datarange.get('start') === -60);
      ok(datarange.get('end') === 5);
      data_source.set('data', [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: -100,
          y: 0
        }
      ]);
      data_source2.set('data', [
        {
          x: 1,
          yy: 1000
        }
      ]);
      ok(datarange.get('start') === -100);
      ok(datarange.get('end') === 1000);
      return start();
    });
  });

  asyncTest('test_datarange1d_can_be_overriden', function() {
    var data_source, data_source2, datarange;
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    });
    data_source2 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          xx: 10,
          yy: -20
        }, {
          xx: 20,
          yy: -30
        }, {
          xx: 30,
          yy: -40
        }, {
          xx: 40,
          yy: -50
        }, {
          xx: 50,
          yy: -60
        }
      ]
    });
    datarange = Collections('DataRange1d').create({
      'sources': [
        {
          'ref': data_source.ref(),
          'columns': ['x', 'y']
        }, {
          'ref': data_source2.ref(),
          'columns': ['yy']
        }
      ],
      'rangepadding': 0.0
    });
    return _.defer(function() {
      ok(datarange.get('start') === -60);
      ok(datarange.get('end') === 5);
      datarange.set({
        'start': 1,
        'end': 10
      });
      ok(datarange.get('start') === 1);
      ok(datarange.get('end') === 10);
      return start();
    });
  });

  test('test_linear_mapper', function() {
    var range1, viewstate;
    range1 = Collections('Range1d').create({
      'start': 0,
      'end': 1
    });
    viewstate = new ViewState({
      'height': 2
    });
    mapper = new LinearMapper({}, {
      data_range: range1,
      viewstate: viewstate,
      screendim: 'height'
    });
    ok(mapper.map_screen(0.5) === 1);
    ok(mapper.map_screen(0) === 0);
    ok(mapper.map_screen(1) === 2);
    ok(mapper.map_data(1) === 0.5);
    ok(mapper.map_data(0) === 0);
    return ok(mapper.map_data(2) === 1);
  });

  test('renderer_selection', function() {
    var data_source, plot, scatterrenderer, scatterrendererview, select, selected, view;
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plot = scatter_plot(null, data_source, 'x', 'y', null, 'circle');
    scatterrenderer = plot.resolve_ref(plot.get('renderers')[0]);
    view = new plot.default_view({
      model: plot
    });
    plot.dinitialize();
    scatterrenderer.dinitialize();
    scatterrenderer.get_obj('xdata_range').dinitialize();
    scatterrenderer.get_obj('ydata_range').dinitialize();
    view.render_deferred_components(true);
    scatterrendererview = view.renderers[scatterrenderer.id];
    selected = scatterrendererview.select([0, 200], null);
    deepEqual(selected, _.range(5));
    selected = scatterrendererview.select(null, [0, 200]);
    deepEqual(selected, _.range(5));
    select = scatterrendererview.select([0, 120], null);
    deepEqual(select, _.range(3));
    select = scatterrendererview.select([0, 120], [80, 200]);
    return deepEqual(select, _.range(3));
  });

}).call(this);
}, "unittest/raw_canvas_test": function(exports, require, module) {(function() {
  var canvas_t, data_set, kinetic_t, kinetic_t2, make_range, side_length;

  side_length = 200;

  make_range = function(num_points) {
    var data, pt, step;
    step = side_length / num_points;
    data = (function() {
      var _i, _len, _ref, _results;
      _ref = _.range(0, side_length, step);
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        pt = _ref[_i];
        _results.push({
          'x': pt,
          'y': pt
        });
      }
      return _results;
    })();
    return data;
  };

  data_set = make_range(100000);

  canvas_t = function() {
    var can1, ctx, ed, point, pt, st, _i, _len;
    expect(0);
    can1 = $('canvas#can1')[0];
    $(can1).attr('height', side_length.toString());
    $(can1).attr('width', side_length.toString());
    ctx = can1.getContext('2d');
    st = new Date();
    point = function(pt) {
      return ctx.fillRect(pt.x, pt.y, 5, 5);
    };
    for (_i = 0, _len = data_set.length; _i < _len; _i++) {
      pt = data_set[_i];
      point(pt);
    }
    ctx.stroke();
    ed = new Date();
    return console.log('canvas', ed - st);
  };

  kinetic_t = function() {
    var layer, pt, stage, _i, _len;
    expect(0);
    stage = new Kinetic.Stage({
      container: $('#container')[0],
      width: 200,
      height: 200
    });
    layer = new Kinetic.Layer();
    for (_i = 0, _len = data_set.length; _i < _len; _i++) {
      pt = data_set[_i];
      layer.add(new Kinetic.RegularPolygon({
        fill: 'red',
        sides: 4,
        x: pt.x,
        y: pt.y,
        radius: 5,
        strokeWidth: 3
      }));
    }
    return stage.add(layer);
  };

  kinetic_t2 = function() {
    var layer, pt, pts, stage, _i, _len;
    expect(0);
    stage = new Kinetic.Stage({
      container: $('#container2')[0],
      width: 200,
      height: 200
    });
    layer = new Kinetic.Layer();
    pts = [];
    for (_i = 0, _len = data_set.length; _i < _len; _i++) {
      pt = data_set[_i];
      pt = new Kinetic.RegularPolygon({
        fill: 'red',
        sides: 4,
        x: pt.x,
        y: pt.y,
        radius: 5,
        strokeWidth: 3
      });
      pts.push(pt);
      layer.add(pt);
    }
    window.pts = pts;
    stage.add(layer);
    window.doMove = function() {
      var ed, pos, st, st2, _j, _len1;
      st = new Date();
      for (_j = 0, _len1 = pts.length; _j < _len1; _j++) {
        pt = pts[_j];
        pos = pt.getPosition();
        pt.setPosition(pos.x + 30, pos.y);
      }
      "";

      st2 = new Date();
      ed = new Date();
      return console.log('total', ed - st, 'adding', st2 - st, 'drawing', ed - st2);
    };
    return $(document).keypress(function() {
      var ed, st;
      st = new Date();
      doMove();
      return ed = new Date();
    });
  };

  window.canvas_t = canvas_t;

  window.kinetic_t = kinetic_t;

  test('test_raw_canvas', canvas_t);

  test('test_raw_kinetic', kinetic_t);

  test('test_raw_kinetic2', kinetic_t2);

}).call(this);
}, "unittest/tools_test": function(exports, require, module) {(function() {
  var Collections, MAX_SIZE, base, setup_interactive, testutils;

  base = require("../base");

  testutils = require("../testutils");

  Collections = base.Collections;

  MAX_SIZE = 500;

  setup_interactive = function() {
    var boxoverlay, data, data_source1, pantool, plot1, pt, scatterrenderer, selecttool, zoomtool;
    data = (function() {
      var _i, _len, _ref, _results;
      _ref = _.range(MAX_SIZE);
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        pt = _ref[_i];
        _results.push({
          'x': pt,
          'y': pt
        });
      }
      return _results;
    })();
    data_source1 = Collections('ObjectArrayDataSource').create({
      data: data
    }, {
      'local': true
    });
    plot1 = testutils.scatter_plot(null, data_source1, 'x', 'y', 'x', 'circle');
    plot1.set('offset', [100, 100]);
    scatterrenderer = plot1.resolve_ref(plot1.get('renderers')[0]);
    pantool = Collections('PanTool').create({
      dataranges: [scatterrenderer.get('xdata_range'), scatterrenderer.get('ydata_range')],
      dimensions: ['width', 'height']
    });
    zoomtool = Collections('ZoomTool').create({
      dataranges: [scatterrenderer.get('xdata_range'), scatterrenderer.get('ydata_range')],
      dimensions: ['width', 'height']
    });
    selecttool = Collections('SelectionTool').create({
      'renderers': [scatterrenderer.ref()]
    });
    boxoverlay = Collections('BoxSelectionOverlay').create({
      'tool': selecttool.ref()
    });
    plot1.set('tools', [pantool.ref(), zoomtool.ref(), selecttool.ref()]);
    plot1.set('overlays', [boxoverlay.ref()]);
    window.plot1 = plot1;
    return plot1;
  };

  test('test_interactive', function() {
    var div, plot1;
    expect(0);
    plot1 = setup_interactive();
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    window.myrender = function() {
      var view;
      view = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      div.append(view.$el);
      view.render();
      return window.view = view;
    };
    return _.defer(window.myrender);
  });

  test('test_pan_tool', function() {
    var div, plot1;
    expect(0);
    " when this test runs you should see only one line, not an\nartifact from an earlier line ";

    plot1 = setup_interactive();
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    window.myrender = function() {
      var view;
      view = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      div.append(view.$el);
      view.render();
      window.view = view;
      window.pantool = plot1.resolve_ref(plot1.get('tools')[0]);
      return _.defer(function() {
        var ptv;
        ptv = _.filter(view.tools, (function(v) {
          return v.model === window.pantool;
        }))[0];
        ptv.dragging = true;
        ptv._set_base_point({
          'bokehX': 0,
          'bokehY': 0
        });
        ptv._drag({
          'bokehX': 30,
          'bokehY': 30
        });
        return window.ptv = ptv;
      });
    };
    return _.defer(window.myrender);
  });

  test('test_two_views', function() {
    var div, plot1;
    expect(0);
    plot1 = setup_interactive();
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    window.myrender = function() {
      var view, view2;
      view = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      view2 = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      div.append(view.$el);
      div.append(view2.$el);
      view.render();
      view2.render();
      window.view = view;
      window.view2 = view2;
      view.viewstate.set('height', 300);
      view.viewstate.set('width', 300);
      view2.viewstate.set('height', 300);
      return view2.viewstate.set('width', 400);
    };
    return _.defer(window.myrender);
  });

}).call(this);
}, "unittest/hasparent_test": function(exports, require, module) {(function() {
  var Collections, HasParent, TestParent, TestParents, base, testparents,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("../base");

  Collections = base.Collections;

  HasParent = base.HasParent;

  TestParent = (function(_super) {

    __extends(TestParent, _super);

    function TestParent() {
      return TestParent.__super__.constructor.apply(this, arguments);
    }

    TestParent.prototype.type = 'TestParent';

    TestParent.prototype.parent_properties = ['testprop'];

    TestParent.prototype.display_defaults = {
      testprop: 'defaulttestprop'
    };

    return TestParent;

  })(HasParent);

  TestParents = (function(_super) {

    __extends(TestParents, _super);

    function TestParents() {
      return TestParents.__super__.constructor.apply(this, arguments);
    }

    TestParents.prototype.model = TestParent;

    return TestParents;

  })(Backbone.Collection);

  testparents = new TestParents();

  exports.testparents = testparents;

  base.locations['TestParent'] = ['./unittest/hasparent_test', 'testparents'];

  test('parent_settings_propagate', function() {
    var child, parent;
    testparents.reset();
    parent = Collections('TestParent').create({
      id: 'parent',
      testprop: 'aassddff'
    });
    child = Collections('TestParent').create({
      id: 'first',
      parent: parent.ref()
    });
    return ok(child.get('testprop') === parent.get('testprop'));
  });

  test('display_defaults_propagate', function() {
    var child, parent;
    testparents.reset();
    parent = Collections('TestParent').create({
      id: 'parent'
    });
    child = Collections('TestParent').create({
      id: 'first',
      parent: parent.ref()
    });
    return ok(child.get('testprop') === parent.get('testprop'));
  });

}).call(this);
}, "unittest/test_utils": function(exports, require, module) {(function() {
  var Collections, Rand, base, make_glyph_test;

  base = require("../../base");

  Collections = base.Collections;

  Rand = (function() {

    function Rand(seed) {
      this.seed = seed;
      this.multiplier = 1664525;
      this.modulo = 4294967296;
      this.offset = 1013904223;
      if (!((this.seed != null) && (0 <= seed && seed < this.modulo))) {
        this.seed = (new Date().valueOf() * new Date().getMilliseconds()) % this.modulo;
      }
    }

    Rand.prototype.seed = function(seed) {
      return this.seed = seed;
    };

    Rand.prototype.randn = function() {
      return this.seed = (this.multiplier * this.seed + this.offset) % this.modulo;
    };

    Rand.prototype.randf = function() {
      return this.randn() / this.modulo;
    };

    Rand.prototype.rand = function(n) {
      return Math.floor(this.randf() * n);
    };

    Rand.prototype.rand2 = function(min, max) {
      return min + this.rand(max - min);
    };

    return Rand;

  })();

  make_glyph_test = function(test_name, data_source, defaults, glyphspec, xrange, yrange, tools, dims) {
    if (tools == null) {
      tools = false;
    }
    if (dims == null) {
      dims = [200, 200];
    }
    return function() {
      var div, glyph, myrender, pantool, plot_model, plot_tools, xaxis, yaxis, zoomtool;
      expect(0);
      plot_tools = [];
      if (tools) {
        pantool = Collections('PanTool').create({
          dataranges: [xrange.ref(), yrange.ref()],
          dimensions: ['width', 'height']
        });
        zoomtool = Collections('ZoomTool').create({
          dataranges: [xrange.ref(), yrange.ref()],
          dimensions: ['width', 'height']
        });
        plot_tools = [pantool, zoomtool];
      }
      glyph = Collections('GlyphRenderer').create({
        data_source: data_source.ref(),
        xdata_range: xrange.ref(),
        ydata_range: yrange.ref(),
        glyphspec: glyphspec
      });
      glyph.set(defaults);
      plot_model = Collections('Plot').create();
      xaxis = Collections('LinearAxis').create({
        orientation: 'bottom',
        parent: plot_model.ref(),
        data_range: xrange.ref()
      });
      yaxis = Collections('LinearAxis').create({
        orientation: 'left',
        parent: plot_model.ref(),
        data_range: yrange.ref()
      });
      plot_model.set({
        renderers: [glyph.ref()],
        axes: [xaxis.ref(), yaxis.ref()],
        tools: plot_tools,
        width: dims[0],
        height: dims[1]
      });
      div = $('<div></div>');
      $('body').append(div);
      myrender = function() {
        var view;
        view = new plot_model.default_view({
          model: plot_model
        });
        div.append(view.$el);
        view.render();
        return console.log('Test ' + test_name);
      };
      return _.defer(myrender);
    };
  };

  exports.make_glyph_test = make_glyph_test;

  exports.Rand = Rand;

}).call(this);
}, "unittest/legend_test": function(exports, require, module) {(function() {
  var Collections, base, glyph_plot, line_plot, scatter_plot, testutils;

  base = require("../base");

  Collections = base.Collections;

  testutils = require("../testutils");

  line_plot = testutils.line_plot;

  scatter_plot = testutils.scatter_plot;

  glyph_plot = testutils.glyph_plot;

  test('legend_test', function() {
    var data_source, div, legend, myrender, old_renderers, plotmodel;
    data_source = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: 1,
          y: -2
        }, {
          x: 2,
          y: -3
        }, {
          x: 3,
          y: -4
        }, {
          x: 4,
          y: -5
        }, {
          x: 5,
          y: -6
        }
      ]
    }, {
      'local': true
    });
    plotmodel = scatter_plot(null, data_source, 'x', 'y', null, 'circle');
    legend = Collections('Legend').create({
      legends: [
        {
          name: "widgets",
          color: "#888",
          source_field: "x"
        }, {
          name: "quxbits",
          color: "#00F",
          source_field: "Y"
        }
      ],
      position: "top_right",
      parent: plotmodel.ref()
    });
    old_renderers = plotmodel.get('renderers');
    old_renderers.push(legend.ref());
    plotmodel.set('renderers', old_renderers);
    window.plot = plotmodel;
    div = $('<div/>');
    $('body').append(div);
    myrender = function() {
      var view;
      view = new plotmodel.default_view({
        model: plotmodel
      });
      div.append(view.$el);
      return view.render();
    };
    console.log('test_simple_plot');
    _.defer(myrender);
    return expect(0);
  });

}).call(this);
}, "unittest/primitives/line_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [1, 2, 3, 4, 3, 2, 1]
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [9, 8, 7, 6, 5, 4, 3],
        line_color: 'orange'
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [3, 4, 5, 6, 7, 8, 9],
        line_color: 'blue',
        line_dash: [4, 6]
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [7, 7, 7, 7, 7, 7, 7],
        line_width: 6,
        line_color: 'green',
        line_alpha: 0.4
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'line',
    xs: 'xs',
    ys: 'ys'
  };

  test('line_glyph', make_glyph_test('line_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/segment_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x0: 1,
        y0: 5,
        x1: 2,
        y1: 5.5
      }, {
        x0: 2,
        y0: 4,
        x1: 3,
        y1: 4.5
      }, {
        x0: 3,
        y0: 3,
        x1: 4,
        y1: 3.5
      }, {
        x0: 4,
        y0: 2,
        x1: 5,
        y1: 2.5
      }, {
        x0: 5,
        y0: 1,
        x1: 6,
        y1: 1.5
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'segment',
    x0: 'x0',
    y0: 'y0',
    x1: 'x1',
    y1: 'y1'
  };

  test('segment_glyph', make_glyph_test('segment_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/area_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [1, 2, 3, 4, 3, 2, 1],
        fill: 'blue'
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [9, 8, 7, 6, 5, 4, 5],
        line_color: 'orange'
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [6, 4, 5, 6, 7, 8, 9],
        line_color: 'blue',
        line_dash: [3, 2]
      }, {
        xs: [2, 3, 4, 5, 6, 7, 8],
        ys: [7, 8, 9, 9, 9, 9, 8],
        line_width: 6,
        line_color: 'green',
        line_alpha: 0.4
      }
    ]
  });

  defaults = {
    fill_alpha: 0.5
  };

  glyph = {
    type: 'area',
    xs: 'xs',
    ys: 'ys'
  };

  test('area_glyph', make_glyph_test('area_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/quadcurve_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x0: 1,
        y0: 5,
        x1: 2,
        y1: 5,
        cx: 3,
        cy: 6
      }, {
        x0: 2,
        y0: 4,
        x1: 3,
        y1: 4,
        cx: 4,
        cy: 6
      }, {
        x0: 3,
        y0: 3,
        x1: 4,
        y1: 3,
        cx: 5,
        cy: 6
      }, {
        x0: 4,
        y0: 2,
        x1: 5,
        y1: 2,
        cx: 6,
        cy: 6
      }, {
        x0: 5,
        y0: 1,
        x1: 6,
        y1: 1,
        cx: 7,
        cy: 6
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'quadcurve',
    x0: 'x0',
    y0: 'y0',
    x1: 'x1',
    y1: 'y1',
    cx: 'cx',
    cy: 'cy'
  };

  test('quadcurve_glyph', make_glyph_test('quadcurve_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/text_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5
      }, {
        x: 2,
        y: 4,
        text: 'bar',
        text_color: 'orange'
      }, {
        x: 3,
        y: 3
      }, {
        x: 4,
        y: 2
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    text: 'foo',
    angle: -0.2
  };

  glyph = {
    type: 'text',
    x: 'x',
    y: 'y'
  };

  test('text_glyph', make_glyph_test('text_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/circle_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5,
        radius: 10
      }, {
        x: 2,
        y: 4
      }, {
        x: 3,
        y: 3,
        fill: 'red'
      }, {
        x: 4,
        y: 2,
        radius: 8,
        fill_alpha: 0.3
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'circle',
    fill: 'blue',
    radius: {
      field: 'radius',
      "default": 5
    },
    units: 'screen',
    x: 'x',
    y: 'y'
  };

  test('circle_glyph', make_glyph_test('circle_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/ray_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5,
        angle: -1.3,
        length: 0
      }, {
        x: 2,
        y: 4,
        angle: -1.2,
        length: 40,
        line_color: 'blue'
      }, {
        x: 3,
        y: 3,
        angle: -1.1,
        length: 30
      }, {
        x: 4,
        y: 2,
        angle: -1.0,
        length: 20
      }, {
        x: 5,
        y: 1,
        angle: -0.9,
        length: 10
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'ray',
    x: 'x',
    y: 'y',
    angle: 'angle',
    length: 'length'
  };

  test('ray_glyph', make_glyph_test('ray_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/oval_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5
      }, {
        x: 2,
        y: 4,
        angle: 0.2
      }, {
        x: 3,
        y: 3,
        fill: "red"
      }, {
        x: 4,
        y: 2,
        fill_alpha: 0.3
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    width: 20,
    width_units: "screen",
    height: 28,
    height_units: "screen",
    angle: 0
  };

  glyph = {
    type: 'oval',
    fill: 'blue',
    x: 'x',
    y: 'y'
  };

  test('oval_glyph', make_glyph_test('oval_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/quad_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        left: 1,
        right: 1.75,
        bottom: 5,
        top: 6
      }, {
        left: 2,
        right: 3.00,
        bottom: 4,
        top: 4.75
      }, {
        left: 3,
        right: 3.75,
        bottom: 3,
        top: 3.75,
        fill: 'red'
      }, {
        left: 4,
        right: 4.75,
        bottom: 2,
        top: 3.75,
        fill_alpha: 0.3
      }, {
        left: 5,
        right: 5.76,
        bottom: 1,
        top: 1.75
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'quad',
    fill: 'blue',
    left: 'left',
    right: 'right',
    bottom: 'bottom',
    top: 'top'
  };

  test('quad_glyph', make_glyph_test('quad_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/rect_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5
      }, {
        x: 2,
        y: 4,
        angle: 0.7
      }, {
        x: 3,
        y: 3,
        fill: 'red'
      }, {
        x: 4,
        y: 2,
        fill_alpha: 0.3
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    angle: 0.4,
    width: 12,
    width_units: 'screen',
    height: 15,
    height_units: 'screen'
  };

  glyph = {
    type: 'rect',
    fill: 'blue',
    x: 'x',
    y: 'y'
  };

  test('rect_glyph', make_glyph_test('rect_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/image_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5
      }, {
        x: 2,
        y: 4,
        image: 'http://localhost:5000/static/sad.png'
      }, {
        x: 3,
        y: 3
      }, {
        x: 4,
        y: 2
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    image: 'http://localhost:5000/static/glad.png',
    angle: 0.3
  };

  glyph = {
    type: 'image',
    x: 'x',
    y: 'y'
  };

  test('image_glyph', make_glyph_test('image_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/arc_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5
      }, {
        x: 2,
        y: 4,
        direction: 'anticlock',
        line_color: 'orange'
      }, {
        x: 3,
        y: 3
      }, {
        x: 4,
        y: 2
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    radius: 10,
    start_angle: 0.8,
    end_angle: 3.8,
    direction: 'clock'
  };

  glyph = {
    type: 'arc',
    x: 'x',
    y: 'y',
    line_color: {
      field: 'line_color'
    }
  };

  test('arc_glyph', make_glyph_test('arc_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/bezier_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x0: 1,
        y0: 5,
        x1: 2,
        y1: 5,
        cx0: 1.5,
        cy0: 4,
        cx1: 4,
        cy1: 8
      }, {
        x0: 2,
        y0: 4,
        x1: 3,
        y1: 4,
        cx0: 2.5,
        cy0: 4,
        cx1: 5,
        cy1: 7
      }, {
        x0: 3,
        y0: 3,
        x1: 4,
        y1: 3,
        cx0: 3.5,
        cy0: 4,
        cx1: 6,
        cy1: 6
      }, {
        x0: 4,
        y0: 2,
        x1: 5,
        y1: 2,
        cx0: 4.5,
        cy0: 4,
        cx1: 7,
        cy1: 5
      }, {
        x0: 5,
        y0: 1,
        x1: 6,
        y1: 1,
        cx0: 5.5,
        cy0: 4,
        cx1: 8,
        cy1: 4
      }
    ]
  });

  defaults = {};

  glyph = {
    type: 'bezier',
    x0: 'x0',
    y0: 'y0',
    x1: 'x1',
    y1: 'y1',
    cx0: 'cx0',
    cy0: 'cy0',
    cx1: 'cx1',
    cy1: 'cy1'
  };

  test('bezier_glyph', make_glyph_test('bezier_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/primitives/wedge_test": function(exports, require, module) {(function() {
  var Collections, data_source, defaults, glyph, make_glyph_test, range;

  Collections = require('../../base').Collections;

  make_glyph_test = require('../test_utils').make_glyph_test;

  range = Collections('Range1d').create({
    start: 0,
    end: 10
  });

  data_source = Collections('ObjectArrayDataSource').create({
    data: [
      {
        x: 1,
        y: 5,
        radius: 10
      }, {
        x: 2,
        y: 4
      }, {
        x: 3,
        y: 3,
        fill: 'red'
      }, {
        x: 4,
        y: 2,
        radius: 8,
        fill_alpha: 0.3
      }, {
        x: 5,
        y: 1
      }
    ]
  });

  defaults = {
    radius: 10,
    start_angle: 0.1,
    end_angle: 3.9,
    direction: 'clock'
  };

  glyph = {
    type: 'wedge',
    fill: 'blue',
    x: 'x',
    y: 'y'
  };

  test('wedge_glyph', make_glyph_test('wedge_glyph', data_source, defaults, glyph, range, range));

}).call(this);
}, "unittest/perf_test": function(exports, require, module) {(function() {
  var Collections, Rand, circle_fast, circle_slow, colors, defaults, heights, i, make_glyph_test, r, radii, rect_fast, rect_slow, source, val, widths, x, xdr, y, ydr, zip;

  Collections = require('../base').Collections;

  make_glyph_test = require('./test_utils').make_glyph_test;

  Rand = require('./test_utils').Rand;

  zip = function() {
    var arr, i, length, lengthArray, _i, _results;
    lengthArray = (function() {
      var _i, _len, _results;
      _results = [];
      for (_i = 0, _len = arguments.length; _i < _len; _i++) {
        arr = arguments[_i];
        _results.push(arr.length);
      }
      return _results;
    }).apply(this, arguments);
    length = Math.min.apply(Math, lengthArray);
    _results = [];
    for (i = _i = 0; 0 <= length ? _i < length : _i > length; i = 0 <= length ? ++_i : --_i) {
      _results.push((function() {
        var _j, _len, _results1;
        _results1 = [];
        for (_j = 0, _len = arguments.length; _j < _len; _j++) {
          arr = arguments[_j];
          _results1.push(arr[i]);
        }
        return _results1;
      }).apply(this, arguments));
    }
    return _results;
  };

  x = (function() {
    var _i, _len, _ref, _results;
    _ref = _.range(600);
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      x = _ref[_i];
      _results.push(x / 30);
    }
    return _results;
  })();

  y = (function() {
    var _i, _len, _results;
    _results = [];
    for (_i = 0, _len = x.length; _i < _len; _i++) {
      y = x[_i];
      _results.push(Math.sin(y));
    }
    return _results;
  })();

  widths = (function() {
    var _i, _len, _results;
    _results = [];
    for (_i = 0, _len = x.length; _i < _len; _i++) {
      i = x[_i];
      _results.push(0.01);
    }
    return _results;
  })();

  heights = (function() {
    var _i, _len, _results;
    _results = [];
    for (_i = 0, _len = x.length; _i < _len; _i++) {
      i = x[_i];
      _results.push(0.4);
    }
    return _results;
  })();

  colors = (function() {
    var _i, _len, _results;
    _results = [];
    for (_i = 0, _len = y.length; _i < _len; _i++) {
      val = y[_i];
      _results.push("rgb(" + (Math.floor(155 + 100 * val)) + ", " + (Math.floor(100 + 50 * val)) + ", " + (Math.floor(120 - 50 * val)) + ")");
    }
    return _results;
  })();

  source = Collections('ColumnDataSource').create({
    data: {
      x: x,
      y: y,
      width: widths,
      height: heights,
      fill: colors
    }
  });

  xdr = Collections('DataRange1d').create({
    sources: [
      {
        ref: source.ref(),
        columns: ['x']
      }
    ]
  });

  ydr = Collections('DataRange1d').create({
    sources: [
      {
        ref: source.ref(),
        columns: ['y']
      }
    ]
  });

  defaults = {};

  rect_fast = {
    x: 'x',
    y: 'y',
    width: 'width',
    height: 'height',
    fill: 'red',
    type: 'rect',
    line_color: null,
    fast_path: true,
    angle: 0
  };

  test('rect_perf_fast', make_glyph_test('rect_perf_fast', source, defaults, rect_fast, xdr, ydr, true, [800, 400]));

  xdr = Collections('DataRange1d').create({
    sources: [
      {
        ref: source.ref(),
        columns: ['x']
      }
    ]
  });

  ydr = Collections('DataRange1d').create({
    sources: [
      {
        ref: source.ref(),
        columns: ['y']
      }
    ]
  });

  rect_slow = {
    x: 'x',
    y: 'y',
    width: 'width',
    height: 'height',
    type: 'rect',
    fill: 'fill',
    line_color: null,
    angle: 0.1
  };

  test('rect_perf_slow', make_glyph_test('rect_perf_slow', source, defaults, rect_slow, xdr, ydr, true, [800, 400]));

  r = new Rand(123456789);

  x = (function() {
    var _i, _len, _ref, _results;
    _ref = _.range(4000);
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      i = _ref[_i];
      _results.push(r.randf() * 100);
    }
    return _results;
  })();

  y = (function() {
    var _i, _len, _ref, _results;
    _ref = _.range(4000);
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      i = _ref[_i];
      _results.push(r.randf() * 100);
    }
    return _results;
  })();

  radii = (function() {
    var _i, _len, _ref, _results;
    _ref = _.range(4000);
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      i = _ref[_i];
      _results.push(r.randf() + 0.5);
    }
    return _results;
  })();

  colors = (function() {
    var _i, _len, _ref, _results;
    _ref = zip(x, y);
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      val = _ref[_i];
      _results.push("rgb(" + (Math.floor(50 + 2 * val[0])) + ", " + (Math.floor(30 + 2 * val[1])) + ", 150)");
    }
    return _results;
  })();

  source = Collections('ColumnDataSource').create({
    data: {
      x: x,
      y: y,
      radius: radii,
      fill: colors
    }
  });

  xdr = Collections('Range1d').create({
    start: 0,
    end: 100
  });

  ydr = Collections('Range1d').create({
    start: 0,
    end: 100
  });

  circle_fast = {
    x: 'x',
    y: 'y',
    radius: 'radius',
    radius_units: 'data',
    fill: 'red',
    fill_alpha: 0.5,
    type: 'circle',
    line_color: null,
    fast_path: true
  };

  test('circle_perf_fast', make_glyph_test('circle_perf_fast', source, defaults, circle_fast, xdr, ydr, true, [600, 600]));

  xdr = Collections('Range1d').create({
    start: 0,
    end: 100
  });

  ydr = Collections('Range1d').create({
    start: 0,
    end: 100
  });

  circle_slow = {
    x: 'x',
    y: 'y',
    radius: 'radius',
    radius_units: 'data',
    fill: 'fill',
    fill_alpha: 0.5,
    type: 'circle',
    line_color: null
  };

  test('circle_perf_slow', make_glyph_test('circle_perf_slow', source, defaults, circle_slow, xdr, ydr, true, [600, 600]));

}).call(this);
}, "unittest/tick_test": function(exports, require, module) {(function() {
  var argsort, auto_interval, calc_bound, tick_intervals, ticks;

  ticks = require("../ticks");

  calc_bound = ticks.calc_bound;

  tick_intervals = ticks.tick_intervals;

  auto_interval = ticks.auto_interval;

  argsort = ticks.argsort;

  test('test_calc_bound', function() {
    expect(4);
    equal(calc_bound(3.0, 2, true), 4);
    equal(calc_bound(3.0, 2, false), 2);
    equal(calc_bound(4.0, 2, true), 4);
    return equal(calc_bound(4.0, 2, false), 4);
  });

  test('test_tick_intervals', function() {
    expect(3);
    equal(tick_intervals(0.0, 100.0, 13), 10);
    equal(tick_intervals(0.0, 120.0, 3), 50);
    return equal(tick_intervals(0.0, 100.0, 5), 25);
  });

  test('auto_interval', function() {
    equal(auto_interval(0.0, 100.0), 20);
    equal(auto_interval(0.0, 130.0), 25);
    return equal(auto_interval(30.0, 50.0), 2.5);
  });

  test('argsort', function() {
    var argsorted, argsorted2, expected, expected2, orig, orig2;
    orig = [-3, -2, -1];
    argsorted = argsort(orig);
    expected = [0, 1, 2];
    deepEqual(argsorted, expected);
    orig2 = [3, -2, -1];
    argsorted2 = argsort(orig2);
    expected2 = [1, 2, 0];
    deepEqual(argsorted2, expected2);
    return true;
  });

  test('_sorted', function() {
    var ab, bc;
    ab = [2, 4, 7];
    deepEqual(_.sorted(ab), [2, 4, 7]);
    ab = [2, 4, 7];
    bc = _.sorted(ab);
    bc[0] = 'a';
    deepEqual(ab, [2, 4, 7]);
    ab = [2, -4, 7];
    deepEqual([-4, 2, 7], _.sorted(ab));
    return null;
  });

}).call(this);
}, "unittest/date_test": function(exports, require, module) {(function() {
  var Collections, base, line_plot, scatter_plot, testutils;

  base = require("../base");

  Collections = base.Collections;

  testutils = require("../testutils");

  line_plot = testutils.line_plot;

  scatter_plot = testutils.scatter_plot;

  test('test_date_hour_intervals', function() {
    var data_source1, date_axis, div, interval, old_axis, pantool, plot1, scatterrenderer, selecttool, zoomtool;
    expect(0);
    base = Number(new Date());
    interval = 3600 * 1000.0;
    data_source1 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: base,
          y: -2
        }, {
          x: base + interval,
          y: -3
        }, {
          x: base + interval * 2,
          y: -4
        }, {
          x: base + interval * 3,
          y: -5
        }, {
          x: base + interval * 4,
          y: -6
        }
      ]
    });
    plot1 = scatter_plot(null, data_source1, 'x', 'y', 'x', 'circle');
    old_axis = plot1.resolve_ref(plot1.get('axes')[0]);
    date_axis = Collections('LinearDateAxis').create(old_axis.attributes);
    plot1.get('axes')[0] = date_axis.ref();
    scatterrenderer = plot1.resolve_ref(plot1.get('renderers')[0]);
    pantool = Collections('PanTool').create({
      'xmappers': [scatterrenderer.get('xmapper')],
      'ymappers': [scatterrenderer.get('ymapper')]
    });
    zoomtool = Collections('ZoomTool').create({
      'xmappers': [scatterrenderer.get('xmapper')],
      'ymappers': [scatterrenderer.get('ymapper')]
    });
    selecttool = Collections('SelectionTool').create({
      'renderers': [scatterrenderer.ref()],
      'data_source_options': {
        'local': true
      }
    });
    plot1.set('tools', [pantool.ref(), zoomtool.ref(), selecttool.ref()]);
    window.plot1 = plot1;
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    window.myrender = function() {
      var view;
      view = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      div.append(view.$el);
      view.render();
      plot1.set({
        'width': 300
      });
      plot1.set({
        'height': 300
      });
      return window.view = view;
    };
    return _.defer(window.myrender);
  });

  test('test_date_day_intervals', function() {
    var data_source1, date_axis, div, interval, old_axis, pantool, plot1, scatterrenderer, selectoverlay, selecttool, zoomtool;
    expect(0);
    base = Number(new Date());
    interval = 3600 * 1000.0 * 24;
    data_source1 = Collections('ObjectArrayDataSource').create({
      data: [
        {
          x: base,
          y: -2
        }, {
          x: base + interval,
          y: -3
        }, {
          x: base + interval * 2,
          y: -4
        }, {
          x: base + interval * 3,
          y: -5
        }, {
          x: base + interval * 4,
          y: -6
        }
      ]
    });
    plot1 = scatter_plot(null, data_source1, 'x', 'y', 'x', 'circle');
    old_axis = plot1.resolve_ref(plot1.get('axes')[0]);
    date_axis = Collections('LinearDateAxis').create(old_axis.attributes);
    plot1.get('axes')[0] = date_axis.ref();
    scatterrenderer = plot1.resolve_ref(plot1.get('renderers')[0]);
    pantool = Collections('PanTool').create({
      'xmappers': [scatterrenderer.get('xmapper')],
      'ymappers': [scatterrenderer.get('ymapper')]
    });
    zoomtool = Collections('ZoomTool').create({
      'xmappers': [scatterrenderer.get('xmapper')],
      'ymappers': [scatterrenderer.get('ymapper')]
    });
    selecttool = Collections('SelectionTool').create({
      'renderers': [scatterrenderer.ref()]
    });
    selectoverlay = Collections('BoxSelectionOverlay').create({
      'tool': selecttool.ref()
    });
    plot1.set('tools', [pantool.ref(), zoomtool.ref(), selecttool.ref()]);
    plot1.set('overlays', [selectoverlay.ref()]);
    window.plot1 = plot1;
    div = $('<div style="border:1px solid black"></div>');
    $('body').append(div);
    window.myrender = function() {
      var view;
      view = new plot1.default_view({
        model: plot1,
        render_loop: true
      });
      div.append(view.$el);
      view.render();
      plot1.set({
        'width': 300
      });
      plot1.set({
        'height': 300
      });
      return window.view = view;
    };
    return _.defer(window.myrender);
  });

}).call(this);
}, "schema_renderers": function(exports, require, module) {(function() {
  var Collections, HasParent, LineRenderer, LineRendererView, LineRenderers, LinearMapper, PlotWidget, ScatterRenderer, ScatterRendererView, ScatterRenderers, XYRenderer, XYRendererView, base, mapper, safebind,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("./base");

  Collections = base.Collections;

  HasParent = base.HasParent;

  PlotWidget = base.PlotWidget;

  safebind = base.safebind;

  mapper = require("./mapper");

  LinearMapper = mapper.LinearMapper;

  XYRendererView = (function(_super) {

    __extends(XYRendererView, _super);

    function XYRendererView() {
      return XYRendererView.__super__.constructor.apply(this, arguments);
    }

    XYRendererView.prototype.initialize = function(options) {
      XYRendererView.__super__.initialize.call(this, options);
      this.set_xmapper();
      return this.set_ymapper();
    };

    XYRendererView.prototype.bind_bokeh_events = function() {
      safebind(this, this.model, 'change', this.request_render);
      safebind(this, this.plot_view.viewstate, 'change', this.request_render);
      safebind(this, this.mget_obj('data_source'), 'change', this.request_render);
      safebind(this, this.model, 'change:xdata_range', this.set_xmapper);
      safebind(this, this.model, 'change:ydata_range', this.set_ymapper);
      safebind(this, this.mget_obj('xdata_range'), 'change', this.request_render);
      return safebind(this, this.mget_obj('ydata_range'), 'change', this.request_render);
    };

    XYRendererView.prototype.set_xmapper = function() {
      this.xmapper = new LinearMapper({}, {
        data_range: this.mget_obj('xdata_range'),
        viewstate: this.plot_view.viewstate,
        screendim: 'width'
      });
      return this.request_render();
    };

    XYRendererView.prototype.set_ymapper = function() {
      this.ymapper = new LinearMapper({}, {
        data_range: this.mget_obj('ydata_range'),
        viewstate: this.plot_view.viewstate,
        screendim: 'height'
      });
      return this.request_render();
    };

    XYRendererView.prototype.select = function(xscreenbounds, yscreenbounds) {
      var func, source, xdatabounds, ydatabounds;
      if (xscreenbounds) {
        mapper = this.xmapper;
        xdatabounds = [mapper.map_data(xscreenbounds[0]), mapper.map_data(xscreenbounds[1])];
      } else {
        xdatabounds = null;
      }
      if (yscreenbounds) {
        mapper = this.ymapper;
        ydatabounds = [mapper.map_data(yscreenbounds[0]), mapper.map_data(yscreenbounds[1])];
      } else {
        ydatabounds = null;
      }
      func = function(xval, yval) {
        var val;
        val = ((xdatabounds === null) || (xval > xdatabounds[0] && xval < xdatabounds[1])) && ((ydatabounds === null) || (yval > ydatabounds[0] && yval < ydatabounds[1]));
        return val;
      };
      source = this.mget_obj('data_source');
      return source.select([this.mget('xfield'), this.mget('yfield')], func);
    };

    XYRendererView.prototype.calc_buffer = function(data) {
      "use strict";

      var datax, datay, own_options, pv, pvo, screenx, screeny, x, xfield, y, yfield;
      pv = this.plot_view;
      pvo = this.plot_view.options;
      own_options = this.options;
      xfield = this.model.get('xfield');
      yfield = this.model.get('yfield');
      datax = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          x = data[_i];
          _results.push(x[xfield]);
        }
        return _results;
      })();
      screenx = this.xmapper.v_map_screen(datax);
      screenx = pv.viewstate.v_xpos(screenx);
      datay = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = data.length; _i < _len; _i++) {
          y = data[_i];
          _results.push(y[yfield]);
        }
        return _results;
      })();
      screeny = this.ymapper.v_map_screen(datay);
      screeny = pv.viewstate.v_ypos(screeny);
      this.screeny = screeny;
      return this.screenx = screenx;
    };

    return XYRendererView;

  })(PlotWidget);

  LineRendererView = (function(_super) {

    __extends(LineRendererView, _super);

    function LineRendererView() {
      return LineRendererView.__super__.constructor.apply(this, arguments);
    }

    LineRendererView.prototype.render = function() {
      var data, idx, x, y, _i, _ref;
      LineRendererView.__super__.render.call(this);
      data = this.model.get_obj('data_source').get('data');
      this.calc_buffer(data);
      this.plot_view.ctx.fillStyle = this.mget('foreground_color');
      this.plot_view.ctx.strokeStyle = this.mget('foreground_color');
      this.plot_view.ctx.beginPath();
      this.plot_view.ctx.moveTo(this.screenx[0], this.screeny[0]);
      for (idx = _i = 1, _ref = this.screenx.length; 1 <= _ref ? _i <= _ref : _i >= _ref; idx = 1 <= _ref ? ++_i : --_i) {
        x = this.screenx[idx];
        y = this.screeny[idx];
        if (isNaN(x) || isNaN(y)) {
          this.plot_view.ctx.stroke();
          this.plot_view.ctx.beginPath();
          continue;
        }
        this.plot_view.ctx.lineTo(x, y);
      }
      this.plot_view.ctx.stroke();
      this.render_end();
      return null;
    };

    return LineRendererView;

  })(XYRendererView);

  ScatterRendererView = (function(_super) {

    __extends(ScatterRendererView, _super);

    function ScatterRendererView() {
      return ScatterRendererView.__super__.constructor.apply(this, arguments);
    }

    ScatterRendererView.prototype.render = function() {
      "use strict";

      var color_arr, color_field, color_mapper, comp_color, ctx, data, foreground_color, idx, mark_type, sel_idxs, selected, selecting, unselected_color, _i, _j, _len, _ref;
      ScatterRendererView.__super__.render.call(this);
      selected = {};
      sel_idxs = this.model.get_obj('data_source').get('selected');
      if (sel_idxs.length === 0) {
        selecting = false;
      } else {
        selecting = true;
      }
      for (_i = 0, _len = sel_idxs.length; _i < _len; _i++) {
        idx = sel_idxs[_i];
        selected[idx] = true;
      }
      data = this.model.get_obj('data_source').get('data');
      this.calc_buffer(data);
      this.plot_view.ctx.beginPath();
      foreground_color = this.mget('foreground_color');
      unselected_color = this.mget('unselected_color');
      color_field = this.mget('color_field');
      ctx = this.plot_view.ctx;
      if (color_field) {
        color_mapper = this.model.get_obj('color_mapper');
        color_arr = this.model.get('color_field');
      }
      mark_type = this.mget('mark');
      for (idx = _j = 0, _ref = data.length; 0 <= _ref ? _j <= _ref : _j >= _ref; idx = 0 <= _ref ? ++_j : --_j) {
        if (selecting && !selected[idx]) {
          this.plot_view.ctx.strokeStyle = unselected_color;
          this.plot_view.ctx.fillStyle = unselected_color;
        } else if (color_field) {
          comp_color = color_mapper.map_screen(idx);
          this.plot_view.ctx.strokeStyle = comp_color;
          this.plot_view.ctx.fillStyle = comp_color;
        } else {
          this.plot_view.ctx.strokeStyle = foreground_color;
          this.plot_view.ctx.fillStyle = foreground_color;
        }
        if (mark_type === "square") {
          this.addPolygon(this.screenx[idx], this.screeny[idx]);
        } else {
          this.addCircle(this.screenx[idx], this.screeny[idx]);
        }
      }
      this.plot_view.ctx.stroke();
      this.render_end();
      return null;
    };

    return ScatterRendererView;

  })(XYRendererView);

  XYRenderer = (function(_super) {

    __extends(XYRenderer, _super);

    function XYRenderer() {
      return XYRenderer.__super__.constructor.apply(this, arguments);
    }

    return XYRenderer;

  })(HasParent);

  XYRenderer.prototype.defaults = _.clone(XYRenderer.prototype.defaults);

  _.extend(XYRenderer.prototype.defaults, {
    xdata_range: null,
    ydata_range: null,
    xfield: null,
    yfield: null,
    data_source: null
  });

  LineRenderer = (function(_super) {

    __extends(LineRenderer, _super);

    function LineRenderer() {
      return LineRenderer.__super__.constructor.apply(this, arguments);
    }

    LineRenderer.prototype.type = 'LineRenderer';

    LineRenderer.prototype.default_view = LineRendererView;

    return LineRenderer;

  })(XYRenderer);

  LineRenderer.prototype.defaults = _.clone(LineRenderer.prototype.defaults);

  _.extend(LineRenderer.prototype.defaults, {
    xmapper: null,
    ymapper: null,
    xfield: null,
    yfield: null,
    color: "#000"
  });

  LineRenderers = (function(_super) {

    __extends(LineRenderers, _super);

    function LineRenderers() {
      return LineRenderers.__super__.constructor.apply(this, arguments);
    }

    LineRenderers.prototype.model = LineRenderer;

    return LineRenderers;

  })(Backbone.Collection);

  ScatterRenderer = (function(_super) {

    __extends(ScatterRenderer, _super);

    function ScatterRenderer() {
      return ScatterRenderer.__super__.constructor.apply(this, arguments);
    }

    ScatterRenderer.prototype.type = 'ScatterRenderer';

    ScatterRenderer.prototype.default_view = ScatterRendererView;

    return ScatterRenderer;

  })(XYRenderer);

  ScatterRenderer.prototype.defaults = _.clone(ScatterRenderer.prototype.defaults);

  _.extend(ScatterRenderer.prototype.defaults, {
    data_source: null,
    xmapper: null,
    ymapper: null,
    xfield: null,
    yfield: null,
    colormapper: null,
    colorfield: null,
    mark: 'circle'
  });

  ScatterRenderers = (function(_super) {

    __extends(ScatterRenderers, _super);

    function ScatterRenderers() {
      return ScatterRenderers.__super__.constructor.apply(this, arguments);
    }

    ScatterRenderers.prototype.model = ScatterRenderer;

    return ScatterRenderers;

  })(Backbone.Collection);

  exports.scatterrenderers = new ScatterRenderers;

  exports.linerenderers = new LineRenderers;

  exports.ScatterRenderer = ScatterRenderer;

  exports.ScatterRendererView = ScatterRendererView;

  exports.LineRenderer = LineRenderer;

  exports.LineRendererView = LineRendererView;

  exports.XYRenderer = XYRenderer;

  exports.XYRendererView = XYRendererView;

}).call(this);
}, "pandas/pandas": function(exports, require, module) {(function() {
  var ContinuumView, ENTER, HasParent, PandasDataSource, PandasDataSources, PandasPivot, PandasPivotView, PandasPivots, PandasPlotSource, PandasPlotSources, base, datasource, pandas_template, pandaspivots, safebind,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  base = require("../base");

  ContinuumView = base.ContinuumView;

  safebind = base.safebind;

  HasParent = base.HasParent;

  pandas_template = require("./pandaspivot");

  ENTER = 13;

  PandasPivotView = (function(_super) {

    __extends(PandasPivotView, _super);

    function PandasPivotView() {
      this.colors = __bind(this.colors, this);

      this.pandasend = __bind(this.pandasend, this);

      this.pandasnext = __bind(this.pandasnext, this);

      this.pandasback = __bind(this.pandasback, this);

      this.pandasbeginning = __bind(this.pandasbeginning, this);

      this.toggle_more_controls = __bind(this.toggle_more_controls, this);

      this.sort = __bind(this.sort, this);
      return PandasPivotView.__super__.constructor.apply(this, arguments);
    }

    PandasPivotView.prototype.initialize = function(options) {
      PandasPivotView.__super__.initialize.call(this, options);
      safebind(this, this.model, 'destroy', this.remove);
      safebind(this, this.model, 'change', this.render);
      this.controls_hide = true;
      return this.render();
    };

    PandasPivotView.prototype.events = {
      "keyup .pandasgroup": 'pandasgroup',
      "keyup .pandasoffset": 'pandasoffset',
      "keyup .pandassize": 'pandassize',
      "change .pandasagg": 'pandasagg',
      "click .pandasbeginning": 'pandasbeginning',
      "click .pandasback": 'pandasback',
      "click .pandasnext": 'pandasnext',
      "click .pandasend": 'pandasend',
      "click .controlsmore": 'toggle_more_controls',
      "click .pandascolumn": 'sort'
    };

    PandasPivotView.prototype.sort = function(e) {
      var colname;
      colname = $(e.currentTarget).text();
      return this.model.toggle_column_sort(colname);
    };

    PandasPivotView.prototype.toggle_more_controls = function() {
      if (this.controls_hide) {
        this.controls_hide = false;
      } else {
        this.controls_hide = true;
      }
      return this.render();
    };

    PandasPivotView.prototype.pandasbeginning = function() {
      return this.model.go_beginning();
    };

    PandasPivotView.prototype.pandasback = function() {
      return this.model.go_back();
    };

    PandasPivotView.prototype.pandasnext = function() {
      return this.model.go_forward();
    };

    PandasPivotView.prototype.pandasend = function() {
      return this.model.go_end();
    };

    PandasPivotView.prototype.pandasoffset = function(e) {
      var offset;
      if (e.keyCode === ENTER) {
        offset = this.$el.find('.pandasoffset').val();
        offset = Number(offset);
        if (_.isNaN(offset)) {
          offset = this.model.defaults.offset;
        }
        return this.model.save('offset', offset, {
          wait: true
        });
      }
    };

    PandasPivotView.prototype.pandassize = function(e) {
      var size, sizetxt;
      if (e.keyCode === ENTER) {
        sizetxt = this.$el.find('.pandassize').val();
        size = Number(sizetxt);
        if (_.isNaN(size) || sizetxt === "") {
          size = this.model.defaults.length;
        }
        if (size + this.mget('offset') > this.mget('maxlength')) {
          size = this.mget('maxlength') - this.mget('offset');
        }
        return this.model.save('length', size, {
          wait: true
        });
      }
    };

    PandasPivotView.prototype.pandasagg = function() {
      return this.model.save('agg', this.$el.find('.pandasagg').val(), {
        'wait': true
      });
    };

    PandasPivotView.prototype.fromcsv = function(str) {
      if (!str) {
        return [];
      }
      return _.map(str.split(","), function(x) {
        return x.trim();
      });
    };

    PandasPivotView.prototype.pandasgroup = function(e) {
      if (e.keyCode === ENTER) {
        return this.model.save('groups', this.fromcsv(this.$el.find(".pandasgroup").val()), {
          'wait': true
        });
      }
    };

    PandasPivotView.prototype.colors = function() {
      if (this.mget('counts') && this.mget('selected')) {
        return _.map(_.zip(this.mget('counts'), this.mget('selected')), function(temp) {
          var alpha, count, selected;
          count = temp[0], selected = temp[1];
          alpha = selected / count;
          return "rgba(0,0,255," + alpha + ")";
        });
      } else {
        return null;
      }
    };

    PandasPivotView.prototype.render = function() {
      var colors, groups, html, obj, sort, sort_ascendings, template_data, _i, _len, _ref;
      groups = this.mget('groups');
      if (_.isArray(groups)) {
        groups = groups.join(",");
      }
      sort = this.mget('sort');
      if (_.isArray(sort)) {
        sort = sort.join(",");
      }
      colors = this.colors();
      sort_ascendings = {};
      _ref = this.mget('sort');
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        obj = _ref[_i];
        sort_ascendings[obj['column']] = obj['ascending'];
      }
      template_data = {
        columns: this.mget('columns'),
        data: this.mget('data'),
        groups: groups,
        sort_ascendings: sort_ascendings,
        height: this.mget('height'),
        width: this.mget('width'),
        offset: this.mget('offset'),
        length: this.mget('length'),
        maxlength: this.mget('maxlength'),
        counts: this.mget('counts'),
        selected: this.mget('selected'),
        controls_hide: this.controls_hide,
        colors: colors,
        index: this.mget('index')
      };
      this.$el.empty();
      html = pandas_template(template_data);
      this.$el.html(html);
      this.$el.find("option[value=\"" + (this.mget('agg')) + "\"]").attr('selected', 'selected');
      return this.$el.addClass("bokehtable");
    };

    return PandasPivotView;

  })(ContinuumView);

  datasource = require("../datasource");

  PandasPlotSource = (function(_super) {

    __extends(PandasPlotSource, _super);

    function PandasPlotSource() {
      return PandasPlotSource.__super__.constructor.apply(this, arguments);
    }

    PandasPlotSource.prototype.type = 'PandasPlotSource';

    PandasPlotSource.prototype.initialize = function(attrs, options) {
      PandasPlotSource.__super__.initialize.call(this, attrs, options);
      this.select_serverside = _.throttle(this._select_serverside, 500);
      return safebind(this, this, 'change:selected', this.select_serverside);
    };

    PandasPlotSource.prototype._select_serverside = function() {
      var pandassource;
      pandassource = this.get_obj('pandassource');
      console.log('selecting', this.get('selected'), pandassource);
      pandassource.save({
        selected: this.get('selected')
      }, {
        wait: true
      });
      return null;
    };

    return PandasPlotSource;

  })(datasource.ObjectArrayDataSource);

  PandasPlotSources = (function(_super) {

    __extends(PandasPlotSources, _super);

    function PandasPlotSources() {
      return PandasPlotSources.__super__.constructor.apply(this, arguments);
    }

    PandasPlotSources.prototype.model = PandasPlotSource;

    return PandasPlotSources;

  })(Backbone.Collection);

  PandasPivot = (function(_super) {

    __extends(PandasPivot, _super);

    function PandasPivot() {
      this.toggle_column_sort = __bind(this.toggle_column_sort, this);

      this.dinitialize = __bind(this.dinitialize, this);
      return PandasPivot.__super__.constructor.apply(this, arguments);
    }

    PandasPivot.prototype.type = 'PandasPivot';

    PandasPivot.prototype.initialize = function(attrs, options) {
      var _this = this;
      PandasPivot.__super__.initialize.call(this, attrs, options);
      return this.throttled_fetch = _.throttle((function() {
        return _this.fetch();
      }), 500);
    };

    PandasPivot.prototype.dinitialize = function(attrs, options) {
      PandasPivot.__super__.dinitialize.call(this, attrs, options);
      return safebind(this, this.get_obj('pandassource'), 'change', this.throttled_fetch);
    };

    PandasPivot.prototype.fetch = function(options) {
      return PandasPivot.__super__.fetch.call(this, options);
    };

    PandasPivot.prototype.toggle_column_sort = function(colname) {
      var sort, sorting;
      sorting = this.get('sort');
      this.unset('sort', {
        'silent': true
      });
      sort = _.filter(sorting, function(x) {
        return x['column'] === colname;
      });
      if (sort.length > 0) {
        sort = sort[0];
      } else {
        sorting = _.clone(sorting);
        sorting.push({
          column: colname,
          ascending: true
        });
        this.save('sort', sorting, {
          'wait': true
        });
        return;
      }
      if (sort['ascending']) {
        sort['ascending'] = false;
        this.save('sort', sorting, {
          'wait': true
        });
      } else {
        sorting = _.filter(sorting, function(x) {
          return x['column'] !== colname;
        });
        this.save('sort', sorting, {
          'wait': true
        });
      }
    };

    PandasPivot.prototype.go_beginning = function() {
      this.set('offset', 0);
      return this.save();
    };

    PandasPivot.prototype.go_back = function() {
      var offset;
      offset = this.get('offset');
      offset = offset - this.get('length');
      if (offset < 0) {
        offset = 0;
      }
      this.set('offset', offset);
      return this.save();
    };

    PandasPivot.prototype.go_forward = function() {
      var maxoffset, offset;
      offset = this.get('offset');
      offset = offset + this.get('length');
      maxoffset = this.get('maxlength') - this.get('length');
      if (offset > maxoffset) {
        offset = maxoffset;
      }
      this.set('offset', offset);
      return this.save();
    };

    PandasPivot.prototype.go_end = function() {
      var maxoffset;
      maxoffset = this.get('maxlength') - this.get('length');
      this.set('offset', maxoffset);
      return this.save();
    };

    PandasPivot.prototype.defaults = {
      path: '',
      sort: [],
      groups: [],
      agg: 'sum',
      offset: 0,
      length: 100,
      maxlength: 1000,
      data: null,
      columns: [],
      width: 400
    };

    PandasPivot.prototype.default_view = PandasPivotView;

    return PandasPivot;

  })(HasParent);

  PandasPivots = (function(_super) {

    __extends(PandasPivots, _super);

    function PandasPivots() {
      return PandasPivots.__super__.constructor.apply(this, arguments);
    }

    PandasPivots.prototype.model = PandasPivot;

    return PandasPivots;

  })(Backbone.Collection);

  PandasDataSource = (function(_super) {

    __extends(PandasDataSource, _super);

    function PandasDataSource() {
      return PandasDataSource.__super__.constructor.apply(this, arguments);
    }

    PandasDataSource.prototype.type = 'PandasDataSource';

    PandasDataSource.prototype.initialize = function(attrs, options) {
      return PandasDataSource.__super__.initialize.call(this, attrs, options);
    };

    PandasDataSource.prototype.defaults = {
      selected: []
    };

    PandasDataSource.prototype.save = function(key, val, options) {
      var attrs;
      if (key === null || _.isObject(key)) {
        attrs = key;
        options = val;
      } else {
        attrs = {};
        attrs[key] = val;
      }
      if (!options) {
        options = {};
      }
      options.patch = true;
      return PandasDataSource.__super__.save.call(this, attrs, options);
    };

    return PandasDataSource;

  })(HasParent);

  PandasDataSources = (function(_super) {

    __extends(PandasDataSources, _super);

    function PandasDataSources() {
      return PandasDataSources.__super__.constructor.apply(this, arguments);
    }

    PandasDataSources.prototype.model = PandasDataSource;

    return PandasDataSources;

  })(Backbone.Collection);

  pandaspivots = new PandasPivots;

  exports.pandaspivots = pandaspivots;

  exports.PandasPivot = PandasPivot;

  exports.PandasPivotView = PandasPivotView;

  exports.PandasDataSource = PandasDataSource;

  exports.pandasdatasources = new PandasDataSources;

  exports.PandasPlotSource = PandasPlotSource;

  exports.pandasplotsources = new PandasPlotSources;

}).call(this);
}, "pandas/pandaspivot": function(exports, require, module) {module.exports = function(__obj) {
  if (!__obj) __obj = {};
  var __out = [], __capture = function(callback) {
    var out = __out, result;
    __out = [];
    callback.call(this);
    result = __out.join('');
    __out = out;
    return __safe(result);
  }, __sanitize = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else if (typeof value !== 'undefined' && value != null) {
      return __escape(value);
    } else {
      return '';
    }
  }, __safe, __objSafe = __obj.safe, __escape = __obj.escape;
  __safe = __obj.safe = function(value) {
    if (value && value.ecoSafe) {
      return value;
    } else {
      if (!(typeof value !== 'undefined' && value != null)) value = '';
      var result = new String(value);
      result.ecoSafe = true;
      return result;
    }
  };
  if (!__escape) {
    __escape = __obj.escape = function(value) {
      return ('' + value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    };
  }
  (function() {
    (function() {
      var column, datapoint, idx, _i, _j, _k, _len, _len1, _len2, _ref, _ref1, _ref2;
    
      __out.push('<form class="form-inline">\n  <p>Displaying entries ');
    
      __out.push(__sanitize(this.offset));
    
      __out.push(' \n    through ');
    
      __out.push(__sanitize(this.offset + this.length));
    
      __out.push(' of \n    ');
    
      __out.push(__sanitize(this.maxlength));
    
      __out.push('\n  </p>\n  \n  <table class="table" style="max-width:');
    
      __out.push(__sanitize(this.width));
    
      __out.push('px">\n    <tr>\n      <td colspan="1">\n        <label>Offset</label>\n        <input type="text" class="pandasoffset" value="');
    
      __out.push(__sanitize(this.offset));
    
      __out.push('"/>\n      </td>\n      <td colspan="1">\n        <label>Size</label>\n        <input type="text" class="pandassize" value="');
    
      __out.push(__sanitize(this.length));
    
      __out.push('"/>\n      </td>\n      <td>\n        <a href="#" class="pandasbeginning">\n          <i class="pandasicons icon-fast-backward"></i>\n        </a>\n        <a href="#" class="pandasback">\n          <i class="pandasicons icon-backward"></i>\n        </a>\n        <a href="#" class="pandasnext">\n          <i class="pandasicons icon-forward"></i>\n        </a>\n        <a href="#" class="pandasend">\n          <i class="pandasicons icon-fast-forward"></i>\n        </a>\n      </td>\n    <tr>\n      <td colspan="2">\n        <label>GroupBy </label>\n        <input type="text" class="pandasgroup" value="');
    
      __out.push(__sanitize(this.groups));
    
      __out.push('"/>\n      </td>\n      <td colspan="2">\n        <label>Aggregation</label>\n        <select class="pandasagg">\n          <option value="sum">sum</option>\n          <option value="mean">mean</option>\n          <option value="std">std</option>\n          <option value="max">max</option>\n          <option value="min">min</option>\n        </select>\n      </td>\n    </tr>\n  </table>\n</form>\n\n<table class="table\n              table-bordered table-condensed"\n       style="max-height:');
    
      __out.push(__sanitize(this.height));
    
      __out.push('px;max-width:');
    
      __out.push(__sanitize(this.width));
    
      __out.push('px"\n       >\n  <thead>\n    ');
    
      if (this.counts) {
        __out.push('\n    <th>counts</th>\n    ');
      }
    
      __out.push('\n    <th>index</th>\n    ');
    
      _ref = this.columns;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        column = _ref[_i];
        __out.push('\n    <th><a class="pandascolumn">');
        __out.push(__sanitize(column));
        __out.push('</a>\n        ');
        if (this.sort_ascendings[column] === true) {
          __out.push('\n        <i class="icon-chevron-up"></i>\n        ');
        } else if (this.sort_ascendings[column] === false) {
          __out.push('\n        <i class="icon-chevron-down"></i>\n        ');
        }
        __out.push('\n    </th>\n    ');
      }
    
      __out.push('\n  </thead>\n  ');
    
      _ref1 = this.data;
      for (idx = _j = 0, _len1 = _ref1.length; _j < _len1; idx = ++_j) {
        datapoint = _ref1[idx];
        __out.push('\n  \n  ');
        if (this.colors) {
          __out.push('\n  <tr style="background-color:');
          __out.push(__sanitize(this.colors[idx]));
          __out.push('">\n  ');
        } else {
          __out.push('\n  <tr>\n  ');
        }
        __out.push('\n  \n    ');
        if (this.counts) {
          __out.push('\n      ');
          if (this.selected && this.selected[idx]) {
            __out.push('\n    <td> ');
            __out.push(__sanitize(this.selected[idx]));
            __out.push('/');
            __out.push(__sanitize(this.counts[idx]));
            __out.push(' </td>\n      ');
          } else {
            __out.push('\n    <td> ');
            __out.push(__sanitize(this.counts[idx]));
            __out.push(' </td>\n      ');
          }
          __out.push('\n    ');
        }
        __out.push('\n    <td> ');
        __out.push(__sanitize(this.index[idx]));
        __out.push(' </td>\n    ');
        _ref2 = this.columns;
        for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
          column = _ref2[_k];
          __out.push('\n    <td> ');
          __out.push(__sanitize(datapoint[column]));
          __out.push(' </td>\n    ');
        }
        __out.push('\n  </tr>\n  ');
      }
    
      __out.push('\n</table>\n');
    
    }).call(this);
    
  }).call(__obj);
  __obj.safe = __objSafe, __obj.escape = __escape;
  return __out.join('');
}}, "mapper": function(exports, require, module) {(function() {
  var Collections, DiscreteColorMapper, DiscreteColorMappers, HasParent, HasProperties, LinearMapper, base, safebind,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  base = require("./base");

  Collections = base.Collections;

  safebind = base.safebind;

  HasParent = base.HasParent;

  HasProperties = base.HasProperties;

  LinearMapper = (function(_super) {

    __extends(LinearMapper, _super);

    function LinearMapper() {
      return LinearMapper.__super__.constructor.apply(this, arguments);
    }

    LinearMapper.prototype.initialize = function(attrs, options) {
      LinearMapper.__super__.initialize.call(this, attrs, options);
      this.data_range = options.data_range;
      this.viewstate = options.viewstate;
      this.screendim = options.screendim;
      this.register_property('scalestate', this._get_scale, true);
      this.add_dependencies('scalestate', this.viewstate, this.screendim);
      return this.add_dependencies('scalestate', this.data_range, ['start', 'end']);
    };

    LinearMapper.prototype._get_scale = function() {
      var offset, scale_factor, screendim;
      screendim = this.viewstate.get(this.screendim);
      scale_factor = this.viewstate.get(this.screendim);
      scale_factor = scale_factor / (this.data_range.get('end') - this.data_range.get('start'));
      offset = -(scale_factor * this.data_range.get('start'));
      return [scale_factor, offset];
    };

    LinearMapper.prototype.v_map_screen = function(datav) {
      var data, idx, offset, scale_factor, _i, _len, _ref;
      _ref = this.get('scalestate'), scale_factor = _ref[0], offset = _ref[1];
      for (idx = _i = 0, _len = datav.length; _i < _len; idx = ++_i) {
        data = datav[idx];
        datav[idx] = scale_factor * data + offset;
      }
      return datav;
    };

    LinearMapper.prototype.map_screen = function(data) {
      var offset, scale_factor, _ref;
      _ref = this.get('scalestate'), scale_factor = _ref[0], offset = _ref[1];
      return scale_factor * data + offset;
    };

    LinearMapper.prototype.map_data = function(screen) {
      var offset, scale_factor, _ref;
      _ref = this.get('scalestate'), scale_factor = _ref[0], offset = _ref[1];
      return (screen - offset) / scale_factor;
    };

    return LinearMapper;

  })(HasParent);

  DiscreteColorMapper = (function(_super) {

    __extends(DiscreteColorMapper, _super);

    function DiscreteColorMapper() {
      this._get_scale = __bind(this._get_scale, this);

      this._get_factor_map = __bind(this._get_factor_map, this);
      return DiscreteColorMapper.__super__.constructor.apply(this, arguments);
    }

    DiscreteColorMapper.prototype.type = 'DiscreteColorMapper';

    DiscreteColorMapper.prototype._get_factor_map = function() {
      var domain_map, index, val, _i, _len, _ref;
      domain_map = {};
      _ref = this.get_obj('data_range').get('values');
      for (index = _i = 0, _len = _ref.length; _i < _len; index = ++_i) {
        val = _ref[index];
        domain_map[val] = index;
      }
      return domain_map;
    };

    DiscreteColorMapper.prototype._get_scale = function() {
      return d3.scale.ordinal().domain(_.values(this.get('factor_map'))).range(this.get('colors'));
    };

    DiscreteColorMapper.prototype.dinitialize = function(attrs, options) {
      DiscreteColorMapper.__super__.dinitialize.call(this, attrs, options);
      this.register_property('factor_map', this._get_factor_map, true);
      this.add_dependencies('factor_map', this, 'data_range');
      this.register_property('scale', this._get_scale, true);
      return this.add_dependencies('scale', this, ['colors', 'factor_map']);
    };

    DiscreteColorMapper.prototype.map_screen = function(data) {
      return this.get('scale')(this.get('factor_map')[data]);
    };

    return DiscreteColorMapper;

  })(HasProperties);

  DiscreteColorMapper.prototype.defaults = _.clone(DiscreteColorMapper.prototype.defaults);

  _.extend(DiscreteColorMapper.prototype.defaults, {
    colors: ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7", "#bcbd22", "#dbdb8d", "#17becf", "#9edae5"],
    data_range: null
  });

  DiscreteColorMappers = (function(_super) {

    __extends(DiscreteColorMappers, _super);

    function DiscreteColorMappers() {
      return DiscreteColorMappers.__super__.constructor.apply(this, arguments);
    }

    DiscreteColorMappers.prototype.model = DiscreteColorMapper;

    return DiscreteColorMappers;

  })(Backbone.Collection);

  exports.discretecolormappers = new DiscreteColorMappers;

  exports.LinearMapper = LinearMapper;

  exports.DiscreteColorMapper = DiscreteColorMapper;

}).call(this);
}
});

