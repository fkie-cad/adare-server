<template>
  <q-page class="flex justify-center">
    <RequestList class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import RequestList from 'components/RequestList.vue';

export default {
  name: 'RequestsListPage',
  components: {RequestList},

};

</script>
