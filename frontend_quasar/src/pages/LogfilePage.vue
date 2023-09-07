<template>
  <q-page class="row items-center justify-evenly">
    <LogFile :experimentrunuuid="experimentrunuuid"/>
  </q-page>
</template>


<script lang="ts">
import LogFile from 'components/LogFile.vue';

export default {
  name: 'LoginPage',

  props: {
    experimentrunuuid: {
      type: String,
      required: true,
    },
  },

  components: {
    LogFile,
  },



};
</script>
