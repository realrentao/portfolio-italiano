/**
 * edge-tts 音频播放管理器
 * 替代 Web Speech API，使用预生成的 edge-tts MP3 音频文件播放意大利语发音
 */
(function () {
  'use strict';

  const toast = document.getElementById('audioToast');
  let toastTimer = null;
  let currentAudio = null;
  let audioMap = null;
  let audioLoaded = false;

  /* ---- Toast 提示 ---- */
  function showToast() {
    if (!toast) return;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove('show');
    }, 1800);
  }

  /* ---- 加载音频映射表 ---- */
  function loadAudioMap(callback) {
    if (audioLoaded && audioMap) {
      if (callback) callback();
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'audio/audio_map.json', true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          audioMap = JSON.parse(xhr.responseText);
          audioLoaded = true;
          if (callback) callback();
        } catch (e) {
          console.warn('[edge-tts] 解析 audio_map.json 失败', e);
        }
      } else {
        console.warn('[edge-tts] 加载 audio_map.json 失败，状态码:', xhr.status);
      }
    };
    xhr.onerror = function () {
      console.warn('[edge-tts] 加载 audio_map.json 网络错误');
    };
    xhr.send();
  }

  /* ---- 播放音频 ---- */
  function playAudio(text, element) {
    if (!audioMap) {
      loadAudioMap(function () {
        playAudio(text, element);
      });
      return;
    }

    // 停止当前播放
    stopCurrent();

    var filename = audioMap[text];
    if (!filename) {
      console.warn('[edge-tts] 未找到文本的音频:', text.slice(0, 30) + '...');
      return;
    }

    var audioPath = 'audio/' + filename;
    var audio = new Audio(audioPath);
    currentAudio = audio;

    // 高亮正在播放的元素
    if (element) {
      element.classList.add('speaking');
    }

    audio.addEventListener('ended', function () {
      if (element) element.classList.remove('speaking');
      currentAudio = null;
    });

    audio.addEventListener('error', function () {
      if (element) element.classList.remove('speaking');
      currentAudio = null;
      console.warn('[edge-tts] 播放失败:', audioPath);
    });

    audio.play().catch(function (err) {
      if (element) element.classList.remove('speaking');
      currentAudio = null;
      console.warn('[edge-tts] 播放被阻止:', err);
    });

    showToast();
  }

  /* ---- 停止当前播放 ---- */
  function stopCurrent() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
    // 清除所有元素的 speaking 状态
    document.querySelectorAll('.it.speaking').forEach(function (el) {
      el.classList.remove('speaking');
    });
  }

  /* ---- 初始化 ---- */
  function init() {
    // 预加载音频映射
    loadAudioMap();

    // 绑定点击事件
    document.querySelectorAll('.it[data-speak]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.stopPropagation();
        var text = this.getAttribute('data-speak');
        playAudio(text, this);
      });
    });
  }

  // 等 DOM 加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
