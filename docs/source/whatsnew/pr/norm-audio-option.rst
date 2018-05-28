Added 'norm' keyword argument to Audio object.
Default of norm=True preserves prior behavior of normalizing (rescaling;
expanding or compressing) audio to max scale.
Calling Audio() with norm=False will disable this normalization.  It will clip 
the (float) audio signal between -1 and 1 first, to avoid generating runtime
errors.

  - ``IPython.display.Audio``
