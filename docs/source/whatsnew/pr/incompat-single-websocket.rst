* The notebook now uses a single websocket at `/kernels/<kernel-id>/channels` instead of separate
  `/kernels/<kernel-id>/{shell|iopub|stdin}` channels. Messages on each channel are identified by a
  `channel` key in the message dict, for both send and recv.
