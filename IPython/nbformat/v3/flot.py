import IPython.core.display
import string

class plot():
    nplots = 0
    pixelsx = 600
    pixelsy = 300
    
    def builddata(self,data,data1):
        datastring = ""
        for index, item in enumerate(data):
            datastring += "[" + str(item) + ", " + str(data1[index]) +"]" +", "
        datastring = string.rstrip(datastring,", ") + "];"
        return datastring

    def readdata(self,data,data1,label):
        d = ""
        labelstring = ""
        if data is not None:
            #print data[0].shape
            if type(data[0]) == list or ('numpy' in str(type(data[0])) and data[0].shape != () ):           
                n = len(data)
                for index,item in enumerate(data):
                    d= d + "var d"+str(index)+" = ["+ self.builddata(item,data1[index])+"\n"
                    if label is not None and type(label) == list:
                        labelstring += "{ label:\"" +label[index] + "\", data:d" + str(index) + " },"
                    else:
                        labelstring += "{ data:d" + str(index) + " },"
                labelstring = string.rstrip(labelstring,",")
            else:
                n = 1
                datastring = "var d1 = ["
                if data1 is not None:
                    for index, item in enumerate(data):
                        datastring += "[" + str(item) + ", " + str(data1[index]) +"]" +", "
                    datastring = string.rstrip(datastring,", ") + "];"
                else:
                    for index, item in enumerate(data):
                        datastring += "[" + str(index) + ", " + str(item) +"]" +", "
                    datastring = string.rstrip(datastring,",") + "];"
                
                if label is not None and type(label) == str:
                    labelstring = "{ label : \"" + label + "\"," + "data:d1}"
                else:
                    labelstring = "{data:d1}"
                d = datastring

        return d, labelstring, n
            
    def flotplot(self,data=None,data1=None,label = None):
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
            '''
            datastring = "["
            if data1 is not None:
                for index, item in enumerate(data):
                    datastring += "[" + str(item) + ", " + str(data1[index]) +"]" +", "
                datastring = string.rstrip(datastring,", ") + "];"
            else:
                for index, item in enumerate(data):
                    datastring += "[" + str(index) + ", " + str(item) +"]" +", "
                datastring = string.rstrip(datastring,",") + "];"
            if label is not None and type(label) == str:
                label = "label : \"" + label + "\","
            else:
                label = ""
            '''
            
            #src = "var data = "+ datastring + """
            d, label, n = self.readdata(data,data1,label)
                            
            src = d + """
            var options = {
            selection: { mode: "xy" },
            };
            $.plot($("#placeholder""" + str(self.nplots) + """"), [ """ + label + """],options);
            """
            #print src
        else:
            src = test
        self.insertplaceholder()
        self.nplots = self.nplots + 1
        IPython.core.display.display_javascript(IPython.core.display.Javascript(data=src))

    def insertplaceholder(self):
        src = """
        <div id="placeholder""" + str(self.nplots) + """"" style="width:
        """ + str(self.pixelsx) + """px;height:""" + str(self.pixelsy) + """px;"></div>
        """
        IPython.core.display.display_html(IPython.core.display.HTML(data=src))


