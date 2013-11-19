// Test renaming of notebooks
//

casper.notebook_test(function () {
    this.printLog();
    this.then(function () {
        url = this.evaluate(function() {
            IPython.notebook.rename("foo");
            console.log("hmmm");
            console.log(IPython.notebook.get_notebook_name());
            //$("span#notebook_name")[0].click();
            //$("input")[0].value = "please-work";
            //$(".btn-primary")[0].click();
            //console.log(IPython.notebook.get_notebook_name());
            return document.location.href;
        });

        this.echo("url:" + url);
    });
    this.click("span#notebook_name");
    this.waitForSelector('input', function then() {
        this.echo("input is live");
        this.evaluate(function () {
            $("input")[0].value = "please-work";
            //$(".btn-primary")[0].click();
        });
    });

    this.then(function() {
        this.evaluate(function () {
            console.log('input value:' +  $("input")[0].value);
            console.log(IPython.notebook.get_notebook_name());
        });
    });
    //this.fill('', {'name' : 'hello'});
    this.thenClick(".btn-primary");

    this.waitWhileSelector('input', function then() {
        this.echo("input is no more");
        this.evaluate(function () {
            console.log(IPython.notebook.get_notebook_name());
        });
    });

    this.waitForUrl(/please-work\.ipynb/, function() {
        this.echo("horray") ;
    }, function timeout() {
        this.echo("nope, timedout :\\");

    });

    this.then(function(){
        var nbname = this.evaluate(function (){
            return IPython.notebook.get_notebook_name();
        });
        this.test.assertEquals(nbname, 'please-work');
    
    });

});

