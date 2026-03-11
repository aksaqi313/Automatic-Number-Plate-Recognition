/* ── ANPR Frontend · App Logic ── */

let currentMode = 'image';  // 'image' | 'video'
let selectedFile = null;

// ── Mode Switching ────────────────────────────────────────────────
function setMode(mode) {
    currentMode = mode;
    clearPreview();
    hideResults();
    hideError();

    document.getElementById('btnImage').classList.toggle('active', mode === 'image');
    document.getElementById('btnVideo').classList.toggle('active', mode === 'video');

    const fileInput = document.getElementById('fileInput');
    const dropTitle = document.getElementById('dropTitle');
    const dropSub = document.getElementById('dropSub');
    const imgIcon = document.getElementById('dropIconImage');
    const vidIcon = document.getElementById('dropIconVideo');

    if (mode === 'image') {
        fileInput.accept = 'image/*';
        dropTitle.textContent = 'Drop your image here';
        dropSub.textContent = 'Supports JPG, PNG, BMP, WebP';
        imgIcon.style.display = '';
        vidIcon.style.display = 'none';
    } else {
        fileInput.accept = 'video/*';
        dropTitle.textContent = 'Drop your video here';
        dropSub.textContent = 'Supports MP4, AVI, MOV, MKV, WebM';
        imgIcon.style.display = 'none';
        vidIcon.style.display = '';
    }
    fileInput.value = '';
}

// ── File Selection ────────────────────────────────────────────────
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    loadFile(file);
}

function loadFile(file) {
    selectedFile = file;
    const url = URL.createObjectURL(file);
    const sizeKB = (file.size / 1024).toFixed(1);
    const sizeMB = (file.size / 1024 / 1024).toFixed(2);

    document.getElementById('dropZone').style.display = 'none';
    document.getElementById('previewArea').style.display = 'flex';
    document.getElementById('previewLabel').textContent = 'Selected File';
    document.getElementById('fileInfo').textContent =
        `${file.name}  ·  ${sizeMB > 1 ? sizeMB + ' MB' : sizeKB + ' KB'}  ·  ${file.type}`;

    const img = document.getElementById('previewImage');
    const vid = document.getElementById('previewVideo');

    if (currentMode === 'image') {
        img.src = url; img.style.display = '';
        vid.style.display = 'none';
    } else {
        vid.src = url; vid.style.display = '';
        img.style.display = 'none';
    }
    hideResults();
    hideError();
}

function clearPreview() {
    selectedFile = null;
    document.getElementById('dropZone').style.display = 'flex';
    document.getElementById('previewArea').style.display = 'none';
    document.getElementById('previewImage').src = '';
    document.getElementById('previewVideo').src = '';
    document.getElementById('fileInput').value = '';
    hideResults();
    hideError();
}

// ── Drag & Drop ───────────────────────────────────────────────────
const dropZone = document.getElementById('dropZone');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (!file) return;
    // Auto-switch mode based on file type
    if (file.type.startsWith('video/')) setMode('video');
    else setMode('image');
    loadFile(file);
});
dropZone.addEventListener('click', (e) => {
    if (e.target.id === 'btnBrowse') return;
    document.getElementById('fileInput').click();
});

// ── Detection (Image / Video) ─────────────────────────────────────
async function runDetection() {
    if (!selectedFile) return;
    setLoading(true);
    hideError();
    hideResults();

    const endpoint = currentMode === 'image'
        ? '/detect/image'
        : '/detect/video';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const resp = await fetch(endpoint, { method: 'POST', body: formData });
        const data = await resp.json();

        if (!resp.ok) {
            showError(data.detail || `Server error: ${resp.status}`);
            return;
        }
        if (!data.success) {
            showError('Detection failed. Please try another file.');
            return;
        }

        if (currentMode === 'image') renderImageResults(data);
        else renderVideoResults(data);

    } catch (err) {
        showError('Network error: ' + err.message);
    } finally {
        setLoading(false);
    }
}

// ── Detection (RTSP / Stream) ─────────────────────────────────────
async function runStreamDetection() {
    const input = document.getElementById('rtspInput');
    const url = input.value.trim();
    if (!url) {
        showError('Please paste a valid RTSP / stream URL.');
        return;
    }

    hideError();
    hideResults();

    const btn = document.getElementById('btnRtsp');
    const text = document.getElementById('rtspBtnText');
    const loader = document.getElementById('rtspBtnLoader');
    btn.disabled = true;
    text.style.display = 'none';
    loader.style.display = 'flex';

    try {
        const resp = await fetch(`/detect/stream?url=${encodeURIComponent(url)}`);
        const data = await resp.json();

        if (!resp.ok) {
            showError(data.detail || `Stream error: ${resp.status}`);
            return;
        }
        if (!data.success) {
            showError('Stream detection failed. Please check the URL and try again.');
            return;
        }

        renderStreamResults(data);
    } catch (err) {
        showError('Network / stream error: ' + err.message);
    } finally {
        btn.disabled = false;
        text.style.display = 'inline';
        loader.style.display = 'none';
    }
}

// ── Render Image Results ──────────────────────────────────────────
function renderImageResults(data) {
    const { total_plates, plates, annotated_image } = data;

    // Stats
    document.getElementById('resultsStats').textContent =
        `${total_plates} plate${total_plates !== 1 ? 's' : ''} detected`;

    // Annotated image
    const wrap = document.getElementById('annotatedMediaWrap');
    wrap.innerHTML = '';
    if (annotated_image) {
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + annotated_image;
        img.alt = 'Annotated Result';
        wrap.appendChild(img);
    }

    // Plates list
    renderPlateCards(plates, 'image');
    showResults();
}

// ── Render Video Results ──────────────────────────────────────────
function renderVideoResults(data) {
    const { total_unique_plates, plate_texts, annotated_video, frames_processed } = data;

    document.getElementById('resultsStats').textContent =
        `${total_unique_plates} unique plate${total_unique_plates !== 1 ? 's' : ''} · ${frames_processed} frames processed`;

    const wrap = document.getElementById('annotatedMediaWrap');
    wrap.innerHTML = '';
    if (annotated_video) {
        const vid = document.createElement('video');
        vid.src = 'data:video/mp4;base64,' + annotated_video;
        vid.controls = true;
        vid.style.maxWidth = '100%';
        wrap.appendChild(vid);
    }

    // Video returns only text list
    const fakePlates = plate_texts.map(t => ({ text: t, confidence: null, crop_image: null }));
    renderPlateCards(fakePlates, 'video');
    showResults();
}

// ── Render Stream Results ─────────────────────────────────────────
function renderStreamResults(data) {
    const { total_unique_plates, plate_texts, annotated_frame, frames_processed } = data;

    document.getElementById('resultsStats').textContent =
        `${total_unique_plates} unique plate${total_unique_plates !== 1 ? 's' : ''} · ${frames_processed} frames processed from stream`;

    const wrap = document.getElementById('annotatedMediaWrap');
    wrap.innerHTML = '';
    if (annotated_frame) {
        const img = document.createElement('img');
        img.src = 'data:image/jpeg;base64,' + annotated_frame;
        img.alt = 'Stream snapshot';
        wrap.appendChild(img);
    }

    const fakePlates = plate_texts.map(t => ({ text: t, confidence: null, crop_image: null }));
    renderPlateCards(fakePlates, 'stream');
    showResults();
}

// ── Plate Cards ───────────────────────────────────────────────────
function renderPlateCards(plates, mode) {
    const list = document.getElementById('platesList');
    list.innerHTML = '';

    if (!plates || plates.length === 0) {
        list.innerHTML = `
      <div class="no-plates">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        <p>No license plates detected.</p>
        <p style="margin-top:6px;font-size:0.8rem">Try a clearer or closer image.</p>
      </div>`;
        return;
    }

    plates.forEach((plate, i) => {
        const item = document.createElement('div');
        item.className = 'plate-item';
        item.style.animationDelay = `${i * 60}ms`;

        const text = plate.text || '';
        const confHtml = plate.confidence !== null
            ? `<span class="conf-badge">${(plate.confidence * 100).toFixed(0)}%</span>`
            : '';
        const thumbHtml = plate.crop_image
            ? `<div class="plate-thumb"><img src="data:image/jpeg;base64,${plate.crop_image}" alt="Plate crop" /></div>`
            : '';

        item.innerHTML = `
      <div class="plate-number ${!text ? 'empty' : ''}">${text || '(unreadable)'}</div>
      <div class="plate-meta">
        <span>Plate #${i + 1}</span>
        ${confHtml}
      </div>
      ${thumbHtml}
    `;
        list.appendChild(item);
    });
}

// ── UI Helpers ────────────────────────────────────────────────────
function setLoading(on) {
    const btn = document.getElementById('btnDetect');
    document.getElementById('detectBtnText').style.display = on ? 'none' : 'flex';
    document.getElementById('detectBtnLoader').style.display = on ? 'flex' : 'none';
    btn.disabled = on;
}

function showResults() {
    document.getElementById('resultsSection').style.display = 'block';
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}
function hideResults() { document.getElementById('resultsSection').style.display = 'none'; }

function showError(msg) {
    const banner = document.getElementById('errorBanner');
    document.getElementById('errorMsg').textContent = msg;
    banner.style.display = 'flex';
}
function hideError() { document.getElementById('errorBanner').style.display = 'none'; }
