import IPython.core.display
import string

class plot():
    nplots = 0
    
    def flotplot(self,data=None,data1=None):
        #print self.nplots
        test = """
            var d1 = [];
            for (var i = 0; i < 14; i += 0.5)
                d1.push([i, Math.sin(i)]);

            var d2 = [[0, 3], [4, 8], [8, 5], [9, 13]];

            // a null signifies separate line segments
            var d3 = [[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]];
    
            $.plot($("#placeholder""" + str(self.nplots) + """"), [ d1, d2, d3 ]);
    
        """
        if data is not None and len(data) > 0:
            datastring = "["
            if data1 is not None:
                for index, item in enumerate(data):
                    datastring += "[" + str(item) + ", " + str(data1[index]) +"]" +", "
                datastring = string.rstrip(datastring,", ") + "];"
            else:
                for index, item in enumerate(data):
                    datastring += "[" + str(index) + ", " + str(item) +"]" +", "
                datastring = string.rstrip(datastring,",") + "];"
            src = "var data = " + datastring + """
            var options = {
            selection: { mode: "xy" },
            };
            $.plot($("#placeholder""" + str(self.nplots) + """"), [ data ],options);
            """
            #print src
        else:
            src = test
        self.insertplaceholder()
        self.nplots = self.nplots + 1
        IPython.core.display.display_javascript(IPython.core.display.Javascript(data=src))

    def insertplaceholder(self):
        src = """
        <div id="placeholder""" + str(self.nplots) + """"" style="width:600px;height:300px;"></div>
        """
        IPython.core.display.display_html(IPython.core.display.HTML(data=src))


