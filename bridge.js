require('dotenv').config();
const { default: makeWASocket, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// --- KONFIGURASI ---
const toxicWords = [
    'anjing', 'babi', 'monyet', 'kunyuk', 'asu', 'celeng', 'bajing', 'landak', 'garangan', 'anying', 'jing', 'kanjut', 'pantek', 'puki', 'pukas', 'toket', 'tobrut', 'tembolok', 'asoe', 'andjing',
    'goblok', 'tolol', 'bego', 'idiot', 'cacat', 'sinting', 'gila', 'autis', 'bloon', 'yatim', 'nigga', 'negro', 'beloon', 'dongo', 'dungu', 'geblek', 'dongok', 'coli', 'peli', 'janco', 'ongok',
    'peler', 'memek', 'kontol', 'jembut', 'itil', 'ngentot', 'ngewe', 'tempik', 'titit', 'pepek', 'cukimai', 'entot', 'kampang', 'menyodok', 'merodok', 'modar', 'monyong', 'sialan', 'taruk', 'gendut',
    'bangsat', 'keparat', 'brengsek', 'lonte', 'perek', 'jablay', 'bajingan', 'pelacur', 'pendoza', 'ewe', 'koit', 'kojor', 'memberaki', 'mengamput', 'mengancuk', 'mengayut', 'mengentot', 'kampret',
    'taik', 'tai', 'bangke', 'bangkae', 'jancok', 'jancuk', 'ancuk', 'ancok', 'cok', 'cuk', 'bgst', 'fuck', 'shit', 'bitch', 'asshole', 'dick', 'pussy', 'cunt', 'motherfucker', 'bastard', 'abus',
    'anj', 'ajg', 'anjg', 'mnyet', 'ppk', 'kntl', 'mmk', 'pukimak', 'telang', 'lasso', 'dodol', 'bengak', 'pilat', 'gathel', 'gegares', 'geladak', 'beal', 'gelayaran', 'mampus', 'bacot', 'cungur'
];
const pythonUrl = process.env.PYTHON_URL || 'http://flask:8000';

let quizData = {}; 
let nextRequests = {}; 

function normalizeText(str) {
    return str.toLowerCase()
        .replace(/0/g, 'o').replace(/1/g, 'i').replace(/3/g, 'e')
        .replace(/4/g, 'a').replace(/5/g, 's').replace(/7/g, 'j')
        .replace(/8/g, 'b').replace(/[^a-z0-9\s]/g, '');
}

async function connectWA() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info');
    const { version } = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: false,
        browser: ["Ubuntu", "Chrome", "20.0.04"]
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { qr, connection, pairingCode } = update;

        if (qr) {
            console.log("Scan this QR with WhatsApp:");
            require('qrcode-terminal').generate(qr, { small: true });
        }

        if (pairingCode) {
            console.log("📱 Pairing code:", pairingCode);
            console.log("Enter this code in WhatsApp (Linked Devices → Link with phone number).");
        }

        if (connection === 'open') {
            console.log("✅ BOT BELINDA ONLINE");
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
            console.log("Gagal membuat kuis.");
        }
    }

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

        // ANTI-TOXIC
        if (isGroup && text) {
            const cleanText = normalizeText(text);
            const words = cleanText.split(/\s+/);
            if (words.some(w => toxicWords.includes(w))) {
                try { await sock.sendMessage(sender, { delete: m.key }); return; } catch (e) {}
            }
        }

        // COMMANDS
        if (text.startsWith('!')) {
            const args = text.split(' ');
            const cmd = args[0].toLowerCase();

            if (cmd === '!help') {
                return sock.sendMessage(sender, { text: `╔══════════════════╗
        ║     🤖 *BELINDA HELP* ║
        ╚══════════════════╝

        ┣ 📝 *!quiz* [jml] [mapel] [level]
        ┣ ⏭️ *!next* (Butuh 2 org)
        ┣ ℹ️ *!info*
        ┣ 🤖 *!bot*
        ┣ 🧹 *!reset*

        *MAPEL:* tik, mtk, ipa, ips, b.ing, b.indo, umum, sbdp, pkwu, pai, pkn
        *LEVEL:* ez, mid, hrd` });
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

            // ✅ FIXED !info
            if (cmd === '!info') {
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "get" });
                return sock.sendMessage(sender, {
                    text: `*ℹ️ STATUS*\nAI: ${res.data.active ? 'ON ✅' : 'OFF ❌'}\nQuiz: Active ✅`
                });
            }

            // ✅ FIXED !bot (toggle AI without admin check)
            if (cmd === '!bot') {
                const res = await axios.post(`${pythonUrl}/status`, { sender, action: "toggle" });
                return sock.sendMessage(sender, {
                    text: `🤖 AI is now: ${res.data.active ? 'ON ✅' : 'OFF ❌'}`
                });
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
            } catch (e) {
                console.error("Error handling message:", e.message);
                await sock.sendMessage(sender, { text: "⚠️ Sorry, something went wrong." });
            }
        }
    });
}
connectWA();