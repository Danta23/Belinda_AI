require('dotenv').config(); // support .env
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('baileys');
const { sendButtons } = require('@ryuu-reinzz/button-helper');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');

// --- KONFIGURASI ---
const toxicWords = [
    // --- INDONESIA ---
    'anjing', 'babi', 'monyet', 'kunyuk', 'asu', 'celeng', 'bajing', 'landak', 'garangan', 'anying', 'jing', 'kanjut', 'pantek', 'puki', 'pukas', 'toket', 'tobrut', 'tembolok', 'asoe', 'andjing',
    'goblok', 'tolol', 'bego', 'idiot', 'cacat', 'sinting', 'gila', 'autis', 'bloon', 'yatim', 'nigga', 'negro', 'beloon', 'dongo', 'dungu', 'geblek', 'dongok', 'coli', 'peli', 'janco', 'ongok',
    'peler', 'memek', 'kontol', 'jembut', 'itil', 'ngentot', 'ngewe', 'tempik', 'titit', 'pepek', 'cukimai', 'entot', 'kampang', 'menyodok', 'merodok', 'modar', 'monyong', 'sialan', 'taruk', 'gendut',
    'bangsat', 'keparat', 'brengsek', 'lonte', 'perek', 'jablay', 'bajingan', 'pelacur', 'pendoza', 'ewe', 'koit', 'kojor', 'memberaki', 'mengamput', 'mengancuk', 'mengayut', 'mengentot', 'kampret',
    'taik', 'tai', 'bangke', 'bangkae', 'jancok', 'jancuk', 'ancuk', 'ancok', 'cok', 'cuk', 'bgst', 'anj', 'ajg', 'anjg', 'mnyet', 'ppk', 'kntl', 'mmk', 'pukimak', 'telang', 'lasso', 'dodol', 'bengak', 
    'pilat', 'gathel', 'gegares', 'geladak', 'beal', 'gelayaran', 'mampus', 'bacot', 'cungur', 'palkon', 'pabu', 'picek', 'budek', 'budeg', 'bolot', 'kopok', 'pecun', 'perek', 'ayam', 'jamet', 'jablay',

    // --- ENGLISH ---
    'fuck', 'shit', 'bitch', 'asshole', 'dick', 'pussy', 'cunt', 'motherfucker', 'bastard', 'abus', 'faggot', 'fag', 'slut', 'whore', 'jerk', 'prick', 'bollocks', 'wanker', 'twat', 'piss', 'cock',
    'nigger', 'negro', 'retard', 'dumbass', 'bullshit', 'cum', 'semen', 'porn', 'porno', 'ass', 'arse', 'hoe', 'skank', 'tit', 'tits',

    // --- REGIONAL (JAWA, SUNDA, DLL) ---
    'asu', 'raimu', 'matamu', 'ndasmu', 'dancok', 'jancok', 'cok', 'jangkrik', 'mbokmu', 'tempik', 'jembut', 'jembutmu', 'silit', 'silitmu', 'picek', 'kopok', 'mbelgedes', 'budeg', 'cocote', 'lambemu',
    'anying', 'anyink', 'goblog', 'belegug', 'sia', 'sia mah', 'maneh', 'kebluk', 'modar', 'kokod', 'beungeut', 'gejul', 'boro'
];
const pythonUrl = process.env.PYTHON_URL || 'http://127.0.0.1:8000';

// --- CHAT HISTORY ---
const historyFile = 'chat_history.json';
function loadHistory() {
    if (fs.existsSync(historyFile)) {
        try {
            if (fs.statSync(historyFile).isDirectory()) {
                console.error(`Error: '${historyFile}' is a directory, not a file. Chat history will not be loaded or saved until this is manually resolved.`);
                return [];
            }
            const data = fs.readFileSync(historyFile, 'utf8');
            if (!data) return []; // Handle empty file
            return JSON.parse(data);
        } catch (e) {
            console.log(`Warning: Could not read or parse '${historyFile}'. A new one will be created. Error: ${e.message}`);
            return [];
        }
    }
    return [];
}
function saveHistory(history) {
    try {
        if (fs.existsSync(historyFile) && fs.statSync(historyFile).isDirectory()) {
            return;
        }
        fs.writeFileSync(historyFile, JSON.stringify(history, null, 2));
    } catch (e) {
        console.error(`Error saving chat history: ${e.message}`);
    }
}
let chatHistory = loadHistory();

// IP & Port Bridge (default: 127.0.0.1:9000)
const bridgeHost = process.env.BRIDGE_HOST || '127.0.0.1';
const bridgePort = process.env.BRIDGE_PORT || '9000';

let quizData = {};
let gameData = {};
let nextRequests = {};

// --- ANTI-SYSTEM SETTINGS ---
let antiSettings = {}; 
// Struktur: { "jid": { toxic: true, link: false, spam: false } }
let spamTracker = {};
// Struktur: { "jid": { "user": { lastMsg: "", count: 0 } } }
let afkData = {};
// Struktur: { "user_jid": { reason: "", time: Date } }

// --- NEW SYSTEM SETTINGS ---
let customLists = {}; // { jid: { listName: [userJids] } }
let globalLimit = 35; // Default limit
let usageTracker = {}; // { jid: { date: "YYYY-MM-DD", count: 0 } }

function drawProgressBar(current, total, label = "Loading") {
    const size = 20;
    const percent = Math.min(current / total, 1);
    const filled = Math.round(size * percent);
    const empty = size - filled;
    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    process.stdout.write(`\r${label}: [${bar}] ${Math.round(percent * 100)}% `);
    if (percent >= 1) process.stdout.write('\n');
}

function normalizeText(str) {
    return str.toLowerCase()
        .replace(/0/g, 'o').replace(/1/g, 'i').replace(/3/g, 'e')
        .replace(/4/g, 'a').replace(/5/g, 's').replace(/7/g, 'j')
        .replace(/8/g, 'b').replace(/[^a-z0-9\s]/g, '');
}

async function connectWA() {
    console.log("⏳ Starting connection in 5 seconds to wait for network...");
    await new Promise(resolve => setTimeout(resolve, 5000));

    const { state, saveCreds } = await useMultiFileAuthState(process.env.SESSION_NAME || 'auth_info');

    let version, isLatest;
    try {
        const v = await fetchLatestBaileysVersion();
        version = v.version;
        isLatest = v.isLatest;
    } catch (e) {
        console.log("⚠️ Could not fetch latest WA version, using default.");
        version = [2, 3000, 1015901307]; // Fallback version
        isLatest = false;
    }

    console.log(`using WA v${version.join('.')}, isLatest: ${isLatest}`);

    const history = loadHistory();
    const total = history.length;
    console.log("⏳ Loading chat history...");
    for (let i = 0; i < total; i++) {
        if (i % Math.ceil(total / 20) === 0) drawProgressBar(i, total, "Syncing History");
    }
    drawProgressBar(total, total, "Syncing History");
    console.log("✅ History synced.");

    const sock = makeWASocket({
        version,
        auth: state,
        browser: ["Ubuntu", "Chrome", "121.0.6167.85"],
        logger: require('pino')({ level: 'error' }), // Only log errors
        connectTimeoutMs: 60000,
        defaultQueryTimeoutMs: 0,
        keepAliveIntervalMs: 10000,
        generateHighQualityLinkPreview: true,
        getMessage: async (key) => {
            return { conversation: 'Belinda AI is active' };
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, qr, lastDisconnect } = update;
        if (qr) {
            console.log("📸 New QR Code generated. Please scan:");
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'open') {
            console.log(`✅ BOT BELINDA ONLINE (Bridge: ${bridgeHost}:${bridgePort})`);
        }
        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode || 0;
            const shouldReconnect = (
                reason !== DisconnectReason.loggedOut &&
                reason !== DisconnectReason.badSession &&
                reason !== DisconnectReason.connectionReplaced
            );

            console.log(`❌ Connection closed. Reason code: ${reason}. Reconnecting: ${shouldReconnect}`);

            if (reason === DisconnectReason.loggedOut || reason === DisconnectReason.badSession) {
                console.log("⚠️ Session is invalid or logged out. Please delete the session folder and scan again.");
            } else if (reason === DisconnectReason.connectionReplaced) {
                console.log("⚠️ Connection replaced by another session. Stopping current bridge.");
            } else if (reason === 408 || reason === 503) {
                console.log("⚠️ Server error or timeout. Retrying in 20s...");
                if (shouldReconnect) setTimeout(connectWA, 20000);
            } else if (shouldReconnect) {
                const delay = 10000;
                console.log(`⏳ Reconnecting in ${delay / 1000}s...`);
                setTimeout(connectWA, delay);
            }
        }
    });

    // --- WELCOME MESSAGE ---
    sock.ev.on('group-participants.update', async (anu) => {
        if (anu.action === 'add') {
            try {
                await new Promise(resolve => setTimeout(resolve, 1500));
                const metadata = await sock.groupMetadata(anu.id);
                for (let participant of anu.participants) {
                    const jid = typeof participant === 'string' ? participant : participant.id;
                    const mentionJid = jid.split('@')[0];
                    const welcomeText = `👋 *Halo @${mentionJid}!*\n\nSelamat datang di grup *${metadata.subject}*.\n\nSemoga betah di sini ya!`;
                    await sock.sendMessage(anu.id, { text: welcomeText, mentions: [jid] });
                }
            } catch (e) { console.log("Error Welcome Message:", e.message); }
        }
    });

    // --- FUNGSI CREATE QUIZ ---
    async function createQuiz(group) {
        const data = quizData[group];
        if (data.currentNum >= data.maxSoal) {
            const content = {
                text: `🏁 *QUIZ SELESAI!*\n\nBerhasil menyelesaikan ${data.maxSoal} soal *${data.mapel.toUpperCase()}* (${data.diff.toUpperCase()}).\n\n_Pilih opsi di bawah untuk lanjut atau berhenti._`,
                footer: "🤖 Belinda AI Quiz",
                buttons: [
                    { id: '!quiz', text: '🔄 Ulangi Quiz' }
                ]
            };

            try {
                await sendButtons(sock, group, content);
            } catch (e) {
                console.error("Gagal mengirim tombol:", e);
                await sock.sendMessage(group, { text: content.text + "\n\n1. !quiz" });
            }
            delete quizData[group];
            return;
        }

        data.currentNum++;
        await sock.sendMessage(group, { text: `⏳ Menyiapkan soal ke-${data.currentNum}/${data.maxSoal}...` });

        try {
            const prompt = `Buatkan 1 soal PG (Pilihan Ganda) ${data.mapel} untuk tingkat ${data.diff} (A-E). ` +
                `Pastikan soalnya variatif, menantang, and berbeda dari topik umum. ` +
                `Berikan pilihan jawaban A sampai E. Tulis 'KUNCI: X' di akhir soal. [Seed: ${Math.random().toString(36).substring(7)}]`;

            const res = await axios.post(`${pythonUrl}/chat`, { sender: group, msg: prompt });

            const parts = res.data.split('KUNCI:');
            const cleanText = parts[0].trim();
            const keyChar = parts[1]?.trim()[0].toUpperCase();

            const poll = await sock.sendMessage(group, {
                poll: {
                    name: `*SOAL ${data.currentNum}/${data.maxSoal}* (${data.mapel.toUpperCase()} - ${data.diff.toUpperCase()})\n\n${cleanText}`,
                    values: ['A', 'B', 'C', 'D', 'E'],
                    selectableCount: 1
                }
            });

            data.msgId = poll.key.id;
            data.question = cleanText;
            data.index = ['A', 'B', 'C', 'D', 'E'].indexOf(keyChar);
            nextRequests[group] = [];
        } catch (e) {
            data.currentNum--;
            console.log("Gagal membuat kuis:", e.message);
        }
    }

    // --- MESSAGE HANDLER ---
    sock.ev.on('messages.upsert', async ({ messages }) => {
        const m = messages[0];
        if (!m.message || m.key.fromMe) return;

        const sender = m.key.remoteJid;

        const buttonText = m.message.buttonsResponseMessage?.selectedDisplayText || m.message.templateButtonReplyMessage?.selectedDisplayText || "";
        const buttonId = m.message.buttonsResponseMessage?.selectedButtonId || m.message.templateButtonReplyMessage?.selectedId || "";
        const interactiveResponse = m.message.interactiveResponseMessage?.nativeFlowResponseMessage?.paramsJson;
        let interactiveId = "";
        if (interactiveResponse) {
            try {
                const parsed = JSON.parse(interactiveResponse);
                interactiveId = parsed.id;
            } catch (e) { }
        }

        const text_orig = (m.message.conversation || m.message.extendedTextMessage?.text || "").trim();
        const text = (interactiveId || buttonId || buttonText || text_orig).trim();

        const isGroup = sender.endsWith('@g.us');
        const participant = m.key.participant || sender;

        // --- AFK SYSTEM: AUTO-CLEAR ---
        if (afkData[participant]) {
            const timeDiff = new Date() - afkData[participant].time;
            const hours = Math.floor(timeDiff / 3600000);
            const minutes = Math.floor((timeDiff % 3600000) / 60000);
            const seconds = Math.floor((timeDiff % 60000) / 1000);
            const duration = `${hours > 0 ? hours + ' jam ' : ''}${minutes > 0 ? minutes + ' menit ' : ''}${seconds} detik`;
            
            await sock.sendMessage(sender, { text: `👋 *Selamat datang kembali!*\n\nStatus AFK kamu telah dihapus.\n*Alasan:* ${afkData[participant].reason}\n*Durasi:* ${duration}` });
            delete afkData[participant];
        }

        // --- AFK SYSTEM: MENTION DETECT ---
        const mentions = m.message.extendedTextMessage?.contextInfo?.mentionedJid || [];
        for (let jid of mentions) {
            if (afkData[jid]) {
                await sock.sendMessage(sender, { text: `🤫 *Ssstt!* Orangnya sedang AFK.\n\n*Alasan:* ${afkData[jid].reason}\n*Sejak:* ${new Date(afkData[jid].time).toLocaleTimeString()}` });
            }
        }

        async function isAdmin() {
            if (!isGroup) return true;
            const meta = await sock.groupMetadata(sender);
            return meta.participants.filter(p => p.admin).map(p => p.id).includes(participant);
        }

        // --- ANTI-SYSTEM FILTERS ---
        if (isGroup && text) {
            if (!antiSettings[sender]) antiSettings[sender] = { toxic: true, link: false, spam: false };
            const settings = antiSettings[sender];

            // 1. ANTI-TOXIC
            if (settings.toxic) {
                const cleanText = normalizeText(text);
                const words = cleanText.split(/\s+/);
                if (words.some(w => toxicWords.includes(w))) {
                    try { await sock.sendMessage(sender, { delete: m.key }); return; } catch (e) { }
                }
            }

            // 2. ANTI-LINK
            if (settings.link) {
                const linkRegex = /https?:\/\/[^\s]+/gi;
                const isMediaCommand = text.startsWith('!music') || text.startsWith('!video') || text.startsWith('!image');
                if (linkRegex.test(text) && !isMediaCommand) {
                    try { await sock.sendMessage(sender, { delete: m.key }); return; } catch (e) { }
                }
            }

            // 3. ANTI-SPAM
            if (settings.spam) {
                if (!spamTracker[sender]) spamTracker[sender] = {};
                if (!spamTracker[sender][participant]) spamTracker[sender][participant] = { lastMsg: "", count: 0 };
                
                const userSpam = spamTracker[sender][participant];
                if (text === userSpam.lastMsg) {
                    userSpam.count++;
                    if (userSpam.count >= 3) { // Pesan ke-4 dan seterusnya yang sama akan dihapus
                        try { await sock.sendMessage(sender, { delete: m.key }); return; } catch (e) { }
                    }
                } else {
                    userSpam.lastMsg = text;
                    userSpam.count = 0;
                }
            }
        }

        // --- CHAT HISTORY ---
        if (text && !text.startsWith('!')) {
            const pushName = m.pushName || "User";
            chatHistory.push({ sender, participant, name: pushName, text, time: new Date().toISOString() });
            saveHistory(chatHistory);
        }

        // --- COMMANDS ---
        if (text.startsWith('!')) {
            const args = text.split(' ');
            const cmd = args[0].toLowerCase();

            if (cmd === '!kick') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const target = args[1]?.replace('@', '').replace(/[^0-9]/g, '') + '@s.whatsapp.net';
                try {
                    await sock.groupParticipantsUpdate(sender, [target], 'remove');
                    await sock.sendMessage(sender, { text: `👢 Removed ${args[1]} from the group.` });
                } catch (e) { sock.sendMessage(sender, { text: "⚠️ Failed to remove member." }); }
                return;
            }

            if (cmd === '!cuaca') {
                const city = args.slice(1).join(' ');
                if (!city) return sock.sendMessage(sender, { text: "⚠️ Format: !cuaca {nama_kota}" });

                try {
                    const res = await axios.post(`${pythonUrl}/weather`, { msg: city });
                    await sock.sendMessage(sender, { text: res.data });
                } catch (e) {
                    await sock.sendMessage(sender, { text: `❌ Error: ${e.message}` });
                }
                return;
            }

            if (cmd === '!add') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                if (!args[1]) return sock.sendMessage(sender, { text: "⚠️ Format: !add {nomor} (Contoh: !add 628xxx atau !add 1234xxx)" });

                let num = args[1].replace(/[^0-9]/g, '');
                if (num.startsWith('0')) {
                    num = '62' + num.substring(1);
                }
                const target = num + '@s.whatsapp.net';

                try {
                    const response = await sock.groupParticipantsUpdate(sender, [target], 'add');
                    const result = response[0];

                    if (result.status === "200") {
                        await sock.sendMessage(sender, { text: `✅ Berhasil menambahkan @${num} ke grup.`, mentions: [target] });
                    } else if (result.status === "403") {
                        const code = await sock.groupInviteCode(sender);
                        const inviteLink = `https://chat.whatsapp.com/${code}`;
                        await sock.sendMessage(sender, {
                            text: `⚠️ Tidak bisa menambahkan @${num} secara langsung karena pengaturan privasi mereka.\n\n*Solusi:* Silakan kirimkan link undangan ini ke mereka:\n${inviteLink}`,
                            mentions: [target]
                        });
                    } else if (result.status === "408") {
                        await sock.sendMessage(sender, { text: `❌ Nomor @${num} baru saja keluar dari grup. Tunggu beberapa saat.`, mentions: [target] });
                    } else if (result.status === "409") {
                        await sock.sendMessage(sender, { text: `ℹ️ Nomor @${num} sudah ada di dalam grup.`, mentions: [target] });
                    } else {
                        await sock.sendMessage(sender, { text: `❌ Gagal menambahkan. Status: ${result.status}` });
                    }
                } catch (e) {
                    console.error("Add error:", e);
                    sock.sendMessage(sender, { text: "⚠️ Pastikan bot adalah Admin dan nomor valid dengan kode negara." });
                }
                return;
            }

            if (cmd === '!open') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                await sock.groupSettingUpdate(sender, 'not_announcement');
                await sock.sendMessage(sender, { text: "🔓 Group is now open for all members." });
                return;
            }

            if (cmd === '!close') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                await sock.groupSettingUpdate(sender, 'announcement');
                await sock.sendMessage(sender, { text: "🔒 Group is now restricted to admins only." });
                return;
            }

            if (cmd === '!zero') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                chatHistory = [];
                saveHistory(chatHistory);
                await sock.sendMessage(sender, { text: "🧹 Chat history cleared." });
                return;
            }

            if (cmd === '!spam') {
                if (!(await isAdmin())) return; // Silent return for secret command
                
                const numStr = args[args.length - 1];
                const num = parseInt(numStr);
                const msg = args.slice(1, -1).join(' ');

                if (!msg || isNaN(num)) {
                    return sock.sendMessage(sender, { text: "⚠️ Format: !spam {pesan} {jumlah}" });
                }

                if (num < 1 || num > 1000) {
                    return sock.sendMessage(sender, { text: "❌ Jumlah minimal 1 dan maksimal 1000." });
                }

                console.log(`🚀 [SPAM START] Sending ${num} messages to ${sender}...`);

                // Execute spam with throttling to avoid being flagged/banned by WA
                for (let i = 0; i < num; i++) {
                    try {
                        await sock.sendMessage(sender, { text: msg });
                        
                        // Small delay after every message (150ms)
                        await new Promise(resolve => setTimeout(resolve, 150));
                        
                        // Longer pause every 100 messages to let the server breathe
                        if (i > 0 && i % 100 === 0) {
                            await new Promise(resolve => setTimeout(resolve, 2000));
                        }
                    } catch (e) {
                        console.error(`Spam error at index ${i}:`, e.message);
                        if (e.message.includes('rate-overlimit') || e.message.includes('429')) {
                            await new Promise(resolve => setTimeout(resolve, 5000));
                        }
                    }
                }
                console.log(`✅ [SPAM FINISHED] Successfully sent ${num} messages to ${sender}.`);
                return;
            }

            if (cmd === '!rand') {
                if (!(await isAdmin())) return;
                
                // Stress test: BigInt calculation with 20-digit random numbers
                const gen20Digit = () => Array.from({length: 20}, () => Math.floor(Math.random() * 10)).join('');
                
                const num1 = BigInt(gen20Digit());
                const num2 = BigInt(gen20Digit());
                const result = num1 * num2;

                const response = `🔢 *BIGINT STRESS TEST*\n\n` +
                                 `*Num 1:* ${num1}\n` +
                                 `*Num 2:* ${num2}\n\n` +
                                 `*Hasil Kali:* ${result}\n\n` +
                                 `_Kalkulasi 20-digit sukses dijalankan._`;
                
                return sock.sendMessage(sender, { text: response });
            }

            if (cmd === '!halo') {
                const mentionJid = participant.split('@')[0];
                return sock.sendMessage(sender, { 
                    text: `Halo juga @${mentionJid} 👋`, 
                    mentions: [participant] 
                });
            }

            if (cmd === '!test') {
                return sock.sendMessage(sender, { text: "Masuk" });
            }

            if (cmd === '!image') {
                const url = args[1];
                if (!url) return sock.sendMessage(sender, { text: "⚠️ Format: !image {url_gambar}" });

                const { key } = await sock.sendMessage(sender, { text: "⏳ Sedang mengunduh gambar..." });
                try {
                    const response = await axios.get(url, { 
                        responseType: 'arraybuffer',
                        headers: {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                        }
                    });

                    const contentType = response.headers['content-type'];
                    if (!contentType || !contentType.startsWith('image/')) {
                        return sock.sendMessage(sender, { 
                            text: "❌ Link tersebut bukan merupakan link gambar langsung (direct image link).\n\n*Tips:* Gunakan link yang berakhiran .jpg, .png, atau .webp", 
                            edit: key 
                        });
                    }

                    const buffer = Buffer.from(response.data); // Fixed: No 'utf-8' encoding for binary data
                    await sock.sendMessage(sender, { image: buffer, caption: "✅ Gambar berhasil diunduh!" });
                    await sock.sendMessage(sender, { text: "✅ Selesai!", edit: key });
                } catch (e) {
                    await sock.sendMessage(sender, { text: `❌ Gagal mengambil gambar: ${e.message}`, edit: key });
                }
                return;
            }

            if (cmd === '!rules') {
                if (!isGroup) return sock.sendMessage(sender, { text: "⚠️ Perintah ini hanya bisa digunakan di dalam grup." });
                const meta = await sock.groupMetadata(sender);
                const rules = meta.desc || "Deskripsi grup tidak tersedia.";
                return sock.sendMessage(sender, { text: `📜 *PERATURAN GRUP*\n\n${rules}` });
            }

            if (cmd === '!afk') {
                const reason = args.slice(1).join(' ') || "Tanpa alasan.";
                afkData[participant] = { reason, time: new Date() };
                return sock.sendMessage(sender, { text: `💤 *Status AFK Aktif*\n\nKamu sekarang AFK.\n*Alasan:* ${reason}\n\n_Bot akan otomatis memberitahu jika namamu disebut._` });
            }

            if (cmd === '!sholat') {
                const city = args.slice(1).join(' ');
                if (!city) return sock.sendMessage(sender, { text: "⚠️ Format: !sholat {nama_kota}" });

                try {
                    // Step 1: Search City ID
                    const searchRes = await axios.get(`https://api.myquran.com/v2/sholat/kota/cari/${city}`);
                    if (!searchRes.data.status || searchRes.data.data.length === 0) {
                        return sock.sendMessage(sender, { text: `❌ Kota *${city}* tidak ditemukan.` });
                    }
                    const cityId = searchRes.data.data[0].id;
                    const cityName = searchRes.data.data[0].lokasi;

                    // Step 2: Get Schedule for Today
                    const date = new Date().toISOString().split('T')[0].split('-').join('/');
                    const scheduleRes = await axios.get(`https://api.myquran.com/v2/sholat/jadwal/${cityId}/${date}`);
                    const j = scheduleRes.data.data.jadwal;

                    const text = `🕌 *JADWAL SHOLAT: ${cityName}*\n` +
                                 `📅 Tanggal: ${j.tanggal}\n\n` +
                                 `✨ Imsak: ${j.imsak}\n` +
                                 `✨ Subuh: ${j.subuh}\n` +
                                 `✨ Terbit: ${j.terbit}\n` +
                                 `✨ Dhuha: ${j.dhuha}\n` +
                                 `✨ Dzuhur: ${j.dzuhur}\n` +
                                 `✨ Ashar: ${j.ashar}\n` +
                                 `✨ Maghrib: ${j.maghrib}\n` +
                                 `✨ Isya: ${j.isya}\n\n` +
                                 `_Sumber: api.myquran.com_`;
                    return sock.sendMessage(sender, { text });
                } catch (e) {
                    return sock.sendMessage(sender, { text: `❌ Gagal mengambil jadwal sholat: ${e.message}` });
                }
            }

            if (cmd === '!font') {
                const input = args.slice(1).join(' ');
                if (!input) return sock.sendMessage(sender, { text: "⚠️ Format: !font {teks_kamu}" });

                const maps = {
                    italic: "𝘢bc𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡0123456789",
                    bold: "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔ＶＷＸＹ𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
                    mono: "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳ＥＦＧＨＩ𝙹𝙺ＬＭＮＯＰ𝚀𝚁ＳＴＵＶＷＸＹＺ𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
                    script: "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜𝐵𝒞𝒟ＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ0123456789",
                    bubble: "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ⓪①②③④⑤⑥⑦⑧⑨",
                    square: "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉0123456789",
                    gothic: "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ0123456789",
                    tiny: "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ0123456789",
                    wide: "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９",
                    struck: "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊ＴＵＶＷＸＹＺ𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
                    slashed: "a̸b̸c̸d̸e̸f̸g̸h̸i̸j̸k̸l̸m̸n̸o̸p̸q̸r̸s̸t̸u̸v̸w̸x̸y̸z̸A̸B̸C̸D̸E̸F̸G̸H̸I̸J̸K̸L̸M̸N̸O̸P̸Q̸R̸S̸T̸U̸V̸W̸X̸Y̸Z̸0̸1̸2̸3̸4̸5̸6̸7̸8̸9̸",
                    underline: "a̲b̲c̲d̲e̲f̲g̲h̲i̲j̲k̲l̲m̲n̲o̲p̲q̲r̲s̲t̲u̲v̲w̲x̲y̲z̲A̲B̲C̲D̲E̲F̲G̲H̲I̲J̲K̲L̲M̲N̲O̲P̲Q̲R̲S̲T̲U̲V̲W̲X̲Y̲Z̲0̲1̲2̲3̲4̲5̲6̲7̲8̲9̲"
                };

                const normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

                const convert = (txt, map) => {
                    const targetChars = [...map];
                    return txt.split('').map(c => {
                        const idx = normal.indexOf(c);
                        if (idx === -1) return c;
                        return targetChars[idx] || c;
                    }).join('');
                };

                const resText = `✨ *AESTHETIC FONTS*\n\n` +
                                `*Italic:* \n${convert(input, maps.italic)}\n\n` +
                                `*Bold:* \n${convert(input, maps.bold)}\n\n` +
                                `*Monospace:* \n${convert(input, maps.mono)}\n\n` +
                                `*Cursive:* \n${convert(input, maps.script)}\n\n` +
                                `*Bubbled:* \n${convert(input, maps.bubble)}\n\n` +
                                `*Squared:* \n${convert(input, maps.square)}\n\n` +
                                `*Gothic:* \n${convert(input, maps.gothic)}\n\n` +
                                `*Tiny Caps:* \n${convert(input, maps.tiny)}\n\n` +
                                `*Wide:* \n${convert(input, maps.wide)}\n\n` +
                                `*Double Struck:* \n${convert(input, maps.struck)}\n\n` +
                                `*Slashed:* \n${convert(input, maps.slashed)}\n\n` +
                                `*Underlined:* \n${convert(input, maps.underline)}`;
                
                return sock.sendMessage(sender, { text: resText });
            }

            if (cmd === '!limit') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const n = args[1];
                if (n === 'inf') globalLimit = Infinity;
                else if (!isNaN(parseInt(n)) && parseInt(n) >= 35) globalLimit = parseInt(n);
                else return sock.sendMessage(sender, { text: "⚠️ Limit minimal 35 atau 'inf'" });
                return sock.sendMessage(sender, { text: `✅ Limit diatur ke: ${globalLimit}` });
            }

            if (cmd === '!anti') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const type = args[1]?.toLowerCase();
                const bool = args[2]?.toLowerCase();

                if (!['toxic', 'link', 'spam'].includes(type) || !['true', 'false'].includes(bool)) {
                    return sock.sendMessage(sender, { text: "⚠️ Format: !anti {toxic/link/spam} {true/false}" });
                }

                if (!antiSettings[sender]) antiSettings[sender] = { toxic: true, link: false, spam: false };
                antiSettings[sender][type] = (bool === 'true');

                return sock.sendMessage(sender, { text: `✅ *ANTI-${type.toUpperCase()}* telah diatur menjadi: *${bool.toUpperCase()}*` });
            }

            if (cmd === '!list') {
                const [mode, name] = [args[1], args[2]];
                if (!mode) {
                    const titles = Object.keys(customLists[sender] || {});
                    return sock.sendMessage(sender, { text: `📋 *DAFTAR LIST TERSEDIA:*\n\n${titles.length > 0 ? titles.join('\n') : "Tidak ada list."}` });
                }

                if (mode === 'clear' && name === 'all') {
                    if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Admin only." });
                    customLists[sender] = {};
                    return sock.sendMessage(sender, { text: "🧹 Semua list dihapus." });
                }
                if (!name) return sock.sendMessage(sender, { text: "⚠️ Format: !list {mode} {name}" });
                if (!customLists[sender]) customLists[sender] = {};
                if (mode === 'create' || mode === 'clear') {
                    if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Admin only." });
                    if (mode === 'create') { customLists[sender][name] = []; return sock.sendMessage(sender, { text: `✅ List *${name}* dibuat.` }); }
                    if (!customLists[sender][name]) return sock.sendMessage(sender, { text: `❌ List *${name}* tidak ditemukan.` });
                    if (mode === 'clear') { delete customLists[sender][name]; return sock.sendMessage(sender, { text: `🧹 List *${name}* dihapus.` }); }
                }
                if (!customLists[sender][name]) return sock.sendMessage(sender, { text: `❌ List *${name}* tidak ditemukan.` });
                if (mode === 'addme') { 
                    if (!customLists[sender][name].includes(participant)) customLists[sender][name].push(participant);
                    return sock.sendMessage(sender, { text: `✅ Ditambahkan ke *${name}*.` });
                }
                if (mode === 'delme') {
                    customLists[sender][name] = customLists[sender][name].filter(p => p !== participant);
                    return sock.sendMessage(sender, { text: `✅ Dihapus dari *${name}*.` });
                }
                if (mode === 'print') {
                    if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Admin only." });
                    const listMembers = customLists[sender][name];
                    const listText = listMembers.map((p, i) => `${i + 1}. @${p.split('@')[0]}`).join('\n');
                    return sock.sendMessage(sender, { text: `📋 *DAFTAR ${name.toUpperCase()}*\n\n${listText}`, mentions: listMembers });
                }
                return sock.sendMessage(sender, { text: `👥 List *${name}*: ${customLists[sender][name].length} member.` });
            }

            if (cmd === '!game') {
                const gameType = args[1]?.toLowerCase();
                
                if (gameType === 'tebakangka') {
                    const target = Math.floor(Math.random() * 100) + 1;
                    gameData[sender] = { type: 'tebakangka', target, attempts: 0 };
                    return sock.sendMessage(sender, { text: "🎮 *GAME: TEBAK ANGKA*\n\nAku sudah memilih angka antara *1 sampai 100*. Coba tebak!\n\n_Ketik angka langsung untuk menebak._" });
                } 
                
                if (gameType === 'suit') {
                    gameData[sender] = { type: 'suit' };
                    return sock.sendMessage(sender, { text: "🎮 *GAME: SUIT*\n\nPilih salah satu:\n👊 *Batu*\n✋ *Kertas*\n✌️ *Gunting*\n\n_Ketik pilihannya langsung ya!_" });
                }

                if (gameType === 'tictactoe') {
                    gameData[sender] = { 
                        type: 'tictactoe', 
                        board: ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
                        turn: 'user'
                    };
                    const renderBoard = (b) => `*${b[0]} | ${b[1]} | ${b[2]}*\n*${b[3]} | ${b[4]} | ${b[5]}*\n*${b[6]} | ${b[7]} | ${b[8]}*`;
                    return sock.sendMessage(sender, { 
                        text: `🎮 *GAME: TIC TAC TOE*\n\nKamu: *X* | Bot: *O*\n\n${renderBoard(gameData[sender].board)}\n\n_Ketik angka 1-9 untuk melangkah!_` 
                    });
                }

                if (gameType === 'tebakkata') {
                    const wordList = [
                        { w: 'belinda', h: 'Nama asisten AI Studio 234.' },
                        { w: 'whatsapp', h: 'Aplikasi chat hijau tempat kita berada sekarang.' },
                        { w: 'robot', h: 'Mesin elektronik yang bisa mengerjakan tugas manusia.' },
                        { w: 'indonesia', h: 'Negara dengan bendera merah putih.' },
                        { w: 'internet', h: 'Jaringan dunia yang menghubungkan semua orang.' },
                        { w: 'koding', h: 'Kegiatan menulis instruksi untuk komputer.' },
                        { w: 'komputer', h: 'Alat elektronik yang punya monitor, CPU, dan keyboard.' },
                        { w: 'danta', h: 'Nama pencipta bot Belinda AI.' }
                    ];
                    const picked = wordList[Math.floor(Math.random() * wordList.length)];
                    gameData[sender] = { 
                        type: 'tebakkata', 
                        word: picked.w, 
                        hint: picked.h,
                        guessed: [], 
                        lives: 6 
                    };
                    const display = picked.w.split('').map(l => '_').join(' ');
                    return sock.sendMessage(sender, { 
                        text: `🎮 *GAME: TEBAK KATA*\n\nKata: ${display}\nNyawa: ❤️ ${gameData[sender].lives}\n\n*Petunjuk:* ${picked.h}\n\n_Ketik satu huruf untuk menebak!_` 
                    });
                }

                if (gameType === 'math') {
                    const a = Math.floor(Math.random() * 50) + 1;
                    const b = Math.floor(Math.random() * 50) + 1;
                    const op = ['+', '-', '*'][Math.floor(Math.random() * 3)];
                    let target = 0;
                    if (op === '+') target = a + b;
                    else if (op === '-') target = a - b;
                    else target = a * b;

                    gameData[sender] = { type: 'math', target };
                    return sock.sendMessage(sender, { text: `🎮 *GAME: CEPAT TEPAT*\n\nBerapakah hasil dari:\n*${a} ${op} ${b} = ?*\n\n_Ketik jawabannya langsung!_` });
                }

                if (gameType === 'tebaktebakan') {
                    const puzzles = [
                        { q: "Makan apa yang tidak pernah kenyang?", a: "makan hati" },
                        { q: "Huruf apa yang paling kedinginan?", a: "huruf b" },
                        { q: "Lemari apa yang bisa dimasukkan ke kantong?", a: "lemaribu" },
                        { q: "Sapi, sapi apa yang bisa lari cepat?", a: "sapida motor" },
                        { q: "Kenapa di komputer ada tulisan 'ENTER'?", a: "karena kalau 'ENTAR' programnya gak jalan-jalan" }
                    ];
                    const picked = puzzles[Math.floor(Math.random() * puzzles.length)];
                    gameData[sender] = { 
                        type: 'tebaktebakan', 
                        answer: picked.a.toLowerCase(),
                        wrongAttempts: 0 
                    };
                    return sock.sendMessage(sender, { text: `🎮 *GAME: TEBAK-TEBAKAN*\n\n*Pertanyaan:* ${picked.q}\n\n_Ketik jawabannya langsung ya!_` });
                }

                if (gameType === 'blackjack') {
                    const drawCard = () => Math.floor(Math.random() * 10) + 1;
                    const userCard1 = drawCard();
                    const userCard2 = drawCard();
                    const botCard1 = drawCard();
                    
                    gameData[sender] = { 
                        type: 'blackjack', 
                        userCards: [userCard1, userCard2], 
                        botCards: [botCard1],
                        userTotal: userCard1 + userCard2,
                        botTotal: botCard1
                    };

                    const response = `🃏 *GAME: BLACKJACK*\n\n` +
                                     `Kartu Kamu: *${gameData[sender].userCards.join(', ')}* (Total: ${gameData[sender].userTotal})\n` +
                                     `Kartu Bot: *${gameData[sender].botCards.join(', ')}* (Total: ?)\n\n` +
                                     `Ketik *'hit'* untuk ambil kartu, atau *'stand'* untuk berhenti.`;
                    
                    return sock.sendMessage(sender, { text: response });
                }

                if (gameType === 'mine') {
                    const grid = Array(25).fill('🟦');
                    const mines = [];
                    while(mines.length < 5) {
                        const r = Math.floor(Math.random() * 25);
                        if(!mines.includes(r)) mines.push(r);
                    }
                    gameData[sender] = { type: 'mine', grid, mines, revealed: [], gameOver: false };
                    const renderGrid = (g) => {
                        let res = "";
                        for(let i=0; i<5; i++) {
                            res += g.slice(i*5, i*5+5).join(' ') + "\n";
                        }
                        return res;
                    };
                    return sock.sendMessage(sender, { text: `💣 *GAME: MINESWEEPER*\n\n${renderGrid(grid)}\nAda 5 ranjau tersembunyi! Ketik angka *1-25* untuk membuka kotak.` });
                }

                if (gameType === 'tod') {
                    gameData[sender] = { type: 'tod' };
                    return sock.sendMessage(sender, { text: `🎲 *GAME: TRUTH OR DARE*\n\nPilih salah satu:\n👉 Ketik *truth*\n👉 Ketik *dare*` });
                }

                if (gameType === 'siapaaku') {
                    const list = [
                        { q: "Aku bekerja di langit dan mengemudikan burung besi besar.", a: "pilot" },
                        { q: "Aku punya gigi tapi tidak bisa menggigit, untuk merapikan rambut.", a: "sisir" },
                        { q: "Buah dengan kulit berduri dan bau menyengat.", a: "durian" },
                        { q: "Aku punya layar tapi bukan TV, punya keyboard tapi bukan piano.", a: "laptop" },
                        { q: "Aku dimakan saat dingin, rasa coklat atau vanilla, dan cepat meleleh.", a: "es krim" },
                        { q: "Aku benda bulat yang ditendang orang di lapangan hijau.", a: "bola" },
                        { q: "Aku dipakai di telinga untuk mendengarkan musik secara pribadi.", a: "headset" },
                        { q: "Aku punya banyak daun tapi bukan pohon, punya punggung tapi bukan manusia.", a: "buku" }
                    ];
                    const picked = list[Math.floor(Math.random() * list.length)];
                    gameData[sender] = { type: 'siapaaku', answer: picked.a };
                    return sock.sendMessage(sender, { text: `🧐 *GAME: SIAPA AKU?*\n\n*Petunjuk:* ${picked.q}\n\n_Ketik jawabannya langsung!_` });
                }

                if (gameType === 'hangman') {
                    const words = ['teknologi', 'matahari', 'pahlawan', 'sejarah', 'galaksi', 'samudera', 'belajar', 'seniman'];
                    const picked = words[Math.floor(Math.random() * words.length)];
                    gameData[sender] = { type: 'hangman', word: picked, guessed: [], lives: 6 };
                    
                    const hangmanArt = [
                        "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========", // 6 lives
                        "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========", // 5 lives
                        "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========", // 4 lives
                        "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========", // 3 lives
                        "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========", // 2 lives
                        "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========", // 1 life
                        "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n========="  // 0 lives
                    ];

                    const display = picked.split('').map(() => '_').join(' ');
                    return sock.sendMessage(sender, { 
                        text: `😵 *GAME: HANGMAN*\n\n\`\`\`\n${hangmanArt[0]}\n\`\`\`\n\nKata: ${display}\nNyawa: ❤️ 6\n\n_Ketik satu huruf untuk menebak!_` 
                    });
                }

                if (gameType === 'susunkata') {
                    const list = [
                        { w: 'singapura', s: 'a-n-g-i-p-u-r-s' },
                        { w: 'presiden', s: 'n-e-d-i-s-e-p-r' },
                        { w: 'olahraga', s: 'g-a-r-a-h-l-o' },
                        { w: 'matahari', s: 't-a-m-a-h-a-r-i' },
                        { w: 'belajar', s: 'r-a-j-a-l-e-b' },
                        { w: 'robot', s: 't-o-b-o-r' }
                    ];
                    const picked = list[Math.floor(Math.random() * list.length)];
                    gameData[sender] = { type: 'susunkata', answer: picked.w };
                    return sock.sendMessage(sender, { text: `🧩 *GAME: SUSUN KATA*\n\nSusunlah huruf ini: *${picked.s.toUpperCase()}*\n\n_Ketik jawabannya langsung!_` });
                }

                if (gameType === 'emojiquiz') {
                    const list = [
                        { q: "🕷️ 👨", a: "spiderman" },
                        { q: "🧊 🚢", a: "titanic" },
                        { q: "👸 🍎 🍎", a: "snow white" },
                        { q: "🐱 🐭", a: "tom and jerry" },
                        { q: "🦇 👨", a: "batman" },
                        { q: "👑 🦁", a: "lion king" }
                    ];
                    const picked = list[Math.floor(Math.random() * list.length)];
                    gameData[sender] = { type: 'emojiquiz', answer: picked.a };
                    return sock.sendMessage(sender, { text: `🎭 *GAME: EMOJI QUIZ*\n\nTebak judul film/kartun ini:\n${picked.q}\n\n_Ketik jawabannya langsung!_` });
                }

                if (gameType === 'bom') {
                    const wires = ['merah', 'biru', 'kuning', 'hijau'];
                    const bomb = wires[Math.floor(Math.random() * wires.length)];
                    gameData[sender] = { type: 'bom', correct: bomb };
                    return sock.sendMessage(sender, { text: `💣 *GAME: JINAKKAN BOM*\n\nBom akan meledak dalam 10 detik! Potong satu kabel yang benar:\n🔴 Merah\n🔵 Biru\n🟡 Kuning\n🟢 Hijau\n\n_Ketik nama warna kabelnya!_` });
                }

                if (gameType === 'solitaire') {
                    const deck = [1,2,3,4,5,6,7,8,9,10];
                    const cards = Array(9).fill(0).map(() => deck[Math.floor(Math.random() * deck.length)]);
                    gameData[sender] = { type: 'solitaire', cards };
                    return sock.sendMessage(sender, { text: `🃏 *GAME: MINI SOLITAIRE (Elevens)*\n\nKartu di meja:\n*${cards.join(' | ')}*\n\nPilih dua angka yang jumlahnya *11*!\nFormat: *angka1 angka2* (Contoh: *2 9*)` });
                }

                if (gameType === 'horor') {
                    gameData[sender] = { type: 'horor', step: 1 };
                    return sock.sendMessage(sender, { 
                        text: `🏚️ *GAME: MALAM HOROR*\n\nPilih cerita yang ingin kamu mainkan:\n\n🅰️ *Rumah Tua* (Ketik 'rumah')\n🅱️ *Hutan Terlarang* (Ketik 'hutan')\n\n_Pilih salah satu untuk memulai terormu..._` 
                    });
                }

                if (gameType === 'tebakoutput') {
                    gameData[sender] = { type: 'tebakoutput', state: 'choose_lang', score: 0 };
                    return sock.sendMessage(sender, { text: `💻 *GAME: TEBAK OUTPUT*\n\nPilih bahasa pemrograman:\n1. *Python*\n2. *C++*\n\n_Ketik nama bahasanya untuk memulai!_` });
                }

                if (gameType === 'sudoku') {
                    // Simple 4x4 Sudoku boards
                    const boards = [
                        { b: ['1','2','3','4', '3','4','1','2', '2','3','4','1', '4','1','2','3'], mask: [0, 3, 5, 6, 10, 12, 15] },
                        { b: ['2','4','1','3', '1','3','2','4', '3','1','4','2', '4','2','3','1'], mask: [1, 4, 7, 10, 11, 13] },
                        { b: ['4','3','2','1', '1','2','3','4', '2','1','4','3', '3','4','1','2'], mask: [0, 5, 10, 15] }
                    ];
                    const picked = boards[Math.floor(Math.random() * boards.length)];
                    const current = picked.b.map((v, i) => picked.mask.includes(i) ? v : '.');
                    gameData[sender] = { 
                        type: 'sudoku', 
                        solution: picked.b, 
                        board: current,
                        wrongAttempts: 0 
                    };
                    
                    const render = (b) => 
                        `*${b[0]} ${b[1]} | ${b[2]} ${b[3]}*\n` +
                        `*${b[4]} ${b[5]} | ${b[6]} ${b[7]}*\n` +
                        `-----------\n` +
                        `*${b[8]} ${b[9]} | ${b[10]} ${b[11]}*\n` +
                        `*${b[12]} ${b[13]} | ${b[14]} ${b[15]}*`;

                    return sock.sendMessage(sender, { text: `🧩 *GAME: MINI SUDOKU (4x4)*\n\n${render(current)}\n\nFormat: *baris kolom angka*\n(Contoh: *1 2 3* untuk isi baris 1, kol 2 dengan angka 3)\n_Angka 1-4 saja!_` });
                }

                if (gameType === 'woodber') {
                    const nums = Array(12).fill(0).map(() => Math.floor(Math.random() * 9) + 1);
                    gameData[sender] = { 
                        type: 'woodber', 
                        nums,
                        wrongAttempts: 0
                    };
                    return sock.sendMessage(sender, { text: `🔢 *GAME: WOODBER*\n\nAngka di meja:\n*${nums.join(' | ')}*\n\n1. Pilih dua angka yang *sama* atau berjumlah *10*!\n2. Format: *pos1 pos2* (Contoh: *1 5*)\n3. Ketik *add* jika buntu untuk menambah angka.` });
                }

                const gameHeader = 
                    "╭────────────────╮\n" +
                    "│  🕹️ GAME CENTER  │\n" +
                    "╰────────────────╯\n";

                const gameBody = 
                    `🧠 *LOGIC & BRAIN*\n` +
                    `├ 🔢 !game tebakangka\n` +
                    `├ 🧮 !game math\n` +
                    `├ 🧐 !game siapaaku\n` +
                    `├ 🧩 !game susunkata\n` +
                    `├ 💻 !game tebakoutput\n` +
                    `├ 🧩 !game sudoku\n` +
                    `└ 🔢 !game woodber\n\n` +

                    `🎮 *CASUAL FUN*\n` +
                    `├ 👊 !game suit\n` +
                    `├ ❌ !game tictactoe\n` +
                    `├ 🔡 !game tebakkata\n` +
                    `├ 😵 !game hangman\n` +
                    `└ 🎭 !game emojiquiz\n\n` +

                    `🎰 *STRATEGY & LUCK*\n` +
                    `├ 🃏 !game blackjack\n` +
                    `├ 💣 !game mine\n` +
                    `├ 🃏 !game solitaire\n` +
                    `└ 🧨 !game bom\n\n` +

                    `🎭 *INTERACTIVE*\n` +
                    `├ 🎲 !game tod\n` +
                    `├ 🤔 !game tebaktebakan\n` +
                    `└ 🏚️ !game horor\n\n` +
                    `_Ketik perintah di atas untuk bermain!_`;

                return sock.sendMessage(sender, { text: "```\n" + gameHeader + "```\n" + gameBody });
            }

            if (cmd === '!cari') {
                const query = args.slice(1).join(' ');
                if (!query) return sock.sendMessage(sender, { text: "⚠️ Format: !cari {apa_yang_dicari}" });

                const { key } = await sock.sendMessage(sender, { text: "🔍 Sedang mencari informasi di Google..." });
                try {
                    const res = await axios.post(`${pythonUrl}/search`, { msg: query });
                    await sock.sendMessage(sender, { text: res.data, edit: key });
                } catch (e) {
                    await sock.sendMessage(sender, { text: `❌ Gagal mencari: ${e.message}`, edit: key });
                }
                return;
            }

            if (cmd === '!log') {
                if (chatHistory.length === 0) return sock.sendMessage(sender, { text: "📭 No chat history available." });
                const logs = chatHistory.map(h => `${h.time} | ${h.participant}: ${h.text}`).join('\n');
                await sock.sendMessage(sender, { text: `📝 Chat Log:\n\n${logs.slice(-4000)}` });
                return;
            }

            if (cmd === '!shell') {
                const command = args.slice(1).join(' ');
                if (!command) return sock.sendMessage(sender, { text: "⚠️ Please provide a command." });
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use !shell." });

                const { key } = await sock.sendMessage(sender, { text: "⏳ Executing shell..." });
                let output = "";
                let lastUpdate = Date.now();

                try {
                    const response = await axios({
                        method: 'post',
                        url: `${pythonUrl}/shell`,
                        data: { msg: command },
                        responseType: 'stream'
                    });

                    response.data.on('data', async (chunk) => {
                        output += chunk.toString();
                        if (Date.now() - lastUpdate > 3000) {
                            try {
                                await sock.sendMessage(sender, { text: "```\n" + output.slice(-4000) + "\n```", edit: key });
                                lastUpdate = Date.now();
                            } catch (err) {
                                console.error("Rate limit or edit error in shell:", err.message);
                            }
                        }
                    });

                    response.data.on('end', async () => {
                        try {
                            await sock.sendMessage(sender, { text: "```\n" + output.slice(-4000) + "\n```", edit: key });
                        } catch (err) {
                            console.error("Final shell update error:", err.message);
                        }
                    });
                } catch (e) {
                    try {
                        await sock.sendMessage(sender, { text: `❌ Error: ${e.message}`, edit: key });
                    } catch (err) { }
                }
                return;
            }

            if (cmd === '!music') {
                const url = args[1];
                if (!url) return sock.sendMessage(sender, { text: "⚠️ Please provide a Spotify or YouTube link." });

                const isSpotify = url.includes('spotify.com');
                const isYouTube = url.includes('youtube.com') || url.includes('youtu.be') || url.includes('music.youtube.com');

                if (!isSpotify && !isYouTube) {
                    return sock.sendMessage(sender, { text: "❌ Only Spotify or YouTube links are supported for music." });
                }

                const { key } = await sock.sendMessage(sender, { text: `⏳ Processing ${isSpotify ? 'Spotify' : 'YouTube'} music...` });

                const fileNameBase = `music_${Date.now()}`;
                const { spawn } = require('child_process');
                const path = require('path');

                let searchQuery = url;
                if (isSpotify) {
                    try {
                        const response = await axios.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
                        // Improved Regex to catch both Title and Artist
                        const matchTitle = response.data.match(/<title>(.*?)<\/title>/);
                        if (matchTitle && matchTitle[1]) {
                            let cleanTitle = matchTitle[1]
                                .replace(/ \| Spotify/g, '')
                                .replace(/song and lyrics by /g, ' - ')
                                .replace(/song by /g, ' - ')
                                .trim();
                            searchQuery = cleanTitle;
                            console.log(`🎵 [SPOTIFY DATA] Searching for: ${searchQuery}`);
                        }
                    } catch (e) {
                        console.error("Spotify fetch error:", e.message);
                    }
                }

                const platform = process.platform;
                const isDesktop = platform === 'win32' || platform === 'darwin'; 
                const audioFormat = isDesktop ? 'mp3' : 'opus';
                const audioMime = isDesktop ? 'audio/mpeg' : 'audio/ogg; codecs=opus';
                const isPtt = true;

                // Direct URL for YouTube/YouTube Music, search only for Spotify
                const finalQuery = (isYouTube) ? url : `ytsearch1:${searchQuery}`;

                const args_dl = [
                    '--print', 'after_move:filepath',
                    '-x', '--audio-format', audioFormat,
                    '--no-playlist', '--no-check-certificate',
                    '--audio-quality', '0',
                    '-o', `${fileNameBase}.%(ext)s`,
                    finalQuery
                ];

                console.log(`📡 [DL START] OS: ${platform} | Format: ${audioFormat} | Query: ${finalQuery}`);

                const ls = spawn('yt-dlp', args_dl);
                let lastUpdate = Date.now();
                let stderrData = "";
                let stdoutData = "";

                ls.stderr.on('data', (data) => { 
                    const err = data.toString();
                    stderrData += err;
                    console.error(`[yt-dlp STDERR] ${err.trim()}`);
                });

                ls.stdout.on('data', (data) => {
                    const output = data.toString();
                    stdoutData += output;
                    console.log(`[yt-dlp STDOUT] ${output.trim()}`);
                    const match = output.match(/(\d+\.\d+)%/);
                    if (match && Date.now() - lastUpdate > 4000) {
                        const percent = parseFloat(match[1]);
                        const progress = Math.floor(percent / 10);
                        const bar = '▓'.repeat(progress) + '░'.repeat(10 - progress);
                        sock.sendMessage(sender, { text: `🎵 *Downloading Music (${audioFormat.toUpperCase()})*\n\n[${bar}] ${percent}%\n\n_Sedang memproses pesan suara..._`, edit: key }).catch(() => { });
                        lastUpdate = Date.now();
                    }
                });

                ls.on('close', async (code) => {
                    if (code === 0) {
                        console.log(`✅ [DL SUCCESS] yt-dlp finished for: ${fileNameBase}`);
                        const fullBar = '█'.repeat(20);
                        await sock.sendMessage(sender, { text: `⏳ Processing ${isSpotify ? 'Spotify' : 'YouTube'} music... ✅\n\n🎵 *Downloading Audio*\n\`[${fullBar}] 100.0%\` \n\n_Finishing up, sending to WhatsApp..._`, edit: key }).catch(() => { });
                        await new Promise(resolve => setTimeout(resolve, 2000));

                        const lines = stdoutData.trim().split('\n');
                        let filePath = null;

                        for (const line of lines.reverse()) {
                            const trimmedLine = line.trim();
                            if (trimmedLine && fs.existsSync(trimmedLine) && trimmedLine.includes(fileNameBase)) {
                                filePath = trimmedLine;
                                break;
                            }
                        }

                        if (!filePath) {
                            try {
                                const files = fs.readdirSync(process.cwd());
                                const found = files.find(f => f.startsWith(fileNameBase));
                                if (found) filePath = path.join(process.cwd(), found);
                            } catch (e) { console.error("File search error:", e); }
                        }

                        if (!filePath) {
                            console.error(`❌ [ERROR] Could not find file ${fileNameBase} even after success!`);
                            try { await sock.sendMessage(sender, { text: "❌ Error: Could not find downloaded file. Check console.", edit: key }); } catch (e) { }
                            return;
                        }

                        try {
                            console.log(`📤 [SENDING] File: ${filePath} | Mime: ${audioMime}`);
                            const audioBuffer = fs.readFileSync(filePath);
                            await sock.sendMessage(sender, { 
                                audio: audioBuffer, 
                                mimetype: audioMime, 
                                ptt: isPtt 
                            });

                            try { await sock.sendMessage(sender, { text: "✅ Music sent successfully!", edit: key }); } catch (e) { }
                            setTimeout(() => { if (fs.existsSync(filePath)) fs.unlinkSync(filePath); }, 60000);
                        } catch (e) {
                            console.error(`❌ [SEND ERROR] ${e.message}`);
                            try { await sock.sendMessage(sender, { text: `❌ Error sending: ${e.message}`, edit: key }); } catch (err) { }
                            if (filePath && fs.existsSync(filePath)) fs.unlinkSync(filePath);
                        }
                    } else {
                        console.error(`❌ [DL FAILED] Code: ${code} | Errors: ${stderrData}`);
                        return sock.sendMessage(sender, { text: `❌ Failed to download music. (Code ${code})\n\n_Error:_ ${stderrData.slice(-100)}`, edit: key });
                    }
                });

                return;
            }

            if (cmd === '!video') {
                const url = args[1];
                if (!url) return sock.sendMessage(sender, { text: "⚠️ Please provide a YouTube link." });

                const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
                if (!isYouTube) {
                    return sock.sendMessage(sender, { text: "❌ Only YouTube links are supported untuk !video. (TikTok, IG, FB tidak didukung)" });
                }

                const { key } = await sock.sendMessage(sender, { text: "⏳ Downloading YouTube video..." });

                const fileNameBase = `video_${Date.now()}`;
                const { spawn } = require('child_process');
                const path = require('path');

                const args_dl = ['--print', 'after_move:filepath', '-f', 'best[height<=480][ext=mp4]/best[ext=mp4]/best', '--no-playlist', '--no-check-certificate', '-o', `${fileNameBase}.%(ext)s`, url];

                const ls = spawn('yt-dlp', args_dl);
                let lastUpdate = Date.now();
                let stderrData = "";
                let stdoutData = "";

                ls.stderr.on('data', (data) => { stderrData += data.toString(); });
                ls.stdout.on('data', (data) => {
                    const output = data.toString();
                    stdoutData += output;
                    const match = output.match(/(\d+\.\d+)%/);
                    if (match && Date.now() - lastUpdate > 4000) {
                        const percent = parseFloat(match[1]);
                        const progress = Math.floor(percent / 10);
                        const bar = '█'.repeat(progress) + '▒'.repeat(10 - progress);
                        sock.sendMessage(sender, { text: `🎬 *Downloading Video*\n\n[${bar}] ${percent}%\n\n_Video sedang diproses..._`, edit: key }).catch(() => { });
                        lastUpdate = Date.now();
                    }
                });

                ls.on('close', async (code) => {
                    if (code !== 0) {
                        console.error("yt-dlp error:", stderrData);
                        try { await sock.sendMessage(sender, { text: `❌ Failed to download video. Error: ${stderrData.slice(-100)}`, edit: key }); } catch (e) { }
                        return;
                    }

                    const lines = stdoutData.trim().split('\n');
                    let filePath = null;

                    // Search for a valid filepath in all lines of stdout
                    for (const line of lines.reverse()) {
                        const trimmedLine = line.trim();
                        if (trimmedLine && fs.existsSync(trimmedLine) && trimmedLine.includes(fileNameBase)) {
                            filePath = trimmedLine;
                            break;
                        }
                    }

                    if (!filePath) {
                        const files = fs.readdirSync(process.cwd());
                        const found = files.find(f => f.startsWith(fileNameBase));
                        filePath = found ? path.join(process.cwd(), found) : null;
                    }

                    if (!filePath) {
                        try { await sock.sendMessage(sender, { text: "❌ Error: Video file not found on disk.", edit: key }); } catch (e) { }
                        return;
                    }

                    try {
                        try { await sock.sendMessage(sender, { text: "📤 *Sending video...*", edit: key }); } catch (e) { }
                        await sock.sendMessage(sender, { video: { url: filePath }, caption: "✅ Video sent!" });
                        try { await sock.sendMessage(sender, { text: "✅ Video sent!", edit: key }); } catch (e) { }
                        fs.unlinkSync(filePath);
                    } catch (e) {
                        try { await sock.sendMessage(sender, { text: `❌ Error: ${e.message}`, edit: key }); } catch (err) { }
                        if (filePath && fs.existsSync(filePath)) fs.unlinkSync(filePath);
                    }
                });
                return;
            }

            if (cmd === '!gen') {
                const format = args[1];
                const prompt = args.slice(2).join(' ');
                if (!format || !prompt) return sock.sendMessage(sender, { text: "⚠️ Format: !gen {type:ext} {prompt}\nContoh: !gen scr:py bot auto chat" });

                const { key } = await sock.sendMessage(sender, { text: `⏳ Generating/Searching ${format}... Please wait.` });

                try {
                    const res = await axios.post(`${pythonUrl}/gen`, { sender, format, msg: prompt });

                    if (typeof res.data === 'string') {
                        await sock.sendMessage(sender, { text: res.data, edit: key });
                    } else if (res.data.type === 'document') {
                        const fileName = res.data.path;
                        let mimetype = 'application/octet-stream';

                        if (format.startsWith('doc:')) {
                            const docFmt = format.split(':')[1];
                            mimetype = 'application/vnd.openxmlformats-officedocument.' + (docFmt === 'ppt' ? 'presentationml.presentation' : docFmt === 'word' ? 'wordprocessingml.document' : 'spreadsheetml.sheet');
                        } else if (format.startsWith('scr:')) {
                            const ext = format.split(':')[1];
                            const mimeMap = {
                                'py': 'text/x-python',
                                'lua': 'text/x-lua',
                                'js': 'application/javascript',
                                'ts': 'application/typescript',
                                'cpp': 'text/x-c++src',
                                'c': 'text/x-csrc',
                                'cs': 'text/x-csharp',
                                'java': 'text/x-java',
                                'go': 'text/x-go',
                                'rs': 'text/x-rustsrc',
                                'php': 'application/x-httpd-php',
                                'rb': 'text/x-ruby',
                                'sh': 'application/x-sh',
                                'sql': 'text/x-sql'
                            };
                            mimetype = mimeMap[ext] || 'application/octet-stream';
                        } else if (format.startsWith('3dm:')) {
                            mimetype = 'application/octet-stream';
                        }

                        await sock.sendMessage(sender, {
                            document: { url: `./${fileName}` },
                            mimetype: mimetype,
                            fileName: fileName,
                            caption: `✅ Successfully generated/fetched ${format.toUpperCase()}`
                        });
                        await sock.sendMessage(sender, { text: `✅ File delivered!`, edit: key }).catch(() => { });
                        fs.unlinkSync(fileName);
                    }
                } catch (e) {
                    await sock.sendMessage(sender, { text: `❌ Error: ${e.message}`, edit: key });
                }
                return;
            }

            if (cmd === '!quran') {
                const query = args[1];
                if (!query || !query.includes(':')) return sock.sendMessage(sender, { text: "⚠️ Format: !quran {surah}:{ayah} (Contoh: !quran 1:1)" });

                const [surah, ayah] = query.split(':');
                try {
                    const url = `https://api.alquran.cloud/v1/ayah/${surah}:${ayah}/editions/quran-uthmani,id.indonesian,en.transliteration`;
                    const response = await axios.get(url);
                    const data = response.data.data;
                    const arab = data[0].text;
                    const arti = data[1].text;
                    const latin = data[2].text;
                    const surahName = data[0].surah.englishName;
                    const result = `\n📖 *Surah ${surahName} (${surah}:${ayah})*\n\n${arab}\n\n_(${latin})_\n\n*Artinya:* ${arti}`;
                    await sock.sendMessage(sender, { text: result });
                } catch (e) {
                    await sock.sendMessage(sender, { text: `❌ Gagal mengambil ayat: ${e.message}` });
                }
                return;
            }

            if (cmd === '!help') {
                const asciiHelp =
                    "```\n" +
                    "╔══╗╔══╗╔╗──╔══╗╔═╗─╔══╗──╔══╗╔══╗\n" +
                    "║╔╗║║╔═╝║║──╚╗╔╝║║╚╗║╔╗║──║╔╗║╚╗╔╝\n" +
                    "║╠╩╣║══╗║║───║║─║╔╗║║║║║──║╠╣║─║║─\n" +
                    "║╚═╝╚══╝╚══╝─╚╝─╚╝╚╝╚══╝──╚╝╚╝─╚╝─\n" +
                    "```\n\n";

                return sock.sendMessage(sender, {
                    text: asciiHelp + `🤖 *BELINDA AI HELP MENU*\n\n` +
                        `*Main Features:*\n` +
                        `🔍 !cari {query} (DuckDuckGo)\n` +
                        `🖼️ !image {url} (Download Image)\n` +
                        `🎵 !music {url} (Spotify/YT)\n` +
                        `🎬 !video {url} (YouTube)\n` +
                        `📖 !quran {surah}:{ayah}\n` +
                        `🌦️ !cuaca {kota}\n` +
                        `🕌 !sholat {kota}\n` +
                        `🎮 !game (Text Games)\n\n` +
                        `*Social & Info:*\n` +
                        `💤 !afk {alasan}\n` +
                        `📜 !rules (Group Rules)\n` +
                        `✨ !font {teks}\n` +
                        `ℹ️ !info (AI Status)\n` +
                        `📝 !log (Recent logs)\n\n` +
                        `*Education (Quiz):*\n` +
                        `📝 !quiz [amount] [mapel] [level]\n` +
                        `⏭️ !next / 🧹 !reset\n\n` +
                        `*Generation Tools:*\n` +
                        `🎨 !gen doc:{word|ppt|excel} {prompt}\n` +
                        `💻 !gen scr:{ext} {prompt}\n` +
                        `📦 !gen 3dm:{ext} {prompt}\n\n` +
                        `*Admin Tools:*\n` +
                        `🛡️ !anti {toxic|link|spam} {true|false}\n` +
                        `🤖 !bot (on/off)\n` +
                        `💻 !shell {command}\n` +
                        `📊 !top (View activity)\n` +
                        `👥 !absen (List members)\n` +
                        `📋 !list {mode} {name}\n` +
                        `⏳ !limit {num|inf}\n` +
                        `➕ !add / 👢 !kick {nomor}\n` +
                        `🔓 !open / 🔒 !close\n` +
                        `🧹 !zero (Clear context)\n`
                });
            }

            if (cmd === '!top') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                if (chatHistory.length === 0) return sock.sendMessage(sender, { text: "📭 No chat history found." });
                
                const counts = {};
                chatHistory.forEach(h => {
                    counts[h.participant] = (counts[h.participant] || 0) + 1;
                });
                
                const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
                const mentions = sorted.map(e => e[0]);
                const list = sorted.map((e, i) => `${i + 1}. @${e[0].split('@')[0]} : ${e[1]} pesan`).join('\n');
                
                return sock.sendMessage(sender, { text: `📊 *TOP 10 MEMBER AKTIF*\n\n${list}`, mentions });
            }

            if (cmd === '!absen') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const meta = await sock.groupMetadata(sender);
                
                const mentions = meta.participants.map(p => p.id);
                const list = meta.participants.map((p, i) => `${i + 1}. @${p.id.split('@')[0]}`).join('\n');
                
                return sock.sendMessage(sender, { text: `👥 *DAFTAR ABSEN MEMBER*\n\n${list}`, mentions });
            }

            if (cmd === '!quiz') {
                const jml = parseInt(args[1]);
                const mapelInput = args[2]?.toLowerCase();
                const diffInput = args[3]?.toLowerCase();
                const validMapel = ['tik', 'mtk', 'ipa', 'ips', 'b.ing', 'b.indo', 'umum', 'sbdp', 'pkwu', 'pai', 'pkn'];
                const validDiff = { 'ez': 'mudah', 'mid': 'sedang/normal', 'hrd': 'susah/olympiad' };

                if (isNaN(jml) || jml < 10 || jml > 30) {
                    return sock.sendMessage(sender, { text: "❌ Jumlah soal minimal 10 dan maksimal 30!" });
                }
                if (!validMapel.includes(mapelInput)) {
                    return sock.sendMessage(sender, { text: `❌ Mapel tidak valid!\nPilihan: ${validMapel.join(', ')}` });
                }
                if (!validDiff[diffInput]) {
                    return sock.sendMessage(sender, { text: "❌ Level tidak valid! Pilih: ez, mid, atau hrd." });
                }

                quizData[sender] = { maxSoal: jml, currentNum: 0, mapel: mapelInput, diff: validDiff[diffInput] };
                await createQuiz(sender);
                return;
            }

            if (cmd === '!next') {
                if (!quizData[sender]) return sock.sendMessage(sender, { text: "⚠️ Mulai kuis dulu!" });
                if (!nextRequests[sender]) nextRequests[sender] = [];
                if (!nextRequests[sender].includes(participant)) nextRequests[sender].push(participant);
                if (nextRequests[sender].length < 2) {
                    return sock.sendMessage(sender, { text: `🔔 *${nextRequests[sender].length}/2* klik !next. Butuh 1 lagi.` });
                }

                const data = quizData[sender];
                const keyLetter = ['A', 'B', 'C', 'D', 'E'][data.index];
                try {
                    const explanationPrompt = `Ini adalah soal kuis ${data.mapel}: "${data.question}". ` +
                        `Jawabannya adalah ${keyLetter}. ` +
                        `Tolong berikan penjelasan/pembahasan singkat kenapa itu jawabannya.`;
                    const exp = await axios.post(`${pythonUrl}/chat`, { sender, msg: explanationPrompt });
                    await sock.sendMessage(sender, { text: `📢 *PEMBAHASAN*\n\n✅ Kunci: *${keyLetter}*\n📖 ${exp.data}` });
                } catch (e) {
                    console.error("Gagal mendapatkan penjelasan:", e.message);
                }
                await createQuiz(sender);
                return;
            }

            if (cmd === '!reset') {
                delete quizData[sender];
                delete nextRequests[sender];
                return sock.sendMessage(sender, { text: "🧹 *Data kuis di grup ini telah direset.* Silakan mulai kuis baru dengan !quiz." });
            }

            if (cmd === '!bot') {
                if (!(await isAdmin())) return;
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "toggle" });
                return sock.sendMessage(sender, { text: `🤖 AI: ${res.data.active ? 'ON' : 'OFF'}` });
            }

            if (cmd === '!info') {
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "get" });
                return sock.sendMessage(sender, {
                    text: `*ℹ️ STATUS*\nAI: ${res.data.active ? 'ON ✅' : 'OFF ❌'}\nQuiz: Active ✅`
                });
            }

            // FALLBACK UNKNOWN COMMAND
            return sock.sendMessage(sender, { text: `❌ Perintah *${cmd}* tidak dikenali. Ketik !help untuk melihat daftar perintah.` });
        }

        // --- GAME LOGIC HANDLER (NON-AI) ---
        if (gameData[sender] && !text.startsWith('!')) {
            const game = gameData[sender];
            if (game.type === 'tebakangka') {
                const guess = parseInt(text);
                if (!isNaN(guess)) {
                    game.attempts++;
                    if (guess === game.target) {
                        const attempts = game.attempts;
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🎉 *SELAMAT!* Angka yang benar adalah *${game.target}*.\n\nKamu berhasil menebak dalam *${attempts}* percobaan.` });
                    } else if (guess < game.target) {
                        return sock.sendMessage(sender, { text: "📉 *Terlalu Rendah!* Coba lagi." });
                    } else {
                        return sock.sendMessage(sender, { text: "📈 *Terlalu Tinggi!* Coba lagi." });
                    }
                }
            }
        }

        // --- GAME LOGIC HANDLER (NON-AI) ---
        if (gameData[sender] && !text.startsWith('!')) {
            const game = gameData[sender];
            const input = text.toLowerCase().trim();

            if (game.type === 'tebakangka') {
                const guess = parseInt(input);
                if (!isNaN(guess)) {
                    game.attempts++;
                    if (guess === game.target) {
                        const attempts = game.attempts;
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🎉 *SELAMAT!* Angka yang benar adalah *${game.target}*.\n\nKamu berhasil menebak dalam *${attempts}* percobaan.` });
                    } else if (guess < game.target) {
                        return sock.sendMessage(sender, { text: "📉 *Terlalu Rendah!* Coba lagi." });
                    } else {
                        return sock.sendMessage(sender, { text: "📈 *Terlalu Tinggi!* Coba lagi." });
                    }
                }
            }

            if (game.type === 'suit') {
                const options = ['batu', 'gunting', 'kertas'];
                if (options.includes(input)) {
                    const botChoice = options[Math.floor(Math.random() * options.length)];
                    let result = "";
                    let emoji = { 'batu': '👊', 'gunting': '✌️', 'kertas': '✋' };

                    if (input === botChoice) {
                        result = "🤝 *SERI!* Kita sama-sama pilih hal yang sama.";
                    } else if (
                        (input === 'batu' && botChoice === 'gunting') ||
                        (input === 'gunting' && botChoice === 'kertas') ||
                        (input === 'kertas' && botChoice === 'batu')
                    ) {
                        result = "🥳 *KAMU MENANG!*";
                    } else {
                        result = "😜 *AKU MENANG!*";
                    }

                    const response = `🎮 *HASIL SUIT*\n\n` +
                                     `Kamu: ${emoji[input]} (${input.toUpperCase()})\n` +
                                     `Aku: ${emoji[botChoice]} (${botChoice.toUpperCase()})\n\n` +
                                     `${result}`;
                    
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: response });
                }
            }

            if (game.type === 'tictactoe') {
                const pos = parseInt(input) - 1;
                if (isNaN(pos) || pos < 0 || pos > 8 || game.board[pos] === 'X' || game.board[pos] === 'O') {
                    return; // Ignore invalid move
                }

                // --- HELPER FUNCTIONS ---
                const checkWin = (b) => {
                    const winPatterns = [
                        [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
                        [0, 3, 6], [1, 4, 7], [2, 5, 8], // Cols
                        [0, 4, 8], [2, 4, 6]             // Diagonals
                    ];
                    for (const [a, b_idx, c] of winPatterns) {
                        if (b[a] !== (a+1).toString() && b[a] === b[b_idx] && b[a] === b[c]) return b[a];
                    }
                    return b.every(cell => cell === 'X' || cell === 'O') ? 'draw' : null;
                };

                const renderBoard = (b) => `*${b[0]} | ${b[1]} | ${b[2]}*\n*${b[3]} | ${b[4]} | ${b[5]}*\n*${b[6]} | ${b[7]} | ${b[8]}*`;

                // 1. User Move
                game.board[pos] = 'X';
                let winner = checkWin(game.board);

                if (winner) {
                    const resultText = winner === 'draw' ? "🤝 *SERI!* Game berakhir tanpa pemenang." : "🥳 *KAMU MENANG!* Selamat!";
                    const finalBoard = renderBoard(game.board);
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🎮 *TIC TAC TOE: FINISH*\n\n${finalBoard}\n\n${resultText}` });
                }

                // 2. Bot Move (Simple AI)
                const emptyCells = game.board.filter(c => c !== 'X' && c !== 'O');
                // Try to win, else block, else random
                let botPos = -1;
                // Strategy: just random for now to keep it simple, or smart? Let's do random for brevity.
                const randomIndex = Math.floor(Math.random() * emptyCells.length);
                botPos = parseInt(emptyCells[randomIndex]) - 1;

                game.board[botPos] = 'O';
                winner = checkWin(game.board);

                if (winner) {
                    const resultText = winner === 'draw' ? "🤝 *SERI!* Game berakhir tanpa pemenang." : "😜 *BOT MENANG!* Coba lagi ya.";
                    const finalBoard = renderBoard(game.board);
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🎮 *TIC TAC TOE: FINISH*\n\n${finalBoard}\n\n${resultText}` });
                }

                return sock.sendMessage(sender, { 
                    text: `🎮 *TIC TAC TOE*\n\nKamu: *X* | Bot: *O*\n\n${renderBoard(game.board)}\n\n_Giliranmu! Ketik 1-9._` 
                });
            }

            if (game.type === 'tebakkata') {
                const char = input[0];
                if (!char) return;

                if (game.guessed.includes(char)) {
                    return sock.sendMessage(sender, { text: `⚠️ Huruf *${char.toUpperCase()}* sudah pernah ditebak!` });
                }

                game.guessed.push(char);
                if (game.word.includes(char)) {
                    // Correct guess
                    const display = game.word.split('').map(l => game.guessed.includes(l) ? l.toUpperCase() : '_').join(' ');
                    if (!display.includes('_')) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🥳 *MENANG!* Kamu berhasil menebak kata: *${game.word.toUpperCase()}*` });
                    }
                    return sock.sendMessage(sender, { text: `✅ *Benar!*\n\nKata: ${display}\nNyawa: ❤️ ${game.lives}` });
                } else {
                    // Wrong guess
                    game.lives--;
                    if (game.lives <= 0) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `💀 *KALAH!* Kamu kehabisan nyawa.\n\nKata yang benar adalah: *${game.word.toUpperCase()}*` });
                    }
                    const display = game.word.split('').map(l => game.guessed.includes(l) ? l.toUpperCase() : '_').join(' ');
                    return sock.sendMessage(sender, { text: `❌ *Salah!*\n\nKata: ${display}\nNyawa: ❤️ ${game.lives}\n*Petunjuk:* ${game.hint}` });
                }
            }

            if (game.type === 'math') {
                const ans = parseInt(input);
                if (!isNaN(ans)) {
                    if (ans === game.target) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🎉 *TEPAT!* Jawabanmu benar.` });
                    } else {
                        return sock.sendMessage(sender, { text: "❌ *Salah!* Coba hitung lagi." });
                    }
                }
            }

            if (game.type === 'tebaktebakan') {
                if (input === game.answer) {
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🎉 *BENAR!* Kamu memang pintar.` });
                } else {
                    game.wrongAttempts++;
                    let response = "❌ *Salah!* Ayo coba tebak lagi.";
                    
                    if (game.wrongAttempts >= 3) {
                        const ans = game.answer;
                        const hint = ans[0] + ans.slice(1, -1).replace(/[a-z0-9]/g, '_') + ans[ans.length - 1];
                        response += `\n\n💡 *HINT:* ${hint.toUpperCase()}`;
                    }
                    
                    return sock.sendMessage(sender, { text: response });
                }
            }

            if (game.type === 'blackjack') {
                if (input === 'hit') {
                    const newCard = Math.floor(Math.random() * 10) + 1;
                    game.userCards.push(newCard);
                    game.userTotal += newCard;

                    if (game.userTotal > 21) {
                        const finalTotal = game.userTotal;
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `💥 *BUST!* Total kartu kamu ${finalTotal}. Kamu kalah.` });
                    }

                    return sock.sendMessage(sender, { text: `🃏 *BLACKJACK: HIT*\n\nKartu Kamu: *${game.userCards.join(', ')}* (Total: ${game.userTotal})\n\nKetik *'hit'* atau *'stand'*.` });
                }

                if (input === 'stand') {
                    // Bot turn: draw until >= 17
                    while (game.botTotal < 17) {
                        const botCard = Math.floor(Math.random() * 10) + 1;
                        game.botCards.push(botCard);
                        game.botTotal += botCard;
                    }

                    let result = "";
                    if (game.botTotal > 21 || game.userTotal > game.botTotal) {
                        result = "🥳 *KAMU MENANG!*";
                    } else if (game.userTotal < game.botTotal) {
                        result = "😜 *BOT MENANG!*";
                    } else {
                        result = "🤝 *SERI!* Skor kita sama.";
                    }

                    const finalResponse = `🃏 *BLACKJACK: RESULT*\n\n` +
                                          `Kartu Kamu: *${game.userCards.join(', ')}* (Total: ${game.userTotal})\n` +
                                          `Kartu Bot: *${game.botCards.join(', ')}* (Total: ${game.botTotal})\n\n` +
                                          `${result}`;
                    
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: finalResponse });
                }
            }

            if (game.type === 'mine') {
                const pos = parseInt(input) - 1;
                if(isNaN(pos) || pos < 0 || pos > 24 || game.revealed.includes(pos)) return;

                const renderGrid = (g) => {
                    let res = "";
                    for(let i=0; i<5; i++) res += g.slice(i*5, i*5+5).join(' ') + "\n";
                    return res;
                };

                if(game.mines.includes(pos)) {
                    game.grid[pos] = '💣';
                    const finalGrid = renderGrid(game.grid);
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `💥 *BOOM!* Kamu menginjak ranjau.\n\n${finalGrid}\n*GAME OVER!*` });
                } else {
                    game.grid[pos] = '⬜';
                    game.revealed.push(pos);
                    if(game.revealed.length === 20) {
                        const finalGrid = renderGrid(game.grid);
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🎉 *MENANG!* Kamu berhasil membersihkan semua lahan tanpa meledak.\n\n${finalGrid}` });
                    }
                    return sock.sendMessage(sender, { text: `✅ *AMAN!*\n\n${renderGrid(game.grid)}\nKetik angka lain (1-25).` });
                }
            }

            if (game.type === 'siapaaku') {
                if (input === game.answer) {
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🎉 *BENAR!* Jawaban yang tepat adalah *${input.toUpperCase()}*.` });
                } else {
                    return sock.sendMessage(sender, { text: "❌ *Salah!* Ayo coba tebak lagi." });
                }
            }

            if (game.type === 'hangman') {
                const char = input[0];
                if (!char) return;

                if (game.guessed.includes(char)) {
                    return sock.sendMessage(sender, { text: `⚠️ Huruf *${char.toUpperCase()}* sudah pernah ditebak!` });
                }

                const hangmanArt = [
                    "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========", // 6 lives
                    "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========", // 5 lives
                    "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========", // 4 lives
                    "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========", // 3 lives
                    "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========", // 2 lives
                    "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========", // 1 life
                    "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n========="  // 0 lives
                ];

                game.guessed.push(char);
                if (game.word.includes(char)) {
                    const display = game.word.split('').map(l => game.guessed.includes(l) ? l.toUpperCase() : '_').join(' ');
                    if (!display.includes('_')) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `🥳 *MENANG!* Kamu berhasil menebak kata: *${game.word.toUpperCase()}*` });
                    }
                    const artIndex = 6 - game.lives;
                    return sock.sendMessage(sender, { text: `✅ *Benar!*\n\n\`\`\`\n${hangmanArt[artIndex]}\n\`\`\`\n\nKata: ${display}\nNyawa: ❤️ ${game.lives}` });
                } else {
                    game.lives--;
                    const artIndex = 6 - game.lives;
                    if (game.lives <= 0) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `💀 *KALAH!* Kamu digantung.\n\n\`\`\`\n${hangmanArt[6]}\n\`\`\`\n\nKata yang benar adalah: *${game.word.toUpperCase()}*` });
                    }
                    const display = game.word.split('').map(l => game.guessed.includes(l) ? l.toUpperCase() : '_').join(' ');
                    return sock.sendMessage(sender, { text: `❌ *Salah!*\n\n\`\`\`\n${hangmanArt[artIndex]}\n\`\`\`\n\nKata: ${display}\nNyawa: ❤️ ${game.lives}` });
                }
            }

            if (game.type === 'susunkata' || game.type === 'emojiquiz') {
                if (input === game.answer) {
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🎉 *MANTAP!* Jawabanmu benar: *${input.toUpperCase()}*` });
                } else {
                    return sock.sendMessage(sender, { text: "❌ *Salah!* Coba lagi ya." });
                }
            }

            if (game.type === 'bom') {
                if (input === game.correct) {
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: "✂️ *KLIK...* \n\n🎉 *SELAMAT!* Bom berhasil dijinakkan. Kamu pahlawan hari ini!" });
                } else {
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: "✂️ *BOOOOMMM!!!* 💥\n\nKamu memotong kabel yang salah. Seluruh gedung hancur!" });
                }
            }

            if (game.type === 'tebakoutput') {
                const problems = {
                    python: [
                        { q: "x = 5\ny = 3\nprint(x + y * 2)", a: "11" },
                        { q: "s = 'ABC'\nprint(s[::-1])", a: "CBA" },
                        { q: "nums = [1, 2, 3]\nnums.append(4)\nprint(len(nums))", a: "4" },
                        { q: "x = True\ny = False\nprint(x and not y)", a: "True" },
                        { q: "def f(n):\n  return 1 if n <= 1 else n * f(n-1)\nprint(f(3))", a: "6" },
                        { q: "a = [1, 2]\nb = a * 2\nprint(len(b))", a: "4" },
                        { q: "x = '10'\ny = '20'\nprint(x + y)", a: "1020" },
                        { q: "val = 10\nif val > 5:\n  val -= 2\nelse:\n  val += 2\nprint(val)", a: "8" },
                        { q: "txt = 'python'\nprint(txt[1:4])", a: "yth" },
                        { q: "d = {'a': 1, 'b': 2}\nprint(d.get('c', 3))", a: "3" },
                        { q: "x = 0\nfor i in range(3):\n  x += i\nprint(x)", a: "3" },
                        { q: "print(type(5.0) == float)", a: "True" },
                        { q: "a = 7\nb = 2\nprint(a // b)", a: "3" },
                        { q: "s = 'hello'\nprint(s.upper())", a: "HELLO" },
                        { q: "items = (1, 2, 3)\nprint(items[0])", a: "1" }
                    ],
                    cpp: [
                        { q: "int x = 10;\ncout << x / 3;", a: "3" },
                        { q: "string s = \"Hi\";\ncout << s + \"!\";", a: "Hi!" },
                        { q: "int a = 5, b = 2;\ncout << (a % b);", a: "1" },
                        { q: "int x = 0;\nfor(int i=0; i<3; i++) x++;\ncout << x;", a: "3" },
                        { q: "int arr[] = {10, 20, 30};\ncout << arr[1];", a: "20" },
                        { q: "int x = 5;\nint y = ++x;\ncout << y;", a: "6" },
                        { q: "bool b = true;\ncout << !b;", a: "0" },
                        { q: "string s = \"Code\";\ncout << s.length();", a: "4" },
                        { q: "int a = 10, b = 20;\ncout << (a > b ? a : b);", a: "20" },
                        { q: "int x = 15;\nif(x % 2 == 0) cout << \"E\";\nelse cout << \"O\";", a: "O" },
                        { q: "int sum = 0;\nfor(int i=1; i<=2; i++) sum += i;\ncout << sum;", a: "3" },
                        { q: "int n = 5;\nn *= 2 + 1;\ncout << n;", a: "15" },
                        { q: "char c = 'A';\ncout << (int)c;", a: "65" },
                        { q: "int v[2] = {1, 2};\ncout << v[0] + v[1];", a: "3" },
                        { q: "double d = 2.5;\ncout << (int)d * 2;", a: "4" }
                    ]
                };

                if (game.state === 'choose_lang') {
                    const lang = input === 'python' || input === '1' ? 'python' : (input === 'c++' || input === '2' ? 'cpp' : null);
                    if (!lang) return sock.sendMessage(sender, { text: "⚠️ Pilih 'python' atau 'c++' ya!" });
                    
                    game.lang = lang;
                    game.state = 'playing';
                    const p = problems[lang][Math.floor(Math.random() * problems[lang].length)];
                    game.currentAnswer = p.a;
                    return sock.sendMessage(sender, { text: `🚀 *LANGUAGE: ${lang.toUpperCase()}*\n\nBerapakah output dari kode ini?\n\n\`\`\`${lang}\n${p.q}\n\`\`\`\n\n_Ketik jawabannya langsung!_` });
                }

                if (game.state === 'playing') {
                    if (input === game.currentAnswer.toLowerCase()) {
                        game.score++;
                        const pList = problems[game.lang];
                        const p = pList[Math.floor(Math.random() * pList.length)];
                        game.currentAnswer = p.a;
                        return sock.sendMessage(sender, { text: `✅ *BENAR!* Skor kamu: *${game.score}*\n\n*SOAL BERIKUTNYA:*\n\`\`\`${game.lang}\n${p.q}\n\`\`\`\n\n_Ketik jawabannya langsung!_` });
                    } else {
                        const finalScore = game.score;
                        const correct = game.currentAnswer;
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: `❌ *GAME OVER!*\n\nJawaban yang benar adalah: *${correct}*\nSkor Akhir: *${finalScore}*\n\n_Ayo coba lagi untuk melatih logika kodingmu!_` });
                    }
                }
            }

            if (game.type === 'sudoku') {
                const parts = input.split(' ').map(Number);
                if (parts.length === 3) {
                    const r = parts[0] - 1;
                    const c = parts[1] - 1;
                    const val = parts[2].toString();
                    const idx = r * 4 + c;

                    if (r >= 0 && r < 4 && c >= 0 && c < 4 && idx < 16) {
                        if (game.solution[idx] === val) {
                            game.board[idx] = val;
                            game.wrongAttempts = 0; // Reset counter on correct move
                            const render = (b) => 
                                `*${b[0]} ${b[1]} | ${b[2]} ${b[3]}*\n` +
                                `*${b[4]} ${b[5]} | ${b[6]} ${b[7]}*\n` +
                                `-----------\n` +
                                `*${b[8]} ${b[9]} | ${b[10]} ${b[11]}*\n` +
                                `*${b[12]} ${b[13]} | ${b[14]} ${b[15]}*`;
                            
                            if (!game.board.includes('.')) {
                                delete gameData[sender];
                                return sock.sendMessage(sender, { text: `🎉 *MENANG!* Sudoku selesai.\n\n${render(game.board)}` });
                            }
                            return sock.sendMessage(sender, { text: `✅ *BENAR!*\n\n${render(game.board)}\nLanjutkan!` });
                        } else {
                            game.wrongAttempts++;
                            let response = "❌ *Salah!* Angka itu tidak cocok di sana.";
                            
                            if (game.wrongAttempts >= 3) {
                                // Provide hint: find first empty index and give its coordinates and value
                                const emptyIdx = game.board.indexOf('.');
                                if (emptyIdx !== -1) {
                                    const hintR = Math.floor(emptyIdx / 4) + 1;
                                    const hintC = (emptyIdx % 4) + 1;
                                    const hintVal = game.solution[emptyIdx];
                                    response += `\n\n💡 *HINT:* Coba isi baris *${hintR}* kolom *${hintC}* dengan angka *${hintVal}*.`;
                                }
                            }
                            
                            return sock.sendMessage(sender, { text: response });
                        }
                    }
                }
            }

            if (game.type === 'woodber') {
                // Feature: Add Numbers
                if (input === 'add') {
                    const remaining = game.nums.filter(n => n !== '✅');
                    if (remaining.length === 0) return;
                    game.nums = [...game.nums, ...remaining];
                    return sock.sendMessage(sender, { text: `➕ *ANGKA DITAMBAH!*\n\nMeja: *${game.nums.join(' | ')}*\nLanjutkan pencocokan!` });
                }

                const parts = input.split(' ').map(n => parseInt(n) - 1);
                
                // Helper to check if any moves are left
                const hasMoves = (nums) => {
                    const active = nums.map((v, i) => ({v, i})).filter(x => x.v !== '✅');
                    for (let i = 0; i < active.length; i++) {
                        for (let j = i + 1; j < active.length; j++) {
                            if (active[i].v === active[j].v || active[i].v + active[j].v === 10) return {p1: active[i].i + 1, p2: active[j].i + 1};
                        }
                    }
                    return null;
                };

                if (parts.length === 2) {
                    const p1 = parts[0], p2 = parts[1];
                    if (p1 >= 0 && p1 < game.nums.length && p2 >= 0 && p2 < game.nums.length && p1 !== p2) {
                        const n1 = game.nums[p1], n2 = game.nums[p2];
                        if (n1 === n2 || n1 + n2 === 10) {
                            game.nums[p1] = '✅';
                            game.nums[p2] = '✅';
                            game.wrongAttempts = 0; // Reset on success
                            
                            if (game.nums.every(n => n === '✅')) {
                                delete gameData[sender];
                                return sock.sendMessage(sender, { text: "🎉 *MENANG!* Semua angka berhasil dicocokkan." });
                            }

                            const nextMove = hasMoves(game.nums);
                            if (!nextMove) {
                                return sock.sendMessage(sender, { text: `🛑 *BUNTU!*\n\nMeja: *${game.nums.join(' | ')}*\n\nTidak ada lagi pasangan yang cocok. Ketik *add* untuk menambah baris baru!` });
                            }

                            return sock.sendMessage(sender, { text: `✅ *MATCH!*\n\nMeja: *${game.nums.join(' | ')}*\nLanjutkan!` });
                        } else {
                            game.wrongAttempts++;
                            let response = "❌ Tidak cocok! Harus angka yang sama atau jumlahnya 10.";
                            
                            if (game.wrongAttempts >= 3) {
                                const hint = hasMoves(game.nums);
                                if (hint) {
                                    response += `\n\n💡 *HINT:* Coba cek posisi *${hint.p1}* dan *${hint.p2}*.`;
                                }
                            }
                            return sock.sendMessage(sender, { text: response });
                        }
                    }
                }
            }

            if (game.type === 'solitaire') {
                const parts = input.split(' ').map(Number);
                if (parts.length === 2 && parts[0] + parts[1] === 11) {
                    game.cards = game.cards.filter(c => c !== parts[0] && c !== parts[1]);
                    if (game.cards.length <= 1) {
                        delete gameData[sender];
                        return sock.sendMessage(sender, { text: "🎉 *MENANG!* Meja bersih." });
                    }
                    return sock.sendMessage(sender, { text: `✅ *COCOK!*\n\nKartu sisa: *${game.cards.join(' | ')}*\nLanjutkan!` });
                } else {
                    return sock.sendMessage(sender, { text: "❌ Jumlahnya bukan 11 atau format salah." });
                }
            }

            if (game.type === 'horor') {
                if (game.step === 1) {
                    if (input === 'rumah') {
                        game.path = 'rumah';
                        game.step = 2;
                        return sock.sendMessage(sender, { text: `🏚️ Kamu berdiri di depan rumah tua. Pintu depan terbuka sedikit... Di sebelah kirimu ada jendela yang pecah.\n\nApa yang kamu lakukan?\n👉 Ketik *masuk* (lewat pintu)\n👉 Ketik *jendela* (lewat jendela)` });
                    } else if (input === 'hutan') {
                        game.path = 'hutan';
                        game.step = 2;
                        return sock.sendMessage(sender, { text: `🌲 Kamu tersesat di tengah hutan terlarang. Kamu melihat ada gubuk tua di depanmu, dan sebuah jalan setapak gelap di sebelah kananmu.\n\nApa yang kamu lakukan?\n👉 Ketik *gubuk*\n👉 Ketik *kanan*` });
                    }
                } else if (game.path === 'rumah') {
                    if (game.step === 2) {
                        if (input === 'masuk') {
                            game.step = 3;
                            return sock.sendMessage(sender, { text: `🚪 Kamu masuk ke ruang tamu. Dingin sekali... Tiba-tiba pintu di belakangmu tertutup kencang! BRAKK!\n\nDi depanmu ada tangga ke *atas* dan pintu ke *dapur*.\n\nKe mana kamu pergi?\n👉 Ketik *atas* / *dapur*` });
                        } else if (input === 'jendela') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🩸 *JUMPSCARE!*\n\nSaat kamu melompat lewat jendela, sesosok hantu tanpa kepala menarik kakimu ke bawah tanah! Kamu tewas.\n\n*GAME OVER!*` });
                        }
                    } else if (game.step === 3) {
                        if (input === 'atas') {
                            game.step = 4;
                            return sock.sendMessage(sender, { text: `👣 Kamu naik ke lantai dua. Ada satu kamar dengan cahaya lilin remang-remang. Kamu mendengar suara tangisan wanita...\n\nApa yang kamu lakukan?\n👉 Ketik *intip* (lihat ke dalam)\n👉 Ketik *lari* (turun kembali)` });
                        } else if (input === 'dapur') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🔪 *JUMPSCARE!*\n\nKamu masuk ke dapur dan terpeleset genangan darah. Seorang jagal misterius muncul dari kegelapan dan menebas lehermu!\n\n*GAME OVER!*` });
                        }
                    } else if (game.step === 4) {
                        if (input === 'intip') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `😱 *JUMPSCARE!*\n\nWanita itu menoleh ke arahmu... wajahnya hancur dan matanya melotot tepat di depan matamu! Kamu mati karena serangan jantung!\n\n*GAME OVER!*` });
                        } else if (input === 'lari') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🌟 *SELAMAT!*\n\nKamu lari sekuat tenaga, melompat keluar dari balkon lantai dua dan mendarat di rumput. Kamu terus berlari sampai ke jalan raya dan berhasil selamat dari teror rumah itu!\n\n*YOU WIN!*` });
                        }
                    }
                } else if (game.path === 'hutan') {
                    if (game.step === 2) {
                        if (input === 'gubuk') {
                            game.step = 3;
                            return sock.sendMessage(sender, { text: `🏚️ Di dalam gubuk ada sebuah kotak kayu dan sebuah lubang di lantai.\n\nApa yang kamu lakukan?\n👉 Ketik *kotak* (buka kotak)\n👉 Ketik *lubang* (turun ke bawah)` });
                        } else if (input === 'kanan') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🐺 *Mati!*\n\nKamu bertemu kawanan serigala yang sedang lapar. Kamu habis dimakan.\n\n*GAME OVER!*` });
                        }
                    } else if (game.step === 3) {
                        if (input === 'kotak') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🐍 *Kaget!*\n\nKotak berisi ular berbisa yang langsung menggigit lehermu!\n\n*GAME OVER!*` });
                        } else if (input === 'lubang') {
                            delete gameData[sender];
                            return sock.sendMessage(sender, { text: `🌟 *Selamat!*\n\nLubang itu ternyata jalan keluar rahasia yang terhubung ke belakang bukit. Kamu selamat!\n\n*YOU WIN!*` });
                        }
                    }
                }
            }

            if (game.type === 'tod') {
                if (input === 'truth') {
                    const truths = ["Apa ketakutan terbesar kamu?", "Siapa orang yang diam-diam kamu suka?", "Pernahkah kamu berbohong kepada teman terbaikmu?", "Apa hal paling memalukan yang pernah kamu lakukan?"];
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `💡 *TRUTH:* ${truths[Math.floor(Math.random() * truths.length)]}` });
                }
                if (input === 'dare') {
                    const dares = ["Kirim pesan 'Aku sayang kamu' ke orang ke-3 di daftar chat WA kamu.", "VN nyanyi lagu balonku tapi semua vokal jadi 'O'.", "Kirim screenshot histori pencarian browser kamu ke grup ini.", "Push up 10 kali lalu kirim fotonya ke grup."];
                    delete gameData[sender];
                    return sock.sendMessage(sender, { text: `🔥 *DARE:* ${dares[Math.floor(Math.random() * dares.length)]}` });
                }
            }
        }

        // RESPON AI
        if (text && !text.startsWith('!')) {
            try {
                const st = await axios.post(`${pythonUrl}/status`, { sender, action: "get" });
                if (st.data.active) {
                    await sock.sendPresenceUpdate('composing', sender);
                    const res = await axios.post(`${pythonUrl}/chat`, { sender, msg: text });
                    await sock.sendMessage(sender, { text: res.data });
                }
            } catch (e) { }
        } else if (m.message && (m.message.audioMessage || (m.message.documentMessage && m.message.documentMessage.mimetype.startsWith('audio/')))) {
            try {
                const st = await axios.post(`${pythonUrl}/status`, { sender, action: "get" });
                if (st.data.active) {
                    await sock.sendPresenceUpdate('recording', sender);
                    const { downloadMediaMessage } = require('baileys');
                    const buffer = await downloadMediaMessage(m, 'buffer', {}, { logger: require('pino')({ level: 'silent' }) });
                    if (buffer) {
                        const FormData = require('form-data');
                        const formData = new FormData();
                        formData.append('sender', sender);
                        formData.append('audio', buffer, 'voice_note.ogg');
                        const res = await axios.post(`${pythonUrl}/voice`, formData, {
                            headers: formData.getHeaders()
                        });
                        await sock.sendMessage(sender, { text: res.data });
                    }
                }
            } catch (e) {
                console.error("Audio processing error:", e.message);
            }
        }
    });
}
connectWA();
