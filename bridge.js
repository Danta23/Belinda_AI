require('dotenv').config(); // support .env
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
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
    const sock = makeWASocket({
        auth: state,
        browser: ["Ubuntu","Chrome","20.0.04"]
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
            setTimeout(connectWA, 5000);
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
        const botNumber = sock.user.id.split(':')[0];

        if (data.currentNum >= data.maxSoal) {
            const finishMsg = `🏁 *QUIZ SELESAI!*\n\nBerhasil menyelesaikan ${data.maxSoal} soal *${data.mapel.toUpperCase()}* (${data.diff.toUpperCase()}).\n\n` +
                `*PILIH OPSI:* \n1️⃣ *Lanjutkan:* https://wa.me/${botNumber}?text=!lanjut\n2️⃣ *Selesai:* https://wa.me/${botNumber}?text=!selesai`;
            return sock.sendMessage(group, { text: finishMsg });
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
        const text = (m.message.conversation || m.message.extendedTextMessage?.text || "").trim();
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