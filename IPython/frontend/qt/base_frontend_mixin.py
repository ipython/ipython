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
            old_manager.xreq_channel.message_received.disconnect(self._dispatch)
            old_manager.rep_channel.message_received.connect(self._dispatch)

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
        kernel_manager.xreq_channel.message_received.connect(self._dispatch)
        kernel_manager.rep_channel.message_received.connect(self._dispatch)
        
        # Handle the case where the kernel manager started channels before
        # we connected.
        if kernel_manager.channels_running:
            self._started_channels()

    kernel_manager = property(_get_kernel_manager, _set_kernel_manager)

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------
    
    def _started_channels(self):
        """ Called when the KernelManager channels have started listening or 
            when the frontend is assigned an already listening KernelManager.
        """

    def _stopped_channels(self):
        """ Called when the KernelManager channels have stopped listening or
            when a listening KernelManager is removed from the frontend.
        """

    #---------------------------------------------------------------------------
    # Private interface
    #---------------------------------------------------------------------------

    def _dispatch(self, msg):
        """ Call the frontend handler associated with
        """
        msg_type = msg['msg_type']
        handler = getattr(self, '_handle_' + msg_type, None)
        if handler:
            handler(msg)
