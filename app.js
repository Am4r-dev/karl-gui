const BAUD_RATE = 115200;
const MAX_MOVES = 50;

let port = null;
let writer = null;
let reader = null;
let readableClosed = null;
let busy = false;

let sequence = [];

const connectBtn = document.getElementById('connectBtn');
const statusEl = document.getElementById('status');
const themeToggle = document.getElementById('themeToggle');
const sequenceEl = document.getElementById('sequence');
const clearBtn = document.getElementById('clearBtn');
const loopChk = document.getElementById('loopChk');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const paletteButtons = document.querySelectorAll('.block[data-move]');

/* ---------- Theme ---------- */

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    localStorage.setItem('karl-theme', theme);
}

themeToggle.addEventListener('click', () => {
    const current = document.documentElement.dataset.theme;
    applyTheme(current === 'dark' ? 'light' : 'dark');
});

applyTheme(localStorage.getItem('karl-theme') || 'dark');

/* ---------- Serial ---------- */

let statusResetTimer = null;

function setStatus(text, connected) {
    clearTimeout(statusResetTimer);
    statusEl.textContent = text;
    statusEl.classList.toggle('connected', !!connected);
}

function flashStatus(text) {
    setStatus(text, true);
    statusResetTimer = setTimeout(() => {
        if (writer) setStatus('Verbunden', true);
    }, 2000);
}

function withTimeout(promise, ms) {
    return Promise.race([
        promise,
        new Promise((resolve) => setTimeout(resolve, ms)),
    ]);
}

/* Gibt Streams und Port garantiert wieder frei — auch wenn einzelne
   Schritte fehlschlagen. Reihenfolge ist wichtig: erst Writer schließen,
   dann Reader canceln, dann auf das Pipe-Ende warten, dann Port schließen.
   Sonst bleibt der Port gesperrt und der nächste Verbindungsversuch
   scheitert mit "port already open". */
async function teardownSerial() {
    if (writer) {
        try {
            await withTimeout(writer.close(), 1500);
        } catch (err) {
            /* Stream schon kaputt (z.B. Kabel gezogen) */
        }
        try {
            writer.releaseLock();
        } catch (err) {
            /* Lock war schon frei */
        }
        writer = null;
    }

    if (reader) {
        try {
            await withTimeout(reader.cancel(), 1500);
        } catch (err) {
            /* Reader schon beendet */
        }
        reader = null;
    }

    if (readableClosed) {
        await withTimeout(readableClosed, 1500);
        readableClosed = null;
    }

    if (port) {
        try {
            await withTimeout(port.close(), 1500);
        } catch (err) {
            console.warn('Port schließen fehlgeschlagen:', err);
        }
        port = null;
    }
}

async function connect() {
    if (busy || port) return;

    if (!('serial' in navigator)) {
        setStatus('Web Serial wird nicht unterstützt — Chrome oder Edge nutzen', false);
        return;
    }

    busy = true;
    connectBtn.disabled = true;
    connectBtn.textContent = 'Verbinde…';

    try {
        port = await navigator.serial.requestPort();
        await port.open({ baudRate: BAUD_RATE });

        writer = port.writable.getWriter();
        readLoop();

        setStatus('Verbunden', true);
        connectBtn.textContent = 'Trennen';

        await sendCommand('HELLO');
    } catch (err) {
        await teardownSerial();
        setStatus('Verbindung fehlgeschlagen: ' + err.message, false);
        connectBtn.textContent = 'Calliope verbinden';
    } finally {
        busy = false;
        connectBtn.disabled = false;
        updateControls();
    }
}

async function disconnect() {
    if (busy || !port) return;

    busy = true;
    connectBtn.disabled = true;
    connectBtn.textContent = 'Trenne…';
    setStatus('Trenne…', false);

    // Calliope verabschieden: spielt Abschieds-Sound und startet sich neu,
    // damit er für die nächste Verbindung frisch dasteht
    try {
        await sendCommand('BYE');
    } catch (err) {
        /* Verbindung schon tot — trotzdem aufräumen */
    }

    await teardownSerial();

    busy = false;
    connectBtn.disabled = false;
    connectBtn.textContent = 'Calliope verbinden';
    setStatus('Getrennt ✓ — Calliope startet neu', false);
    updateControls();
}

async function readLoop() {
    const decoder = new TextDecoderStream();
    readableClosed = port.readable.pipeTo(decoder.writable).catch(() => {});
    reader = decoder.readable.getReader();
    let rxBuffer = '';

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) {
                console.log('[Calliope]', value);
                rxBuffer = (rxBuffer + value).slice(-200);
                if (rxBuffer.includes('READY')) {
                    rxBuffer = '';
                    setStatus('Verbunden — Calliope bereit ✓', true);
                }
            }
        }
    } catch (err) {
        console.warn('Serial-Lesefehler:', err);
    } finally {
        try {
            reader.releaseLock();
        } catch (err) {
            /* Lock war schon frei */
        }
    }
}

async function sendCommand(command) {
    if (!writer) return;
    const encoder = new TextEncoder();
    await writer.write(encoder.encode(command + '\n'));
}

connectBtn.addEventListener('click', () => {
    if (port) {
        disconnect();
    } else {
        connect();
    }
});

navigator.serial?.addEventListener('disconnect', async (event) => {
    if (event.target !== port) return;
    await teardownSerial();
    busy = false;
    connectBtn.disabled = false;
    connectBtn.textContent = 'Calliope verbinden';
    setStatus('Verbindung verloren — Kabel gezogen?', false);
    updateControls();
});

/* ---------- Sequenz-Baukasten ---------- */

let dragIndex = null;

function renderSequence() {
    sequenceEl.innerHTML = '';

    if (sequence.length === 0) {
        const li = document.createElement('li');
        li.className = 'empty-hint';
        li.textContent = 'Noch keine Moves — bau dir links deinen Tanz zusammen!';
        sequenceEl.appendChild(li);
        return;
    }

    sequence.forEach((move, i) => {
        const li = document.createElement('li');
        li.className = 'seq-block move-' + move;
        li.draggable = true;
        li.dataset.index = i;

        const grip = document.createElement('span');
        grip.className = 'grip';
        grip.textContent = '⠿';

        const idx = document.createElement('span');
        idx.className = 'idx';
        idx.textContent = i + 1;

        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = 'Move ' + move;

        const remove = document.createElement('button');
        remove.className = 'remove';
        remove.textContent = '✕';
        remove.setAttribute('aria-label', 'Move entfernen');
        remove.addEventListener('click', () => {
            sequence.splice(i, 1);
            renderSequence();
            updateControls();
        });

        li.append(grip, idx, label, remove);

        li.addEventListener('dragstart', () => {
            dragIndex = i;
        });
        li.addEventListener('dragover', (e) => {
            e.preventDefault();
            li.classList.add('drag-over');
        });
        li.addEventListener('dragleave', () => li.classList.remove('drag-over'));
        li.addEventListener('drop', (e) => {
            e.preventDefault();
            li.classList.remove('drag-over');
            if (dragIndex === null || dragIndex === i) return;
            const [moved] = sequence.splice(dragIndex, 1);
            sequence.splice(i, 0, moved);
            dragIndex = null;
            renderSequence();
        });
        li.addEventListener('dragend', () => {
            dragIndex = null;
        });

        sequenceEl.appendChild(li);
    });
}

paletteButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
        if (sequence.length >= MAX_MOVES) {
            flashStatus('Maximal ' + MAX_MOVES + ' Moves pro Tanz');
            return;
        }
        sequence.push(btn.dataset.move);
        renderSequence();
        updateControls();
    });
});

clearBtn.addEventListener('click', () => {
    sequence = [];
    renderSequence();
    updateControls();
});

/* ---------- Senden ---------- */

function updateControls() {
    sendBtn.disabled = !writer || sequence.length === 0;
    stopBtn.disabled = !writer;
}

sendBtn.addEventListener('click', async () => {
    if (!writer || sequence.length === 0) return;
    const loop = loopChk.checked ? '1' : '0';
    await sendCommand('DANCE:' + sequence.join('') + ':' + loop);
    flashStatus('Tanz gesendet ✓');
});

stopBtn.addEventListener('click', async () => {
    if (!writer) return;
    await sendCommand('DANCE::0');
    flashStatus('Stopp gesendet');
});

renderSequence();
updateControls();
