<template>
  <q-page class="flex justify-center">
    <RunDetail :ulid="ulid" class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">

import RunDetail from 'components/RunDetail.vue';

export default {
  name: 'RunDetailsPage',

  components: {
    RunDetail

  },

  props: {
    ulid: {
      type: String,
      required: true,
    },
  },

};

</script>
