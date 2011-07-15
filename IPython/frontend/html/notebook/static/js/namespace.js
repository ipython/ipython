var IPython = IPython || {};

IPython.namespace = function (ns_string) {
    var parts = ns_string.split('.'),
        parent = IPython,
        i;

    // String redundant leading global
    if (parts[0] === "IPython") {
        parts = parts.slice(1);
    }

    for (i=0; i<parts.length; i+=1) {
        // Create property if it doesn't exist
        if (typeof parent[parts[i]] === "undefined") {
            parent[parts[i]] == {};
        }
    }
    return parent;
};



