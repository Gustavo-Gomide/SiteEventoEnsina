// upload.js - Funcionalidade para upload de fotos com preview
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = uploadArea.querySelector('input[type="file"]');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImage = uploadPreview.querySelector('.preview-image');
    const previewName = uploadPreview.querySelector('.preview-name');
    const previewSize = uploadPreview.querySelector('.preview-size');
    const uploadBtn = uploadArea.querySelector('.upload-btn');

    // Configurar o file input para ser acionado pelo botão e área
    uploadBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', function(e) {
        if (e.target !== uploadBtn && e.target !== fileInput) {
            fileInput.click();
        }
    });

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        uploadArea.classList.add('dragover');
    }

    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }

    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    // Handle file selection
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Validar tipo de arquivo
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                showError('Por favor, selecione uma imagem válida (JPEG, PNG, GIF ou WebP).');
                return;
            }

            // Validar tamanho do arquivo (5MB máximo)
            const maxSize = 5 * 1024 * 1024; // 5MB
            if (file.size > maxSize) {
                showError('A imagem deve ter no máximo 5MB.');
                return;
            }

            // Mostrar preview
            showPreview(file);
        }
    }

    function showPreview(file) {
        const reader = new FileReader();

        reader.onload = function(e) {
            // Atualizar preview
            previewImage.src = e.target.result;
            previewName.textContent = file.name;
            previewSize.textContent = formatFileSize(file.size);

            // Mostrar preview
            uploadPreview.classList.add('active');
            
            // Adicionar classe para indicar que há arquivo selecionado
            uploadArea.classList.add('has-file');
            
            // Atualizar texto da área de upload
            const uploadText = uploadArea.querySelector('.upload-text');
            uploadText.textContent = 'Arquivo selecionado';
            
            // Atualizar texto do botão
            uploadBtn.textContent = 'Alterar arquivo';
        }

        reader.onerror = function() {
            showError('Erro ao ler o arquivo. Tente novamente.');
        }

        reader.readAsDataURL(file);
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function showError(message) {
        // Criar ou atualizar mensagem de erro
        let errorElement = uploadArea.querySelector('.upload-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'upload-error erro';
            uploadArea.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        errorElement.style.display = 'block';

        // Remover mensagem após 5 segundos
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }

    // Efeito de loading simulado (opcional)
    function simulateUpload() {
        uploadArea.classList.add('uploading');
        setTimeout(() => {
            uploadArea.classList.remove('uploading');
            showSuccess('Upload realizado com sucesso!');
        }, 2000);
    }

    function showSuccess(message) {
        const successElement = document.createElement('div');
        successElement.className = 'upload-success';
        successElement.style.cssText = `
            color: #4CAF50;
            background: rgba(76, 175, 80, 0.1);
            padding: 0.5rem;
            border-radius: 4px;
            margin-top: 0.5rem;
            text-align: center;
            border-left: 3px solid #4CAF50;
        `;
        successElement.textContent = message;
        
        uploadArea.appendChild(successElement);

        setTimeout(() => {
            successElement.remove();
        }, 3000);
    }

    // Remover preview se necessário
    function clearPreview() {
        uploadPreview.classList.remove('active');
        uploadArea.classList.remove('has-file');
        
        const uploadText = uploadArea.querySelector('.upload-text');
        uploadText.textContent = 'Clique para fazer upload da foto';
        
        uploadBtn.textContent = 'Selecionar arquivo';
        
        fileInput.value = '';
    }

    // Adicionar botão para remover preview (opcional)
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.textContent = 'Remover';
    removeBtn.style.cssText = `
        background: #dc3545;
        color: white;
        border: none;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 0.5rem;
        font-size: 0.8rem;
    `;
    removeBtn.addEventListener('click', clearPreview);
    uploadPreview.appendChild(removeBtn);

    // Adicionar estilos CSS dinamicamente para elementos criados
    const style = document.createElement('style');
    style.textContent = `
        .upload-error {
            position: absolute;
            bottom: -40px;
            left: 0;
            right: 0;
            text-align: center;
            background: rgba(255, 107, 107, 0.1);
            border: 1px solid #ff6b6b;
            border-radius: 4px;
            padding: 0.5rem;
            z-index: 10;
        }
        
        .upload-success {
            animation: fadeInUp 0.5s ease;
        }
        
        .upload-area.has-file .upload-icon {
            color: #4CAF50 !important;
        }
        
        .upload-preview {
            transition: all 0.3s ease;
        }
        
        .upload-preview.active {
            animation: fadeInUp 0.5s ease;
        }
    `;
    document.head.appendChild(style);
});