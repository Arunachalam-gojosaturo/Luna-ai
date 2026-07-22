const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const pino = require('pino');

const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const QR_PATH = path.join(__dirname, 'qr.png');
const QR_TXT_PATH = path.join(__dirname, 'qr_base64.txt');

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    
    const sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: true
    });

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log('New QR Code generated');
            try {
                const qrBase64 = await QRCode.toDataURL(qr);
                fs.writeFileSync(QR_TXT_PATH, qrBase64);
                await QRCode.toFile(QR_PATH, qr);
            } catch (err) {
                console.error("Error generating QR files:", err);
            }
        }

        if (connection === 'close') {
            const shouldReconnect = lastDisconnect.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Connection closed due to', lastDisconnect.error, ', reconnecting:', shouldReconnect);
            if (shouldReconnect) {
                setTimeout(connectToWhatsApp, 3000);
            } else {
                console.log('Logged out. Clearing auth directory and restarting.');
                try {
                    fs.rmSync(AUTH_DIR, { recursive: true, force: true });
                } catch (e) {}
                setTimeout(connectToWhatsApp, 3000);
            }
        } else if (connection === 'open') {
            console.log('WhatsApp connection successfully opened!');
            try {
                if (fs.existsSync(QR_PATH)) fs.unlinkSync(QR_PATH);
                if (fs.existsSync(QR_TXT_PATH)) fs.unlinkSync(QR_TXT_PATH);
            } catch (e) {}
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.upsert', async m => {
        if (m.type === 'notify') {
            for (const msg of m.messages) {
                // Rule 1 & 2 & 3: Only direct DMs, not from me, not group, not status
                if (msg.key.fromMe) continue;
                const jid = msg.key.remoteJid;
                if (!jid || jid.endsWith('@g.us') || jid === 'status@broadcast') {
                    continue;
                }

                // Check text
                const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text;
                if (!text) continue;

                console.log(`Direct DM from ${jid}: ${text}`);

                try {
                    // Call the main LUNA Command executor
                    const response = await axios.post('http://localhost:3000/api/luna/command', {
                        command: text,
                        history: [],
                        activeView: "chat",
                        groqKey: "",
                        openRouterKey: "",
                        openaiKey: "",
                        modelSelection: "",
                        activeProvider: "groq"
                    });

                    const data = response.data;
                    if (data && data.speech) {
                        console.log(`Replying to ${jid} with: ${data.speech}`);
                        // Rule 5: Reply must contain BOTH a Text Message AND a Voice Note (via TTS).
                        // Send text first
                        await sock.sendMessage(jid, { text: data.speech });

                        // Call TTS generation endpoint to get audio stream
                        const ttsResponse = await axios.post('http://localhost:3000/api/tts', {
                            text: data.speech,
                            provider: 'edge',
                            voiceId: 'en-US-AriaNeural'
                        }, { responseType: 'arraybuffer' });

                        const audioPath = path.join(__dirname, `reply_${Date.now()}.mp3`);
                        fs.writeFileSync(audioPath, ttsResponse.data);

                        // Send audio as PTT/Voice Note
                        await sock.sendMessage(jid, {
                            audio: { url: audioPath },
                            mimetype: 'audio/mp4',
                            ptt: true
                        });

                        // Clean up temporary audio file after a short delay
                        setTimeout(() => {
                            try {
                                if (fs.existsSync(audioPath)) fs.unlinkSync(audioPath);
                            } catch (e) {}
                        }, 5000);
                    }
                } catch (err) {
                    console.error('Error replying to WhatsApp JID', jid, err.message);
                }
            }
        }
    });
}

connectToWhatsApp().catch(err => console.error("Critical error in WhatsApp client:", err));
