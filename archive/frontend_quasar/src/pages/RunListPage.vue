<template>
  <q-page class="flex justify-center">
    <RunList class="q-pa-lg tw-w-full" />
  </q-page>
</template>

<script lang="ts">

import RunList from 'components/RunList.vue';

export default {
  name: 'RunListPage',

  components: {
    RunList
  },

  props: {
  },

};

</script>


