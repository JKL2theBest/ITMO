const LAST_EXPORT_KEY = 'last_export';

/**
 * Экспорт текущих вкладок
 */
export async function exportCurrentTabs() {
  const tabs = await chrome.tabs.query({ currentWindow: true });
  const tabsInfo = [];

  for (const t of tabs) {
    let favIcon = '';
    if (t.favIconUrl) {
      try {
        const res = await fetch(t.favIconUrl);
        const blob = await res.blob();
        favIcon = await new Promise(resolve => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        });
      } catch (e) {
        console.warn(`Не удалось загрузить favicon ${t.favIconUrl}`, e);
      }
    }
    tabsInfo.push({
      title: t.title,
      url: t.url,
      favIcon
    });
  }

  const payload = {
    timestamp: new Date().toISOString(),
    tabs: tabsInfo
  };

  const key = `export_${payload.timestamp}`;
  await chrome.storage.local.set({
    [key]: payload,
    [LAST_EXPORT_KEY]: payload
  });

  return payload;
}

/**
 * @param {File} file - Файл для импорта
 */
export async function importTabsFromFile(file) {
  const text = await file.text();
  const json = JSON.parse(text);
  await chrome.storage.local.set({ [LAST_EXPORT_KEY]: json });
  return json;
}

/**
 * @param {{timestamp: string, tabs: Array}} payload - Данные для восстановления вкладок
 */
export async function restoreTabsFromPayload(payload) {
  const originalTabs = await chrome.tabs.query({ currentWindow: true });
  const originalIds = originalTabs.map(t => t.id);
  const urlsToKeep = payload.tabs.map(t => t.url);

  // Открываем вкладки, которые должны быть восстановлены
  const tabsToOpen = payload.tabs.filter(t => !originalTabs.some(o => o.url === t.url));
  for (const tab of tabsToOpen) {
    try {
      await chrome.tabs.create({ url: tab.url });
    } catch (error) {
      console.warn(`Не удалось открыть URL: ${tab.url}`, error);
    }
  }

  // Закрываем все вкладки, которые не находятся в списке для восстановления
  const tabsToClose = originalTabs.filter(t => !urlsToKeep.includes(t.url));
  const tabIdsToClose = tabsToClose.map(t => t.id);

  if (tabIdsToClose.length > 0) {
    await chrome.tabs.remove(tabIdsToClose); // Закрываем все вкладки, которые не должны быть восстановлены
  }
}

/**
 * Возвращает последний экспорт
 */
export async function getLastExport() {
  const stored = await chrome.storage.local.get(LAST_EXPORT_KEY);
  return stored[LAST_EXPORT_KEY];
}

/**
 * Получает все экспортированные вкладки
 */
export async function getAllExports() {
  const all = await chrome.storage.local.get(null);
  return Object.entries(all)
    .filter(([k, v]) => k.startsWith('export_') && v && Array.isArray(v.tabs))
    .sort((a, b) => new Date(b[1].timestamp) - new Date(a[1].timestamp));
}

/**
 * Очистка истории экспорта
 */
export async function clearExportHistory() {
  const all = await chrome.storage.local.get(null);
  const keys = Object.keys(all).filter(k => k.startsWith('export_') || k === LAST_EXPORT_KEY);
  await chrome.storage.local.remove(keys);
}

/**
 * @param {Array<string>} urls - Список URL для открытия
 * @param {Array<number>} originalIds - Список ID вкладок для закрытия
 */
window.restoreTabs = async function(urls, originalIds) {
  try {
    for (const url of urls) {
      try {
        await chrome.tabs.create({ url });
      } catch (error) {
        console.warn(`Не удалось открыть URL: ${url}`, error);
      }
    }

    for (const id of originalIds) {
      try {
        await chrome.tabs.remove(id);
      } catch (error) {
        console.warn(`Не удалось закрыть вкладку с ID: ${id}`, error);
      }
    }
  } catch (error) {
    console.error('Ошибка при восстановлении вкладок:', error);
  }
};

/**
 * @param {{timestamp: string, tabs: Array}} payload - Данные для экспорта
 */
window.downloadJson = function(payload) {
  try {
    const json = JSON.stringify(payload, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    chrome.downloads.download({
      url,
      filename: `tabs_export_${payload.timestamp.replace(/[:.]/g, '-')}.json`
    });
  } catch (error) {
    console.error('Ошибка при создании и загрузке JSON:', error);
  }
};
