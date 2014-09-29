({
  baseUrl: 'static',
  generateSourceMaps: true,
  paths: {
    underscore : 'components/underscore/underscore-min',
    backbone : 'components/backbone/backbone-min',
    jquery: 'components/jquery/jquery.min',
    bootstrap: 'components/bootstrap/js/bootstrap.min',
    bootstraptour: 'components/bootstrap-tour/build/js/bootstrap-tour.min',
    dateformat: 'dateformat/date.format',
    jqueryui: 'components/jquery-ui/ui/minified/jquery-ui.min',
    highlight: 'components/highlight.js/build/highlight.pack',
    moment: "components/moment/moment",
  },
  shim: {
    underscore: {
      exports: '_'
    },
    backbone: {
      deps: ["underscore", "jquery"],
      exports: "Backbone"
    },
    bootstrap: {
      deps: ["jquery"],
      exports: "bootstrap"
    },
    bootstraptour: {
      deps: ["bootstrap"],
      exports: "Tour"
    },
    dateformat: {
      exports: "dateFormat"
    },
    jqueryui: {
      deps: ["jquery"],
      exports: "$"
    },
    highlight: {
      exports: "hljs"
    },
  },
    
  exclude: [
  "custom/custom",
  ],
  optimize: "none",
})