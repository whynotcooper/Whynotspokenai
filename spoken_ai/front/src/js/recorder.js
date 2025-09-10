let recorder;
let isRecording = false;
let dialogueHistory = [];

// 初始化录音
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        const audioContext = new AudioContext();
        const input = audioContext.createMediaStreamSource(stream);
        recorder = new Recorder(input);
    });

function toggleRecording() {
    if (!isRecording) {
        recorder.record();
        isRecording = true;
        document.getElementById('recordBtn').innerText = '⏹ 停止录音';
        document.getElementById('recordingStatus').innerText = '正在录音...';
    } else {
        recorder.stop();
        isRecording = false;
        document.getElementById('recordBtn').innerText = '🎤 开始录音';
        document.getElementById('recordingStatus').innerText = '正在处理...';

        recorder.exportWAV(uploadAudio);
        recorder.clear();
    }
}

function uploadAudio(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.wav');
    formData.append('topic', document.getElementById('topicSelect').value);

    fetch('/api/process_audio/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': '{{ csrf_token }}' }
    })
    .then(res => res.json())
    .then(data => {
        addMessage('user', data.transcription);
        addMessage('coach', data.feedback);
    });
}

function addMessage(sender, text) {
    const chatBox = document.getElementById('chatBox');
    const div = document.createElement('div');
    div.className = `alert ${sender === 'user' ? 'alert-info' : 'alert-warning'}`;
    div.innerHTML = `<strong>${sender === 'user' ? '你' : '教练'}:</strong> ${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function endTraining() {
    Swal.fire('训练已结束', '你可以生成学习报告了！', 'info');
}

function generateReport() {
    fetch('/api/generate_report/', {
        method: 'POST',
        headers: { 'X-CSRFToken': '{{ csrf_token }}' }
    })
    .then(res => res.blob())
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'spoken_report.pdf';
        a.click();
    });
}