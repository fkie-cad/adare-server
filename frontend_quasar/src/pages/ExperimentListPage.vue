<template>
  <q-page class="flex justify-center">
    <ExperimentList :scenario="scenario" class="q-pa-lg tw-w-full" />
  </q-page>
</template>

<script lang="ts">
import ExperimentList from 'components/ExperimentList.vue';

export default {
  name: 'ExperimentListPage',

  components: {
    ExperimentList
  },

  props: {
    scenario: {
      type: String,
      required: false,
    },
  },

};

</script>
