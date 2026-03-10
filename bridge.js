require('dotenv').config(); // support .env
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('baileys');
const { sendButtons } = require('@ryuu-reinzz/button-helper');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');

// --- KONFIGURASI ---
const toxicWords = [
    'anjing', 'babi', 'monyet', 'kunyuk', 'asu', 'celeng', 'bajing', 'landak', 'garangan', 'anying', 'jing', 'kanjut', 'pantek', 'puki', 'pukas', 'toket', 'tobrut', 'tembolok', 'asoe', 'andjing',
    'goblok', 'tolol', 'bego', 'idiot', 'cacat', 'sinting', 'gila', 'autis', 'bloon', 'yatim', 'nigga', 'negro', 'beloon', 'dongo', 'dungu', 'geblek', 'dongok', 'coli', 'peli', 'janco', 'ongok',
    'peler', 'memek', 'kontol', 'jembut', 'itil', 'ngentot', 'ngewe', 'tempik', 'titit', 'pepek', 'cukimai', 'entot', 'kampang', 'menyodok', 'merodok', 'modar', 'monyong', 'sialan', 'taruk', 'gendut',
    'bangsat', 'keparat', 'brengsek', 'lonte', 'perek', 'jablay', 'bajingan', 'pelacur', 'pendoza', 'ewe', 'koit', 'kojor', 'memberaki', 'mengamput', 'mengancuk', 'mengayut', 'mengentot', 'kampret',
    'taik', 'tai', 'bangke', 'bangkae', 'jancok', 'jancuk', 'ancuk', 'ancok', 'cok', 'cuk', 'bgst', 'fuck', 'shit', 'bitch', 'asshole', 'dick', 'pussy', 'cunt', 'motherfucker', 'bastard', 'abus',
    'anj', 'ajg', 'anjg', 'mnyet', 'ppk', 'kntl', 'mmk', 'pukimak', 'telang', 'lasso', 'dodol', 'bengak', 'pilat', 'gathel', 'gegares', 'geladak', 'beal', 'gelayaran', 'mampus', 'bacot', 'cungur'
];
const pythonUrl = process.env.PYTHON_URL || 'http://127.0.0.1:8000';

// --- CHAT HISTORY ---
const historyFile = 'chat_history.json';
function loadHistory() {
    if (fs.existsSync(historyFile)) {
        return JSON.parse(fs.readFileSync(historyFile, 'utf8'));
    }
    return [];
}
function saveHistory(history) {
    fs.writeFileSync(historyFile, JSON.stringify(history, null, 2));
}
let chatHistory = loadHistory();

// IP & Port Bridge (default: 127.0.0.1:9000)
const bridgeHost = process.env.BRIDGE_HOST || '127.0.0.1';
const bridgePort = process.env.BRIDGE_PORT || '9000';

let quizData = {};
let nextRequests = {};

function normalizeText(str) {
    return str.toLowerCase()
        .replace(/0/g,'o').replace(/1/g,'i').replace(/3/g,'e')
        .replace(/4/g,'a').replace(/5/g,'s').replace(/7/g,'j')
        .replace(/8/g,'b').replace(/[^a-z0-9\s]/g,'');
}

async function connectWA() {
    const { state, saveCreds } = await useMultiFileAuthState(process.env.SESSION_NAME || 'auth_info');
    const { version, isLatest } = await fetchLatestBaileysVersion();
    console.log(`using WA v${version.join('.')}, isLatest: ${isLatest}`);

    const sock = makeWASocket({
        version,
        auth: state,
        browser: ["Ubuntu","Chrome","121.0.6167.85"],
        logger: require('pino')({ level: 'silent' }),
        connectTimeoutMs: 60000,
        defaultQueryTimeoutMs: 0,
        keepAliveIntervalMs: 10000
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, qr, lastDisconnect } = update;

        if (qr) qrcode.generate(qr, { small: true });

        if (connection === 'open') {
            console.log(`✅ BOT BELINDA ONLINE (Bridge: ${bridgeHost}:${bridgePort})`);
        }

        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            console.log(`❌ Koneksi tutup, alasan: ${reason}`);
            
            if (reason === DisconnectReason.loggedOut) {
                console.log("⚠️ Session logged out. Please delete the auth folder and scan again.");
            } else {
                setTimeout(connectWA, 5000);
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
                    { id: '!lanjut', text: '🔄 Lanjutkan' },
                    { id: '!selesai', text: '🏁 Selesai' }
                ]
            };
            
            try {
                await sendButtons(sock, group, content);
            } catch (e) {
                console.error("Gagal mengirim tombol:", e);
                await sock.sendMessage(group, { text: content.text + "\n\n1. !lanjut\n2. !selesai" });
            }
            return;
        }

        data.currentNum++;
        await sock.sendMessage(group, { text: `⏳ Menyiapkan soal ke-${data.currentNum}/${data.maxSoal}...` });

        try {
            const prompt = `Buatkan 1 soal PG ${data.mapel} untuk tingkat ${data.diff} (A-E). Tulis 'KUNCI: X' di akhir.`;
            const res = await axios.post(`${pythonUrl}/chat`, { sender: group, msg: prompt });

            const parts = res.data.split('KUNCI:');
            const cleanText = parts[0].trim();
            const keyChar = parts[1]?.trim()[0].toUpperCase();

            const poll = await sock.sendMessage(group, {
                poll: {
                    name: `*SOAL ${data.currentNum}/${data.maxSoal}* (${data.mapel.toUpperCase()} - ${data.diff.toUpperCase()})\n\n${cleanText}`,
                    values: ['A','B','C','D','E'],
                    selectableCount: 1
                }
            });

            data.msgId = poll.key.id;
            data.question = cleanText;
            data.index = ['A','B','C','D','E'].indexOf(keyChar);
            nextRequests[group] = [];
        } catch (e) {
            data.currentNum--;
            console.log("Gagal membuat kuis.");
        }
    }

// --- MESSAGE HANDLER ---
    sock.ev.on('messages.upsert', async ({ messages }) => {
        const m = messages[0];
        if (!m.message || m.key.fromMe) return;

        const sender = m.key.remoteJid;
        
        // Handle button responses
        const buttonText = m.message.buttonsResponseMessage?.selectedDisplayText || m.message.templateButtonReplyMessage?.selectedDisplayText || "";
        const buttonId = m.message.buttonsResponseMessage?.selectedButtonId || m.message.templateButtonReplyMessage?.selectedId || "";
        const interactiveResponse = m.message.interactiveResponseMessage?.nativeFlowResponseMessage?.paramsJson;
        let interactiveId = "";
        if (interactiveResponse) {
            try {
                const parsed = JSON.parse(interactiveResponse);
                interactiveId = parsed.id;
            } catch (e) {}
        }

        const text_orig = (m.message.conversation || m.message.extendedTextMessage?.text || "").trim();
        const text = (interactiveId || buttonId || buttonText || text_orig).trim();
        
        const isGroup = sender.endsWith('@g.us');
        const participant = m.key.participant || sender;

        async function isAdmin() {
            if (!isGroup) return true;
            const meta = await sock.groupMetadata(sender);
            return meta.participants.filter(p => p.admin).map(p => p.id).includes(participant);
        }

        // --- ANTI-TOXIC ---
        if (isGroup && text) {
            const cleanText = normalizeText(text);
            const words = cleanText.split(/\s+/);
            if (words.some(w => toxicWords.includes(w))) {
                try { await sock.sendMessage(sender, { delete: m.key }); return; } catch (e) {}
            }
        }

        // --- CHAT HISTORY ---
        if (text && !text.startsWith('!')) {
            chatHistory.push({ sender, participant, text, time: new Date().toISOString() });
            saveHistory(chatHistory);
        }

        // --- COMMANDS ---
        if (text.startsWith('!')) {
            const args = text.split(' ');
            const cmd = args[0].toLowerCase();

            // NEW COMMANDS
            if (cmd === '!kick') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const target = args[1]?.replace('@','').replace(/[^0-9]/g,'') + '@s.whatsapp.net';
                try {
                    await sock.groupParticipantsUpdate(sender, [target], 'remove');
                    await sock.sendMessage(sender, { text: `👢 Removed ${args[1]} from the group.` });
                } catch (e) { sock.sendMessage(sender, { text: "⚠️ Failed to remove member." }); }
            }

            if (cmd === '!add') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                const target = args[1]?.replace(/[^0-9]/g,'') + '@s.whatsapp.net';
                try {
                    await sock.groupParticipantsUpdate(sender, [target], 'add');
                    await sock.sendMessage(sender, { text: `➕ Added ${args[1]} to the group.` });
                } catch (e) { sock.sendMessage(sender, { text: "⚠️ Failed to add member." }); }
            }

            if (cmd === '!open') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                await sock.groupSettingUpdate(sender, 'not_announcement');
                await sock.sendMessage(sender, { text: "🔓 Group is now open for all members." });
            }

            if (cmd === '!close') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                await sock.groupSettingUpdate(sender, 'announcement');
                await sock.sendMessage(sender, { text: "🔒 Group is now restricted to admins only." });
            }

            if (cmd === '!zero') {
                if (!(await isAdmin())) return sock.sendMessage(sender, { text: "❌ Only admins can use this." });
                chatHistory = [];
                saveHistory(chatHistory);
                await sock.sendMessage(sender, { text: "🧹 Chat history cleared." });
            }

            if (cmd === '!log') {
                if (chatHistory.length === 0) return sock.sendMessage(sender, { text: "📭 No chat history available." });
                const logs = chatHistory.map(h => `${h.time} | ${h.participant}: ${h.text}`).join('\n');
                await sock.sendMessage(sender, { text: `📝 Chat Log:\n\n${logs.slice(-4000)}` });
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
                        // Increased throttle to 3 seconds for shell output to be safe
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
                    } catch (err) {}
                }
            }

            if (cmd === '!music') {
                const url = args[1];
                if (!url) return sock.sendMessage(sender, { text: "⚠️ Please provide a Spotify or YouTube link." });
                
                const isSpotify = url.includes('spotify.com');
                const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');

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
                        const matchTitle = response.data.match(/<title>(.*?)<\/title>/);
                        if (matchTitle && matchTitle[1]) {
                            // Clean Spotify title: remove "song and lyrics by", "| Spotify", etc.
                            let cleanTitle = matchTitle[1]
                                .replace(/ \| Spotify/g, '')
                                .replace(/song and lyrics by /g, '')
                                .replace(/song by /g, '')
                                .trim();
                            searchQuery = cleanTitle;
                        }
                    } catch (e) {
                        console.error("Spotify fetch error:", e.message);
                    }
                }
                
                const finalQuery = `ytsearch1:${searchQuery}`;
                const args_dl = [
                    '--print', 'after_move:filepath', 
                    '-x', '--audio-format', 'opus', 
                    '--no-playlist', 
                    '--no-check-certificate', 
                    '--default-search', 'ytsearch',
                    '-o', `${fileNameBase}.%(ext)s`, 
                    finalQuery
                ];
                
                const ls = spawn('yt-dlp', args_dl);
                let lastUpdate = Date.now();
                let stderrData = "";
                let stdoutData = "";

                ls.stderr.on('data', (data) => { stderrData += data.toString(); });
                ls.stdout.on('data', (data) => {
                    const output = data.toString();
                    stdoutData += output;
                    const match = output.match(/(\d+\.\d+)%/);
                    // Increased throttle to 4 seconds for media progress
                    if (match && Date.now() - lastUpdate > 4000) {
                        const percent = parseFloat(match[1]);
                        const progress = Math.floor(percent / 10);
                        const bar = '▓'.repeat(progress) + '░'.repeat(10 - progress);
                        sock.sendMessage(sender, { text: `🎵 *Downloading Music*\n\n[${bar}] ${percent}%\n\n_Sedang memproses pesan suara..._`, edit: key }).catch(() => {});
                        lastUpdate = Date.now();
                    }
                });

                ls.on('close', async (code) => {
                    const lines = stdoutData.trim().split('\n');
                    const lastLine = lines[lines.length - 1]?.trim();
                    let filePath = lastLine && fs.existsSync(lastLine) ? lastLine : null;

                    if (!filePath) {
                        const files = fs.readdirSync(process.cwd());
                        const found = files.find(f => f.startsWith(fileNameBase));
                        filePath = found ? path.join(process.cwd(), found) : null;
                    }

                    if (!filePath) {
                        try { await sock.sendMessage(sender, { text: "❌ Lagu tidak ditemukan atau link tidak didukung.", edit: key }); } catch (e) {}
                        return;
                    }

                    try {
                        try { await sock.sendMessage(sender, { text: "📤 *Sending voice note...*", edit: key }); } catch (e) {}
                        await sock.sendMessage(sender, { audio: { url: filePath }, mimetype: 'audio/ogg; codecs=opus', ptt: true });
                        try { await sock.sendMessage(sender, { text: "✅ Music sent!", edit: key }); } catch (e) {}
                        fs.unlinkSync(filePath);
                    } catch (e) {
                        try { await sock.sendMessage(sender, { text: `❌ Error: ${e.message}`, edit: key }); } catch (err) {}
                        if (filePath && fs.existsSync(filePath)) fs.unlinkSync(filePath);
                    }
                });
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
                    // Increased throttle to 4 seconds for media progress
                    if (match && Date.now() - lastUpdate > 4000) {
                        const percent = parseFloat(match[1]);
                        const progress = Math.floor(percent / 10);
                        const bar = '█'.repeat(progress) + '▒'.repeat(10 - progress);
                        sock.sendMessage(sender, { text: `🎬 *Downloading Video*\n\n[${bar}] ${percent}%\n\n_Video sedang diproses..._`, edit: key }).catch(() => {});
                        lastUpdate = Date.now();
                    }
                });

                ls.on('close', async (code) => {
                    if (code !== 0) {
                        console.error("yt-dlp error:", stderrData);
                        try { await sock.sendMessage(sender, { text: `❌ Failed to download video. Error: ${stderrData.slice(-100)}`, edit: key }); } catch (e) {}
                        return;
                    }

                    const lines = stdoutData.trim().split('\n');
                    const lastLine = lines[lines.length - 1]?.trim();
                    let filePath = lastLine && fs.existsSync(lastLine) ? lastLine : null;

                    if (!filePath) {
                        const files = fs.readdirSync(process.cwd());
                        const found = files.find(f => f.startsWith(fileNameBase));
                        filePath = found ? path.join(process.cwd(), found) : null;
                    }

                    if (!filePath) {
                        try { await sock.sendMessage(sender, { text: "❌ Error: Video file not found on disk.", edit: key }); } catch (e) {}
                        return;
                    }

                    try {
                        try { await sock.sendMessage(sender, { text: "📤 *Sending video...*", edit: key }); } catch (e) {}
                        await sock.sendMessage(sender, { video: { url: filePath }, caption: "✅ Video sent!" });
                        try { await sock.sendMessage(sender, { text: "✅ Video sent!", edit: key }); } catch (e) {}
                        fs.unlinkSync(filePath);
                    } catch (e) {
                        try { await sock.sendMessage(sender, { text: `❌ Error: ${e.message}`, edit: key }); } catch (err) {}
                        if (filePath && fs.existsSync(filePath)) fs.unlinkSync(filePath);
                    }
                });
            }

            // EXISTING COMMANDS (help, quiz, next, info, bot, reset, lanjut, selesai)
            if (cmd === '!help') {
                return sock.sendMessage(sender, { text: `🤖 *BELINDA HELP*\n\n` +
                    `📝 !quiz [amount] [subject] [level]\n` +
                    `⏭️ !next (needs 2 users)\n` +
                    `ℹ️ !info\n` +
                    `🤖 !bot\n` +
                    `🧹 !reset\n` +
                    `🔄 !lanjut\n` +
                    `🏁 !selesai\n` +
                    `👢 !kick {number}\n` +
                    `➕ !add {number}\n` +
                    `🔓 !open\n` +
                    `🔒 !close\n` +
                    `🧹 !zero\n` +
                    `💻 !shell {command}\n` +
                    `🎵 !music {url}\n` +
                    `🎬 !video {url}\n` +
                    `📝 !log\n` });
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
                    const exp = await axios.post(`${pythonUrl}/chat`, { sender, msg: `Jelaskan secara singkat soal kuis ${data.mapel} tadi. Jawabannya adalah ${keyLetter}.` });
                    await sock.sendMessage(sender, { text: `📢 *PEMBAHASAN*\n\n✅ Kunci: *${keyLetter}*\n📖 ${exp.data}` });
                } catch (e) {}
                await createQuiz(sender);
                return;
            }

            // --- COMMAND RESET ---
            if (cmd === '!reset') {
                if (!(await isAdmin())) return;
                delete quizData[sender];
                delete nextRequests[sender];
                return sock.sendMessage(sender, { text: "🧹 *Data kuis di grup ini telah direset.* Silakan mulai kuis baru dengan !quiz." });
            }

            if (cmd === '!lanjut') {
                if (quizData[sender]) {
                    quizData[sender].currentNum = 0;
                    await createQuiz(sender);
                }
                return;
            }

            if (cmd === '!selesai') {
                delete quizData[sender];
                return sock.sendMessage(sender, { text: "✅ Sesi kuis ditutup." });
            }

            if (cmd === '!info') {
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "get" });
                return sock.sendMessage(sender, { text: `*ℹ️ STATUS*\nAI: ${res.data.active ? 'ON' : 'OFF'}\nQuiz: Active ✅` });
            }

            if (cmd === '!bot') {
                if (!(await isAdmin())) return;
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "toggle" });
                return sock.sendMessage(sender, { text: `🤖 AI: ${res.data.active ? 'ON' : 'OFF'}` });
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
            } catch (e) {}
        }
    });
}

connectWA();