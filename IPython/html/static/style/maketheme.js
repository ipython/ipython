#!/usr/bin/env node


var cliArgs = require("command-line-args");

/* define the command-line options */
var cli = cliArgs([
    { name: "help", type: Boolean, description: "Print usage instructions", alias: 'h', defaultOption:false},
    { name: "in", type: String, description: "The input files basename (no .less)", defaultOption:false},
    { name: "watch", type: Boolean, description: "watch for chenges in the mail less.file", defaultOption:false },
    { name: "out", type: String,  description: "The output files", defaultOption:false }
]);

/* parse the supplied command-line values */
var options = cli.parse();

if(options.help || !Object.getOwnPropertyNames(options).length){
    var usage = cli.getUsage({
        header: "Compile IPython theme",
        footer: "\n  Example:\n\n"+
                "\tmaketheme.js --in style --out style.min.css\n"+
                "\tmaketheme.js --in my_varaibles --out custom.css"
    });

    console.log(usage);
} else {
    options.in = options.in || 'custom';
    options.out = options.out || 'style.min.css';
    var mapfile = options.out+'.map'

    var less = require('less')
    var fs = require('fs');
     
    var fullimport = "@import '"+__dirname+"/style' ; @import '"+options.in+"';";

    options.sourceMap = {// sourceMapFullFilename: 'style/style.min.css.map',
         sourceMapBasepath: __dirname+'/..', 
         sourceMapRootpath: '../',
         sourceMapInputFilename: __dirname+'/style.less',
         sourceMapOutputFilename: options.out,
         sourceMapFilename: mapfile,
         sourceMapFileInline: false 
    }

    var render = function(){
        console.log('compiling', options.in+'.less' , 'to', options.out )
        less.render(fullimport, options)
            .then(function(output) {
                console.log('writing',options.out)
                fs.writeFile(options.out, output.css, function(err) {
                    if(err) {
                        console.log('got err',err);
                    }
                }); 
                console.log('writing .map file:', mapfile);
                fs.writeFile(mapfile, output.map, function(err) {
                    if(err) {
                        console.log(err);
                    }
                }); 
            },
            function(error) {
                console.log(error)
            });
    }

    if(options.watch){
        console.log('watching over', options.in+'.less')
        fs.watchFile(options.in+'.less', render)
    } else {
        render()
    }
}
