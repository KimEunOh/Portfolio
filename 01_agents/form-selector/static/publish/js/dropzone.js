Dropzone.autoDiscover = false;

// 확장자를 MIME 타입으로 변환하는 유틸리티 함수
function convertExtensionsToMimeTypes(extensions) {
    const mimeMap = {
        pdf: 'application/pdf',
        ppt: 'application/vnd.ms-powerpoint',
        pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        hwp: 'application/x-hwp',
        doc: 'application/msword',
        docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        xls: 'application/vnd.ms-excel',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        csv: 'text/csv',
        txt: 'text/plain',
        zip: 'application/zip',
        rar: 'application/vnd.rar',
        '7z': 'application/x-7z-compressed',
        tar: 'application/x-tar',
        mp4: 'video/mp4',
        avi: 'video/x-msvideo',
        mkv: 'video/x-matroska',
        mov: 'video/quicktime',
        mp3: 'audio/mpeg',
        wav: 'audio/wav',
        ogg: 'audio/ogg',
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        png: 'image/png',
        gif: 'image/gif',
        svg: 'image/svg+xml',
        webp: 'image/webp',
        bmp: 'image/bmp',
        ico: 'image/vnd.microsoft.icon',
        html: 'text/html',
        htm: 'text/html',
        // 필요한 확장자를 추가하세요
    };

    return extensions
        .split(',')
        .map(ext => ext.trim().replace('.', '').toLowerCase())
        .map(ext => mimeMap[ext] || ext) // MIME 타입으로 변환하거나 기본값 유지
        .join(',');
}

/**
 *
 *
 * @param selector : 드랍존selector
 * @param options
 * {
 *	uploadedFiles : 드랍존에 세팅할 업로드 된 파일 [{name, size, id}, {}...] (default: [])
 *	maxFiles : 최대 파일 개수 (default: 1)
 *	acceptedExtensions : 허용 확장자 (default: *)
 *	url : 업로드 url (즉시 업로드가 아니라 사용하지 않음)
 *	fileRemoveCallback : 파일 삭제 후 콜백 함수(default: null)
 * }
 * @returns {*}
 */
// Dropzone 초기화 함수
function initDropzone(selector, options) {
    let defaultOption = {
        uploadedFiles: [],
        maxFiles: 1,
        acceptedExtensions: '*',
        url: '/upload',
        fileRemoveCallback: null,
        maxFileSize: (1024 * 1024 * 1024 * 10),  //default 10MB
        maxRequestSize: (1024 * 1024 * 1024 * 50)   //default 50MB
    }
    options = options || {};
    options = {...defaultOption, ...options };
    // uploadedFiles, maxFiles, acceptedExtensions = '*'
    const dropzoneElement = document.querySelector(selector);

    if (!dropzoneElement) return; // 선택자가 유효하지 않으면 종료

    let existingFileCount = options.uploadedFiles.length;

    // 확장자를 MIME 타입으로 변환
    const acceptedMimeTypes = options.acceptedExtensions === '*' ? '*' : convertExtensionsToMimeTypes(options.acceptedExtensions);

    const myDropzone = new Dropzone(dropzoneElement, {
        url: options.url, // 파일을 업로드할 서버 경로
        autoProcessQueue: false, // 파일 자동 업로드 비활성화
        autoQueue: false, // 드래그 드랍 후 바로 서버로 전송
        clickable: dropzoneElement.querySelector(selector + ' .btn_upload'), // 사용자 정의 버튼을 클릭하여 파일 선택
        maxFiles: (options.maxFiles === 0 || options.maxFiles < 0) ? null : options.maxFiles, // 최대 파일 첨부 개수 설정
        maxFileSize: (options.maxFileSize === 0 || options.maxFileSize < 0) ? null : options.maxFileSize,	// 첨부파일 사이즈 설정
        maxRequestSize: (options.maxRequestSize === 0 || options.maxRequestSize < 0) ? null : options.maxRequestSize,	// 첨부파일 전체 사이즈 설정
        acceptedFiles: acceptedMimeTypes, // 동적으로 설정된 파일 타입
        addRemoveLinks: true, // 업로드 후 파일 삭제버튼 표시 여부
        dictRemoveFile: '삭제', // 삭제버튼 표시 텍스트
        init: function() {
            const myDropzone = this;

            /*$("button[type='submit']").click(function(e) {
                console.log('submit');
                e.preventDefault();
                e.stopPropagation();

                if (myDropzone.getQueuedFiles().length <= 0 ) {
                    alert('업로드할 파일이 없습니다.');
                    return false;
                } else {
                    console.log("lng", myDropzone.getQueuedFiles().length, myDropzone.getUploadingFiles());
                    if(myDropzone.getQueuedFiles().length > 0) {
                        myDropzone.processQueue();
                    }
                }
            });*/

            // 이미 업로드된 파일 표시
            addExistingFiles(myDropzone, options.uploadedFiles);

            // 새 파일이 추가될 때 처리
            myDropzone.on('addedfile', function(file) {
                handleAddedFile(myDropzone, file, existingFileCount++, options.maxFiles);
                checkFileType(myDropzone, file, acceptedMimeTypes);

                // 파일 확장자 가져오기
                const fileExtension = file.name.split('.').pop().toLowerCase();

                // 확장자에 따른 클래스 추가
                const previewElement = file.previewElement;
                previewElement.classList.add('file_'+fileExtension);
            });

            // 파일이 제거되면 기존 파일 개수를 업데이트
            myDropzone.on('removedfile', function(file) {
                existingFileCount = handleRemovedFile(existingFileCount);
                if (options.fileRemoveCallback && typeof options.fileRemoveCallback === 'function') {
                    options.fileRemoveCallback(file);
                }
            });
            myDropzone.on("resetFiles", function () {
                $(selector).find(".dz-success").remove();
                for (let file of myDropzone.files) {
                    myDropzone.emit("removedfile", file);
                }
                myDropzone.files = [];
                return myDropzone.emit("reset");
            });
            myDropzone.on("addFileCount", function (count) {
                existingFileCount += count;
            });
            myDropzone.on("fileCount", function () {
                return $(selector).find(".dz-preview").length;
            });
        }
    });
    return myDropzone;
}

// 드랍존의 파일 개수 리턴
function getDropzoneFileCount(id) {
    return $(`${id}`).find(".dz-preview").length;
}

// 이미 업로드된 파일 추가 함수
function addExistingFiles(myDropzone, uploadedFiles) {
    uploadedFiles.forEach(function(fileInfo) {
        const mockFile = { name: fileInfo.name, size: fileInfo.size, id: fileInfo.id, type: fileInfo.type };
        const mockFileExtension = fileInfo.name.split('.').pop().toLowerCase();

        // Dropzone에 기존 파일 추가
        myDropzone.emit('addedfile', mockFile);

        // 이미지 파일의 경우 썸네일 생성
        if (fileInfo.url) {
            myDropzone.emit('thumbnail', mockFile, fileInfo.url); // 이미지 URL로 썸네일 표시
        }

        // 업로드 완료 상태로 표시
        myDropzone.emit('complete', mockFile);

        // 업로드된 파일 성공적으로 표시
        mockFile.previewElement.classList.add('dz-success', 'dz-complete', 'file_'+mockFileExtension);
    });
}

// 새 파일이 추가될 때 파일 개수와 타입 체크
function handleAddedFile(myDropzone, file, existingFileCount, maxFiles) {
    // 기존 파일 개수 + 새 파일 개수 > 최대 파일 개수일 경우, 새 파일 제거
    if (maxFiles !== null && existingFileCount + myDropzone.files.length > maxFiles) {
        showAlert('error', '에러', '확인', '', '최대 파일 첨부 개수를 초과했습니다.');
        myDropzone.removeFile(file); // 초과한 파일을 제거
    }
    if (file.size > myDropzone.options.maxFileSize) {
        showAlert('error', '에러', '확인', '', '최대 업로드 사이즈를 초과했습니다.');
        myDropzone.removeFile(file); // 초과한 파일을 제거
    }
    if (myDropzone.files && myDropzone.files.length > 0) {
        let totalSize = 0;
        $.each(myDropzone.files, function (index, item) {
            totalSize += item.size;
        });
        if (totalSize > myDropzone.options.maxRequestSize) {
            showAlert('error', '에러', '확인', '', '전체 파일 최대 업로드 사이즈를 초과했습니다.');
            myDropzone.removeFile(file); // 초과한 파일을 제거
        }
    }
}

// 파일이 제거될 때 기존 파일 개수를 감소
function handleRemovedFile(existingFileCount) {
    if (existingFileCount > 0) {
        existingFileCount--;
    }
    return existingFileCount;
}

// 파일 타입 체크
function checkFileType(myDropzone, file, acceptedFiles) {
    const fileType = file.type;
    const acceptedFileTypes = acceptedFiles.split(','); // 예: 'image/jpeg,image/png' -> ['image/jpeg', 'image/png']

    if (acceptedFiles !== '*') {
        if (acceptedFiles.includes('image/*')) {
            // image/* 가 포함된 경우, 파일 타입이 image로 시작하는지 체크
            if (!fileType.startsWith('image/')) {
                showAlert('error', '에러', '확인', '', '허용된 파일 형식이 아닙니다.');
                myDropzone.removeFile(file);
            }
        } else if (!acceptedFileTypes.includes(fileType)) {
            // 다른 특정 파일 형식인 경우
            showAlert('error', '에러', '확인', '', '허용된 파일 형식이 아닙니다.');
            myDropzone.removeFile(file);
        }
    }
}