IHF = function(addr) {
    this.socket = new WebSocket(addr);
    this.socket.firstConnection = true;
    this.socket.onopen = function (event) { this.send(document.cookie) }
    this.socket.onerror = function (event) { console.log(event); }
    this.socket.onmessage = function (event) {
        console.log(event.data)
        received = JSON.parse(event.data)
        for (c in received.cookie) {
            document.cookie = c+'='+received.cookie[c]
        }
        if (this.firstConnection) {
            console.log(received.data)
            template_f = Function.apply(null, ['app', 'return `' + received.template +'`'])
            this.app = new Reef('html', {
                data: received.data,
                template: template_f
            });
            this.app.render();
            this.firstConnection = false;
        }
        else
        {
            this.app.data = received.data
        }
    }
    this.socket.onclose = function (event) { console.log("Server disconnected"); document.location.reload(true); }
  }
IHF.prototype.send = function(f) {
    var args = Array.from(arguments);
    this.socket.send(JSON.stringify(args));
}

IHF.prototype.sendFile = function(f, id) {
    var file = document.getElementById(id).files[0]
    var reader = new FileReader()
    reader.onloadend = c => {
        var to_send = [f, file.name, c.target.result];
        this.socket.send('file:'+JSON.stringify(to_send));
    }
    reader.readAsDataURL(file);
}

IHF.prototype.sendForm = function(f) {
    var args = Array.from(arguments);
    for (i = 1; i < args.length; i++) {
        id = '#'+args[i]
        args[i] = $(id).val()
    }
    this.socket.send(JSON.stringify(args));
}