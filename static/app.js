// Elements
const elPlcList = document.getElementById('plc-list');
const mainView = document.getElementById('main-view');
const emptyView = document.getElementById('empty-view');
const modal = document.getElementById('new-plc-modal');

const elHeaderName = document.getElementById('header-name');
const elHeaderStatus = document.getElementById('header-status');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const btnDelete = document.getElementById('btn-delete');
const btnSaveCfg = document.getElementById('btn-save-cfg');

const inCfgName = document.getElementById('cfg-name');
const inCfgPort = document.getElementById('cfg-port');
const inCfgSeries = document.getElementById('cfg-series');
const inCfgDiscInt = document.getElementById('cfg-disc-int');
const inCfgDiscChan = document.getElementById('cfg-disc-chan');
const inCfgScriptInt = document.getElementById('cfg-script-int');

const tbBody = document.querySelector('#device-table tbody');
const btnPrev = document.getElementById('btn-prev-page');
const btnNext = document.getElementById('btn-next-page');
const elPageInfo = document.getElementById('page-info');

// State
let plcs = [];
let currentPlc = null;
let currentPage = 0;
const PAGE_SIZE = 100;
let editor = null;
let ws = null;
let memoryCache = new Array(65536).fill(0);

// Initialize
async function init() {
    await fetchPlcs();
    setupWebSocket();
    setupMonaco();
    setupEventListeners();
}

async function fetchPlcs() {
    const res = await fetch('/api/plcs');
    plcs = await res.json();
    renderPlcList();
    if (currentPlc) {
        const updated = plcs.find(p => p.name === currentPlc.name);
        if (updated) {
            currentPlc = updated;
            updateHeaderStatus();
        } else {
            selectPlc(null);
        }
    }
}

function renderPlcList() {
    elPlcList.innerHTML = '';
    plcs.forEach(plc => {
        const li = document.createElement('li');
        li.className = `plc-item ${currentPlc && currentPlc.name === plc.name ? 'active' : ''}`;
        li.innerHTML = `
            <span class="plc-name">${plc.name}</span>
            <div class="status-indicator ${plc.is_running ? 'running' : ''}"></div>
        `;
        li.onclick = () => selectPlc(plc);
        elPlcList.appendChild(li);
    });
}

async function selectPlc(plc) {
    currentPlc = plc;
    renderPlcList();
    
    if (!plc) {
        mainView.style.display = 'none';
        emptyView.style.display = 'flex';
        return;
    }
    
    mainView.style.display = 'flex';
    emptyView.style.display = 'none';
    
    // Fill Config
    elHeaderName.textContent = plc.name;
    updateHeaderStatus();
    
    inCfgName.value = plc.name;
    inCfgPort.value = plc.port;
    inCfgSeries.value = plc.series;
    inCfgDiscInt.value = plc.disconnect_event.interval_sec;
    inCfgDiscChan.value = plc.disconnect_event.chance_percent;
    inCfgScriptInt.value = plc.script_interval_ms;
    
    // Load Script
    const res = await fetch(`/api/plcs/${plc.name}/script`);
    const data = await res.json();
    if (editor) {
        editor.setValue(data.code || '');
    } else {
        // Wait for monaco
        setTimeout(() => editor && editor.setValue(data.code || ''), 500);
    }
    
    // Load Memory
    currentPage = 0;
    await fetchMemory();
}

function updateHeaderStatus() {
    if (!currentPlc) return;
    elHeaderStatus.className = `status-badge ${currentPlc.is_running ? 'running' : 'stopped'}`;
    elHeaderStatus.textContent = currentPlc.is_running ? 'Running' : 'Stopped';
    btnStart.style.display = currentPlc.is_running ? 'none' : 'block';
    btnStop.style.display = currentPlc.is_running ? 'block' : 'none';
}

async function fetchMemory() {
    if (!currentPlc) return;
    const start = currentPage * PAGE_SIZE;
    const res = await fetch(`/api/plcs/${currentPlc.name}/memory?start=${start}&length=${PAGE_SIZE}`);
    const data = await res.json();
    if (!data.error) {
        for (let i = 0; i < data.values.length; i++) {
            memoryCache[start + i] = data.values[i];
        }
        renderMemoryTable();
    }
}

function renderMemoryTable() {
    tbBody.innerHTML = '';
    const start = currentPage * PAGE_SIZE;
    elPageInfo.textContent = `D${start} - D${start + PAGE_SIZE - 1}`;
    
    for (let i = 0; i < PAGE_SIZE; i++) {
        const addr = start + i;
        const val = memoryCache[addr];
        
        // Convert to string (2 ASCII chars)
        const char1 = val & 0xFF;
        const char2 = (val >> 8) & 0xFF;
        const s1 = (char1 >= 32 && char1 <= 126) ? String.fromCharCode(char1) : '.';
        const s2 = (char2 >= 32 && char2 <= 126) ? String.fromCharCode(char2) : '.';
        const str = s1 + s2;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>D${addr}</td>
            <td class="val-dec" data-addr="${addr}">${val}</td>
            <td class="val-hex" data-addr="${addr}">0x${val.toString(16).padStart(4, '0').toUpperCase()}</td>
            <td class="val-str" data-addr="${addr}">${str}</td>
        `;
        tbBody.appendChild(tr);
    }
}

// WebSocket setup
function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === 'update' && currentPlc && data.plc === currentPlc.name) {
            // Need to reload current page
            fetchMemory();
        }
    };
    ws.onclose = () => {
        console.log('WS closed, reconnecting in 3s...');
        setTimeout(setupWebSocket, 3000);
    };
}

// Monaco Editor setup
function setupMonaco() {
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
    require(['vs/editor/editor.main'], function() {
        editor = monaco.editor.create(document.getElementById('monaco-container'), {
            value: '',
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace"
        });
    });
}

function setupEventListeners() {
    // Modal
    document.getElementById('btn-new-plc').onclick = () => modal.classList.add('show');
    document.getElementById('btn-cancel-new').onclick = () => modal.classList.remove('show');
    document.getElementById('btn-confirm-new').onclick = async () => {
        const name = document.getElementById('new-plc-name').value;
        const port = document.getElementById('new-plc-port').value;
        if (!name) return;
        
        await fetch('/api/plcs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, port: parseInt(port) })
        });
        modal.classList.remove('show');
        document.getElementById('new-plc-name').value = '';
        await fetchPlcs();
    };

    // Actions
    btnStart.onclick = async () => {
        await fetch(`/api/plcs/${currentPlc.name}/start`, { method: 'POST' });
        await fetchPlcs();
    };
    
    btnStop.onclick = async () => {
        await fetch(`/api/plcs/${currentPlc.name}/stop`, { method: 'POST' });
        await fetchPlcs();
    };
    
    btnDelete.onclick = async () => {
        if (!confirm('Are you sure you want to delete this PLC?')) return;
        await fetch(`/api/plcs/${currentPlc.name}`, { method: 'DELETE' });
        currentPlc = null;
        await fetchPlcs();
    };
    
    btnSaveCfg.onclick = async () => {
        const config = {
            name: inCfgName.value,
            port: parseInt(inCfgPort.value),
            series: inCfgSeries.value,
            disconnect_event: {
                interval_sec: parseInt(inCfgDiscInt.value),
                chance_percent: parseInt(inCfgDiscChan.value)
            },
            script_interval_ms: parseInt(inCfgScriptInt.value)
        };
        await fetch(`/api/plcs/${currentPlc.name}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        await fetchPlcs();
    };

    document.getElementById('btn-save-script').onclick = async () => {
        if (!currentPlc || !editor) return;
        await fetch(`/api/plcs/${currentPlc.name}/script`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: editor.getValue() })
        });
        alert('Script saved and reloaded!');
    };

    // Pagination
    btnPrev.onclick = () => {
        if (currentPage > 0) {
            currentPage--;
            fetchMemory();
        }
    };
    btnNext.onclick = () => {
        if (currentPage < 655) { // 65536 / 100
            currentPage++;
            fetchMemory();
        }
    };

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).style.display = 'flex';
        };
    });

    // Edit Table Cells
    tbBody.addEventListener('dblclick', (e) => {
        const td = e.target.closest('td');
        if (!td || td.cellIndex === 0 || td.cellIndex === 3) return; // Don't edit address or string column
        
        const addr = parseInt(td.dataset.addr);
        const originalVal = memoryCache[addr];
        
        const input = document.createElement('input');
        input.type = 'number';
        input.value = originalVal;
        
        td.classList.add('cell-editing');
        td.innerHTML = '';
        td.appendChild(input);
        input.focus();
        
        const finishEdit = async () => {
            td.classList.remove('cell-editing');
            let newVal = parseInt(input.value);
            if (isNaN(newVal)) newVal = originalVal;
            if (newVal < 0) newVal = 0;
            if (newVal > 65535) newVal = 65535;
            
            if (newVal !== originalVal) {
                // Save to backend
                await fetch(`/api/plcs/${currentPlc.name}/memory`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address: addr, values: [newVal] })
                });
                memoryCache[addr] = newVal;
            }
            renderMemoryTable();
        };
        
        input.onblur = finishEdit;
        input.onkeydown = (e) => {
            if (e.key === 'Enter') finishEdit();
            if (e.key === 'Escape') {
                td.classList.remove('cell-editing');
                renderMemoryTable();
            }
        };
    });
}

init();
