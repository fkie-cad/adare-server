<template>
  <q-page class="flex justify-center">
    <EnvironmentList class="q-pa-lg tw-w-full"/>
  </q-page>
</template>

<script lang="ts">
import EnvironmentList from 'components/EnvironmentList.vue';

export default {
  name: 'EnvironmentListPage',

  components: {
    EnvironmentList,
  },

  props: {
  },

};

</script>


