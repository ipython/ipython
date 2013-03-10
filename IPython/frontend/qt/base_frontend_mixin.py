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

    def _get_kernel_client(self):
        """Returns the current kernel client.
        """
        return self._kernel_client

    def _set_kernel_client(self, kernel_client):
        """Disconnect from the current kernel client (if any) and set a new
            kernel client.
        """
        # Disconnect the old kernel client, if necessary.
        old_client = self._kernel_client
        if old_client is not None:
            old_client.started_channels.disconnect(self._started_channels)
            old_client.stopped_channels.disconnect(self._stopped_channels)

            # Disconnect the old kernel client's channels.
            old_client.iopub_channel.message_received.disconnect(self._dispatch)
            old_client.shell_channel.message_received.disconnect(self._dispatch)
            old_client.stdin_channel.message_received.disconnect(self._dispatch)
            old_client.hb_channel.kernel_died.disconnect(
                self._handle_kernel_died)

            # Handle the case where the old kernel client is still listening.
            if old_client.channels_running:
                self._stopped_channels()

        # Set the new kernel client.
        self._kernel_client = kernel_client
        if kernel_client is None:
            return

        # Connect the new kernel client.
        kernel_client.started_channels.connect(self._started_channels)
        kernel_client.stopped_channels.connect(self._stopped_channels)

        # Connect the new kernel client's channels.
        kernel_client.iopub_channel.message_received.connect(self._dispatch)
        kernel_client.shell_channel.message_received.connect(self._dispatch)
        kernel_client.stdin_channel.message_received.connect(self._dispatch)
        kernel_client.hb_channel.kernel_died.connect(self._handle_kernel_died)

        # Handle the case where the kernel client started channels before
        # we connected.
        if kernel_client.channels_running:
            self._started_channels()

    kernel_client = property(_get_kernel_client, _set_kernel_client)

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

    def _started_kernel(self):
        """Called when the KernelManager starts (or restarts) the kernel subprocess.
        Channels may or may not be running at this point.
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
        session = self._kernel_client.session.session
        parent = msg['parent_header']
        if not parent:
            # if the message has no parent, assume it is meant for all frontends
            return True
        else:
            return parent.get('session') == session
