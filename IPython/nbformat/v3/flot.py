import IPython.core.display
import string
import json

class plot():
    '''
    This class contains methods for using the javascript plotting backend flot
    to plot in an ipython notebook. the number of pixels can be set using the
    pixelsx and pixelsy atttributes and the legend location can be set using 
    the legendloc attribute.
    possible legendloc values : 'ne', 'nw', 'se', 'sw'
    '''
    nplots = 0
    pixelsx = 600
    pixelsy = 300
    legendloc = "ne" 
    
    def readdata(self,data,data1,label):
        #This function takes the python data and encodes it into JSON data
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
        '''
        This method plots the inputs data and data1 based on the following
        rules. If only data exists each array in that input field will be
        plotted with the x-axis having interger values. If data exists
        in both data and data1 it will be assumed to be of the format:
        [x0,x1,x2...]
        [y0,y1,y2...]
        where xn and yn are either numerical values of arrays of values.
        the label is assumed to be a string if there is only one input set
        or an array of strings equal in length to the number of arrays in
        data.
        '''
        if data is not None and len(data) > 0:      
            d, label = self.readdata(data,data1,label)                            
            src = d + """
            var options = {
            selection: { mode: "xy" },
            legend: { position:\"""" + self.legendloc + """\"},
            };
            $.plot($("#placeholder""" + str(self.nplots) + """"), [ """ + label + """],options);
            """
        else:
            print "No data given to plot"
            return
        self.insertplaceholder()
        self.nplots = self.nplots + 1
        IPython.core.display.display_javascript(IPython.core.display.Javascript(data=src))

    def insertplaceholder(self):
        #This function inserts the html tag for the plot
        src = """
        <div id="placeholder""" + str(self.nplots) + """"" style="width:
        """ + str(self.pixelsx) + """px;height:""" + str(self.pixelsy) + """px;"></div>
        """
        IPython.core.display.display_html(IPython.core.display.HTML(data=src))


