<template>
  <q-page class="flex justify-center">
    <ScenarioExperimentList :uuid="uuid" class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import ScenarioExperimentList from 'components/ScenarioExperimentList.vue';

export default {
  name: 'ScenarioExperimentPage',

  props: {
    uuid: {
      type: String,
      required: true
    }
  },


  components: {
    ScenarioExperimentList
  },

};

</script>
