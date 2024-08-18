<template>
  <q-page class="flex justify-center">
    <TestfunctionSetList class="q-pa-lg tw-w-full" />
  </q-page>
</template>

<script lang="ts">
import TestfunctionSetList from 'components/TestfunctionSetList.vue';

export default {
  name: 'TestfunctionsetListPage',

  components: {
    TestfunctionSetList,
  },

  props: {
  },

};

</script>


