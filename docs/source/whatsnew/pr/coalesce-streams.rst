- Consecutive stream (stdout/stderr) output is merged into a single output
  in the notebook document.
  Previously, all output messages were preserved as separate output fields in the JSON.
  Now, the same merge is applied to the stored output as the displayed output,
  improving document load time for notebooks with many small outputs.
