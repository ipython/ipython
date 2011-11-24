""" Defines a convenient mix-in class for implementing Qt frontends.
"""

class BaseFrontendMixin(object):
    """ A mix-in class for implementing Qt frontends.

    To handle messages of a particular type, frontends need only define an
    appropriate handler method. For example, to handle 'stream' messaged, define
    a '_handle_stream(msg)' method.
    """

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' concrete interface
    #---------------------------------------------------------------------------

    def _get_kernel_manager(self):
        """ Returns the current kernel manager.
        """
        return self._kernel_manager

    def _set_kernel_manager(self, kernel_manager):
        """ Disconnect from the current kernel manager (if any) and set a new
            kernel manager.
        """
        # Disconnect the old kernel manager, if necessary.
        old_manager = self._kernel_manager
        if old_manager is not None:
            old_manager.started_channels.disconnect(self._started_channels)
            old_manager.stopped_channels.disconnect(self._stopped_channels)

            # Disconnect the old kernel manager's channels.
            old_manager.sub_channel.message_received.disconnect(self._dispatch)
            old_manager.shell_channel.message_received.disconnect(self._dispatch)
            old_manager.stdin_channel.message_received.disconnect(self._dispatch)
            old_manager.hb_channel.kernel_died.disconnect(
                self._handle_kernel_died)

            # Handle the case where the old kernel manager is still listening.
            if old_manager.channels_running:
                self._stopped_channels()

        # Set the new kernel manager.
        self._kernel_manager = kernel_manager
        if kernel_manager is None:
            return

        # Connect the new kernel manager.
        kernel_manager.started_channels.connect(self._started_channels)
        kernel_manager.stopped_channels.connect(self._stopped_channels)

        # Connect the new kernel manager's channels.
        kernel_manager.sub_channel.message_received.connect(self._dispatch)
        kernel_manager.shell_channel.message_received.connect(self._dispatch)
        kernel_manager.stdin_channel.message_received.connect(self._dispatch)
        kernel_manager.hb_channel.kernel_died.connect(self._handle_kernel_died)

        # Handle the case where the kernel manager started channels before
        # we connected.
        if kernel_manager.channels_running:
            self._started_channels()

    kernel_manager = property(_get_kernel_manager, _set_kernel_manager)

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_kernel_died(self, since_last_heartbeat):
        """ This is called when the ``kernel_died`` signal is emitted.

        This method is called when the kernel heartbeat has not been
        active for a certain amount of time. The typical action will be to
        give the user the option of restarting the kernel.

        Parameters
        ----------
        since_last_heartbeat : float
            The time since the heartbeat was last received.
        """

    def _started_channels(self):
        """ Called when the KernelManager channels have started listening or
            when the frontend is assigned an already listening KernelManager.
        """

    def _stopped_channels(self):
        """ Called when the KernelManager channels have stopped listening or
            when a listening KernelManager is removed from the frontend.
        """

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' protected interface
    #---------------------------------------------------------------------------

    def _dispatch(self, msg):
        """ Calls the frontend handler associated with the message type of the
            given message.
        """
        msg_type = msg['header']['msg_type']
        handler = getattr(self, '_handle_' + msg_type, None)
        if handler:
            handler(msg)

    def _is_from_this_session(self, msg):
        """ Returns whether a reply from the kernel originated from a request
            from this frontend.
        """
        session = self._kernel_manager.session.session
        parent = msg['parent_header']
        if not parent:
            # if the message has no parent, assume it is meant for all frontends
            return True
        else:
            return parent.get('session') == session
