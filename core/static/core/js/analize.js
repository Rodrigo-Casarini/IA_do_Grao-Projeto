document.addEventListener('DOMContentLoaded', () => {
    const cameraVideo = document.getElementById('camera-video');
    const cameraSelect = document.getElementById('camera-select');
    const activateCameraButton = document.getElementById('activate-camera');
    const captureFrameButton = document.getElementById('capture-frame');
    const cameraPlaceholder = document.getElementById('camera-placeholder');
    const liveLabel = document.getElementById('live-label');
    const cameraAlert = document.getElementById('camera-alert');
    const imageInput = document.getElementById('id_imagens');
    const imagePreviewList = document.getElementById('image-preview-list');
    const cameraPreviewList = document.getElementById('camera-preview-list');
    const captureCount = document.getElementById('capture-count');
    let cameraStream = null;
    let captureIndex = 0;
    let selectedFiles = [];
    let uploadedFiles = [];

    function showCameraAlert(message, isError = false) {
        if (!cameraAlert) return;

        cameraAlert.textContent = message;
        cameraAlert.hidden = !message;
        cameraAlert.style.display = message ? 'block' : 'none';
        cameraAlert.style.color = isError ? '#a72d2d' : '#0a7f59';
    }

    function updateCaptureState() {
        if (!captureCount || !captureFrameButton) return;

        captureCount.textContent = `${selectedFiles.length} de 3 imagens adicionadas`;
        captureFrameButton.disabled = selectedFiles.length >= 3 || !cameraStream;
    }

    function syncInputFiles() {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(item => dataTransfer.items.add(item.file));
        imageInput.files = dataTransfer.files;
    }

    function renderPreviewList(container, items, label) {
        if (!container) return;

        container.innerHTML = '';
        items.forEach((item, index) => {
            const file = item.file;
            const preview = document.createElement('div');
            preview.className = 'image-preview-item';

            const image = document.createElement('img');
            image.className = 'upload-preview-image';
            image.alt = `Prévia da imagem ${index + 1}`;
            const imageUrl = URL.createObjectURL(file);
            image.src = imageUrl;
            image.onload = () => URL.revokeObjectURL(imageUrl);

            const caption = document.createElement('span');
            caption.textContent = `${label} ${index + 1}`;

            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'remove-image-btn';
            removeButton.textContent = 'Remover';
            removeButton.addEventListener('click', () => {
                selectedFiles = selectedFiles.filter(candidate => candidate !== item);
                uploadedFiles = selectedFiles
                    .filter(item => item.source === 'upload')
                    .map(item => item.file);
                syncInputFiles();
                renderPreviews();
                updateCaptureState();
            });

            preview.append(image, caption, removeButton);
            container.appendChild(preview);
        });
    }

    function renderPreviews() {
        renderPreviewList(
            imagePreviewList,
            selectedFiles.filter(item => item.source === 'upload'),
            'Upload',
        );
        renderPreviewList(
            cameraPreviewList,
            selectedFiles.filter(item => item.source === 'camera'),
            'Captura',
        );
    }

    async function listCameras() {
        if (!navigator.mediaDevices?.enumerateDevices || !cameraSelect) return;

        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameras = devices.filter(device => device.kind === 'videoinput');
        cameraSelect.innerHTML = '<option value="">Selecionar câmera</option>';

        cameras.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.textContent = `Câmera ${index + 1}`;
            cameraSelect.appendChild(option);
        });
    }

    async function activateCamera() {
        if (!navigator.mediaDevices?.getUserMedia) {
            showCameraAlert('Seu navegador não suporta acesso à câmera.', true);
            return;
        }

        try {
            const videoConstraints = cameraSelect.value
                ? { deviceId: { exact: cameraSelect.value } }
                : {
                    facingMode: { ideal: 'user' },
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30, max: 30 },
                };

            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: videoConstraints,
                audio: false,
            });
            cameraVideo.srcObject = cameraStream;
            cameraVideo.muted = true;
            cameraVideo.playsInline = true;
            await cameraVideo.play();

            cameraPlaceholder.hidden = true;
            liveLabel.hidden = false;
            updateCaptureState();
            showCameraAlert('Câmera ativada com sucesso.');
            await listCameras();
        } catch (error) {
            console.error('Erro ao acessar a câmera:', error);
            const errorMessages = {
                NotAllowedError: 'A permissão da câmera foi bloqueada pelo navegador.',
                NotFoundError: 'Nenhuma câmera foi encontrada neste dispositivo.',
                NotReadableError: 'A câmera está sendo usada por outro aplicativo.',
                OverconstrainedError: 'A câmera selecionada não está disponível.',
                SecurityError: 'O navegador bloqueou o acesso à câmera nesta página.',
            };
            const message = errorMessages[error.name]
                || `Não foi possível acessar a câmera (${error.name || 'erro desconhecido'}).`;
            showCameraAlert(message, true);
        }
    }

    function dataUrlToFile(dataUrl, fileName) {
        const [header, encodedData] = dataUrl.split(',');
        const byteString = atob(encodedData);
        const mimeType = header.split(':')[1].split(';')[0];
        const bytes = new Uint8Array(byteString.length);

        for (let index = 0; index < byteString.length; index += 1) {
            bytes[index] = byteString.charCodeAt(index);
        }

        return new File([bytes], fileName, { type: mimeType });
    }

    function stopCamera() {
        if (!cameraStream) return;

        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
        updateCaptureState();
    }

    function setupFilePreview() {
        if (!imageInput || !imagePreviewList) return;

        imageInput.addEventListener('change', () => {
            const newFiles = Array.from(imageInput.files);
            uploadedFiles = [...uploadedFiles, ...newFiles].filter((file, index, files) => (
                files.findIndex(candidate => (
                    candidate.name === file.name
                    && candidate.size === file.size
                    && candidate.lastModified === file.lastModified
                )) === index
            )).slice(0, 3);
            const cameraFiles = selectedFiles.filter(item => item.source === 'camera');
            selectedFiles = [
                ...uploadedFiles.map(file => ({ file, source: 'upload' })),
                ...cameraFiles,
            ].slice(0, 3);
            uploadedFiles = selectedFiles
                .filter(item => item.source === 'upload')
                .map(item => item.file);
            syncInputFiles();
            renderPreviews();
            updateCaptureState();
        });
    }

    function setupCamera() {
        if (!cameraVideo || !cameraSelect || !activateCameraButton || !captureFrameButton) return;

        activateCameraButton.addEventListener('click', activateCamera);
        cameraSelect.addEventListener('change', async () => {
            stopCamera();
            await activateCamera();
        });

        captureFrameButton.addEventListener('click', () => {
            if (!cameraStream || !cameraVideo.videoWidth || !cameraVideo.videoHeight) {
                showCameraAlert('Ative a câmera antes de capturar a imagem.', true);
                return;
            }

            if (selectedFiles.length >= 3) {
                showCameraAlert('Você já adicionou o limite de 3 imagens.', true);
                return;
            }

            const canvas = document.createElement('canvas');
            canvas.width = cameraVideo.videoWidth;
            canvas.height = cameraVideo.videoHeight;
            canvas.getContext('2d').drawImage(
                cameraVideo,
                0,
                0,
                canvas.width,
                canvas.height,
            );

            const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
            selectedFiles.push({
                file: dataUrlToFile(dataUrl, `captura-camera-${captureIndex + 1}.jpg`),
                source: 'camera',
            });
            captureIndex += 1;
            syncInputFiles();
            renderPreviews();
            updateCaptureState();
            showCameraAlert('Imagem capturada e adicionada à sequência.');
        });

        listCameras();
        updateCaptureState();
    }

    function setupAnalysisSelection() {
        const selectAll = document.getElementById('select-all-analyses');
        const checkboxes = Array.from(document.querySelectorAll('.analysis-checkbox'));
        const deleteButton = document.getElementById('delete-selected');
        const deleteForm = document.getElementById('delete-analyses-form');

        if (!selectAll || !deleteButton || !deleteForm) return;

        function updateSelection() {
            const selectedCount = checkboxes.filter(checkbox => checkbox.checked).length;
            deleteButton.disabled = selectedCount === 0;
            selectAll.checked = checkboxes.length > 0 && selectedCount === checkboxes.length;
            selectAll.indeterminate = selectedCount > 0 && selectedCount < checkboxes.length;
        }

        selectAll.addEventListener('change', () => {
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
            updateSelection();
        });

        checkboxes.forEach(checkbox => checkbox.addEventListener('change', updateSelection));
        deleteForm.addEventListener('submit', event => {
            const selectedCount = checkboxes.filter(checkbox => checkbox.checked).length;
            const message = `Excluir ${selectedCount} análise(s) selecionada(s)? Esta ação não pode ser desfeita.`;

            if (!window.confirm(message)) event.preventDefault();
        });
    }

    function setupDetailsModals() {
        const openButtons = document.querySelectorAll('[data-details-target]');

        openButtons.forEach(button => {
            const modal = document.getElementById(button.dataset.detailsTarget);
            if (!modal) return;

            button.addEventListener('click', () => {
                modal.hidden = false;
                updateModalState();
            });

            modal.querySelector('[data-details-close]')?.addEventListener('click', () => {
                modal.hidden = true;
                updateModalState();
            });

            modal.addEventListener('click', event => {
                if (event.target === modal) {
                    modal.hidden = true;
                    updateModalState();
                }
            });
        });
    }

    function updateModalState() {
        const openModal = document.querySelector('.details-modal:not([hidden]), .image-viewer-modal:not([hidden])');
        document.body.classList.toggle('modal-open', Boolean(openModal));
    }

    function setupImageViewer() {
        const modal = document.getElementById('image-viewer');
        const photo = document.getElementById('image-viewer-photo');
        const overlay = document.getElementById('image-viewer-boxes');
        if (!modal || !photo || !overlay) return;

        function closeViewer() {
            modal.hidden = true;
            photo.removeAttribute('src');
            overlay.replaceChildren();
            updateModalState();
        }

        document.querySelectorAll('[data-image-viewer]').forEach(button => {
            button.addEventListener('click', () => {
                let imageData;
                try {
                    imageData = JSON.parse(button.dataset.imageBoxes || '{}');
                } catch (error) {
                    imageData = {};
                }

                photo.src = button.dataset.imageUrl;
                photo.alt = button.dataset.imageAlt || 'Imagem analisada';
                overlay.setAttribute('viewBox', `0 0 ${imageData.largura || 1} ${imageData.altura || 1}`);
                overlay.replaceChildren();

                (imageData.caixas || []).forEach(box => {
                    const rectangle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    rectangle.setAttribute('x', box.x1);
                    rectangle.setAttribute('y', box.y1);
                    rectangle.setAttribute('width', box.x2 - box.x1);
                    rectangle.setAttribute('height', box.y2 - box.y1);
                    const boxClass = {
                        mofado: 'mold-detection-box',
                        saudavel: 'healthy-detection-box',
                        incompativel: 'incompatible-detection-box',
                    }[box.estado] || 'incompatible-detection-box';
                    rectangle.setAttribute('class', boxClass);
                    overlay.appendChild(rectangle);
                });

                modal.hidden = false;
                updateModalState();
                modal.querySelector('[data-image-viewer-close]')?.focus();
            });
        });

        modal.querySelector('[data-image-viewer-close]')?.addEventListener('click', closeViewer);
        modal.addEventListener('click', event => {
            if (event.target === modal) closeViewer();
        });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && !modal.hidden) closeViewer();
        });
    }

    setupCamera();
    setupFilePreview();
    setupAnalysisSelection();
    setupDetailsModals();
    setupImageViewer();
});
