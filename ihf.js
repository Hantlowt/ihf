IHF = function(addr) {
    this.socket = new WebSocket(addr);
    this.socket.firstConnection = true;
    this.socket.onopen = function (event) { this.send('hello') }
    this.socket.onerror = function (event) { console.log(event); }
    this.socket.onmessage = function (event) {
        console.log(event.data)
        data_received = JSON.parse(event.data)
        if (this.firstConnection) {
            console.log(data_received)
            template_received = Function.apply(null, ['app', 'return `' + data_received.template +'`'])
            console.log(data_received)
            this.app = new Reef('html', {
                data: data_received,
                template: template_received
            });
            this.app.render();
            this.firstConnection = false;
        }
        else
        {
            this.app.data = data_received
        }
    }
    this.socket.onclose = function (event) { console.log("Server disconnected"); }
  }
IHF.prototype.send = function(f) {
    var args = Array.from(arguments);
    this.socket.send(JSON.stringify(args));
    }