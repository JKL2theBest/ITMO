import {
  exportCurrentTabs,
  importTabsFromFile,
  restoreTabsFromPayload,
  getLastExport,
  getAllExports,
  clearExportHistory
} from './utils.js';

let lastExportPayload = null;

const elements = {
  exportBtn: document.getElementById('exportTabs'),
  downloadBtn: document.getElementById('downloadLast'),
  importInput: document.getElementById('importFile'),
  restoreBtn: document.getElementById('restoreImport'),
  exportList: document.getElementById('exportList'),
  clearBtn: document.getElementById('clearHistory')
};

async function render() {
  elements.exportList.innerHTML = '';

  try {
    const entries = await getAllExports();

    if (!entries.length) {
      elements.exportList.textContent = 'Нет сохранённых экспортов';
      return;
    }
    // Создание элементов списка экспортов
    entries.forEach(([key, payload]) => {
      const item = createExportItem(payload);
      elements.exportList.appendChild(item);
    });
  } catch (error) {
    console.error('Ошибка при рендеринге истории:', error);
  }
}

function createExportItem(payload) {
  const item = document.createElement('div');
  item.className = 'export-item';

  const header = createExportHeader(payload);
  item.appendChild(header);

  const details = createExportDetails(payload);
  item.appendChild(details);

  return item;
}

function createExportHeader(payload) {
  const header = document.createElement('div');
  header.className = 'export-header';

  // Дата
  const dateEl = document.createElement('span');
  dateEl.className = 'date';
  dateEl.textContent = new Date(payload.timestamp).toLocaleString();
  header.appendChild(dateEl);

  // Иконки вкладок
  const iconContainer = document.createElement('div');
  iconContainer.className = 'icon-container';

  payload.tabs.forEach(tab => {
    if (tab.favIcon) {
      const img = document.createElement('img');
      img.src = tab.favIcon;
      img.alt = tab.title;
      img.className = 'tab-icon';
      iconContainer.appendChild(img);
    }
  });

  header.appendChild(iconContainer);

  // Кнопки действий
  const btns = document.createElement('div');
  btns.className = 'item-buttons';

  const downloadBtn = document.createElement('button');
  downloadBtn.className = 'btn';
  downloadBtn.textContent = 'Скачать';
  downloadBtn.onclick = () => window.downloadJson(payload);
  btns.appendChild(downloadBtn);

  const restoreBtn = document.createElement('button');
  restoreBtn.className = 'btn';
  restoreBtn.textContent = 'Откатиться';
  restoreBtn.onclick = () => restoreTabsFromPayload(payload).catch(console.error);
  btns.appendChild(restoreBtn);

  header.appendChild(btns);

  return header;
}

function createExportDetails(payload) {
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = 'Показать JSON';

  const pre = document.createElement('pre');
  pre.textContent = JSON.stringify(payload, null, 2);

  details.append(summary, pre);

  return details;
}

function handleExport() {
  exportCurrentTabs()
    .then(payload => {
      lastExportPayload = payload;
      elements.downloadBtn.disabled = false;
      render();
    })
    .catch(error => {
      console.error('Ошибка при экспорте:', error);
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
      render();
    })
    .catch(error => {
      console.error('Ошибка при импорте:', error);
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

function handleClearHistory() {
  const confirmClear = confirm('Подтвердите удаление истории');
  if (!confirmClear) return;

  clearExportHistory()
    .then(render)
    .catch(error => {
      console.error('Ошибка при очистке истории:', error);
    });
}

// Обработчики событий
elements.exportBtn.addEventListener('click', handleExport);
elements.downloadBtn.addEventListener('click', handleDownload);
elements.importInput.addEventListener('change', handleImport);
elements.restoreBtn.addEventListener('click', handleRestore);
elements.clearBtn.addEventListener('click', handleClearHistory);

document.addEventListener('DOMContentLoaded', render);
