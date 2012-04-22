import IPython.core.display
import string
import json

class plot():
    nplots = 0
    pixelsx = 600
    pixelsy = 300
    
    def readdata(self,data,data1,label):
        d = ""
        labelstring = ""
        encoder = json.JSONEncoder()
        if data is not None:
            if type(data[0]) == list or ('numpy' in str(type(data[0])) and data[0].shape != () ):           
                n = len(data)
                for index,item in enumerate(data):
                    d += "var d"+str(index)+" ="+ encoder.encode(zip(item,data1[index])) +";\n"                 
                    if label is not None and type(label) == list:
                        labelstring += "{ label:\"" +label[index] + "\", data:d" + str(index) + " },"
                    else:
                        labelstring += "{ data:d" + str(index) + " },"
                labelstring = string.rstrip(labelstring,",")
            else:
                datastring = "var d1 = "
                if data1 is not None:
                    datastring += encoder.encode(zip(data,data1)) +";"
                else:
                    datastring += encoder.encode(zip(data,range(len(data)))) +";"
                
                if label is not None and type(label) == str:
                    labelstring = "{ label : \"" + label + "\"," + "data:d1}"
                else:
                    labelstring = "{data:d1}"
                d = datastring

        return d, labelstring
            
    def flotplot(self,data=None,data1=None,label = None):
        if data is not None and len(data) > 0:      
            d, label = self.readdata(data,data1,label)                            
            src = d + """
            var options = {
            selection: { mode: "xy" },
            };
            $.plot($("#placeholder""" + str(self.nplots) + """"), [ """ + label + """],options);
            """
            print src
        else:
            print "No data given to plot"
            return
        self.insertplaceholder()
        self.nplots = self.nplots + 1
        IPython.core.display.display_javascript(IPython.core.display.Javascript(data=src))

    def insertplaceholder(self):
        src = """
        <div id="placeholder""" + str(self.nplots) + """"" style="width:
        """ + str(self.pixelsx) + """px;height:""" + str(self.pixelsy) + """px;"></div>
        """
        IPython.core.display.display_html(IPython.core.display.HTML(data=src))


