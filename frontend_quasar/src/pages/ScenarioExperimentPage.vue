<template>
  <q-page class="row items-center justify-evenly">
    <ScenarioExperimentList :uuid="uuid"/>
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
