/*
 * Auto Grow Textarea Plugin
 * by Jevin 5/11/2010
 * http://www.technoreply.com/autogrow-textarea-plugin/
 *
 * Modified by Rob G (aka Fudgey/Mottie)
 *  - Converted into a plugin
 *  - Added ability to calculate approximate # cols when textarea is set to 100%
 */

(function($){
 // if "full" is true, auto adjust textarea cols
 $.fn.autoGrow = function(full){

  // resize textarea
  var grow = function(d){
   var linesCount = 0,
       // modified split rule from
       // http://stackoverflow.com/questions/2035910/how-to-get-the-number-of-lines-in-a-textarea/2036424#2036424
       lines = d.txt.value.split(/\r|\r\n|\n/);
   for (var i = lines.length-1; i>=0; --i){
    linesCount += Math.round((lines[i].length / d.colsDefault) + 1);
   }
   if (linesCount >= d.rowsDefault) {
    d.txt.rows = linesCount + 1; // added one more here because of IE
   } else {
    d.txt.rows = d.rowsDefault;
   }
  };

  // Calculate # of columns from width of textarea
  // this is a very rough approximation; set textarea CSS width to 100% to maintain full size
  var setColsWidth = function(d){
   var pWidth = d.$txt.parent().innerWidth();
   // if char width not set, add window resize events
   if (d.charWidth === 0){
    $(window).resize(function(){
     setColsWidth(d);
     grow(d);
    });
    // assume charwidth is roughly 1/2 font-size (on average)
    d.charWidth = parseInt(d.$txt.css('font-size'),10)/2; 
   }
   var cols = Math.round(pWidth / d.charWidth); // calculate number of columns
   d.colsDefault = cols;
   d.$txt.attr('cols', cols );
  };

  // set default textarea size
  var setDefaultValues = function(d){
   // call cols-adjusting script if $("textarea").autoGrow(true);
   if (full && d.charWidth === 0) { setColsWidth(d); }
   d.colsDefault = d.txt.cols;
   d.rowsDefault = d.txt.rows;
  };
  
  return this.each(function(){
   // defaults
   var d = {
    colsDefault : 0,
    rowsDefault : 0,
    charWidth   : 0,
    txt         : this,
    $txt        : $(this)
   };
   // bind keyup
   d.txt.onkeyup = function(){
    grow(d);
   };
   setDefaultValues(d);
   grow(d);
  });

 };
})(jQuery);