<template>
  <q-page class="flex justify-center">
    <EnvironmentOverview :name="name" class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import EnvironmentOverview from 'components/EnvironmentOverview.vue';

export default {
  name: 'EnvironmentPage',

  components: {
    EnvironmentOverview,
  },

  props: {
    name: {
      type: String,
      required: true,
    },
  },
};
</script>
