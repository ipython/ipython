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
    _kernel_client = None
    _kernel_manager = None

    @property
    def kernel_client(self):
        """Returns the current kernel client."""
        return self._kernel_client

    @kernel_client.setter
    def kernel_client(self, kernel_client):
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
        # hb_channel
        kernel_client.hb_channel.kernel_died.connect(self._handle_kernel_died)

        # Handle the case where the kernel client started channels before
        # we connected.
        if kernel_client.channels_running:
            self._started_channels()

    @property
    def kernel_manager(self):
        """The kernel manager, if any"""
        return self._kernel_manager

    @kernel_manager.setter
    def kernel_manager(self, kernel_manager):
        old_man = self._kernel_manager
        if old_man is not None:
            old_man.kernel_restarted.disconnect(self._handle_kernel_restarted)

        self._kernel_manager = kernel_manager
        if kernel_manager is None:
            return

        kernel_manager.kernel_restarted.connect(self._handle_kernel_restarted)

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_kernel_died(self, since_last_heartbeat):
        """ This is called when the ``kernel_died`` signal is emitted.

        This method is called when the kernel heartbeat has not been
        active for a certain amount of time.
        This is a strictly passive notification -
        the kernel is likely being restarted by its KernelManager.

        Parameters
        ----------
        since_last_heartbeat : float
            The time since the heartbeat was last received.
        """

    def _handle_kernel_restarted(self):
        """ This is called when the ``kernel_restarted`` signal is emitted.

        This method is called when the kernel has been restarted by the
        autorestart mechanism.

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
    
    def from_here(self, msg):
        """Return whether a message is from this session"""
        session_id = self._kernel_client.session.session
        return msg['parent_header'].get("session", session_id) == session_id
    
    def include_output(self, msg):
        """Return whether we should include a given output message"""
        if self._hidden:
            return False
        from_here = self.from_here(msg)
        if msg['msg_type'] == 'execute_input':
            # only echo inputs not from here
            return self.include_other_output and not from_here
        
        if self.include_other_output:
            return True
        else:
            return from_here
    
