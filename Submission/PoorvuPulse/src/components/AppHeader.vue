<script setup lang="ts">
  import {useAppStore} from '@/stores/app.store';
  import {Bars3Icon} from '@heroicons/vue/24/outline';
  import {Cog6ToothIcon} from '@heroicons/vue/24/outline';
  import {QuestionMarkCircleIcon} from '@heroicons/vue/24/outline';
  import {useSettingsStore} from '@/stores/settings.store';

  const appStore = useAppStore();
  const settingsStore = useSettingsStore();
</script>

<template>
  <div class="p-2 bg-gray-700 flex justify-between">
    <div title="Toggle sidebar"><Bars3Icon class="h-6 w-6 text-white cursor-pointer hover:text-blue-400" @click="appStore.toggleSidebar()"></Bars3Icon></div>
    <div class="flex">
      <div title="Show settings"><Cog6ToothIcon class="h-6 w-6 text-white cursor-pointer hover:text-blue-400" @click="settingsStore.showSettings()"></Cog6ToothIcon></div>
      <div title="About" class="ml-2"><QuestionMarkCircleIcon class="h-6 w-6 text-white cursor-pointer hover:text-blue-400" @click="appStore.showAbout()"></QuestionMarkCircleIcon></div>
    </div>
  </div>
</template>
