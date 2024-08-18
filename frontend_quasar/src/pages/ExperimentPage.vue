<template>
  <q-page class="flex justify-center">
    <ExperimentOverview :ulid="ulid" class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import ExperimentOverview from 'components/ExperimentOverview.vue';

export default {
  name: 'ExperimentPage',

  components: {
    ExperimentOverview
  },

  props: {
    ulid: {
      type: String,
      required: true,
    },
  },

};

</script>
