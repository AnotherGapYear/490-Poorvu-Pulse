<script setup lang="ts">
  import {FwbButton, FwbModal} from 'flowbite-vue';
  import {useAppStore} from '@/stores/app.store';

  const appStore = useAppStore();
</script>

<template>
  <fwb-modal v-if="appStore.isAboutVisible" @close="appStore.hideAbout()" not-escapable persistent>
    <template #header>
      <div class="text-lg">About</div>
    </template>
    <template #body>
      <div class="flex">
        <div class="ml-5">Poorvu Pulse is a thesis project developed for the Yale Writing Center, a division of the Poorvu Center for Teaching and Learning. This AI-powered tool analyzes student feedback from writing consultations to provide meaningful insights about Writing Center services. By leveraging semantic search technology, Poorvu Pulse matches user queries with relevant student experiences, helping Writing Partners and administrators, better understand consultation effectiveness and areas for improvement. All feedback is anonymized to maintain privacy while offering valuable patterns and insights that can enhance the Writing Center's mission of supporting Yale students in their writing journey.</div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end">
        <fwb-button @click="appStore.hideAbout()" color="alternative" class="rounded ml-2">Close</fwb-button>
      </div>
    </template>
  </fwb-modal>
</template>

<style scoped>
  /* img {
    width: 110px;
  } */
</style>
