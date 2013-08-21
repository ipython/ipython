function figure(figure_number, websocket_url) {
	if (typeof(WebSocket) !== 'undefined') {
		this.WebSocket = WebSocket;
	} else {
		alert('Your browser does not have WebSocket support.');
	};
	
	var ws = new this.WebSocket(websocket_url);
	ws.binaryType = "blob";

	var message = document.getElementById('fig-message');
	var canvas = document.getElementById('fig-canvas');
	var context = canvas.getContext("2d");

	var rubberband_canvas = document.getElementById('fig-rubberband-canvas');
	var rubberband_context = rubberband_canvas.getContext("2d");
	rubberband_context.strokeStyle = "#000000";
	
	var img = new Image();
	img.addEventListener("load", function() {
		context.drawImage(this, 0, 0);
		// once it's drawn we can forget the blob straight away
		window.URL.revokeObjectURL(this.src);
	}, false);

	img.onunload = function() {
		ws.close();
	}

	ws.onmessage = function socket_on_message(event) {
		if (event.data instanceof Blob) {
			img.src = window.URL.createObjectURL(event.data);
			ws.send('{"type": "ack"}')
			return;
		} else {
			var msg = JSON.parse(event.data);
		
			switch(msg['type']) {
			case 'message':
				message.textContent = msg['message'];
				break;

			case 'cursor':
				var cursor = msg['cursor'];
				var cursor_styles = ['pointer', 'default', 'crosshair', 'move'];
				canvas.style.cursor = cursor_styles[cursor];
				break;
		
			case 'resize':
				var size = msg['size'];
				if (size[0] != canvas.width || size[1] != canvas.height) {
					canvas.width = size[0];
					canvas.height = size[1];
					rubberband_canvas.width = size[0];
					rubberband_canvas.height = size[1];

					parent.postMessage({
						iframe_id: 'iframe-' + figure_number,
						iframe_height: document.body.scrollHeight
					}, '*');

					ws.send(JSON.stringify({
						type: 'refresh'
					}));
				}
				break;
		
			case 'rubberband':
				var x0 = msg['x0'];
				var y0 = canvas.height - msg['y0'];
				var x1 = msg['x1'];
				var y1 = canvas.height - msg['y1'];
				x0 = Math.floor(x0) + 0.5;
				y0 = Math.floor(y0) + 0.5;
				x1 = Math.floor(x1) + 0.5;
				y1 = Math.floor(y1) + 0.5;
				var min_x = Math.min(x0, x1);
				var min_y = Math.min(y0, y1);
				var width = Math.abs(x1 - x0);
				var height = Math.abs(y1 - y0);
		
				rubberband_context.clearRect(0, 0, canvas.width, canvas.height);
				rubberband_context.strokeRect(min_x, min_y, width, height);
				break;
			}
		}
	};

	this.send_message = function(message) {
		if (ws.readystate = WebSocket.OPEN) {
			ws.send(JSON.stringify(message));
		}
	}

	this.mouse_event = function(event, name) {
		var canvas_pos = findPos(canvas)
		
		if (this.focus_on_mouseover && name === 'motion_notify')
		{
			canvas.focus();
		}
		
		var x = event.pageX - canvas_pos.x;
		var y = event.pageY - canvas_pos.y;

		this.send_message({
			type: name,
			x: x,
			y: y,
			button: event.button
		});

		/* This prevents the web browser from automatically changing to
		 * the text insertion cursor when the button is pressed.  We want
		 * to control all of the cursor setting manually through the
		 * 'cursor' event from matplotlib */
		event.preventDefault();
		return false;   
	};

	this.key_event = function(event, name) {
		/* Don't fire events just when a modifier is changed.  Modifiers are
		   sent along with other keys. */
		if (event.keyCode >= 16 && event.keyCode <= 20) {
			return;
		}

		value = '';
		if (event.ctrlKey) {
			value += "ctrl+";
		}
		if (event.altKey) {
			value += "alt+";
		}
		value += String.fromCharCode(event.keyCode).toLowerCase();

		this.send_message({
			type: name,
			key: value
		});
	};

};

function findPos(obj) {
	// Find the position of the given HTML node.
	
	var curleft = 0, curtop = 0;
	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
			curtop += obj.offsetTop;
		} while (obj = obj.offsetParent);
		return { x: curleft, y: curtop };
	}
	return undefined;
}
