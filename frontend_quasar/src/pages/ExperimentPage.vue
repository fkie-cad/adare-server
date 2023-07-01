<template>
  <q-page class="row items-center justify-evenly">
    <ExperimentList/>
  </q-page>
</template>

<script lang="ts">
import ExperimentList from 'components/ExperimentList.vue';

export default {
  name: 'ExperimentPage',

  components: {
    ExperimentList
  },

};

</script>
