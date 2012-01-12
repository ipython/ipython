//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// On document ready
//============================================================================


$(document).ready(function () {
    if (window.MathJax){ 
        // MathJax loaded
        MathJax.Hub.Config({
            tex2jax: {
                inlineMath: [ ['$','$'], ["\\(","\\)"] ],
                displayMath: [ ['$$','$$'], ["\\[","\\]"] ]
            },
            displayAlign: 'left', // Change this to 'center' to center equations.
            "HTML-CSS": {
                styles: {'.MathJax_Display': {"margin": 0}}
            }
        });
    }else if (window.mathjax_url != ""){
        // Don't have MathJax, but should. Show dialog.
        var dialog = $('<div></div>')
            .append(
                $("<p></p>").addClass('dialog').html(
                    "Math/LaTeX rendering will be disabled."
                )
            ).append(
                $("<p></p>").addClass('dialog').html(
                    "If you have administrative access to the notebook server and" +
                    " a working internet connection, you can install a local copy" +
                    " of MathJax for offline use with the following command on the server" +
                    " at a Python or IPython prompt:"
                )
            ).append(
                $("<pre></pre>").addClass('dialog').html(
                    ">>> from IPython.external import mathjax; mathjax.install_mathjax()"
                )
            ).append(
                $("<p></p>").addClass('dialog').html(
                    "This will try to install MathJax into the IPython source directory."
                )
            ).append(
                $("<p></p>").addClass('dialog').html(
                    "If IPython is installed to a location that requires" +
                    " administrative privileges to write, you will need to make this call as" +
                    " an administrator, via 'sudo'."
                )
            ).append(
                $("<p></p>").addClass('dialog').html(
                    "When you start the notebook server, you can instruct it to disable MathJax support altogether:"
                )
            ).append(
                $("<pre></pre>").addClass('dialog').html(
                    "$ ipython notebook --no-mathjax"
                )
            ).append(
                $("<p></p>").addClass('dialog').html(
                    "which will prevent this dialog from appearing."
                )
            ).dialog({
                title: "Failed to retrieve MathJax from '" + window.mathjax_url + "'",
                width: "70%",
                modal: true,
            })
    }else{
        // No MathJax, but none expected. No dialog.
    }
    
    IPython.markdown_converter = new Markdown.Converter();
    IPython.read_only = $('meta[name=read_only]').attr("content") == 'True';

    $('div#header').addClass('border-box-sizing');
    $('div#main_app').addClass('border-box-sizing ui-widget ui-widget-content');
    $('div#notebook_panel').addClass('border-box-sizing ui-widget');

    IPython.save_widget = new IPython.SaveWidget('span#save_widget');
    IPython.login_widget = new IPython.LoginWidget('span#login_widget');
    IPython.notebook = new IPython.Notebook('div#notebook');

    // These have display: none in the css file and are made visible here to prevent FLOUC.
    $('div#header').css('display','block');
    $('div#main_app').css('display','block');

    // Perform these actions after the notebook has been loaded.
    IPython.notebook.load_notebook(function () {});

});

