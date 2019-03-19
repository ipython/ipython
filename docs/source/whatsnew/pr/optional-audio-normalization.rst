Make audio normalization optional
=================================

Added 'normalize' argument to `IPython.display.Audio`. This argument applies
when audio data is given as an array of samples. The default of `normalize=True`
preserves prior behavior of normalizing the audio to the maximum possible range.
Setting to `False` disables normalization.