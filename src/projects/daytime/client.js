// daytime client
// node client.js -t -p 4313 127.0.0.1

const net = require("net");
const dgram = require("dgram");

let tcp = false;
let udp = false;
let port = 13;
let server = null;

let args = process.argv.slice(2);

for (let i = 0; i < args.length; i++) {
  if (args[i] == "-h" || args[i] == "--help") {
    console.log("usage: node client.js [-t] [-u] [-p PORT] server");
    console.log("  -t, --tcp   use TCP");
    console.log("  -u, --udp   use UDP");
    console.log("  -p PORT     port number");
    process.exit(0);
  } else if (args[i] == "-t" || args[i] == "--tcp") {
    tcp = true;
  } else if (args[i] == "-u" || args[i] == "--udp") {
    udp = true;
  } else if (args[i] == "-p" || args[i] == "--port") {
    i = i + 1;
    port = parseInt(args[i]);
  } else {
    server = args[i];
  }
}

if (server == null) {
  console.log("need a server address");
  process.exit(1);
}

if (tcp == false && udp == false) {
  console.log("pick --tcp or --udp");
  process.exit(1);
}

if (tcp == true && udp == true) {
  console.log("pick only one protocol");
  process.exit(1);
}

if (tcp) {
  console.log("Starting a TCP client");
  let sock = net.createConnection({ host: server, port: port });
  let data = "";

  sock.on("data", function (chunk) {
    data = data + chunk.toString();
  });

  sock.on("end", function () {
    console.log("");
    console.log(data.trim());
    console.log("");
    console.log("Client closed");
  });

  sock.on("error", function (err) {
    console.log("error: " + err.message);
  });
} else {
  // udp
  console.log("Starting a UDP client");
  let sock = dgram.createSocket("udp4");

  sock.on("message", function (msg) {
    console.log("");
    console.log(msg.toString().trim());
    console.log("");
    console.log("Client closed");
    sock.close();
  });

  sock.on("error", function (err) {
    console.log("error: " + err.message);
  });

  // just send something so the server replies
  sock.send(Buffer.from("hi"), port, server);
}
