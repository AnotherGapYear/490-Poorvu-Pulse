import {defineStore} from 'pinia';
import {ref, watch} from 'vue';
import {db} from '@/db';
import type {Settings} from '@/models/settings.model';

export const useSettingsStore = defineStore('settings', () => {
  const DEFAULT_TEMP = '0.5';
  const DEFAULT_MODEL = 'gemini-1.5-pro';
  const DEFAULT_MAX_TOKENS = '20000';

  const areSettingsVisible = ref(false);

  const apiKey = ref<string>('');
  const temp = ref<string>('');
  const model = ref<string>('');
  const maxTokens = ref<string>('');
  const dbReloadCount = ref(0);

  function showSettings() {
    areSettingsVisible.value = true;
  }

  function hideSettings() {
    areSettingsVisible.value = false;
  }

  async function reloadSettings(i = 1) {
    try {
      const settings = await db.settings.get(1);
      if (!settings) {
        if (i > 1) {
          throw new Error('Endless loop while creating settings DB');
        }
        await db.settings.add({
          apiKey: '',
          temp: DEFAULT_TEMP,
          model: DEFAULT_MODEL,
          maxTokens: DEFAULT_MAX_TOKENS
        });
        i++;
        await reloadSettings(i);
      } else {
        apiKey.value = settings.apiKey;
        temp.value = settings.temp;
        model.value = settings.model;
        maxTokens.value = settings.maxTokens;
        dbReloadCount.value++;
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function updateSettings(form: Settings) {
    try {
      await db.settings.update(1, {
        apiKey: form.apiKey,
        temp: form.temp,
        model: form.model,
        maxTokens: form.maxTokens
      });
    } catch (e) {
      console.error(e);
    }
  }

  watch(areSettingsVisible, async (newValue, oldValue) => {
    if (oldValue === true && newValue === false) {
      await reloadSettings();
    }
  });

  return {
    areSettingsVisible,
    apiKey,
    temp,
    model,
    maxTokens,
    dbReloadCount,
    showSettings,
    hideSettings,
    reloadSettings,
    updateSettings
  };
});
