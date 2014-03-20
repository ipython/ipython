

var normalized_shortcuts = [
    'ctrl-shift-m',
    'alt-meta-p',
];

var to_normalize = [
    ['shift-%', 'shift-5'],
    ['ShiFT-MeTa-CtRl-AlT-m', 'alt-ctrl-meta-shift-m'],
];

var unshifted = "` 1 2 3 4 5 6 7 8 9 0 - = q w e r t y u i o p [ ] \\ a s d f g h j k l ; ' z x c v b n m , . /";
//  shifted   = '~ ! @ # $ % ^ & * ( ) _ + Q W E R T Y U I O P { } |  A S D F G H J K L : " Z X C V B N M < > ?';

casper.notebook_test(function () {

    this.then(function () {
        this.each(unshifted.split(' '), function (self, item) {
            var result = this.evaluate(function (sc) {
                var e = IPython.keyboard.shortcut_to_event(sc);
                var sc2 = IPython.keyboard.event_to_shortcut(e);
                return sc2;
            }, item);
            this.test.assertEquals(result, item, 'Shortcut to event roundtrip: '+item);
        });
    });

    this.then(function () {
        this.each(to_normalize, function (self, item) {
            var result = this.evaluate(function (pair) {
                return IPython.keyboard.normalize_shortcut(pair[0]);
            }, item);
            this.test.assertEquals(result, item[1], 'Normalize shortcut: '+item[0]);
        });
    });

    this.then(function () {
        this.each(normalized_shortcuts, function (self, item) {
            var result = this.evaluate(function (sc) {
                var e = IPython.keyboard.shortcut_to_event(sc);
                var sc2 = IPython.keyboard.event_to_shortcut(e);
                return sc2;
            }, item);
            this.test.assertEquals(result, item, 'Shortcut to event roundtrip: '+item);
        });
    });

});
