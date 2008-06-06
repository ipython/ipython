/***

MochiKit.LoggingPane 1.4

See <http://mochikit.com/> for documentation, downloads, license, etc.

(c) 2005 Bob Ippolito.  All rights Reserved.

***/

if (typeof(dojo) != 'undefined') {
    dojo.provide('MochiKit.LoggingPane');
    dojo.require('MochiKit.Logging');
    dojo.require('MochiKit.Base');
}

if (typeof(JSAN) != 'undefined') {
    JSAN.use("MochiKit.Logging", []);
    JSAN.use("MochiKit.Base", []);
}

try {
    if (typeof(MochiKit.Base) == 'undefined' || typeof(MochiKit.Logging) == 'undefined') {
        throw "";
    }
} catch (e) {
    throw "MochiKit.LoggingPane depends on MochiKit.Base and MochiKit.Logging!";
}

if (typeof(MochiKit.LoggingPane) == 'undefined') {
    MochiKit.LoggingPane = {};
}

MochiKit.LoggingPane.NAME = "MochiKit.LoggingPane";
MochiKit.LoggingPane.VERSION = "1.4";
MochiKit.LoggingPane.__repr__ = function () {
    return "[" + this.NAME + " " + this.VERSION + "]";
};

MochiKit.LoggingPane.toString = function () {
    return this.__repr__();
};

/** @id MochiKit.LoggingPane.createLoggingPane */
MochiKit.LoggingPane.createLoggingPane = function (inline/* = false */) {
    var m = MochiKit.LoggingPane;
    inline = !(!inline);
    if (m._loggingPane && m._loggingPane.inline != inline) {
        m._loggingPane.closePane();
        m._loggingPane = null;
    }
    if (!m._loggingPane || m._loggingPane.closed) {
        m._loggingPane = new m.LoggingPane(inline, MochiKit.Logging.logger);
    }
    return m._loggingPane;
};

/** @id MochiKit.LoggingPane.LoggingPane */
MochiKit.LoggingPane.LoggingPane = function (inline/* = false */, logger/* = MochiKit.Logging.logger */) {

    /* Use a div if inline, pop up a window if not */
    /* Create the elements */
    if (typeof(logger) == "undefined" || logger === null) {
        logger = MochiKit.Logging.logger;
    }
    this.logger = logger;
    var update = MochiKit.Base.update;
    var updatetree = MochiKit.Base.updatetree;
    var bind = MochiKit.Base.bind;
    var clone = MochiKit.Base.clone;
    var win = window;
    var uid = "_MochiKit_LoggingPane";
    if (typeof(MochiKit.DOM) != "undefined") {
        win = MochiKit.DOM.currentWindow();
    }
    if (!inline) {
        // name the popup with the base URL for uniqueness
        var url = win.location.href.split("?")[0].replace(/[#:\/.><&-]/g, "_");
        var name = uid + "_" + url;
        var nwin = win.open("", name, "dependent,resizable,height=200");
        if (!nwin) {
            alert("Not able to open debugging window due to pop-up blocking.");
            return undefined;
        }
        nwin.document.write(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" '
            + '"http://www.w3.org/TR/html4/loose.dtd">'
            + '<html><head><title>[MochiKit.LoggingPane]</title></head>'
            + '<body></body></html>'
        );
        nwin.document.close();
        nwin.document.title += ' ' + win.document.title;
        win = nwin;
    }
    var doc = win.document;
    this.doc = doc;

    // Connect to the debug pane if it already exists (i.e. in a window orphaned by the page being refreshed)
    var debugPane = doc.getElementById(uid);
    var existing_pane = !!debugPane;
    if (debugPane && typeof(debugPane.loggingPane) != "undefined") {
        debugPane.loggingPane.logger = this.logger;
        debugPane.loggingPane.buildAndApplyFilter();
        return debugPane.loggingPane;
    }

    if (existing_pane) {
        // clear any existing contents
        var child;
        while ((child = debugPane.firstChild)) {
            debugPane.removeChild(child);
        }
    } else {
        debugPane = doc.createElement("div");
        debugPane.id = uid;
    }
    debugPane.loggingPane = this;
    var levelFilterField = doc.createElement("input");
    var infoFilterField = doc.createElement("input");
    var filterButton = doc.createElement("button");
    var loadButton = doc.createElement("button");
    var clearButton = doc.createElement("button");
    var closeButton = doc.createElement("button");
    var logPaneArea = doc.createElement("div");
    var logPane = doc.createElement("div");

    /* Set up the functions */
    var listenerId = uid + "_Listener";
    this.colorTable = clone(this.colorTable);
    var messages = [];
    var messageFilter = null;

    /** @id MochiKit.LoggingPane.messageLevel */
    var messageLevel = function (msg) {
        var level = msg.level;
        if (typeof(level) == "number") {
            level = MochiKit.Logging.LogLevel[level];
        }
        return level;
    };

    /** @id MochiKit.LoggingPane.messageText */
    var messageText = function (msg) {
        return msg.info.join(" ");
    };

    /** @id MochiKit.LoggingPane.addMessageText */
    var addMessageText = bind(function (msg) {
        var level = messageLevel(msg);
        var text = messageText(msg);
        var c = this.colorTable[level];
        var p = doc.createElement("span");
        p.className = "MochiKit-LogMessage MochiKit-LogLevel-" + level;
        p.style.cssText = "margin: 0px; white-space: -moz-pre-wrap; white-space: -o-pre-wrap; white-space: pre-wrap; white-space: pre-line; word-wrap: break-word; wrap-option: emergency; color: " + c;
        p.appendChild(doc.createTextNode(level + ": " + text));
        logPane.appendChild(p);
        logPane.appendChild(doc.createElement("br"));
        if (logPaneArea.offsetHeight > logPaneArea.scrollHeight) {
            logPaneArea.scrollTop = 0;
        } else {
            logPaneArea.scrollTop = logPaneArea.scrollHeight;
        }
    }, this);

    /** @id MochiKit.LoggingPane.addMessage */
    var addMessage = function (msg) {
        messages[messages.length] = msg;
        addMessageText(msg);
    };

    /** @id MochiKit.LoggingPane.buildMessageFilter */
    var buildMessageFilter = function () {
        var levelre, infore;
        try {
            /* Catch any exceptions that might arise due to invalid regexes */
            levelre = new RegExp(levelFilterField.value);
            infore = new RegExp(infoFilterField.value);
        } catch(e) {
            /* If there was an error with the regexes, do no filtering */
            logDebug("Error in filter regex: " + e.message);
            return null;
        }

        return function (msg) {
            return (
                levelre.test(messageLevel(msg)) &&
                infore.test(messageText(msg))
            );
        };
    };

    /** @id MochiKit.LoggingPane.clearMessagePane */
    var clearMessagePane = function () {
        while (logPane.firstChild) {
            logPane.removeChild(logPane.firstChild);
        }
    };

    /** @id MochiKit.LoggingPane.clearMessages */
    var clearMessages = function () {
        messages = [];
        clearMessagePane();
    };

    /** @id MochiKit.LoggingPane.closePane */
    var closePane = bind(function () {
        if (this.closed) {
            return;
        }
        this.closed = true;
        if (MochiKit.LoggingPane._loggingPane == this) {
            MochiKit.LoggingPane._loggingPane = null;
        }
        this.logger.removeListener(listenerId);
        try {
            try {
              debugPane.loggingPane = null;
            } catch(e) { logFatal("Bookmarklet was closed incorrectly."); }
            if (inline) {
                debugPane.parentNode.removeChild(debugPane);
            } else {
                this.win.close();
            }
        } catch(e) {}
    }, this);

    /** @id MochiKit.LoggingPane.filterMessages */
    var filterMessages = function () {
        clearMessagePane();

        for (var i = 0; i < messages.length; i++) {
            var msg = messages[i];
            if (messageFilter === null || messageFilter(msg)) {
                addMessageText(msg);
            }
        }
    };

    this.buildAndApplyFilter = function () {
        messageFilter = buildMessageFilter();

        filterMessages();

        this.logger.removeListener(listenerId);
        this.logger.addListener(listenerId, messageFilter, addMessage);
    };


    /** @id MochiKit.LoggingPane.loadMessages */
    var loadMessages = bind(function () {
        messages = this.logger.getMessages();
        filterMessages();
    }, this);

    /** @id MochiKit.LoggingPane.filterOnEnter */
    var filterOnEnter = bind(function (event) {
        event = event || window.event;
        key = event.which || event.keyCode;
        if (key == 13) {
            this.buildAndApplyFilter();
        }
    }, this);

    /* Create the debug pane */
    var style = "display: block; z-index: 1000; left: 0px; bottom: 0px; position: fixed; width: 100%; background-color: white; font: " + this.logFont;
    if (inline) {
        style += "; height: 10em; border-top: 2px solid black";
    } else {
        style += "; height: 100%;";
    }
    debugPane.style.cssText = style;

    if (!existing_pane) {
        doc.body.appendChild(debugPane);
    }

    /* Create the filter fields */
    style = {"cssText": "width: 33%; display: inline; font: " + this.logFont};

    updatetree(levelFilterField, {
        "value": "FATAL|ERROR|WARNING|INFO|DEBUG",
        "onkeypress": filterOnEnter,
        "style": style
    });
    debugPane.appendChild(levelFilterField);

    updatetree(infoFilterField, {
        "value": ".*",
        "onkeypress": filterOnEnter,
        "style": style
    });
    debugPane.appendChild(infoFilterField);

    /* Create the buttons */
    style = "width: 8%; display:inline; font: " + this.logFont;

    filterButton.appendChild(doc.createTextNode("Filter"));
    filterButton.onclick = bind("buildAndApplyFilter", this);
    filterButton.style.cssText = style;
    debugPane.appendChild(filterButton);

    loadButton.appendChild(doc.createTextNode("Load"));
    loadButton.onclick = loadMessages;
    loadButton.style.cssText = style;
    debugPane.appendChild(loadButton);

    clearButton.appendChild(doc.createTextNode("Clear"));
    clearButton.onclick = clearMessages;
    clearButton.style.cssText = style;
    debugPane.appendChild(clearButton);

    closeButton.appendChild(doc.createTextNode("Close"));
    closeButton.onclick = closePane;
    closeButton.style.cssText = style;
    debugPane.appendChild(closeButton);

    /* Create the logging pane */
    logPaneArea.style.cssText = "overflow: auto; width: 100%";
    logPane.style.cssText = "width: 100%; height: " + (inline ? "8em" : "100%");

    logPaneArea.appendChild(logPane);
    debugPane.appendChild(logPaneArea);

    this.buildAndApplyFilter();
    loadMessages();

    if (inline) {
        this.win = undefined;
    } else {
        this.win = win;
    }
    this.inline = inline;
    this.closePane = closePane;
    this.closed = false;


    return this;
};

MochiKit.LoggingPane.LoggingPane.prototype = {
    "logFont": "8pt Verdana,sans-serif",
    "colorTable": {
        "ERROR": "red",
        "FATAL": "darkred",
        "WARNING": "blue",
        "INFO": "black",
        "DEBUG": "green"
    }
};


MochiKit.LoggingPane.EXPORT_OK = [
    "LoggingPane"
];

MochiKit.LoggingPane.EXPORT = [
    "createLoggingPane"
];

MochiKit.LoggingPane.__new__ = function () {
    this.EXPORT_TAGS = {
        ":common": this.EXPORT,
        ":all": MochiKit.Base.concat(this.EXPORT, this.EXPORT_OK)
    };

    MochiKit.Base.nameFunctions(this);

    MochiKit.LoggingPane._loggingPane = null;

};

MochiKit.LoggingPane.__new__();

MochiKit.Base._exportSymbols(this, MochiKit.LoggingPane);
