const chatBox   = document.getElementById('chatBox');
const recBtn    = document.getElementById('recBtn');
const recIcon   = document.getElementById('recIcon');
const recText   = document.getElementById('recText');
const themeBtn  = document.getElementById('themeToggle');

let mediaRecorder, chunks = [];

// 深色模式
themeBtn.onclick = () => {
  document.documentElement.toggleAttribute('data-theme',
    document.documentElement.getAttribute('data-theme') !== 'dark' ? 'dark' : null
  );
};

// 创建气泡
function addBubble(text, isUser=false) {
  const div = document.createElement('div');
  div.className = isUser ? 'user-bubble' : 'bot-bubble';
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// 打字机效果
function typeWriter(el, text, speed=40) {
  let i = 0;
  el.textContent = '';
  function type() {
    if (i < text.length) {
      el.textContent += text.charAt(i++);
      setTimeout(type, speed);
    }
  }
  type();
}

// 录音按钮按下
recBtn.addEventListener('mousedown', startRecording);
recBtn.addEventListener('touchstart', startRecording, {passive: true});
// 松开
recBtn.addEventListener('mouseup', stopRecording);
recBtn.addEventListener('touchend', stopRecording);

function startRecording(e) {
  e.preventDefault();
  if (!navigator.mediaDevices) return alert('浏览器不支持录音');
  recBtn.classList.add('recording');
  recIcon.textContent = '⏹️';
  recText.textContent = '松开发送';

  navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => {
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];
      mediaRecorder.ondataavailable = e => chunks.push(e.data);
      mediaRecorder.onstop = sendAudio;
      mediaRecorder.start();
    })
    .catch(err => alert('麦克风权限获取失败：' + err));
}

function stopRecording(e) {
  e.preventDefault();
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
  }
  recBtn.classList.remove('recording');
  recIcon.textContent = '🎤';
  recText.textContent = '按住说话';
}

// 上传音频并获取结果
function sendAudio() {
  const blob = new Blob(chunks, {type: 'audio/wav'});
  const form = new FormData();
  form.append('audio', blob, 'record.wav');

  addBubble('正在识别...', false);

  fetch('/process_audio/', {
    method: 'POST',
    body: form,
    headers: {'X-CSRFToken': getCookie('csrftoken')}
  })
  .then(r => r.json())
  .then(data => {
    // 移除“正在识别...”
    chatBox.removeChild(chatBox.lastChild);
    addBubble(data.transcription, true);
    // 打字机效果展示反馈
    const botDiv = document.createElement('div');
    botDiv.className = 'bot-bubble';
    chatBox.appendChild(botDiv);
    typeWriter(botDiv, data.feedback);
  })
  .catch(err => {
    addBubble('识别失败，请重试：' + err, false);
  });
}

// CSRF
function getCookie(name) {
  let c = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return c ? decodeURIComponent(c[2]) : '';
}
