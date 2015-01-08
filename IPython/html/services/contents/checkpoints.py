"""
Classes for managing Checkpoints.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.config.configurable import LoggingConfigurable


class CheckpointManager(LoggingConfigurable):
    """
    Base class for managing checkpoints for a ContentsManager.

    Subclasses are required to implement:

    create_checkpoint(self, contents_mgr, path)
    restore_checkpoint(self, contents_mgr, checkpoint_id, path)
    rename_checkpoint(self, checkpoint_id, old_path, new_path)
    delete_checkpoint(self, checkpoint_id, path)
    list_checkpoints(self, path)
    """
    def create_checkpoint(self, contents_mgr, path):
        """Create a checkpoint."""
        raise NotImplementedError("must be implemented in a subclass")

    def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
        """Restore a checkpoint"""
        raise NotImplementedError("must be implemented in a subclass")

    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
        """Rename a single checkpoint from old_path to new_path."""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, checkpoint_id, path):
        """delete a checkpoint for a file"""
        raise NotImplementedError("must be implemented in a subclass")

    def list_checkpoints(self, path):
        """Return a list of checkpoints for a given file"""
        raise NotImplementedError("must be implemented in a subclass")

    def rename_all_checkpoints(self, old_path, new_path):
        """Rename all checkpoints for old_path to new_path."""
        for cp in self.list_checkpoints(old_path):
            self.rename_checkpoint(cp['id'], old_path, new_path)

    def delete_all_checkpoints(self, path):
        """Delete all checkpoints for the given path."""
        for checkpoint in self.list_checkpoints(path):
            self.delete_checkpoint(checkpoint['id'], path)


class GenericCheckpointMixin(object):
    """
    Helper for creating CheckpointManagers that can be used with any
    ContentsManager.

    Provides an implementation of `create_checkpoint` and `restore_checkpoint`
    in terms of the following operations:

    create_file_checkpoint(self, content, format, path)
    create_notebook_checkpoint(self, nb, path)
    get_checkpoint(self, checkpoint_id, path, type)

    **Any** valid CheckpointManager implementation should also be valid when
    this mixin is applied.
    """

    def create_checkpoint(self, contents_mgr, path):
        model = contents_mgr.get(path, content=True)
        type = model['type']
        if type == 'notebook':
            return self.create_notebook_checkpoint(
                model['content'],
                path,
            )
        elif type == 'file':
            return self.create_file_checkpoint(
                model['content'],
                model['format'],
                path,
            )

    def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
        """Restore a checkpoint."""
        type = contents_mgr.get(path, content=False)['type']
        model = self.get_checkpoint(checkpoint_id, path, type)
        contents_mgr.save(model, path)

    # Required Methods
    def create_file_checkpoint(self, content, format, path):
        """Create a checkpoint of the current state of a file

        Returns a checkpoint model for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")

    def create_notebook_checkpoint(self, nb, path):
        """Create a checkpoint of the current state of a file

        Returns a checkpoint model for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")

    def get_checkpoint(self, checkpoint_id, path, type):
        """Get the content of a checkpoint.

        Returns an unvalidated model with the same structure as
        the return value of ContentsManager.get
        """
        raise NotImplementedError("must be implemented in a subclass")
