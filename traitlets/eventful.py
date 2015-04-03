"""Contains eventful dict and list implementations."""

# void function used as a callback placeholder.
def _void(*p, **k): return None

class EventfulDict(dict):
    """Eventful dictionary.

    This class inherits from the Python intrinsic dictionary class, dict.  It
    adds events to the get, set, and del actions and optionally allows you to
    intercept and cancel these actions.  The eventfulness isn't recursive.  In
    other words, if you add a dict as a child, the events of that dict won't be
    listened to.  If you find you need something recursive, listen to the `add`
    and `set` methods, and then cancel `dict` values from being set, and instead
    set EventfulDicts that wrap those dicts.  Then you can wire the events
    to the same handlers if necessary.

    See the on_events, on_add, on_set, and on_del methods for registering
    event handlers."""

    def __init__(self, *args, **kwargs):
        """Public constructor"""
        self._add_callback = _void
        self._del_callback = _void
        self._set_callback = _void
        dict.__init__(self, *args, **kwargs)

    def on_events(self, add_callback=None, set_callback=None, del_callback=None):
        """Register callbacks for add, set, and del actions.

        See the doctstrings for on_(add/set/del) for details about each
        callback.

        add_callback: [callback = None]
        set_callback: [callback = None]
        del_callback: [callback = None]"""
        self.on_add(add_callback)
        self.on_set(set_callback)
        self.on_del(del_callback)

    def on_add(self, callback):
        """Register a callback for when an item is added to the dict.

        Allows the listener to detect when items are added to the dictionary and
        optionally cancel the addition.

        callback: callable or None
            If you want to ignore the addition event, pass None as the callback.
            The callback should have a signature of callback(key, value).  The
            callback should return a boolean True if the additon should be
            canceled, False or None otherwise."""
        self._add_callback = callback if callable(callback) else _void

    def on_del(self, callback):
        """Register a callback for when an item is deleted from the dict.

        Allows the listener to detect when items are deleted from the dictionary
        and optionally cancel the deletion.

        callback: callable or None
            If you want to ignore the deletion event, pass None as the callback.
            The callback should have a signature of callback(key).  The
            callback should return a boolean True if the deletion should be
            canceled, False or None otherwise."""
        self._del_callback = callback if callable(callback) else _void

    def on_set(self, callback):
        """Register a callback for when an item is changed in the dict.

        Allows the listener to detect when items are changed in the dictionary
        and optionally cancel the change.

        callback: callable or None
            If you want to ignore the change event, pass None as the callback.
            The callback should have a signature of callback(key, value).  The
            callback should return a boolean True if the change should be
            canceled, False or None otherwise."""
        self._set_callback = callback if callable(callback) else _void

    def pop(self, key):
        """Returns the value of an item in the dictionary and then deletes the
        item from the dictionary."""
        if self._can_del(key):
            return dict.pop(self, key)
        else:
            raise Exception('Cannot `pop`, deletion of key "{}" failed.'.format(key))

    def popitem(self):
        """Pop the next key/value pair from the dictionary."""
        key = next(iter(self))
        return key, self.pop(key)

    def update(self, other_dict):
        """Copy the key/value pairs from another dictionary into this dictionary,
        overwriting any conflicting keys in this dictionary."""
        for (key, value) in other_dict.items():
            self[key] = value

    def clear(self):
        """Clear the dictionary."""
        for key in list(self.keys()):
            del self[key]

    def __setitem__(self, key, value):
        if (key in self and self._can_set(key, value)) or \
        (key not in self and self._can_add(key, value)):
            return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if self._can_del(key):
            return dict.__delitem__(self, key)

    def _can_add(self, key, value):
        """Check if the item can be added to the dict."""
        return not bool(self._add_callback(key, value))

    def _can_del(self, key):
        """Check if the item can be deleted from the dict."""
        return not bool(self._del_callback(key))

    def _can_set(self, key, value):
        """Check if the item can be changed in the dict."""
        return not bool(self._set_callback(key, value))


class EventfulList(list):
    """Eventful list.

    This class inherits from the Python intrinsic `list` class.  It adds events
    that allow you to listen for actions that modify the list.  You can
    optionally cancel the actions.

    See the on_del, on_set, on_insert, on_sort, and on_reverse methods for
    registering an event handler.

    Some of the method docstrings were taken from the Python documentation at
    https://docs.python.org/2/tutorial/datastructures.html"""

    def __init__(self, *pargs, **kwargs):
        """Public constructor"""
        self._insert_callback = _void
        self._set_callback = _void
        self._del_callback = _void
        self._sort_callback = _void
        self._reverse_callback = _void
        list.__init__(self, *pargs, **kwargs)

    def on_events(self, insert_callback=None, set_callback=None,
        del_callback=None, reverse_callback=None, sort_callback=None):
        """Register callbacks for add, set, and del actions.

        See the doctstrings for on_(insert/set/del/reverse/sort) for details
        about each callback.

        insert_callback: [callback = None]
        set_callback: [callback = None]
        del_callback: [callback = None]
        reverse_callback: [callback = None]
        sort_callback: [callback = None]"""
        self.on_insert(insert_callback)
        self.on_set(set_callback)
        self.on_del(del_callback)
        self.on_reverse(reverse_callback)
        self.on_sort(sort_callback)

    def on_insert(self, callback):
        """Register a callback for when an item is inserted into the list.

        Allows the listener to detect when items are inserted into the list and
        optionally cancel the insertion.

        callback: callable or None
            If you want to ignore the insertion event, pass None as the callback.
            The callback should have a signature of callback(index, value).  The
            callback should return a boolean True if the insertion should be
            canceled, False or None otherwise."""
        self._insert_callback = callback if callable(callback) else _void

    def on_del(self, callback):
        """Register a callback for item deletion.

        Allows the listener to detect when items are deleted from the list and
        optionally cancel the deletion.

        callback: callable or None
            If you want to ignore the deletion event, pass None as the callback.
            The callback should have a signature of callback(index).  The
            callback should return a boolean True if the deletion should be
            canceled, False or None otherwise."""
        self._del_callback = callback if callable(callback) else _void

    def on_set(self, callback):
        """Register a callback for items are set.

        Allows the listener to detect when items are set and optionally cancel
        the setting.  Note, `set` is also called when one or more items are
        added to the end of the list.

        callback: callable or None
            If you want to ignore the set event, pass None as the callback.
            The callback should have a signature of callback(index, value).  The
            callback should return a boolean True if the set should be
            canceled, False or None otherwise."""
        self._set_callback = callback if callable(callback) else _void

    def on_reverse(self, callback):
        """Register a callback for list reversal.

        callback: callable or None
            If you want to ignore the reverse event, pass None as the callback.
            The callback should have a signature of callback().  The
            callback should return a boolean True if the reverse should be
            canceled, False or None otherwise."""
        self._reverse_callback = callback if callable(callback) else _void

    def on_sort(self, callback):
        """Register a callback for sortting of the list.

        callback: callable or None
            If you want to ignore the sort event, pass None as the callback.
            The callback signature should match that of Python list's `.sort`
            method or `callback(*pargs, **kwargs)` as a catch all. The callback
            should return a boolean True if the reverse should be canceled,
            False or None otherwise."""
        self._sort_callback = callback if callable(callback) else _void

    def append(self, x):
        """Add an item to the end of the list."""
        self[len(self):] = [x]

    def extend(self, L):
        """Extend the list by appending all the items in the given list."""
        self[len(self):] = L

    def remove(self, x):
        """Remove the first item from the list whose value is x. It is an error
        if there is no such item."""
        del self[self.index(x)]

    def pop(self, i=None):
        """Remove the item at the given position in the list, and return it. If
        no index is specified, a.pop() removes and returns the last item in the
        list."""
        if i is None:
            i = len(self) - 1
        val = self[i]
        del self[i]
        return val

    def reverse(self):
        """Reverse the elements of the list, in place."""
        if self._can_reverse():
            list.reverse(self)

    def insert(self, index, value):
        """Insert an item at a given position. The first argument is the index
        of the element before which to insert, so a.insert(0, x) inserts at the
        front of the list, and a.insert(len(a), x) is equivalent to
        a.append(x)."""
        if self._can_insert(index, value):
            list.insert(self, index, value)

    def sort(self, *pargs, **kwargs):
        """Sort the items of the list in place (the arguments can be used for
        sort customization, see Python's sorted() for their explanation)."""
        if self._can_sort(*pargs, **kwargs):
            list.sort(self, *pargs, **kwargs)

    def __delitem__(self, index):
        if self._can_del(index):
            list.__delitem__(self, index)

    def __setitem__(self, index, value):
        if self._can_set(index, value):
            list.__setitem__(self, index, value)

    def __setslice__(self, start, end, value):
        if self._can_set(slice(start, end), value):
            list.__setslice__(self, start, end, value)

    def _can_insert(self, index, value):
        """Check if the item can be inserted."""
        return not bool(self._insert_callback(index, value))

    def _can_del(self, index):
        """Check if the item can be deleted."""
        return not bool(self._del_callback(index))

    def _can_set(self, index, value):
        """Check if the item can be set."""
        return not bool(self._set_callback(index, value))

    def _can_reverse(self):
        """Check if the list can be reversed."""
        return not bool(self._reverse_callback())

    def _can_sort(self, *pargs, **kwargs):
        """Check if the list can be sorted."""
        return not bool(self._sort_callback(*pargs, **kwargs))
