casper.notebook_test(function () {
    var input = [
        "\033[0m[\033[0minfo\033[0m] \033[0mtext\033[0m",
        "\033[0m[\033[33mwarn\033[0m] \033[0m\tmore text\033[0m",
        "\033[0m[\033[33mwarn\033[0m] \033[0m  https://some/url/to/a/file.ext\033[0m",
        "\033[0m[\033[31merror\033[0m] \033[0m\033[0m",
        "\033[0m[\033[31merror\033[0m] \033[0m\teven more text\033[0m",
        "\033[0m[\033[31merror\033[0m] \033[0m\t\tand more more text\033[0m"].join("\n");

    var output = [
        "[info] text",
        "[<span  class=\"ansiyellow\">warn</span>] \tmore text",
        "[<span  class=\"ansiyellow\">warn</span>]   https://some/url/to/a/file.ext",
        "[<span  class=\"ansired\">error</span>] ",
        "[<span  class=\"ansired\">error</span>] \teven more text",
        "[<span  class=\"ansired\">error</span>] \t\tand more more text"].join("\n");

    var result = this.evaluate(function (input) {
        return IPython.utils.fixConsole(input);
    }, input);

    this.test.assertEquals(result, output, "IPython.utils.fixConsole() handles [0m correctly");
});
