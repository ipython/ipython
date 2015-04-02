* The :magic:`matplotlib` magic can now act as a cell magic, in which case, the
  matplotlib backend is reverted back to its previous value after the execution
  of the cell. If matplotlib interactive support was not active, the choosen
  backend remains active.
