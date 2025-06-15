import {
  exportCurrentTabs,
  importTabsFromFile,
  restoreTabsFromPayload,
  getLastExport
} from './utils.js';

let lastExportPayload = null;

const elements = {
  exportBtn: document.getElementById('exportTabs'),
  downloadBtn: document.getElementById('downloadLast'),
  importInput: document.getElementById('importFile'),
  restoreBtn: document.getElementById('restoreImport'),
  openOptionsBtn: document.getElementById('openOptions')
};

function handleExport() {
  exportCurrentTabs()
    .then(payload => {
      lastExportPayload = payload;
      elements.downloadBtn.disabled = false;
    })
    .catch(error => {
      console.error('Ошибка при экспорте вкладок:', error);
    });
}

function handleDownload() {
  if (lastExportPayload) {
    window.downloadJson(lastExportPayload);
  }
}

function handleImport(e) {
  const file = e.target.files[0];
  if (!file) return;

  importTabsFromFile(file)
    .then(payload => {
      lastExportPayload = payload;
      elements.restoreBtn.disabled = false;
    })
    .catch(error => {
      console.error('Ошибка при импорте JSON:', error);
      alert('Неверный JSON-файл');
      e.target.value = '';
    });
}

function handleRestore() {
  getLastExport()
    .then(payload => {
      if (payload && Array.isArray(payload.tabs)) {
        restoreTabsFromPayload(payload).catch(console.error);
      }
    })
    .catch(error => {
      console.error('Ошибка при восстановлении вкладок:', error);
    });
}

function openOptions() {
  chrome.runtime.openOptionsPage();
}

// Обработчики событий
elements.exportBtn.addEventListener('click', handleExport);
elements.downloadBtn.addEventListener('click', handleDownload);
elements.importInput.addEventListener('change', handleImport);
elements.restoreBtn.addEventListener('click', handleRestore);
elements.openOptionsBtn.addEventListener('click', openOptions);
