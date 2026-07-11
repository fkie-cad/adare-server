<template>
  <q-page class="flex justify-center">
    <ScenarioList class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import ScenarioList from 'components/ScenarioList.vue';

export default {
  name: 'IndexPage',

  components: {
    ScenarioList
  },

};

</script>
