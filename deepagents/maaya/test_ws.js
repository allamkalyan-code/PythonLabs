const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.on('open', () => {
    console.log('Connected');
    ws.send(JSON.stringify({ type: 'message', content: 'SUPER SECRET KEYWORD' }));
});

ws.on('message', (data) => {
    console.log('Received:', data.toString());
});

ws.on('close', (code, reason) => {
    console.log('Disconnected', code, reason.toString());
});

ws.on('error', console.error);

setTimeout(() => {
    console.log('Timeout reached. Closing.');
    ws.close();
}, 5000);
