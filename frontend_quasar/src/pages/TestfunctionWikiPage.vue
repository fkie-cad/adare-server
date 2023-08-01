<template>
  <q-page class="row items-center justify-evenly">
    <TestfunctionWiki/>
  </q-page>
</template>

<script lang="ts">
import TestfunctionWiki from 'components/TestfunctionWiki.vue';

export default {
  name: 'IndexPage',

  components: {
    TestfunctionWiki,
  },

};

</script>
